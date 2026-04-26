"""Generation job models for async question generation."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Text, String
from sqlalchemy.orm import relationship

from app.database import Base


class JobStatus(str, PyEnum):
    """Generation job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStandardStatus(str, PyEnum):
    """Per-standard generation statuses."""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class GenerationJob(Base):
    """Tracks an async question generation job."""
    __tablename__ = "generation_jobs"

    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=False, default=JobStatus.PENDING.value)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="SET NULL"))
    grade_id = Column(Integer, ForeignKey("grades.id", ondelete="SET NULL"))
    total_standards = Column(Integer, nullable=False, default=0)
    completed_standards = Column(Integer, nullable=False, default=0)
    failed_standards = Column(Integer, nullable=False, default=0)
    questions_created = Column(Integer, nullable=False, default=0)
    errors = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    question_type = Column(String(50), default="multiple_choice")
    model = Column(String(100))
    timeout = Column(Integer, default=300)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    job_standards = relationship(
        "GenerationJobStandard",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
    subject = relationship("Subject", foreign_keys=[subject_id], lazy="joined")
    grade = relationship("Grade", foreign_keys=[grade_id], lazy="joined")

    def __repr__(self):
        return f"<GenerationJob(id={self.id}, status='{self.status}')>"


class GenerationJobStandard(Base):
    """Tracks per-standard progress within a generation job."""
    __tablename__ = "generation_job_standards"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("generation_jobs.id", ondelete="CASCADE"), nullable=False)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)
    questions_requested = Column(Integer, nullable=False, default=1)
    questions_created = Column(Integer, nullable=False, default=0)
    status = Column(String(20), default=JobStandardStatus.PENDING.value)
    error = Column(Text)

    @property
    def standard_code(self) -> Optional[str]:
        return self.standard.code if self.standard else None

    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    job = relationship("GenerationJob", back_populates="job_standards")
    standard = relationship("Standard", lazy="joined")

    def __repr__(self):
        return f"<GenerationJobStandard(job_id={self.job_id}, standard_id={self.standard_id}, status='{self.status}')>"
