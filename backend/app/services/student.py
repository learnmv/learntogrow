import logging
from datetime import datetime, time, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.models import AnsweredQuestion, Standard, Domain, Question, StudentDomainAbility

logger = logging.getLogger(__name__)


def get_skill_level(theta: float, questions_attempted: int) -> tuple[str, str, float]:
    """Convert internal ability into student-facing level text."""
    if questions_attempted <= 0:
        return "Getting Started", "Start with a few warm-up questions.", 0.0

    progress = max(0.0, min(1.0, theta))
    if progress < 0.26:
        return "Getting Started", "Start with a few warm-up questions.", progress
    if progress < 0.46:
        return "Building", "You are getting familiar with this skill.", progress
    if progress < 0.66:
        return "Improving", "Nice progress. Keep practicing.", progress
    if progress < 0.86:
        return "Strong", "You are doing well here.", progress
    return "Mastered", "Great work. Try a challenge next.", progress


def get_recommendation(
    level: str,
    questions_attempted: int,
    accuracy: Optional[float],
    incorrect_count: int,
    active_questions: int,
) -> tuple[int, str]:
    """Rank skill cards by what is most useful for the student next."""
    if active_questions == 0:
        return 0, "No practice questions are available yet."
    if questions_attempted == 0:
        return 80, "You have not practiced this skill yet."
    if incorrect_count > 0 and (accuracy is None or accuracy < 0.7):
        return 100, "Recent mistakes make this a good skill to review."
    if level in {"Getting Started", "Building"}:
        return 90, "A few more questions will build confidence here."
    if level == "Improving":
        return 70, "You are close to a stronger level."
    if level == "Strong":
        return 40, "Keep this fresh with a short practice round."
    return 20, "You are ready for a challenge when you want one."


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

    def get_daily_goal(self, student_id: int, target: int = 10) -> dict:
        """Get today's question goal progress for a student."""
        today = datetime.utcnow().date()
        start = datetime.combine(today, time.min)
        end = start + timedelta(days=1)

        result = self.db.query(
            func.count(AnsweredQuestion.id).label("answered"),
            func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct"),
        ).filter(
            AnsweredQuestion.student_id == student_id,
            AnsweredQuestion.answered_at >= start,
            AnsweredQuestion.answered_at < end,
        ).first()

        answered_today = result.answered or 0
        correct_today = result.correct or 0
        remaining = max(target - answered_today, 0)
        completed = answered_today >= target
        progress = min(answered_today / target, 1.0) if target > 0 else 1.0

        if completed:
            message = "Goal complete. Nice work today."
        elif answered_today == 0:
            message = "Answer your first question to start today's goal."
        else:
            message = f"{remaining} question{'s' if remaining != 1 else ''} left to finish today's goal."

        return {
            "target": target,
            "answered_today": answered_today,
            "correct_today": correct_today,
            "remaining": remaining,
            "completed": completed,
            "progress": progress,
            "message": message,
        }

    def get_skill_map(
        self,
        student_id: int,
        subject_id: Optional[int] = None,
        grade_id: Optional[int] = None,
    ) -> List[dict]:
        """Build the student's domain skill map with friendly levels."""
        domain_query = self.db.query(Domain).join(Standard, Standard.domain_id == Domain.id)

        if subject_id is not None:
            domain_query = domain_query.filter(Domain.subject_id == subject_id)
        if grade_id is not None:
            domain_query = domain_query.filter(Standard.grade_id == grade_id)

        domains = domain_query.distinct().order_by(Domain.display_order, Domain.name).all()
        domain_ids = [domain.id for domain in domains]

        if not domain_ids:
            return []

        answer_stats_query = self.db.query(
            Standard.domain_id.label("domain_id"),
            func.count(AnsweredQuestion.id).label("questions_attempted"),
            func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct_count"),
        ).join(
            Standard,
            AnsweredQuestion.standard_id == Standard.id,
        ).filter(
            AnsweredQuestion.student_id == student_id,
            Standard.domain_id.in_(domain_ids),
        )

        if grade_id is not None:
            answer_stats_query = answer_stats_query.filter(Standard.grade_id == grade_id)

        answer_stats = {
            row.domain_id: row
            for row in answer_stats_query.group_by(Standard.domain_id).all()
        }

        ability_records = {
            ability.domain_id: ability
            for ability in self.db.query(StudentDomainAbility).filter(
                StudentDomainAbility.student_id == student_id,
                StudentDomainAbility.domain_id.in_(domain_ids),
            ).all()
        }

        standard_counts_query = self.db.query(
            Standard.domain_id.label("domain_id"),
            func.count(func.distinct(Standard.id)).label("total_standards"),
        ).filter(Standard.domain_id.in_(domain_ids))

        question_counts_query = self.db.query(
            Standard.domain_id.label("domain_id"),
            func.count(Question.id).label("active_questions"),
        ).join(
            Question,
            Question.standard_id == Standard.id,
        ).filter(
            Standard.domain_id.in_(domain_ids),
            Question.is_active == True,
            Question.question_type == "multiple_choice",
        )

        if grade_id is not None:
            standard_counts_query = standard_counts_query.filter(Standard.grade_id == grade_id)
            question_counts_query = question_counts_query.filter(Standard.grade_id == grade_id)

        standard_counts = {
            row.domain_id: row.total_standards or 0
            for row in standard_counts_query.group_by(Standard.domain_id).all()
        }
        question_counts = {
            row.domain_id: row.active_questions or 0
            for row in question_counts_query.group_by(Standard.domain_id).all()
        }

        skill_map = []
        for domain in domains:
            stats = answer_stats.get(domain.id)
            ability = ability_records.get(domain.id)

            questions_attempted = stats.questions_attempted or 0 if stats else 0
            correct_count = stats.correct_count or 0 if stats else 0
            incorrect_count = max(questions_attempted - correct_count, 0)
            accuracy = correct_count / questions_attempted if questions_attempted > 0 else None
            theta = float(ability.theta) if ability else 0.0
            correct_streak = ability.correct_streak if ability else 0

            level, description, progress = get_skill_level(theta, questions_attempted)
            active_questions = question_counts.get(domain.id, 0)
            sort_priority, recommendation_reason = get_recommendation(
                level=level,
                questions_attempted=questions_attempted,
                accuracy=accuracy,
                incorrect_count=incorrect_count,
                active_questions=active_questions,
            )

            skill_map.append({
                "domain_id": domain.id,
                "domain_name": domain.name,
                "domain_code": domain.code,
                "progress": progress,
                "level": level,
                "level_description": description,
                "questions_attempted": questions_attempted,
                "correct_count": correct_count,
                "incorrect_count": incorrect_count,
                "accuracy": accuracy,
                "correct_streak": correct_streak,
                "total_standards": standard_counts.get(domain.id, 0),
                "active_questions": active_questions,
                "recommended": False,
                "recommendation_reason": recommendation_reason,
                "sort_priority": sort_priority,
            })

        skill_map.sort(key=lambda item: (-item["sort_priority"], item["domain_name"]))
        for item in skill_map:
            item["recommended"] = item["sort_priority"] > 0
            break

        return skill_map

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
                "keywords": (
                    list(s.keywords)
                    if isinstance(s.keywords, list)
                    else (s.keywords.split(",") if s.keywords else [])
                ),
            }
            for s in standards
        ]
