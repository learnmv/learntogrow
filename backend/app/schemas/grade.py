from pydantic import BaseModel
from typing import Optional

class GradeResponse(BaseModel):
    id: int
    level: int
    subject_id: int
    display_name: Optional[str] = None

    class Config:
        from_attributes = True
