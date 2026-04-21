from pydantic import BaseModel, Field
from typing import List, Optional


class DomainProgressResponse(BaseModel):
    """Student progress for a single domain."""
    domain_id: int
    domain_name: str
    domain_code: str
    total_answered: int
    correct_count: int
    accuracy: float
    current_difficulty: float
    last_answered_at: Optional[str] = None


class StrengthWeaknessItem(BaseModel):
    """A domain that's either a strength or weakness."""
    domain_id: int
    domain_name: str
    domain_code: str
    accuracy: float
    total_answered: int
    recommendation: str


class StudentStrengthsWeaknesses(BaseModel):
    """Student strengths and weaknesses overview."""
    strengths: List[StrengthWeaknessItem]
    weaknesses: List[StrengthWeaknessItem]
    recommendations: List[str]
