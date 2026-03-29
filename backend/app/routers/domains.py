from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.dependencies import get_curriculum_service
from app.services import CurriculumService
from app.schemas import DomainResponse
from app.models import Domain

router = APIRouter(prefix="/domains", tags=["domains"])

@router.get("", response_model=List[DomainResponse])
def get_domains(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    service: CurriculumService = Depends(get_curriculum_service)
):
    if subject_id:
        return service.db.query(Domain).filter(Domain.subject_id == subject_id).all()
    return service.db.query(Domain).all()
