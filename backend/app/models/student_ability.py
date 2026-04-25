"""Student domain ability model for adaptive learning."""

from datetime import datetime
from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, UniqueConstraint

from app.database import Base


class StudentDomainAbility(Base):
    """Tracks per-student ability per domain using an ELO-like theta score."""
    __tablename__ = "student_domain_ability"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id", ondelete="CASCADE"), nullable=False)
    theta = Column(Numeric(4, 3), nullable=False, default=0.35)
    questions_attempted = Column(Integer, nullable=False, default=0)
    correct_streak = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (UniqueConstraint("student_id", "domain_id", name="uix_student_domain"),)

    def __repr__(self):
        return (f"<StudentDomainAbility(student_id={self.student_id}, "
                f"domain_id={self.domain_id}, theta={self.theta})>")
