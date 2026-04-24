import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.models import AnsweredQuestion, Standard

logger = logging.getLogger(__name__)


class StudentService:
    """Service for student self-service operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_progress_summary(self, student_id: int) -> dict:
        """Get a student's progress summary from answered_questions."""
        # Total answered and correct count
        total_result = self.db.query(
            func.count(AnsweredQuestion.id).label("total"),
            func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct")
        ).filter(AnsweredQuestion.student_id == student_id).first()

        total_answered = total_result.total or 0
        correct_count = total_result.correct or 0 if total_result.total else 0
        accuracy = correct_count / total_answered if total_answered > 0 else None

        # Unique standards attempted
        standards_result = self.db.query(
            func.count(func.distinct(AnsweredQuestion.standard_id)).label("count")
        ).filter(AnsweredQuestion.student_id == student_id).first()
        standards_attempted = standards_result.count or 0

        # Recent answers (last 20)
        recent = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).order_by(AnsweredQuestion.answered_at.desc()).limit(20).all()

        recent_answers = []
        for answer in recent:
            standard = self.db.query(Standard).filter(Standard.id == answer.standard_id).first()
            recent_answers.append({
                "question_id": answer.question_id,
                "standard_code": standard.code if standard else "Unknown",
                "is_correct": answer.is_correct,
                "answered_at": answer.answered_at,
            })

        return {
            "total_answered": total_answered,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "standards_attempted": standards_attempted,
            "recent_answers": recent_answers,
        }

    def get_answer_history(self, student_id: int) -> dict:
        """Get a student's full answer history."""
        return self.get_progress_summary(student_id)
