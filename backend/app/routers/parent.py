from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.dependencies import get_db
from app.services import ParentService
from app.routers.auth import require_role
from app.schemas.parent import (
    ParentStudentLinkResponse,
    ParentStudentLinkCreate,
    ParentAssistantChatRequest,
    ParentAssistantChatResponse,
    StudentDetailForParent,
)
from app.schemas.quiz_assignment import (
    QuizAssignmentCreateRequest,
    QuizAssignmentDetail,
    QuizAssignmentSummary,
)

router = APIRouter(prefix="/parent", tags=["parent"])


@router.get("/children", response_model=List[ParentStudentLinkResponse])
def get_linked_children(
    current_user: dict = Depends(require_role(["parent"])),
    db: Session = Depends(get_db)
):
    """Get all students linked to the current parent."""
    parent_service = ParentService(db)
    return parent_service.get_linked_students(current_user["user_id"])


@router.post("/link-request", status_code=status.HTTP_201_CREATED)
def request_student_link(
    request: ParentStudentLinkCreate,
    current_user: dict = Depends(require_role(["parent"])),
    db: Session = Depends(get_db)
):
    """Request to link with a student."""
    parent_service = ParentService(db)

    try:
        link = parent_service.request_student_link(
            parent_id=current_user["user_id"],
            student_email_or_username=request.student_email_or_username
        )
        return {
            "message": "Link request submitted. Waiting for admin approval.",
            "link_id": link.id,
            "status": link.status.value
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/child/{student_id}/progress", response_model=StudentDetailForParent)
def get_child_progress(
    student_id: int,
    current_user: dict = Depends(require_role(["parent"])),
    db: Session = Depends(get_db)
):
    """Get detailed progress for a linked child."""
    parent_service = ParentService(db)

    try:
        return parent_service.get_student_detail_for_parent(
            parent_id=current_user["user_id"],
            student_id=student_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/assistant/chat", response_model=ParentAssistantChatResponse)
def chat_with_parent_assistant(
    request: ParentAssistantChatRequest,
    current_user: dict = Depends(require_role(["parent"])),
    db: Session = Depends(get_db)
):
    """Ask the parent assistant about linked children or curriculum syllabus."""
    parent_service = ParentService(db)
    return parent_service.handle_assistant_chat(
        parent_id=current_user["user_id"],
        request=request,
    )


@router.post("/quiz-assignments", response_model=QuizAssignmentDetail, status_code=status.HTTP_201_CREATED)
def create_quiz_assignment(
    request: QuizAssignmentCreateRequest,
    current_user: dict = Depends(require_role(["parent"])),
    db: Session = Depends(get_db)
):
    """Create a quiz assignment for a linked child using existing questions."""
    parent_service = ParentService(db)
    try:
        return parent_service.create_quiz_assignment(
            parent_id=current_user["user_id"],
            request=request,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/quiz-assignments", response_model=List[QuizAssignmentSummary])
def get_quiz_assignments(
    current_user: dict = Depends(require_role(["parent"])),
    db: Session = Depends(get_db)
):
    """List quiz assignments created by the current parent."""
    parent_service = ParentService(db)
    return parent_service.get_quiz_assignments_for_parent(current_user["user_id"])


@router.get("/quiz-assignments/{assignment_id}", response_model=QuizAssignmentDetail)
def get_quiz_assignment(
    assignment_id: int,
    current_user: dict = Depends(require_role(["parent"])),
    db: Session = Depends(get_db)
):
    """Get a quiz assignment created by the current parent."""
    parent_service = ParentService(db)
    try:
        return parent_service.get_quiz_assignment_for_parent(current_user["user_id"], assignment_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
