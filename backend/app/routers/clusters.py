from fastapi import APIRouter, Depends, Query
from typing import List, Optional

from app.dependencies import get_curriculum_service
from app.services import CurriculumService
from app.schemas import ClusterResponse
from app.models import Cluster

router = APIRouter(prefix="/clusters", tags=["clusters"])

@router.get("", response_model=List[ClusterResponse])
def get_clusters(
    domain_id: Optional[int] = Query(None, description="Filter by domain ID"),
    grade_id: Optional[int] = Query(None, description="Filter by grade ID"),
    service: CurriculumService = Depends(get_curriculum_service)
):
    if domain_id and grade_id:
        return service.get_clusters_by_grade_and_domain(grade_id, domain_id)
    elif domain_id:
        return service.get_clusters_by_domain(domain_id)
    return service.db.query(Cluster).all()
