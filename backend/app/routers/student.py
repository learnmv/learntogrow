from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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