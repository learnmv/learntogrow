from pydantic import BaseModel
from typing import Optional

class DomainResponse(BaseModel):
    id: int
    code: str
    name: str
    subject_id: int
    display_order: int = 0

    class Config:
        from_attributes = True
