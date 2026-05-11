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


class DailyGoalResponse(BaseModel):
    target: int
    answered_today: int
    correct_today: int
    remaining: int
    completed: bool
    progress: float
    message: str


class SkillMapDomainResponse(BaseModel):
    domain_id: int
    domain_name: str
    domain_code: str
    progress: float
    level: str
    level_description: str
    questions_attempted: int
    correct_count: int
    incorrect_count: int
    accuracy: Optional[float] = None
    correct_streak: int
    total_standards: int
    active_questions: int
    recommended: bool
    recommendation_reason: str
    sort_priority: int
