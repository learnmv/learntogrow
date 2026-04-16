from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, Integer

from app.models import User, UserRole, ParentStudentLink, LinkStatus, AnsweredQuestion, Standard
from app.schemas.parent import ParentStudentLinkResponse, StudentProgressSummary, StudentDetailForParent


class ParentService:
    """Service for parent-student relationship management."""

    def __init__(self, db: Session):
        self.db = db

    def get_linked_students(self, parent_id: int) -> List[ParentStudentLinkResponse]:
        """Get all students linked to a parent."""
        links = self.db.query(ParentStudentLink).options(
            joinedload(ParentStudentLink.student)
        ).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.status == LinkStatus.APPROVED
        ).all()

        result = []
        for link in links:
            if link.student:
                result.append(ParentStudentLinkResponse(
                    id=link.id,
                    parent_id=link.parent_id,
                    student_id=link.student_id,
                    student_name=link.student.full_name or link.student.username,
                    student_email=link.student.email,
                    student_username=link.student.username,
                    status=link.status.value,
                    requested_at=link.requested_at,
                    approved_at=link.approved_at
                ))

        return result

    def request_student_link(self, parent_id: int, student_email_or_username: str) -> Optional[ParentStudentLink]:
        """Create a pending link request from parent to student."""
        # Find student
        student = self.db.query(User).filter(
            User.email == student_email_or_username,
            User.role == UserRole.STUDENT,
            User.is_active == True
        ).first()

        if not student:
            student = self.db.query(User).filter(
                User.username == student_email_or_username,
                User.role == UserRole.STUDENT,
                User.is_active == True
            ).first()

        if not student:
            raise ValueError(f"No active student found with email or username: {student_email_or_username}")

        # Check if link already exists
        existing = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student.id
        ).first()

        if existing:
            if existing.status == LinkStatus.APPROVED:
                raise ValueError("You are already linked to this student")
            elif existing.status == LinkStatus.PENDING:
                raise ValueError("A link request is already pending for this student")
            else:
                # Rejected - allow re-request
                existing.status = LinkStatus.PENDING
                existing.requested_at = datetime.utcnow()
                self.db.commit()
                return existing

        # Create new pending link
        link = ParentStudentLink(
            parent_id=parent_id,
            student_id=student.id,
            status=LinkStatus.PENDING,
            requested_at=datetime.utcnow()
        )

        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)

        return link

    def get_pending_links(self) -> List[dict]:
        """Get all pending link requests (for admin review)."""
        links = self.db.query(ParentStudentLink).options(
            joinedload(ParentStudentLink.parent),
            joinedload(ParentStudentLink.student)
        ).filter(
            ParentStudentLink.status == LinkStatus.PENDING
        ).order_by(
            ParentStudentLink.requested_at
        ).all()

        result = []
        for link in links:
            if link.parent and link.student:
                result.append({
                    "id": link.id,
                    "parent_name": link.parent.full_name or link.parent.username,
                    "parent_email": link.parent.email,
                    "parent_username": link.parent.username,
                    "student_name": link.student.full_name or link.student.username,
                    "student_email": link.student.email,
                    "student_username": link.student.username,
                    "requested_at": link.requested_at
                })

        return result

    def approve_link(self, link_id: int, admin_id: int) -> bool:
        """Approve a parent-student link request."""
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.id == link_id,
            ParentStudentLink.status == LinkStatus.PENDING
        ).first()

        if not link:
            return False

        link.status = LinkStatus.APPROVED
        link.approved_at = datetime.utcnow()
        link.approved_by = admin_id

        self.db.commit()
        return True

    def reject_link(self, link_id: int, admin_id: int, reason: Optional[str] = None) -> bool:
        """Reject a parent-student link request."""
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.id == link_id,
            ParentStudentLink.status == LinkStatus.PENDING
        ).first()

        if not link:
            return False

        link.status = LinkStatus.REJECTED
        link.approved_at = datetime.utcnow()
        link.approved_by = admin_id
        link.rejected_reason = reason

        self.db.commit()
        return True

    def get_student_progress_summary(self, student_id: int) -> StudentProgressSummary:
        """Get progress summary for a student using answered_questions."""
        student = self.db.query(User).filter(
            User.id == student_id,
            User.role == UserRole.STUDENT
        ).first()

        if not student:
            raise ValueError("Student not found")

        # Get total answers and correct count
        total_result = self.db.query(
            func.count(AnsweredQuestion.id).label("total"),
            func.sum(func.cast(AnsweredQuestion.is_correct, Integer)).label("correct")
        ).filter(AnsweredQuestion.student_id == student_id).first()

        total_answered = total_result.total or 0
        correct_count = total_result.correct or 0 if total_result.total else 0
        accuracy = correct_count / total_answered if total_answered > 0 else None

        # Get last answer
        last_answer = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).order_by(
            AnsweredQuestion.answered_at.desc()
        ).first()

        # Get recent answers with standard info
        recent_answers = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).options(
            joinedload(AnsweredQuestion.standard)
        ).order_by(
            AnsweredQuestion.answered_at.desc()
        ).limit(10).all()

        recent_list = []
        for answer in recent_answers:
            recent_list.append({
                "answer_id": answer.id,
                "question_id": answer.question_id,
                "standard_code": answer.standard.code if answer.standard else None,
                "is_correct": answer.is_correct,
                "answered_at": answer.answered_at.isoformat() if answer.answered_at else None
            })

        # Get unique standards attempted
        standards_attempted = self.db.query(func.count(func.distinct(AnsweredQuestion.standard_id))).filter(
            AnsweredQuestion.student_id == student_id
        ).scalar()

        return StudentProgressSummary(
            student_id=student_id,
            student_name=student.full_name or student.username,
            student_username=student.username,
            total_attempts=total_answered,
            average_score=round(accuracy * 100, 2) if accuracy else None,
            last_attempt_at=last_answer.answered_at if last_answer else None,
            recent_attempts=recent_list
        )

    def get_student_detail_for_parent(self, parent_id: int, student_id: int) -> StudentDetailForParent:
        """Get detailed student info for a linked parent."""
        # Verify link exists
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student_id,
            ParentStudentLink.status == LinkStatus.APPROVED
        ).first()

        if not link:
            raise ValueError("You are not linked to this student or the link is pending approval")

        summary = self.get_student_progress_summary(student_id)

        # Get more detailed recent answers with standard info
        recent_answers = self.db.query(AnsweredQuestion).filter(
            AnsweredQuestion.student_id == student_id
        ).options(
            joinedload(AnsweredQuestion.standard)
        ).order_by(
            AnsweredQuestion.answered_at.desc()
        ).limit(20).all()

        detailed_attempts = []
        for answer in recent_answers:
            detailed_attempts.append({
                "answer_id": answer.id,
                "question_id": answer.question_id,
                "standard_code": answer.standard.code if answer.standard else None,
                "standard_description": answer.standard.description if answer.standard else None,
                "is_correct": answer.is_correct,
                "answered_at": answer.answered_at.isoformat() if answer.answered_at else None
            })

        student = self.db.query(User).filter(User.id == student_id).first()

        return StudentDetailForParent(
            student_id=student_id,
            student_name=student.full_name or student.username,
            student_username=student.username,
            email=student.email,
            total_attempts=summary.total_attempts,
            average_score=summary.average_score,
            standards_attempted=len(set(a.standard_id for a in recent_answers)),
            recent_attempts=detailed_attempts
        )

    def can_view_student(self, parent_id: int, student_id: int) -> bool:
        """Check if parent can view student's progress."""
        link = self.db.query(ParentStudentLink).filter(
            ParentStudentLink.parent_id == parent_id,
            ParentStudentLink.student_id == student_id,
            ParentStudentLink.status == LinkStatus.APPROVED
        ).first()

        return link is not None
