import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.models import AnsweredQuestion, Standard, Domain

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

        return {
            "total_answered": total_answered,
            "correct_count": correct_count,
            "accuracy": accuracy,
            "standards_attempted": standards_attempted,
        }

    def get_mistake_standards(self, student_id: int, subject_id: Optional[int] = None, grade_id: Optional[int] = None) -> List[dict]:
        """Get unique standards where the student answered incorrectly."""
        # Get distinct standard_ids of wrong answers
        wrong_standard_ids = self.db.query(
            func.distinct(AnsweredQuestion.standard_id).label("standard_id")
        ).filter(
            AnsweredQuestion.student_id == student_id,
            AnsweredQuestion.is_correct == False
        ).subquery()

        # Fetch full Standard records, optionally filtered by subject/grade
        query = self.db.query(Standard).filter(Standard.id.in_(wrong_standard_ids))

        if grade_id is not None:
            query = query.filter(Standard.grade_id == grade_id)

        if subject_id is not None:
            query = query.join(Domain).filter(Domain.subject_id == subject_id)

        standards = query.order_by(Standard.grade_id, Standard.domain_id, Standard.code).all()

        return [
            {
                "id": s.id,
                "code": s.code,
                "description": s.description,
                "grade_id": s.grade_id,
                "domain_id": s.domain_id,
                "difficulty_base": float(s.difficulty_base) if s.difficulty_base else None,
                "keywords": s.keywords.split(",") if s.keywords else [],
            }
            for s in standards
        ]
