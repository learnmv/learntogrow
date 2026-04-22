import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer

from app.models import User, UserRole, Question, Standard, ParentStudentLink, LinkStatus, QuizAttempt, Domain, Grade, DomainProgress
from app.schemas.admin import UserCreateAdmin
from app.schemas.questions import QuestionEditRequest
from app.services.auth import AuthService

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations."""

    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)

    # ==================== User Management ====================

    def get_all_users(self, role: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with optional role filter."""
        query = self.db.query(User)

        if role:
            query = query.filter(User.role == role)

        return query.offset(skip).limit(limit).all()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_data: UserCreateAdmin) -> User:
        """Create a new user (admin only)."""
        # Check for existing username or email
        if self.auth_service.get_user_by_username(user_data.username):
            raise ValueError(f"Username '{user_data.username}' already exists")

        if self.auth_service.get_user_by_email(user_data.email):
            raise ValueError(f"Email '{user_data.email}' already exists")

        # Use auth service to create user
        from app.schemas.auth import UserCreate
        create_data = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            role=user_data.role,
            full_name=user_data.full_name
        )

        return self.auth_service.create_user(create_data)

    def update_user_status(self, user_id: int, is_active: bool) -> Optional[User]:
        """Activate or deactivate a user account."""
        return self.auth_service.update_user(user_id, is_active=is_active)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user permanently."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        self.db.delete(user)
        self.db.commit()
        return True

    def get_dashboard_stats(self) -> Dict[str, int]:
        """Get dashboard statistics."""
        total_users = self.db.query(func.count(User.id)).scalar()
        total_students = self.db.query(func.count(User.id)).filter(User.role == UserRole.STUDENT).scalar()
        total_parents = self.db.query(func.count(User.id)).filter(User.role == UserRole.PARENT).scalar()
        total_admins = self.db.query(func.count(User.id)).filter(User.role == UserRole.ADMIN).scalar()
        total_questions = self.db.query(func.count(Question.id)).scalar()
        total_attempts = self.db.query(func.count(QuizAttempt.id)).scalar()
        pending_links = self.db.query(func.count(ParentStudentLink.id)).filter(
            ParentStudentLink.status == LinkStatus.PENDING
        ).scalar()

        # Recent attempts (last 7 days)
        recent_attempts = self.db.query(func.count(QuizAttempt.id)).filter(
            QuizAttempt.completed_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
        ).scalar()

        return {
            "total_users": total_users,
            "total_students": total_students,
            "total_parents": total_parents,
            "total_admins": total_admins,
            "total_questions": total_questions,
            "total_quiz_attempts": total_attempts,
            "pending_parent_links": pending_links,
            "recent_quiz_attempts": recent_attempts
        }

    # ==================== Question Management ====================

    def get_questions(
        self,
        standard_id: Optional[int] = None,
        domain_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Question]:
        """Get questions with filters."""
        query = self.db.query(Question)

        if standard_id:
            query = query.filter(Question.standard_id == standard_id)
        if domain_id:
            query = query.join(Standard).filter(Standard.domain_id == domain_id)
        if grade_id:
            query = query.join(Standard).filter(Standard.grade_id == grade_id)
        if is_active is not None:
            query = query.filter(Question.is_active == is_active)

        return query.order_by(Question.created_at.desc()).offset(skip).limit(limit).all()

    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """Get question by ID."""
        return self.db.query(Question).filter(Question.id == question_id).first()

    def update_question(self, question_id: int, updates: Dict[str, Any]) -> Optional[Question]:
        """Update a question."""
        question = self.get_question_by_id(question_id)
        if not question:
            return None

        for field, value in updates.items():
            if hasattr(question, field) and value is not None:
                setattr(question, field, value)

        question.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(question)
        return question

    def delete_question(self, question_id: int) -> bool:
        """Delete a question."""
        question = self.get_question_by_id(question_id)
        if not question:
            return False

        self.db.delete(question)
        self.db.commit()
        return True

    def delete_questions_by_ids(self, question_ids: List[int]) -> int:
        """Delete multiple questions by IDs."""
        count = self.db.query(Question).filter(Question.id.in_(question_ids)).delete(synchronize_session=False)
        self.db.commit()
        return count

    def delete_questions_by_filters(
        self,
        standard_id: Optional[int] = None,
        domain_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> int:
        """Delete all questions matching filters."""
        query = self.db.query(Question)
        if standard_id:
            query = query.filter(Question.standard_id == standard_id)
        if domain_id:
            query = query.join(Standard).filter(Standard.domain_id == domain_id)
        if grade_id:
            query = query.join(Standard).filter(Standard.grade_id == grade_id)
        if is_active is not None:
            query = query.filter(Question.is_active == is_active)

        count = query.delete(synchronize_session=False)
        self.db.commit()
        return count

    def toggle_question_status(self, question_id: int) -> Optional[Question]:
        """Toggle question active status."""
        question = self.get_question_by_id(question_id)
        if not question:
            return None

        question.is_active = not question.is_active
        self.db.commit()
        self.db.refresh(question)
        return question

    # ==================== Question Generation (moved to QuestionGenerationJobService) ====================

    def get_standards_for_generation(
        self,
        subject_id: Optional[int] = None,
        grade_id: Optional[int] = None,
        domain_ids: Optional[List[int]] = None,
        difficulty_min: Optional[float] = None,
        difficulty_max: Optional[float] = None,
        only_diagram_questions: bool = False
    ) -> List[Standard]:
        """Get standards matching generation criteria."""
        query = self.db.query(Standard)

        if subject_id:
            query = query.filter(Standard.domain.has(subject_id=subject_id))
        if grade_id:
            query = query.filter(Standard.grade_id == grade_id)
        if domain_ids:
            query = query.filter(Standard.domain_id.in_(domain_ids))
        if difficulty_min is not None:
            query = query.filter(Standard.difficulty_base >= difficulty_min)
        if difficulty_max is not None:
            query = query.filter(Standard.difficulty_base <= difficulty_max)
        if only_diagram_questions:
            query = query.filter(Standard.requires_diagram == True)

        return query.all()

    # ==================== Question Insights ====================

    def get_question_insights(
        self,
        subject_id: Optional[int] = None,
        grade_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get insights about question coverage per domain."""
        query = self.db.query(Domain).join(Standard)
        if subject_id:
            query = query.filter(Domain.subject_id == subject_id)
        if grade_id:
            query = query.filter(Standard.grade_id == grade_id)
        domains = query.distinct().all()

        total_standards = self.db.query(Standard).filter(
            Standard.grade_id == grade_id if grade_id else True
        ).count()
        total_questions = self.db.query(Question).count()

        domain_insights = []
        for domain in domains:
            standards = self.db.query(Standard).filter(Standard.domain_id == domain.id)
            if grade_id:
                standards = standards.filter(Standard.grade_id == grade_id)
            standards_count = standards.count()
            standard_ids = [s.id for s in standards.all()]

            question_count = self.db.query(Question).filter(
                Question.standard_id.in_(standard_ids)
            ).count() if standard_ids else 0

            # Get aggregate accuracy for this domain
            answered_stats = self.db.query(
                func.count(AnsweredQuestion.id).label("answered"),
                func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct")
            ).filter(
                AnsweredQuestion.standard_id.in_(standard_ids)
            ).first()

            answered_count = answered_stats.answered or 0
            correct_count = answered_stats.correct or 0
            accuracy = correct_count / answered_count if answered_count > 0 else None

            # Coverage status
            avg_difficulty = None
            if question_count > 0:
                avg_result = self.db.query(func.avg(Question.difficulty)).filter(
                    Question.standard_id.in_(standard_ids)
                ).scalar()
                avg_difficulty = float(avg_result) if avg_result else None

            if question_count == 0:
                coverage_status = "none"
            elif question_count < standards_count:
                coverage_status = "low"
            else:
                coverage_status = "good"

            domain_insights.append({
                "domain_id": domain.id,
                "domain_name": domain.name,
                "domain_code": domain.code,
                "standard_count": standards_count,
                "question_count": question_count,
                "answered_count": answered_count,
                "accuracy": accuracy,
                "coverage_status": coverage_status,
                "avg_difficulty": avg_difficulty,
            })

        # Calculate overall coverage
        standards_with_questions = self.db.query(func.count(func.distinct(Question.standard_id))).scalar()
        coverage_percent = (standards_with_questions / total_standards * 100) if total_standards > 0 else 0

        return {
            "total_standards": total_standards,
            "total_questions": total_questions,
            "coverage_percent": round(coverage_percent, 1),
            "domains": domain_insights,
        }

    def get_smart_fill_suggestions(
        self,
        subject_id: int,
        grade_id: Optional[int] = None,
        fill_mode: str = "gaps",
        max_standards: int = 10
    ) -> Dict[str, Any]:
        """Get smart suggestions for question generation based on gaps and student data."""
        query = self.db.query(Standard).filter(Standard.domain.has(subject_id=subject_id))
        if grade_id:
            query = query.filter(Standard.grade_id == grade_id)
        standards = query.all()

        suggestions = []

        for standard in standards:
            question_count = self.db.query(Question).filter(
                Question.standard_id == standard.id
            ).count()

            # Domain accuracy if available
            domain_accuracy = None
            answered_stats = self.db.query(
                func.count(AnsweredQuestion.id).label("answered"),
                func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct")
            ).filter(
                AnsweredQuestion.standard_id == standard.id
            ).first()

            if answered_stats.answered and answered_stats.answered > 0:
                domain_accuracy = answered_stats.correct / answered_stats.answered

            # Determine if this standard needs questions
            reason = None
            suggested_difficulty = float(standard.difficulty_base) if standard.difficulty_base else 0.5
            suggested_count = 2

            if fill_mode == "gaps":
                if question_count == 0:
                    reason = f"No questions for {standard.code}"
                elif question_count < 3:
                    reason = f"Only {question_count} question(s) for {standard.code}"
            elif fill_mode == "struggling":
                if domain_accuracy is not None and domain_accuracy < 0.50:
                    reason = f"Students struggling with {standard.code} (accuracy: {domain_accuracy:.0%})"
                    suggested_difficulty = max(0.2, suggested_difficulty - 0.1)
                    suggested_count = 3
            elif fill_mode == "balanced":
                if question_count == 0:
                    reason = f"No questions for {standard.code}"
                elif domain_accuracy is not None and domain_accuracy < 0.50:
                    reason = f"Students struggling with {standard.code} (accuracy: {domain_accuracy:.0%})"
                    suggested_count = 3

            if reason:
                suggestions.append({
                    "standard_id": standard.id,
                    "standard_code": standard.code,
                    "standard_description": standard.description,
                    "domain_name": standard.domain.name if standard.domain else "Unknown",
                    "reason": reason,
                    "suggested_difficulty": suggested_difficulty,
                    "suggested_count": suggested_count,
                })

        # Sort: gaps first, then struggling, then low count
        suggestions.sort(key=lambda s: (
            0 if "No questions" in s["reason"] else
            1 if "struggling" in s["reason"] else
            2
        ))

        return {
            "suggestions": suggestions[:max_standards],
            "total_suggested": len(suggestions),
            "estimated_generation_time": f"~{len(suggestions[:max_standards]) * 2} minutes",
        }
