"""Generation job models for async question generation."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, Text, String
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
    quality_mode = Column(String(20), nullable=False, default="reviewed")
    candidate_count = Column(Integer, nullable=False, default=1)
    max_repair_attempts = Column(Integer, nullable=False, default=1)
    min_review_score = Column(Numeric(4, 3), nullable=False, default=0.750)
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
    quality_audits = relationship(
        "QuestionGenerationAudit",
        back_populates="job",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

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

    @property
    def avg_quality_score(self) -> Optional[float]:
        scores = [
            float(audit.score)
            for audit in self.quality_audits
            if audit.stage == "review" and audit.score is not None
        ]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 3)

    @property
    def last_review_notes(self) -> Optional[str]:
        reviews = [
            audit
            for audit in self.quality_audits
            if audit.stage == "review" and audit.notes
        ]
        if not reviews:
            return None
        return sorted(reviews, key=lambda audit: audit.created_at or datetime.min)[-1].notes

    @property
    def quality_summary(self) -> dict:
        audits = self.quality_audits or []
        review_scores = [
            float(audit.score)
            for audit in audits
            if audit.stage == "review" and audit.score is not None
        ]
        return {
            "planner_runs": sum(1 for audit in audits if audit.stage == "planner"),
            "candidate_runs": sum(1 for audit in audits if audit.stage == "candidate"),
            "review_runs": sum(1 for audit in audits if audit.stage == "review"),
            "repair_runs": sum(1 for audit in audits if audit.stage == "repair"),
            "best_review_score": round(max(review_scores), 3) if review_scores else None,
        }

    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Relationships
    job = relationship("GenerationJob", back_populates="job_standards")
    standard = relationship("Standard", lazy="joined")
    quality_audits = relationship(
        "QuestionGenerationAudit",
        back_populates="job_standard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<GenerationJobStandard(job_id={self.job_id}, standard_id={self.standard_id}, status='{self.status}')>"


class QuestionGenerationAudit(Base):
    """Stores planner/reviewer/repair details for admin generation jobs."""
    __tablename__ = "question_generation_audits"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("generation_jobs.id", ondelete="CASCADE"))
    job_standard_id = Column(Integer, ForeignKey("generation_job_standards.id", ondelete="CASCADE"))
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"))
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"))
    stage = Column(String(40), nullable=False)
    candidate_index = Column(Integer)
    attempt = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="completed")
    score = Column(Numeric(4, 3))
    prompt_name = Column(String(80))
    model = Column(String(100))
    request_payload = Column(JSON, default=dict)
    response_payload = Column(JSON, default=dict)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("GenerationJob", back_populates="quality_audits")
    job_standard = relationship("GenerationJobStandard", back_populates="quality_audits")
    standard = relationship("Standard", lazy="joined")
    question = relationship("Question", lazy="joined")

    def __repr__(self):
        return f"<QuestionGenerationAudit(job_id={self.job_id}, stage='{self.stage}')>"
