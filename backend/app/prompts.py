"""
Prompt templates for question generation.
Database is the source of truth.
"""

from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

from app.models import GeoGebra, QuestionPrompt


class AppletType(str, Enum):
    """GeoGebra applet types."""
    GRAPHING = "graphing"
    GEOMETRY = "geometry"
    THREE_D = "3d"
    CLASSIC = "classic"
    CAS = "cas"
    SCIENTIFIC = "scientific"


# Default applet type
DEFAULT_APPLET_TYPE = AppletType.GRAPHING


def load_prompt_template(db: Session, question_type: str) -> str:
    """Load prompt template from the database.

    Args:
        db: Database session
        question_type: The type of question (multiple_choice, open_ended, geogebra_diagram, etc.)

    Returns:
        The prompt template string

    Raises:
        ValueError: If the prompt template is not found in the database.
    """
    prompt = db.query(QuestionPrompt).filter(QuestionPrompt.name == question_type).first()
    if prompt:
        return prompt.content
    raise ValueError(f"Prompt template '{question_type}' not found in database")


def get_applet_commands(db: Session, applet_type: AppletType) -> str:
    """Get available commands for a specific applet type from database.

    Args:
        db: Database session
        applet_type: The GeoGebra applet type

    Returns:
        String listing available commands for that applet

    Raises:
        ValueError: If the applet type is not found in the database.
    """
    geogebra = db.query(GeoGebra).filter(GeoGebra.applet_type == applet_type.value).first()
    if geogebra and geogebra.valid_command_template:
        # Convert array to formatted string with dashes
        return "\n".join(f"- {cmd}" for cmd in geogebra.valid_command_template)
    raise ValueError(f"GeoGebra commands for applet type '{applet_type.value}' not found in database")


def _get_answer_field(question_type: str) -> str:
    """Get the answer field JSON snippet based on question type."""
    if question_type == "multiple_choice":
        return '"options": ["option A", "option B", "option C", "option D"],\n    "answer": "the correct option text",'
    return '"answer": "the correct answer",'


def _get_question_requirements(question_type: str) -> str:
    """Get question-specific requirements text."""
    if question_type == "multiple_choice":
        return "- Provide exactly 4 multiple choice options (A, B, C, D)\n- Only one option should be correct\n- Distractors should be plausible but clearly wrong"
    return ""


def format_prompt(
    db: Session,
    question_type: str,
    grade_level: str,
    standard_code: str,
    standard_description: str,
    difficulty: float,
    keywords: str,
    requires_diagram: bool = False,
    applet_type: Optional[AppletType] = None,
) -> str:
    """Format a prompt template with the given parameters.

    Args:
        db: Database session
        question_type: Type of question (multiple_choice, open_ended, geogebra_diagram)
        grade_level: The grade level (e.g., "6", "7", "8")
        standard_code: Standard code (e.g., "6.EE.A.1")
        standard_description: Description of the standard
        difficulty: Difficulty level 0.0-1.0
        keywords: Comma-separated keywords
        requires_diagram: Whether this question needs a GeoGebra diagram
        applet_type: GeoGebra applet type if requires_diagram is True

    Returns:
        Formatted prompt string ready for LLM
    """
    # Pre-compute formatted question type (used in both branches)
    formatted_question_type = question_type.replace("_", " ")

    # If requires_diagram, use the geogebra_diagram template
    if requires_diagram and question_type in ["multiple_choice", "open_ended"]:
        template = load_prompt_template(db, "geogebra_diagram")
        applet = applet_type or DEFAULT_APPLET_TYPE
        applet_commands = get_applet_commands(db, applet)

        return template.format(
            question_type=formatted_question_type,
            grade_level=grade_level,
            standard_code=standard_code,
            standard_description=standard_description,
            difficulty=difficulty,
            keywords=keywords,
            applet_type=applet.value,
            applet_commands=applet_commands,
            question_specific_requirements=_get_question_requirements(question_type),
            answer_field=_get_answer_field(question_type),
        )

    # Standard template for non-diagram questions
    template = load_prompt_template(db, question_type)
    return template.format(
        question_type=formatted_question_type,
        grade_level=grade_level,
        standard_code=standard_code,
        standard_description=standard_description,
        difficulty=difficulty,
        keywords=keywords,
    )


__all__ = [
    'AppletType',
    'DEFAULT_APPLET_TYPE',
    'load_prompt_template',
    'get_applet_commands',
    'format_prompt',
]
