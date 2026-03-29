from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.dependencies import get_curriculum_service
from app.services import CurriculumService
from app.schemas import GradeResponse
from app.models import Grade

router = APIRouter(prefix="/grades", tags=["grades"])

@router.get("", response_model=List[GradeResponse])
def get_grades(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    service: CurriculumService = Depends(get_curriculum_service)
):
    if subject_id:
        return service.get_grades_by_subject(subject_id)
    return service.db.query(Grade).all()
