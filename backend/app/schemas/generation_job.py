"""Pydantic schemas for generation job API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.generation_job import JobStatus, JobStandardStatus


class GenerationJobStandardResponse(BaseModel):
    """Per-standard progress within a generation job."""
    id: int
    standard_id: int
    standard_code: Optional[str] = None
    cluster_id: Optional[int] = None
    target_difficulty: Optional[float] = None
    difficulty_band: Optional[str] = None
    generation_reason: Optional[str] = None
    questions_requested: int = 1
    questions_created: int = 0
    status: str = JobStandardStatus.PENDING.value
    error: Optional[str] = None
    avg_quality_score: Optional[float] = None
    last_review_notes: Optional[str] = None
    quality_summary: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationJobResponse(BaseModel):
    """Generation job overview."""
    id: int
    status: str = JobStatus.PENDING.value
    subject_id: Optional[int] = None
    grade_id: Optional[int] = None
    total_standards: int = 0
    completed_standards: int = 0
    failed_standards: int = 0
    questions_created: int = 0
    question_type: str = "multiple_choice"
    model: Optional[str] = None
    timeout: int = 300
    quality_mode: str = "reviewed"
    candidate_count: int = 1
    max_repair_attempts: int = 1
    min_review_score: float = 0.75
    errors: List[str] = Field(default_factory=list)
    created_by: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationJobDetailResponse(GenerationJobResponse):
    """Generation job with per-standard details."""
    job_standards: List[GenerationJobStandardResponse] = Field(default_factory=list)


class GenerationJobCreateRequest(BaseModel):
    """Create a new generation job."""
    standard_ids: List[int] = Field(..., min_length=1, description="Standards to generate questions for")
    questions_per_standard: int = Field(1, ge=1, le=10, description="Questions per standard")
    question_type: str = Field("multiple_choice", pattern="^(multiple_choice|open_ended)$")
    model: Optional[str] = Field(None, description="Ollama model override")
    timeout: int = Field(300, ge=30, le=600, description="Timeout per question in seconds")
    quality_mode: str = Field("reviewed", pattern="^(fast|reviewed|quality)$")
    candidate_count: int = Field(1, ge=1, le=5)
    max_repair_attempts: int = Field(1, ge=0, le=3)
    min_review_score: float = Field(0.75, ge=0.0, le=1.0)
    subject_id: Optional[int] = Field(None, description="Optional subject context")
    grade_id: Optional[int] = Field(None, description="Optional grade context")


class GenerationJobListParams(BaseModel):
    """Query params for listing jobs."""
    status: Optional[str] = Field(None, description="Filter by status")
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=200)


class GenerationJobRetryRequest(BaseModel):
    """Retry failed standards from a previous job."""
    job_id: int = Field(..., description="Original job ID to retry failed standards from")
