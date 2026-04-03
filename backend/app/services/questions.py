import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Standard

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class QuestionService:
    """Service for generating questions using Ollama."""

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.ollama_url = f"{self.settings.OLLAMA_URL}/api/generate"

    def _load_prompt_template(self, question_type: str) -> str:
        """Load prompt template from file."""
        template_file = PROMPTS_DIR / f"{question_type}.txt"
        if not template_file.exists():
            template_file = PROMPTS_DIR / "open_ended.txt"
        return template_file.read_text()

    def _build_prompt(
        self,
        standard: Standard,
        difficulty: float,
        question_type: str
    ) -> str:
        """Build a prompt for question generation."""
        keywords = ", ".join(standard.keywords) if standard.keywords else "related concepts"

        template = self._load_prompt_template(question_type)

        return template.format(
            question_type=question_type,
            grade_level=standard.grade.level if standard.grade else "appropriate",
            standard_code=standard.code,
            standard_description=standard.description,
            difficulty=difficulty,
            keywords=keywords
        )

    def generate_question(
        self,
        standard_id: int,
        difficulty: Optional[float] = None,
        question_type: str = "multiple_choice",
        custom_prompt: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a question using Ollama."""

        # Fetch standard from database
        standard = self.db.query(Standard).filter(Standard.id == standard_id).first()
        if not standard:
            raise ValueError(f"Standard with ID {standard_id} not found")

        # Use standard's difficulty if not overridden
        actual_difficulty = difficulty if difficulty is not None else (
            float(standard.difficulty_base) if standard.difficulty_base else 0.5
        )

        # Build or use custom prompt
        prompt = custom_prompt if custom_prompt else self._build_prompt(
            standard, actual_difficulty, question_type
        )

        # Use provided model or default from settings
        ollama_model = model if model else self.settings.OLLAMA_MODEL

        logger.info(f"Generating {question_type} question for standard {standard.code}")

        # Prepare Ollama request
        payload = {
            "model": ollama_model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.7
            }
        }

        try:
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
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON response: {generated_text}")
                # Fallback: wrap the response
                question_data = {
                    "question": generated_text,
                    "answer": "See explanation",
                    "explanation": generated_text
                }

            # Add metadata
            question_data["standard_code"] = standard.code
            question_data["difficulty"] = actual_difficulty
            question_data["question_type"] = question_type

            return question_data

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
