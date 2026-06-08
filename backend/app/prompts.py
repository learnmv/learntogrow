"""Prompt templates for text-based question generation."""

from sqlalchemy.orm import Session

from app.models import QuestionPrompt


def load_prompt_template(db: Session, question_type: str) -> str:
    """Load prompt template from the database.

    Args:
        db: Database session
        question_type: The type of question (multiple_choice, open_ended, etc.)

    Returns:
        The prompt template string

    Raises:
        ValueError: If the prompt template is not found in the database.
    """
    prompt = db.query(QuestionPrompt).filter(QuestionPrompt.name == question_type).first()
    if prompt:
        return prompt.content
    raise ValueError(f"Prompt template '{question_type}' not found in database")


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
) -> str:
    """Format a prompt template with the given parameters.

    Args:
        db: Database session
        question_type: Type of question (multiple_choice, open_ended)
        grade_level: The grade level (e.g., "6", "7", "8")
        standard_code: Standard code (e.g., "6.EE.A.1")
        standard_description: Description of the standard
        difficulty: Difficulty level 0.0-1.0
        keywords: Comma-separated keywords
    Returns:
        Formatted prompt string ready for LLM
    """
    formatted_question_type = question_type.replace("_", " ")
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
    'load_prompt_template',
    'format_prompt',
]
