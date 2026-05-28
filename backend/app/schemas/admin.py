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
    quality_mode: str = Field("reviewed", pattern="^(fast|reviewed|quality)$")
    candidate_count: int = Field(1, ge=1, le=5)
    max_repair_attempts: int = Field(1, ge=0, le=3)
    min_review_score: float = Field(0.75, ge=0, le=1)


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
    stimulus: Optional[dict] = None
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


class BulkDeleteRequest(BaseModel):
    """Bulk question deletion request."""
    question_ids: Optional[List[int]] = Field(None, description="Specific question IDs to delete")
    standard_id: Optional[int] = None
    domain_id: Optional[int] = None
    grade_id: Optional[int] = None
    is_active: Optional[bool] = None
    all_matching: bool = Field(False, description="Delete all questions matching filters")


class SmartFillRequest(BaseModel):
    """Smart fill question generation request."""
    subject_id: int
    grade_id: Optional[int] = None
    fill_mode: str = Field("gaps", pattern="^(gaps|struggling|balanced|difficulty|diagrams)$")
    max_standards: int = Field(10, ge=1, le=50)


class DomainInsight(BaseModel):
    """Insight for a single domain."""
    domain_id: int
    domain_name: str
    domain_code: str
    standard_count: int
    question_count: int
    answered_count: int
    accuracy: Optional[float]
    coverage_status: str  # good, low, none
    avg_difficulty: Optional[float]


class QuestionInsightsResponse(BaseModel):
    """Question insights response."""
    total_standards: int
    total_questions: int
    coverage_percent: float
    domains: List[DomainInsight]


class SmartFillSuggestion(BaseModel):
    """Suggestion for smart fill generation."""
    standard_id: int
    standard_code: str
    standard_description: str
    domain_name: str
    reason: str
    suggested_difficulty: float
    suggested_count: int


class SmartFillResponse(BaseModel):
    """Smart fill suggestions response."""
    suggestions: List[SmartFillSuggestion]
    total_suggested: int
    estimated_generation_time: str


class AdminChatMessage(BaseModel):
    """Single message in the admin model chat."""
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str = Field(..., min_length=1, max_length=12000)


class AdminChatRequest(BaseModel):
    """Admin request for direct Ollama chat mode."""
    messages: List[AdminChatMessage] = Field(..., min_length=1, max_length=40)
    temperature: float = Field(0.3, ge=0, le=1)


class AdminChatResponse(BaseModel):
    """Response from the configured Ollama chat model."""
    message: AdminChatMessage
    model: str
