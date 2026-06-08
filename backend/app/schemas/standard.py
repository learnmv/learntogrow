from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class StandardResponse(BaseModel):
    id: int
    code: str
    description: str
    cluster_id: Optional[int] = None
    grade_id: Optional[int] = None
    domain_id: Optional[int] = None
    keywords: Optional[List[str]] = None
    difficulty_base: Optional[float] = None
    conceptual_category: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class StandardFilter(BaseModel):
    grade_id: Optional[int] = None
    domain_id: Optional[int] = None
    cluster_id: Optional[int] = None
    min_difficulty: Optional[float] = None
    max_difficulty: Optional[float] = None
    search_query: Optional[str] = None
