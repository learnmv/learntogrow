from sqlalchemy import CheckConstraint, Column, Integer, String, Text, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class QuizAssignment(Base):
    """Parent-assigned quiz for a student."""
    __tablename__ = "quiz_assignments"
    __table_args__ = (
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard', 'mixed')", name="ck_assignment_difficulty"),
        CheckConstraint("status IN ('assigned', 'in_progress', 'completed')", name="ck_assignment_status"),
        CheckConstraint("question_count >= 0", name="ck_assignment_question_count"),
    )

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"))
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="SET NULL"))
    title = Column(String(150), nullable=False)
    description = Column(Text)
    difficulty = Column(String(20), nullable=False, default="medium")
    status = Column(String(20), nullable=False, default="assigned")
    question_count = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    due_at = Column(TIMESTAMP)

    parent = relationship("User", foreign_keys=[parent_id])
    student = relationship("User", foreign_keys=[student_id])
    subject = relationship("Subject")
    grade = relationship("Grade")
    assignment_questions = relationship(
        "QuizAssignmentQuestion",
        back_populates="assignment",
        cascade="all, delete-orphan",
        order_by="QuizAssignmentQuestion.order_index",
    )


class QuizAssignmentQuestion(Base):
    """Question ordering for a quiz assignment."""
    __tablename__ = "quiz_assignment_questions"
    __table_args__ = (
        UniqueConstraint("assignment_id", "question_id", name="uq_assignment_question"),
        UniqueConstraint("assignment_id", "order_index", name="uq_assignment_order"),
    )

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("quiz_assignments.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, nullable=False)

    assignment = relationship("QuizAssignment", back_populates="assignment_questions")
    question = relationship("Question")
