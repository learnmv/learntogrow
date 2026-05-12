from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class ParentStudentLinkCreate(BaseModel):
    """Request to link parent to student."""
    student_email_or_username: str = Field(..., description="Email or username of the student to link with")


class ParentStudentLinkResponse(BaseModel):
    """Parent-student link response."""
    id: int
    parent_id: int
    student_id: int
    student_name: str
    student_email: str
    student_username: str
    status: str
    requested_at: datetime
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ParentStudentLinkPending(BaseModel):
    """Pending link request for admin review."""
    id: int
    parent_name: str
    parent_email: str
    parent_username: str
    student_name: str
    student_email: str
    student_username: str
    requested_at: datetime

    class Config:
        from_attributes = True


class LinkApprovalRequest(BaseModel):
    """Admin approval/rejection of link."""
    action: str = Field(..., pattern="^(approve|reject)$")
    reason: Optional[str] = None


class StudentProgressSummary(BaseModel):
    """Student progress summary for parent view."""
    student_id: int
    student_name: str
    student_username: str
    total_attempts: int
    average_score: Optional[float] = None
    last_attempt_at: Optional[datetime] = None
    recent_attempts: list = Field(default_factory=list)

    class Config:
        from_attributes = True


class StudentDetailForParent(BaseModel):
    """Detailed student info for parent view."""
    student_id: int
    student_name: str
    student_username: str
    email: str
    total_attempts: int
    average_score: Optional[float] = None
    standards_attempted: int
    recent_attempts: list = Field(default_factory=list)

    class Config:
        from_attributes = True


class ParentAssistantChatRequest(BaseModel):
    """Parent assistant chat request with optional UI-selected context."""
    message: str = Field(..., min_length=1, max_length=1000)
    thread_id: Optional[int] = None
    student_id: Optional[int] = None
    subject_id: Optional[int] = None
    grade_id: Optional[int] = None


class ParentAssistantChatResponse(BaseModel):
    """Parent assistant response for learning, syllabus, and quiz assignment tools."""
    intent: str
    answer: str
    thread_id: Optional[int] = None
    tool_name: Optional[str] = None
    requires_student: bool = False
    requires_subject: bool = False
    suggestions: list[str] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
