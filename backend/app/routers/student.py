from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.services.student import StudentService
from app.routers.auth import require_role

router = APIRouter(prefix="/student", tags=["student"])


@router.get("/progress")
def get_own_progress(
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get the current student's progress summary."""
    service = StudentService(db)
    return service.get_progress_summary(current_user["user_id"])


@router.get("/attempts")
def get_own_attempts(
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get the current student's answer history."""
    service = StudentService(db)
    return service.get_answer_history(current_user["user_id"])


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