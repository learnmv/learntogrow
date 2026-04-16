from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_db
from app.services import AdminService
from app.routers.auth import require_role
from app.schemas.auth import UserResponse
from app.schemas.admin import (
    QuestionGenerateRequestAdmin,
    UserCreateAdmin,
    UserStatusUpdate,
    AdminDashboardStats,
)
from app.schemas.questions import QuestionResponse, QuestionEditRequest
from app.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/dashboard/stats", response_model=AdminDashboardStats)
def get_dashboard_stats(
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get admin dashboard statistics."""
    admin_service = AdminService(db)
    stats = admin_service.get_dashboard_stats()
    return AdminDashboardStats(**stats)


# ==================== User Management ====================

@router.get("/users", response_model=List[UserResponse])
def get_users(
    role: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get all users with optional role filter."""
    admin_service = AdminService(db)
    users = admin_service.get_all_users(role=role, skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreateAdmin,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    admin_service = AdminService(db)

    try:
        user = admin_service.create_user(user_data)
        return UserResponse.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    status_update: UserStatusUpdate,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a user account."""
    admin_service = AdminService(db)

    user = admin_service.update_user_status(user_id, status_update.is_active)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Delete a user permanently."""
    admin_service = AdminService(db)

    # Prevent deleting yourself
    if user_id == current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    success = admin_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return None


# ==================== Parent Link Approval ====================

@router.get("/pending-links")
def get_pending_parent_links(
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get all pending parent-student link requests."""
    from app.services import ParentService
    parent_service = ParentService(db)
    return parent_service.get_pending_links()


@router.post("/approve-link/{link_id}")
def approve_parent_link(
    link_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Approve a parent-student link request."""
    from app.services import ParentService
    parent_service = ParentService(db)

    success = parent_service.approve_link(link_id, current_user["user_id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link request not found or already processed"
        )

    return {"message": "Link request approved"}


@router.post("/reject-link/{link_id}")
def reject_parent_link(
    link_id: int,
    reason: Optional[str] = None,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Reject a parent-student link request."""
    from app.services import ParentService
    parent_service = ParentService(db)

    success = parent_service.reject_link(link_id, current_user["user_id"], reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link request not found or already processed"
        )

    return {"message": "Link request rejected"}


# ==================== Question Management ====================

@router.get("/questions", response_model=List[QuestionResponse])
def get_questions(
    standard_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get questions with filters."""
    admin_service = AdminService(db)
    questions = admin_service.get_questions(
        standard_id=standard_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return questions


@router.patch("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    updates: dict,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Update a question."""
    admin_service = AdminService(db)

    question = admin_service.update_question(question_id, updates)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return question


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Delete a question."""
    admin_service = AdminService(db)

    success = admin_service.delete_question(question_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return None


@router.post("/questions/{question_id}/toggle-status", response_model=QuestionResponse)
def toggle_question_status(
    question_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Toggle question active status."""
    admin_service = AdminService(db)

    question = admin_service.toggle_question_status(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found"
        )

    return question


# ==================== Question Generation ====================

@router.post("/generate-questions")
def generate_questions_admin(
    request: QuestionGenerateRequestAdmin,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Generate questions for selected standards.

    Supports generating questions based on:
    - Subject (required)
    - Grade (optional - all grades if not specified)
    - Domains (optional - all domains if not specified)
    - Specific standards (optional - all standards if not specified)
    - Difficulty range (optional)
    """
    admin_service = AdminService(db)

    # Get standards matching criteria
    standards = admin_service.get_standards_for_generation(
        subject_id=request.subject_id,
        grade_id=request.grade_id,
        domain_ids=request.domain_ids,
        difficulty_min=request.difficulty_min,
        difficulty_max=request.difficulty_max,
        only_diagram_questions=False
    )

    # Filter by specific standards if provided
    if request.standard_ids:
        standards = [s for s in standards if s.id in request.standard_ids]

    if not standards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No standards found matching the specified criteria"
        )

    # Generate questions
    standard_ids = [s.id for s in standards]

    results = admin_service.generate_questions_for_standards(
        standard_ids=standard_ids,
        questions_per_standard=request.questions_per_standard,
        question_type=request.question_type,
        model=request.model,
        timeout=request.timeout
    )

    return {
        "message": f"Question generation completed for {results['completed']} standards",
        "standards_matched": len(standards),
        "standards_completed": results["completed"],
        "standards_failed": results["failed"],
        "questions_created": results["questions_created"],
        "errors": results["errors"] if results["errors"] else None
    }


# ==================== Prompt Management ====================

@router.get("/prompts")
def get_prompts(
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get all prompt templates."""
    from app.models import QuestionPrompt
    from app.schemas.prompt import PromptResponse

    prompts = db.query(QuestionPrompt).order_by(QuestionPrompt.name).all()
    return [PromptResponse.model_validate(p) for p in prompts]


@router.get("/prompts/{name}")
def get_prompt(
    name: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get a specific prompt template by name."""
    from app.models import QuestionPrompt
    from app.schemas.prompt import PromptResponse

    prompt = db.query(QuestionPrompt).filter(QuestionPrompt.name == name).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{name}' not found"
        )
    return PromptResponse.model_validate(prompt)


@router.put("/prompts/{name}")
def update_prompt(
    name: str,
    updates: dict,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Update a prompt template."""
    from app.models import QuestionPrompt
    from app.schemas.prompt import PromptResponse, PromptUpdate

    # Validate input
    validated = PromptUpdate(**updates)

    prompt = db.query(QuestionPrompt).filter(QuestionPrompt.name == name).first()
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{name}' not found"
        )

    # Update fields
    prompt.content = validated.content
    if validated.description is not None:
        prompt.description = validated.description

    db.commit()
    db.refresh(prompt)
    return PromptResponse.model_validate(prompt)


@router.get("/prompt-placeholders")
def get_prompt_placeholders(
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get available placeholders for prompt templates."""
    from app.schemas.prompt import PromptPlaceholdersResponse, PromptPlaceholder

    placeholders = [
        PromptPlaceholder(
            placeholder="{question_type}",
            description="Question type (e.g., 'multiple choice', 'open ended')",
            example="multiple choice"
        ),
        PromptPlaceholder(
            placeholder="{grade_level}",
            description="Grade level number",
            example="6"
        ),
        PromptPlaceholder(
            placeholder="{standard_code}",
            description="Standard code identifier",
            example="6.EE.A.1"
        ),
        PromptPlaceholder(
            placeholder="{standard_description}",
            description="Full description of the standard",
            example="Write and evaluate numerical expressions involving whole-number exponents"
        ),
        PromptPlaceholder(
            placeholder="{difficulty:.1f}",
            description="Difficulty level from 0.0 to 1.0",
            example="0.7"
        ),
        PromptPlaceholder(
            placeholder="{keywords}",
            description="Comma-separated key concepts",
            example="expressions, exponents, evaluation"
        ),
        PromptPlaceholder(
            placeholder="{applet_type}",
            description="GeoGebra applet type (only for diagram questions)",
            example="graphing"
        ),
        PromptPlaceholder(
            placeholder="{applet_commands}",
            description="Available GeoGebra commands (only for diagram questions)",
            example="- Points: A = (1, 2)\\n- Lines: Line(A, B)"
        ),
        PromptPlaceholder(
            placeholder="{question_specific_requirements}",
            description="Additional requirements based on question type",
            example="Provide exactly 4 multiple choice options..."
        ),
        PromptPlaceholder(
            placeholder="{answer_field}",
            description="JSON field for answer based on question type",
            example='"answer": "the correct answer",'
        ),
    ]

    return PromptPlaceholdersResponse(placeholders=placeholders)
