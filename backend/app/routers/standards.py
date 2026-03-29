from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.dependencies import get_curriculum_service
from app.services import CurriculumService
from app.schemas import StandardResponse, StandardFilter

router = APIRouter(prefix="/standards", tags=["standards"])

@router.get("", response_model=List[StandardResponse])
def get_standards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    grade_id: Optional[int] = Query(None),
    domain_id: Optional[int] = Query(None),
    cluster_id: Optional[int] = Query(None),
    min_difficulty: Optional[float] = Query(None, ge=0, le=1),
    max_difficulty: Optional[float] = Query(None, ge=0, le=1),
    service: CurriculumService = Depends(get_curriculum_service)
):
    filters = StandardFilter(
        grade_id=grade_id,
        domain_id=domain_id,
        cluster_id=cluster_id,
        min_difficulty=min_difficulty,
        max_difficulty=max_difficulty
    )
    return service.get_standards(filters, skip=skip, limit=limit)
