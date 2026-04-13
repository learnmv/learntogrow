from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StudentProgressResponse(BaseModel):
    total_answered: int
    correct_count: int
    accuracy: Optional[float] = None
    standards_attempted: int
    recent_answers: List["RecentAnswerResponse"] = []

    class Config:
        from_attributes = True


class RecentAnswerResponse(BaseModel):
    question_id: int
    standard_code: str
    is_correct: bool
    answered_at: datetime

    class Config:
        from_attributes = True