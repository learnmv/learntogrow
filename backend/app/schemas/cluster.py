from pydantic import BaseModel
from typing import Optional

class ClusterResponse(BaseModel):
    id: int
    code: str
    name: str
    domain_id: int
    grade_id: int

    class Config:
        from_attributes = True
