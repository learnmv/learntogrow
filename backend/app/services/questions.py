import json
import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Standard, Question, AnsweredQuestion, DomainProgress, Domain
from app.prompts import format_prompt, AppletType

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_TEMPERATURE = 0.7
TEMPERATURE_INCREMENT = 0.2
BACKOFF_BASE = 2

# Pre-compile regex for option cleaning
_OPTION_LABEL_PATTERN = re.compile(r'^[A-Da-d][\.)\s\-]+\s*')

def validate_question_data(data: dict, standard_code: str) -> dict:
    """Validate and clean question data from LLM.

    Raises:
        ValueError: If question data is invalid or incomplete.
    """
    errors = []

    # Check required fields exist
    if not data.get("question"):
        errors.append("Question text is missing")
    elif len(data["question"].strip()) < 10:
        errors.append(f"Question text too short: '{data['question']}'")
    elif "..." in data["question"] or data["question"].count("?") > 1:
        errors.append(f"Question appears incomplete: '{data['question']}'")

    # Check for placeholder text
    question_lower = data.get("question", "").lower()
    if "when and" in question_lower and "=" not in question_lower:
        errors.append("Question has missing variable values (e.g., 'when and')")

    # Validate multiple choice options
    if data.get("question_type") == "multiple_choice" or "options" in data:
        options = data.get("options", [])
        if not isinstance(options, list):
            errors.append("Options must be a list")
        elif len(options) != 4:
            errors.append(f"Expected 4 options, got {len(options)}")
        else:
            # Check each option has content
            for i, opt in enumerate(options):
                if not opt or len(str(opt).strip()) < 1:
                    errors.append(f"Option {chr(65+i)} is empty")
                elif str(opt).strip() in ["A", "B", "C", "D"]:
                    errors.append(f"Option {chr(65+i)} is just a letter label")

    # Validate GeoGebra commands for diagram questions
    if data.get("requires_diagram"):
        commands = data.get("geogebra_commands")
        if not commands or not isinstance(commands, list) or len(commands) == 0:
            errors.append("GeoGebra commands are required for diagram questions but were missing or empty")
        elif not all(isinstance(cmd, str) and cmd.strip() for cmd in commands):
            errors.append("GeoGebra commands must be a list of non-empty strings")

    # Check answer exists
    if not data.get("answer"):
        errors.append("Answer is missing")

    if errors:
        raise ValueError(f"Invalid question data: {'; '.join(errors)}")

    return data


def clean_option_text(option: str) -> str:
    """Clean option text by removing duplicate letter labels."""
    if not option:
        return option
    # Remove leading patterns like "A)", "B)", "A.", "B.", "A -", "B -"
    return _OPTION_LABEL_PATTERN.sub('', str(option).strip())


