from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.dependencies import get_db
from app.services.student import StudentService
from app.routers.auth import require_role
from app.schemas.student import DailyGoalResponse, SkillMapDomainResponse, StudentProgressResponse
from app.schemas.quiz_assignment import QuizAssignmentDetail, QuizAssignmentSummary

router = APIRouter(prefix="/student", tags=["student"])


@router.get("/progress", response_model=StudentProgressResponse)
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


@router.get("/quiz-assignments", response_model=list[QuizAssignmentSummary])
def get_assigned_quizzes(
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get quizzes assigned to the current student."""
    service = StudentService(db)
    return service.get_quiz_assignments(current_user["user_id"])


@router.get("/quiz-assignments/{assignment_id}", response_model=QuizAssignmentDetail)
def get_assigned_quiz(
    assignment_id: int,
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Get an assigned quiz and its questions."""
    service = StudentService(db)
    try:
        return service.get_quiz_assignment(current_user["user_id"], assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/quiz-assignments/{assignment_id}/start", response_model=QuizAssignmentDetail)
def start_assigned_quiz(
    assignment_id: int,
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Mark an assigned quiz as in progress."""
    service = StudentService(db)
    try:
        return service.start_quiz_assignment(current_user["user_id"], assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/quiz-assignments/{assignment_id}/complete", response_model=QuizAssignmentDetail)
def complete_assigned_quiz(
    assignment_id: int,
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Mark an assigned quiz as completed."""
    service = StudentService(db)
    try:
        return service.complete_quiz_assignment(current_user["user_id"], assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
