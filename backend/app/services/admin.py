import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import User, UserRole, Question, Standard, ParentStudentLink, LinkStatus, QuizAttempt
from app.schemas.admin import UserCreateAdmin
from app.schemas.questions import QuestionEditRequest
from app.services.questions import QuestionService
from app.services.auth import AuthService

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin operations."""

    def __init__(self, db: Session):
        self.db = db
        self.question_service = QuestionService(db)
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
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Question]:
        """Get questions with filters."""
        query = self.db.query(Question)

        if standard_id:
            query = query.filter(Question.standard_id == standard_id)
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

    def toggle_question_status(self, question_id: int) -> Optional[Question]:
        """Toggle question active status."""
        question = self.get_question_by_id(question_id)
        if not question:
            return None

        question.is_active = not question.is_active
        self.db.commit()
        self.db.refresh(question)
        return question

    # ==================== Question Generation ====================

    def generate_questions_for_standards(
        self,
        standard_ids: List[int],
        questions_per_standard: int = 1,
        question_type: str = "multiple_choice",
        model: Optional[str] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """Generate questions for multiple standards."""
        results = {
            "total_standards": len(standard_ids),
            "completed": 0,
            "failed": 0,
            "questions_created": 0,
            "errors": []
        }

        for standard_id in standard_ids:
            try:
                for i in range(questions_per_standard):
                    try:
                        question_data = self.question_service.generate_question(
                            standard_id=standard_id,
                            question_type=question_type,
                            model=model,
                            timeout=timeout
                        )

                        # Create question record
                        question = Question(
                            standard_id=standard_id,
                            question_text=question_data.get("question", ""),
                            question_type=question_type,
                            options=question_data.get("options"),
                            correct_answer=question_data.get("answer", ""),
                            explanation=question_data.get("explanation", ""),
                            difficulty=question_data.get("difficulty", 0.5),
                            requires_diagram=question_data.get("requires_diagram", False),
                            applet_type=question_data.get("applet_type"),
                            geogebra_commands=question_data.get("geogebra_commands"),
                            applet_config=question_data.get("applet_config"),
                            generated_by="admin",
                            is_active=True
                        )

                        self.db.add(question)
                        results["questions_created"] += 1

                    except Exception as e:
                        logger.error(f"Failed to generate question for standard {standard_id}: {e}")
                        results["errors"].append(f"Standard {standard_id}: {str(e)}")

                self.db.commit()
                results["completed"] += 1

            except Exception as e:
                logger.error(f"Failed to process standard {standard_id}: {e}")
                results["failed"] += 1
                results["errors"].append(f"Standard {standard_id}: {str(e)}")

        return results

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
