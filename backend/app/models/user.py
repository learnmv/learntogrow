from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, Enum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    """User role types."""
    STUDENT = "student"
    PARENT = "parent"
    ADMIN = "admin"


class LinkStatus(str, enum.Enum):
    """Parent-student link status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    """User accounts for students, parents, and admins."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    quiz_attempts = relationship("QuizAttempt", back_populates="student")
    parent_links = relationship(
        "ParentStudentLink",
        foreign_keys="ParentStudentLink.parent_id",
        back_populates="parent"
    )
    student_links = relationship(
        "ParentStudentLink",
        foreign_keys="ParentStudentLink.student_id",
        back_populates="student"
    )
    approved_links = relationship(
        "ParentStudentLink",
        foreign_keys="ParentStudentLink.approved_by",
        back_populates="approver"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class PasswordResetToken(Base):
    """Password reset tokens for users."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    used_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship("User", backref="reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken(user_id={self.user_id}, expires_at={self.expires_at})>"


class ParentStudentLink(Base):
    """Links between parent and student accounts."""
    __tablename__ = "parent_student_links"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(LinkStatus), default=LinkStatus.PENDING)
    requested_at = Column(TIMESTAMP, server_default=func.now())
    approved_at = Column(TIMESTAMP)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    rejected_reason = Column(Text)

    # Relationships
    parent = relationship(
        "User",
        foreign_keys=[parent_id],
        back_populates="parent_links"
    )
    student = relationship(
        "User",
        foreign_keys=[student_id],
        back_populates="student_links"
    )
    approver = relationship(
        "User",
        foreign_keys=[approved_by],
        back_populates="approved_links"
    )

    def __repr__(self):
        return f"<ParentStudentLink(parent_id={self.parent_id}, student_id={self.student_id}, status={self.status})>"


class QuizAttempt(Base):
    """Quiz attempts tracked per student."""
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"))
    answers = Column(Text)  # JSON string: {question_id: {selected: "A", correct: true}}
    score = Column(Integer)
    total_questions = Column(Integer)
    time_spent_seconds = Column(Integer)
    completed_at = Column(TIMESTAMP, server_default=func.now())
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    student = relationship("User", back_populates="quiz_attempts")
    standard = relationship("Standard", backref="quiz_attempts")
    question = relationship("Question", backref="quiz_attempts")

    def __repr__(self):
        return f"<QuizAttempt(student_id={self.student_id}, standard_id={self.standard_id}, score={self.score})>"


class AnsweredQuestion(Base):
    """Tracks individual question answers to avoid repeating questions for students."""
    __tablename__ = "answered_questions"
    __table_args__ = (
        UniqueConstraint('student_id', 'question_id', name='uq_student_question'),
    )

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    selected_answer = Column(Text)
    is_correct = Column(Boolean, nullable=False)
    answered_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    student = relationship("User", backref="answered_questions")
    question = relationship("Question", backref="answered_questions")
    standard = relationship("Standard", backref="answered_questions")

    def __repr__(self):
        return f"<AnsweredQuestion(student_id={self.student_id}, question_id={self.question_id}, is_correct={self.is_correct})>"
