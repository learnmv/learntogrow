from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QuestionGenerateRequestAdmin(BaseModel):
    """Admin request to generate questions."""
    subject_id: int = Field(..., description="Subject ID to generate questions for")
    grade_id: Optional[int] = Field(None, description="Specific grade, or null for all grades")
    domain_ids: Optional[List[int]] = Field(None, description="Specific domains, or null for all")
    standard_ids: Optional[List[int]] = Field(None, description="Specific standards, or null for all matching")
    difficulty_min: Optional[float] = Field(None, ge=0, le=1, description="Minimum difficulty (0-1)")
    difficulty_max: Optional[float] = Field(None, ge=0, le=1, description="Maximum difficulty (0-1)")
    questions_per_standard: int = Field(1, ge=1, le=10, description="Number of questions to generate per standard")
    question_type: str = Field("multiple_choice", pattern="^(multiple_choice|open_ended)$")
    model: Optional[str] = Field(None, description="Ollama model to use (default from config)")
    timeout: Optional[int] = Field(300, ge=30, le=600, description="Timeout in seconds")


class QuestionGenerateStatus(BaseModel):
    """Status of question generation job."""
    job_id: str
    status: str  # pending, running, completed, failed
    total_standards: int
    completed_standards: int
    failed_standards: int
    created_questions: int
    errors: List[str] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class QuestionEditRequest(BaseModel):
    """Admin edit question request."""
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: Optional[float] = Field(None, ge=0, le=1)
    is_active: Optional[bool] = None


class UserCreateAdmin(BaseModel):
    """Admin creates user (bypasses normal registration)."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(student|parent|admin)$")
    full_name: Optional[str] = None
    is_active: bool = True


class UserStatusUpdate(BaseModel):
    """Update user status (activate/deactivate)."""
    is_active: bool


class AdminDashboardStats(BaseModel):
    """Dashboard statistics for admin."""
    total_users: int
    total_students: int
    total_parents: int
    total_admins: int
    total_questions: int
    total_quiz_attempts: int
    pending_parent_links: int
    recent_quiz_attempts: int


class BulkQuestionGenerateRequest(BaseModel):
    """Bulk question generation by filters."""
    subject_id: int
    grade_id: Optional[int] = None
    only_diagram_questions: bool = False
    questions_per_standard: int = Field(1, ge=1, le=10)
    question_type: str = "multiple_choice"
    async_mode: bool = True  # Run in background
