from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.services.student import StudentService
from app.routers.auth import require_role
from app.schemas.student import DailyGoalResponse, SkillMapDomainResponse

router = APIRouter(prefix="/student", tags=["student"])


@router.get("/progress")
def get_own_progress(
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get the current student's progress summary."""
    service = StudentService(db)
    return service.get_progress_summary(current_user["user_id"])


@router.get("/daily-goal", response_model=DailyGoalResponse)
def get_daily_goal(
    target: int = Query(10, ge=1, le=50, description="Daily question target"),
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get the current student's daily practice goal."""
    service = StudentService(db)
    return service.get_daily_goal(current_user["user_id"], target=target)


@router.get("/skill-map", response_model=list[SkillMapDomainResponse])
def get_skill_map(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    grade_id: Optional[int] = Query(None, description="Filter by grade ID"),
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get the student's skill map by curriculum domain."""
    service = StudentService(db)
    return service.get_skill_map(
        current_user["user_id"],
        subject_id=subject_id,
        grade_id=grade_id,
    )


@router.get("/mistake-standards")
def get_mistake_standards(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    grade_id: Optional[int] = Query(None, description="Filter by grade ID"),
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get standards the student answered incorrectly.

    - **subject_id**: Optional filter for subject
    - **grade_id**: Optional filter for grade
    """
    service = StudentService(db)
    return service.get_mistake_standards(
        current_user["user_id"],
        subject_id=subject_id,
        grade_id=grade_id
    )
