import logging
import math
import random
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Question,
    Standard,
    StudentDomainAbility,
    AnsweredQuestion,
)

logger = logging.getLogger(__name__)

# ELO-like learning rate
K = 0.15


def get_or_create_ability(db: Session, student_id: int, domain_id: int) -> StudentDomainAbility:
    """Get existing ability record or create one with default theta."""
    ability = (
        db.query(StudentDomainAbility)
        .filter(
            StudentDomainAbility.student_id == student_id,
            StudentDomainAbility.domain_id == domain_id,
        )
        .first()
    )
    if not ability:
        # Find the lowest difficulty_base among standards in this domain to set a reasonable starting theta
        avg_difficulty = (
            db.query(func.avg(Standard.difficulty_base))
            .filter(Standard.domain_id == domain_id)
            .scalar()
        )
        starting_theta = float(avg_difficulty) if avg_difficulty is not None else 0.35

        ability = StudentDomainAbility(
            student_id=student_id,
            domain_id=domain_id,
            theta=max(0.0, min(1.0, round(starting_theta - 0.05, 3))),
        )
        db.add(ability)
        db.commit()
        db.refresh(ability)
    return ability


def get_next_adaptive_question(
    db: Session,
    student_id: int,
    domain_id: int,
) -> Optional[Question]:
    """Select the best un-answered question for a student in a given domain.

    Picks the active question whose difficulty is closest to the student's theta
    and which the student has not yet answered. Top 5 candidates are fetched, and
    a random choice adds variety so the student doesn't see the exact same pattern.
    """
    ability = get_or_create_ability(db, student_id, domain_id)
    theta = float(ability.theta)

    # IDs of questions this student has already answered
    answered_subq = (
        db.query(AnsweredQuestion.question_id)
        .filter(AnsweredQuestion.student_id == student_id)
        .subquery()
    )

    # Fetch top 5 candidates ordered by |difficulty - theta|
    candidates = (
        db.query(Question)
        .join(Standard, Question.standard_id == Standard.id)
        .filter(
            Standard.domain_id == domain_id,
            Question.is_active == True,
            Question.question_type == "multiple_choice",
            ~Question.id.in_(answered_subq),
        )
        .order_by(func.abs(Question.difficulty - theta))
        .limit(10)
        .all()
    )

    if candidates:
        # Add a pinch of randomness: pick among top 5 closest
        top_n = min(5, len(candidates))
        return random.choice(candidates[:top_n])

    # Fallback: any active question in this domain, even if answered before
    fallback = (
        db.query(Question)
        .join(Standard, Question.standard_id == Standard.id)
        .filter(
            Standard.domain_id == domain_id,
            Question.is_active == True,
            Question.question_type == "multiple_choice",
        )
        .order_by(func.random())
        .first()
    )
    return fallback


def update_theta_after_answer(
    db: Session,
    student_id: int,
    domain_id: int,
    question_id: int,
    is_correct: bool,
) -> dict:
    """Recalculate student ability (theta) after answering a question.

    Uses an ELO-like update where the difficulty of the question acts as the opponent rating.
    """
    ability = get_or_create_ability(db, student_id, domain_id)
    theta = float(ability.theta)

    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        logger.warning(f"Question {question_id} not found; skipping theta update")
        return {"theta": theta, "updated": False}

    b = float(question.difficulty) if question.difficulty is not None else 0.5

    # Predicted probability of success
    predicted = 1.0 / (1.0 + math.exp(-(theta - b)))

    if is_correct:
        theta_new = theta + K * (1.0 - predicted)
        ability.correct_streak += 1
    else:
        theta_new = theta - K * predicted
        ability.correct_streak = 0

    # Clamp to [0.0, 1.0]
    ability.theta = max(0.0, min(1.0, round(theta_new, 3)))
    ability.questions_attempted += 1
    ability.updated_at = func.now()

    db.commit()
    db.refresh(ability)

    return {
        "theta": float(ability.theta),
        "previous_theta": round(theta, 3),
        "question_difficulty": b,
        "predicted_success": round(predicted, 3),
        "updated": True,
    }
