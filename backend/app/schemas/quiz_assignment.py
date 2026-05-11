from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.questions import QuestionDBResponse


class QuizAssignmentCreateRequest(BaseModel):
    student_id: int
    title: str = Field(..., min_length=3, max_length=150)
    description: Optional[str] = Field(None, max_length=500)
    subject_id: Optional[int] = None
    grade_id: Optional[int] = None
    domain_ids: list[int] = Field(default_factory=list)
    standard_ids: list[int] = Field(default_factory=list)
    difficulty: str = Field("medium", pattern="^(easy|medium|hard|mixed)$")
    question_count: int = Field(5, ge=1, le=25)
    due_at: Optional[datetime] = None


class QuizAssignmentSummary(BaseModel):
    id: int
    parent_id: int
    student_id: int
    student_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    difficulty: str
    status: str
    question_count: int
    answered_count: int = 0
    correct_count: int = 0
    subject_id: Optional[int] = None
    subject_name: Optional[str] = None
    grade_id: Optional[int] = None
    grade_name: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    due_at: Optional[datetime] = None


class QuizAssignmentAnswerState(BaseModel):
    question_id: int
    selected_answer: Optional[str] = None
    is_correct: bool
    answered_at: Optional[datetime] = None


class QuizAssignmentDetail(QuizAssignmentSummary):
    questions: list[QuestionDBResponse] = Field(default_factory=list)
    answers: list[QuizAssignmentAnswerState] = Field(default_factory=list)
