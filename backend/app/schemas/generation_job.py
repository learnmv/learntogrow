"""Pydantic schemas for generation job API."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.generation_job import JobStatus, JobStandardStatus


class GenerationJobStandardResponse(BaseModel):
    """Per-standard progress within a generation job."""
    id: int
    standard_id: int
    standard_code: Optional[str] = None
    questions_requested: int = 1
    questions_created: int = 0
    status: str = JobStandardStatus.PENDING.value
    error: Optional[str] = None
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
    errors: List[str] = []
    created_by: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerationJobDetailResponse(GenerationJobResponse):
    """Generation job with per-standard details."""
    job_standards: List[GenerationJobStandardResponse] = []


class GenerationJobCreateRequest(BaseModel):
    """Create a new generation job."""
    standard_ids: List[int] = Field(..., min_length=1, description="Standards to generate questions for")
    questions_per_standard: int = Field(1, ge=1, le=10, description="Questions per standard")
    question_type: str = Field("multiple_choice", pattern="^(multiple_choice|open_ended)$")
    model: Optional[str] = Field(None, description="Ollama model override")
    timeout: int = Field(300, ge=30, le=600, description="Timeout per question in seconds")
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
