import json
import logging
import re
import time
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Standard
from app.prompts import format_prompt, AppletType

logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 3
BASE_TEMPERATURE = 0.7
TEMPERATURE_INCREMENT = 0.2
BACKOFF_BASE = 2

# Pre-compile regex for option cleaning
_OPTION_LABEL_PATTERN = re.compile(r'^[A-Da-d][\.)\s\-]+\s*')

# Default GeoGebra commands for common standards
DEFAULT_GEOGEBRA_COMMANDS = {
    "6.NS.5": ["A = (-4, 0)", "B = (4, 0)", "SetCoordSystem(-10, 10, -2, 2)", "SetAxesVisible(true, false)", "SetGridVisible(true)"],
    "6.NS.6": ["P = (3, 2)", "SetCoordSystem(-5, 5, -5, 5)", "SetAxesVisible(true, true)", "SetGridVisible(true)"],
    "6.NS.7": ["A = (-5, 0)", "B = (-2, 0)", "C = (1, 0)", "D = (4, 0)", "SetCoordSystem(-8, 8, -2, 2)", "SetAxesVisible(true, false)"],
    "6.NS.8": ["A = (-4, 3)", "B = (5, 3)", "Segment(A, B)", "SetCoordSystem(-8, 8, -2, 8)", "SetAxesVisible(true, true)", "SetGridVisible(true)"],
    "6.G.1": ["A = (0, 0)", "B = (4, 0)", "C = (2, 3)", "Triangle(A, B, C)", "SetCoordSystem(-1, 5, -1, 4)", "SetAxesVisible(false, false)"],
    "6.G.2": ["A = (0, 0)", "B = (4, 0)", "C = (4, 3)", "D = (0, 3)", "Polygon(A, B, C, D)", "SetFixed(A, true, false)", "SetFixed(B, true, false)", "SetFixed(C, true, false)", "SetFixed(D, true, false)", "SetCoordSystem(-1, 5, -1, 4)"],
    "6.G.3": ["A = (0, 0)", "B = (3, 0)", "C = (3, 2)", "D = (0, 2)", "Polygon(A, B, C, D)", "E = (1.5, 1)", "Point(E)", "SetCoordSystem(-2, 5, -2, 4)"],
    "6.G.4": ["A = (0, 0)", "B = (4, 0)", "C = (4, 3)", "D = (0, 3)", "Polygon(A, B, C, D)", "SetCoordSystem(-1, 5, -1, 4)"],
    "6.SP.4": ["A = (1, 2)", "B = (2, 4)", "C = (3, 3)", "D = (4, 5)", "E = (5, 2)", "List1 = {A, B, C, D, E}", "DotPlot(List1)", "SetCoordSystem(0, 6, 0, 6)"],
    "6.SP.5": ["A = (1, 2)", "B = (2, 5)", "C = (3, 3)", "D = (4, 7)", "E = (5, 4)", "List1 = {A, B, C, D, E}", "BoxPlot(List1)", "SetCoordSystem(0, 6, 0, 8)"],
}


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
    """Service for generating questions using Ollama."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.ollama_url = f"{self.settings.OLLAMA_URL}/api/generate"

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
        model: Optional[str] = None
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
                response = httpx.post(
                    self.ollama_url,
                    json=payload,
                    timeout=self.settings.OLLAMA_TIMEOUT
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

                # Handle GeoGebra commands for diagram questions
                if standard.requires_diagram:
                    if not question_data.get("geogebra_commands"):
                        # Use default commands for this standard if available
                        default_commands = DEFAULT_GEOGEBRA_COMMANDS.get(standard.code)
                        if default_commands:
                            logger.info(f"Using default GeoGebra commands for {standard.code}")
                            question_data["geogebra_commands"] = default_commands
                        else:
                            logger.warning(f"No GeoGebra commands generated for diagram question {standard.code}")
                            question_data["geogebra_commands"] = []

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
                raise TimeoutError(f"Ollama request timed out after {self.settings.OLLAMA_TIMEOUT} seconds")
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
                raise RuntimeError(f"Ollama error: {e.response.text}")
            except Exception as e:
                logger.error(f"Unexpected error calling Ollama: {e}")
                raise

        # All retries exhausted
        logger.error(f"Failed to generate valid question after {MAX_RETRIES} attempts: {last_error}")
        raise RuntimeError(f"Failed to generate valid question after {MAX_RETRIES} attempts. Last error: {last_error}")
