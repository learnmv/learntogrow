from fastapi import APIRouter, Depends
from typing import List

from app.dependencies import get_curriculum_service
from app.services import CurriculumService
from app.schemas import SubjectResponse

router = APIRouter(prefix="/subjects", tags=["subjects"])

@router.get("", response_model=List[SubjectResponse])
def get_subjects(
    service: CurriculumService = Depends(get_curriculum_service)
):
    return service.get_all_subjects()