class QuestionService:
    """Service for generating and fetching questions."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.ollama_url = f"{self.settings.OLLAMA_URL}/api/generate"

    def get_questions_by_standard(
        self,
        standard_id: int,
        limit: Optional[int] = None,
        student_id: Optional[int] = None
    ) -> List[Question]:
        """Fetch active questions for a specific standard.

        If student_id is provided, exclude questions the student has already answered.
        """
        query = self.db.query(Question).filter(
            Question.standard_id == standard_id,
            Question.is_active == True
        )

        # Exclude already-answered questions for this student
        if student_id is not None:
            answered_ids = self.db.query(AnsweredQuestion.question_id).filter(
                AnsweredQuestion.student_id == student_id
            ).subquery()
            query = query.filter(Question.id.notin_(answered_ids))

        if limit:
            query = query.limit(limit)
        return query.all()

    def _build_prompt(
        self,
        standard: Standard,
        difficulty: float,
        question_type: str
    ) -> str:
        """Build a prompt for question generation."""
        keywords = ", ".join(standard.keywords) if standard.keywords else "related concepts"
        grade_level = standard.grade.level if standard.grade else "appropriate"

        # Convert applet_type string to enum if present
        applet_type = None
        if standard.applet_type:
            try:
                applet_type = AppletType(standard.applet_type)
            except ValueError:
                applet_type = None

        # Use the new format_prompt function that handles GeoGebra diagrams
        return format_prompt(
            db=self.db,
            question_type=question_type,
            grade_level=str(grade_level),
            standard_code=standard.code,
            standard_description=standard.description,
            difficulty=difficulty,
            keywords=keywords,
            requires_diagram=standard.requires_diagram,
            applet_type=applet_type,
        )

    def generate_question(
        self,
        standard_id: int,
        difficulty: Optional[float] = None,
        question_type: str = "multiple_choice",
        custom_prompt: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a question using Ollama with validation and retry logic."""

        # Fetch standard from database
        standard = self.db.query(Standard).filter(Standard.id == standard_id).first()
        if not standard:
            raise ValueError(f"Standard with ID {standard_id} not found")

        # Use standard's difficulty if not overridden
        actual_difficulty = difficulty if difficulty is not None else (
            float(standard.difficulty_base) if standard.difficulty_base else 0.5
        )

        # Use provided model or default from settings
        ollama_model = model if model else self.settings.OLLAMA_MODEL

        logger.info(f"Generating {question_type} question for standard {standard.code}")

        # Build prompt (only once, reuse for retries)
        prompt = custom_prompt if custom_prompt else self._build_prompt(
            standard, actual_difficulty, question_type
        )

        # Try up to 3 times with increasing temperature for variety
        last_error = None

        for attempt in range(MAX_RETRIES):
            try:
                # Adjust temperature for retries (higher = more creative)
                temperature = BASE_TEMPERATURE + (attempt * TEMPERATURE_INCREMENT)

                # Prepare Ollama request
                payload = {
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "temperature": temperature
                    }
                }

                # Call Ollama API
                actual_timeout = timeout if timeout is not None else self.settings.OLLAMA_TIMEOUT
                response = httpx.post(
                    self.ollama_url,
                    json=payload,
                    timeout=actual_timeout
                )
                response.raise_for_status()

                result = response.json()
                generated_text = result.get("response", "")

                # Parse the generated JSON
                try:
                    question_data = json.loads(generated_text)
                except json.JSONDecodeError as e:
                    logger.warning(f"Attempt {attempt + 1}: Failed to parse JSON: {e}")
                    last_error = e
                    continue

                # Add metadata
                question_data["standard_code"] = standard.code
                question_data["difficulty"] = actual_difficulty
                question_data["question_type"] = question_type
                question_data["requires_diagram"] = standard.requires_diagram
                question_data["applet_type"] = standard.applet_type

                # Clean option text to remove duplicate labels
                if "options" in question_data and isinstance(question_data["options"], list):
                    question_data["options"] = [clean_option_text(opt) for opt in question_data["options"]]

                # Validate the question data
                validate_question_data(question_data, standard.code)

                # Handle GeoGebra commands for diagram questions — no fallback.
                if standard.requires_diagram:
                    if not question_data.get("geogebra_commands"):
                        raise ValueError(
                            f"Diagram question for {standard.code} is missing required geogebra_commands"
                        )

                    # Ensure applet_config exists
                    if "applet_config" not in question_data:
                        question_data["applet_config"] = {
                            "width": 800,
                            "height": 500,
                            "showToolBar": False,
                            "showAlgebraInput": False,
                            "showMenuBar": False,
                            "showAlgebraView": False
                        }

                logger.info(f"Successfully generated question for {standard.code} on attempt {attempt + 1}")
                return question_data

            except ValueError as e:
                logger.warning(f"Attempt {attempt + 1}: Validation failed: {e}")
                last_error = e
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_BASE ** attempt)
                continue
            except httpx.ConnectError as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                raise ConnectionError(f"Could not connect to Ollama at {self.settings.OLLAMA_URL}. Is Ollama running?")
            except httpx.TimeoutException:
                logger.error("Ollama request timed out")
                raise TimeoutError(f"Ollama request timed out after {actual_timeout} seconds")
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"Ollama error: {e.response.text}")
            except Exception as e:
                logger.error(f"Unexpected error calling Ollama: {e}")
                raise

        # All retries exhausted
        logger.error(f"Failed to generate valid question after {MAX_RETRIES} attempts: {last_error}")
        raise RuntimeError(f"Failed to generate valid question after {MAX_RETRIES} attempts. Last error: {last_error}")

    def get_adaptive_question(
        self,
        student_id: int,
        grade_id: int,
        student_service=None
    ) -> Optional[Question]:
        """Get an adaptively-selected question based on student performance.

        Algorithm:
        1. Calculate priority for each domain (weak domains = higher priority)
        2. Try to find a question at the student's current difficulty level
        3. Fall back to any unanswered question for the grade
        """
        from app.services.student import StudentService
        if student_service is None:
            student_service = StudentService(self.db)

        # Get domain progress for this student
        domain_progress_list = student_service.get_domain_progress(student_id)

        # Get all domains for this grade
        domains = self.db.query(Domain).join(Standard).filter(
            Standard.grade_id == grade_id
        ).distinct().all()

        # Build priority map: lower accuracy -> higher priority
        domain_priorities = {}
        domain_difficulties = {}

        for dp in domain_progress_list:
            domain_priorities[dp["domain_id"]] = float(dp["accuracy"])
            domain_difficulties[dp["domain_id"]] = float(dp["current_difficulty"])

        # For domains with no progress, give medium priority (0.5) so they're still eligible
        for domain in domains:
            if domain.id not in domain_priorities:
                domain_priorities[domain.id] = 0.5
                domain_difficulties[domain.id] = 0.5

        # Sort domains by priority (ascending accuracy = highest priority first)
        sorted_domains = sorted(domain_priorities.keys(), key=lambda d: domain_priorities[d])

        # Get answered question IDs for this student
        answered_ids = self.db.query(AnsweredQuestion.question_id).filter(
            AnsweredQuestion.student_id == student_id
        ).subquery()

        # Try each domain in priority order
        for domain_id in sorted_domains:
            # Get standards in this domain for this grade
            standards = self.db.query(Standard).filter(
                Standard.grade_id == grade_id,
                Standard.domain_id == domain_id
            ).all()

            if not standards:
                continue

            standard_ids = [s.id for s in standards]
            target_difficulty = domain_difficulties.get(domain_id, 0.5)

            # Try to find a question near the target difficulty, unanswered
            question = self.db.query(Question).filter(
                Question.standard_id.in_(standard_ids),
                Question.is_active == True,
                Question.difficulty.between(target_difficulty - 0.15, target_difficulty + 0.15),
                Question.id.notin_(answered_ids)
            ).order_by(func.random()).first()

            if question:
                return question

        # Fallback: any unanswered question for this grade
        standards = self.db.query(Standard).filter(Standard.grade_id == grade_id).all()
        standard_ids = [s.id for s in standards]

        if standard_ids:
            question = self.db.query(Question).filter(
                Question.standard_id.in_(standard_ids),
                Question.is_active == True,
                Question.id.notin_(answered_ids)
            ).order_by(func.random()).first()
            return question

        return None
