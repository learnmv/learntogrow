from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SubjectResponse(BaseModel):
    id: int
    code: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
