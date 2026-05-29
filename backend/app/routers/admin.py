from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, AsyncIterator
import asyncio
import json
import httpx

from app.dependencies import get_db
from app.services import AdminService, QuestionGenerationJobService
from app.services.admin_chat import AdminChatService
from app.routers.auth import require_role
from app.schemas.auth import UserResponse
from app.schemas.admin import (
    QuestionGenerateRequestAdmin,
    UserCreateAdmin,
    UserStatusUpdate,
    AdminDashboardStats,
    BulkDeleteRequest,
    SmartFillRequest,
    ClusterCoveragePlanRequest,
    ClusterCoverageJobRequest,
    ClusterCoveragePlanResponse,
    AdminChatRequest,
    AdminChatResponse,
)
from app.schemas.generation_job import (
    GenerationJobCreateRequest,
    GenerationJobResponse,
    GenerationJobDetailResponse,
    GenerationJobListParams,
)
from app.schemas.questions import QuestionDBResponse
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


# ==================== Admin Model Chat ====================

@router.post("/chat", response_model=AdminChatResponse)
def chat_with_model(
    request: AdminChatRequest,
    current_user: dict = Depends(require_role(["admin"])),
):
    """Chat directly with the configured Ollama model."""
    service = AdminChatService()
    try:
        return service.chat(request.messages, request.temperature)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="The model took too long to respond",
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not connect to Ollama",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ollama returned HTTP {exc.response.status_code}",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )


# ==================== Question Management ====================

@router.get("/questions", response_model=List[QuestionDBResponse])
def get_questions(
    standard_id: Optional[int] = None,
    domain_id: Optional[int] = None,
    grade_id: Optional[int] = None,
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
        domain_id=domain_id,
        grade_id=grade_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return questions


@router.patch("/questions/{question_id}", response_model=QuestionDBResponse)
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


@router.post("/questions/{question_id}/toggle-status", response_model=QuestionDBResponse)
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


@router.post("/questions/bulk-delete")
def bulk_delete_questions(
    request: BulkDeleteRequest,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Delete multiple questions or all questions matching filters."""
    admin_service = AdminService(db)

    if request.all_matching:
        count = admin_service.delete_questions_by_filters(
            standard_id=request.standard_id,
            domain_id=request.domain_id,
            grade_id=request.grade_id,
            is_active=request.is_active
        )
    else:
        if not request.question_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either question_ids or all_matching must be provided"
            )
        count = admin_service.delete_questions_by_ids(request.question_ids)

    return {"deleted": count}


# ==================== Question Generation (legacy — now async) ====================

@router.post("/generate-questions", response_model=GenerationJobResponse)
def generate_questions_admin(
    request: QuestionGenerateRequestAdmin,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """Generate questions for selected standards (async, returns job immediately).

    **Deprecated in favor of POST /admin/generation-jobs** — this endpoint
    is kept for backward compatibility but now returns a generation job
    instead of blocking until completion.
    """
    admin_service = AdminService(db)

    # Resolve standards using the same filtering logic
    standards = admin_service.get_standards_for_generation(
        subject_id=request.subject_id,
        grade_id=request.grade_id,
        domain_ids=request.domain_ids,
        difficulty_min=request.difficulty_min,
        difficulty_max=request.difficulty_max,
        only_diagram_questions=False,
    )

    if request.standard_ids:
        standards = [s for s in standards if s.id in request.standard_ids]

    if not standards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No standards found matching the specified criteria",
        )

    # Create async job
    job_service = QuestionGenerationJobService(db)
    job = job_service.create_job(
        standard_ids=[s.id for s in standards],
        questions_per_standard=request.questions_per_standard,
        question_type=request.question_type,
        model=request.model,
        timeout=request.timeout,
        quality_mode=request.quality_mode,
        candidate_count=request.candidate_count,
        max_repair_attempts=request.max_repair_attempts,
        min_review_score=request.min_review_score,
        subject_id=request.subject_id,
        grade_id=request.grade_id,
        created_by=current_user.get("user_id"),
    )

    # Start in background
    background_tasks.add_task(
        QuestionGenerationJobService.run_job,
        job_id=job.id,
        question_type=request.question_type,
        model=request.model,
        timeout=request.timeout,
        quality_mode=job.quality_mode,
        candidate_count=job.candidate_count,
        max_repair_attempts=job.max_repair_attempts,
        min_review_score=float(job.min_review_score),
    )

    return job


# ==================== Async Generation Jobs ====================

@router.post("/generation-jobs", response_model=GenerationJobResponse, status_code=status.HTTP_201_CREATED)
def create_generation_job(
    request: GenerationJobCreateRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Create an async generation job and start it in the background.

    Returns immediately with the job details. The job runs in a background
    task so the admin gets a job ID to poll for progress.
    """
    service = QuestionGenerationJobService(db)

    job = service.create_job(
        standard_ids=request.standard_ids,
        questions_per_standard=request.questions_per_standard,
        question_type=request.question_type,
        model=request.model,
        timeout=request.timeout,
        quality_mode=request.quality_mode,
        candidate_count=request.candidate_count,
        max_repair_attempts=request.max_repair_attempts,
        min_review_score=request.min_review_score,
        subject_id=request.subject_id,
        grade_id=request.grade_id,
        created_by=current_user.get("user_id"),
    )

    # Start background execution
    background_tasks.add_task(
        QuestionGenerationJobService.run_job,
        job_id=job.id,
        question_type=request.question_type,
        model=request.model,
        timeout=request.timeout,
        quality_mode=job.quality_mode,
        candidate_count=job.candidate_count,
        max_repair_attempts=job.max_repair_attempts,
        min_review_score=float(job.min_review_score),
    )

    return job


@router.post("/coverage-plan", response_model=ClusterCoveragePlanResponse)
def create_cluster_coverage_plan(
    request: ClusterCoveragePlanRequest,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """Preview a cluster coverage plan before creating a generation job."""
    service = QuestionGenerationJobService(db)
    try:
        return service.build_cluster_coverage_plan(
            grade_id=request.grade_id,
            cluster_ids=request.cluster_ids,
            coverage_goal=request.coverage_goal,
            target_per_band=request.target_per_band,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.post("/coverage-jobs", response_model=GenerationJobResponse, status_code=status.HTTP_201_CREATED)
def create_cluster_coverage_job(
    request: ClusterCoverageJobRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    """Create a generation job from an explicit cluster coverage plan."""
    service = QuestionGenerationJobService(db)
    try:
        plan = service.build_cluster_coverage_plan(
            grade_id=request.grade_id,
            cluster_ids=request.cluster_ids,
            coverage_goal=request.coverage_goal,
            target_per_band=request.target_per_band,
        )
        if not plan["items"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selected clusters already satisfy this coverage goal",
            )
        job = service.create_planned_job(
            plan_items=plan["items"],
            question_type=request.question_type,
            model=request.model,
            timeout=request.timeout,
            quality_mode=request.quality_mode,
            candidate_count=request.candidate_count,
            max_repair_attempts=request.max_repair_attempts,
            min_review_score=request.min_review_score,
            subject_id=request.subject_id,
            grade_id=request.grade_id,
            created_by=current_user.get("user_id"),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    background_tasks.add_task(
        QuestionGenerationJobService.run_job,
        job_id=job.id,
        question_type=job.question_type or "multiple_choice",
        model=job.model,
        timeout=job.timeout or 300,
        quality_mode=job.quality_mode,
        candidate_count=job.candidate_count,
        max_repair_attempts=job.max_repair_attempts,
        min_review_score=float(job.min_review_score or 0.75),
    )
    return job


@router.get("/generation-jobs", response_model=List[GenerationJobResponse])
def list_generation_jobs(
    status: Optional[str] = Query(None, description="Filter by job status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """List generation jobs ordered by newest first."""
    service = QuestionGenerationJobService(db)
    jobs = service.get_jobs(status=status, skip=skip, limit=limit)
    return jobs


@router.get("/generation-jobs/{job_id}", response_model=GenerationJobDetailResponse)
def get_generation_job(
    job_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get a single generation job with per-standard progress details."""
    service = QuestionGenerationJobService(db)
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job {job_id} not found"
        )
    return job


@router.get("/generation-jobs/{job_id}/progress")
async def job_progress_stream(
    job_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Server-Sent Events stream for real-time job progress.

    Yields JSON events every 2 seconds while the job is pending or running.
    Automatically closes when the job reaches a terminal state
    (completed, failed, cancelled).
    """
    service = QuestionGenerationJobService(db)

    job = service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation job {job_id} not found"
        )

    async def event_generator() -> AsyncIterator[str]:
        terminal = {"completed", "failed", "cancelled"}
        while True:
            fresh_db = next(get_db())
            try:
                fresh_service = QuestionGenerationJobService(fresh_db)
                current = fresh_service.get_job(job_id)
                if not current:
                    payload = json.dumps({"error": "Job not found"})
                    yield f"event: error\ndata: {payload}\n\n"
                    break

                payload = json.dumps({
                    "job_id": current.id,
                    "status": current.status,
                    "total_standards": current.total_standards,
                    "completed_standards": current.completed_standards,
                    "failed_standards": current.failed_standards,
                    "questions_created": current.questions_created,
                    "quality_mode": current.quality_mode,
                    "candidate_count": current.candidate_count,
                    "max_repair_attempts": current.max_repair_attempts,
                    "min_review_score": float(current.min_review_score or 0.75),
                    "errors": current.errors or [],
                    "started_at": current.started_at.isoformat() if current.started_at else None,
                    "completed_at": current.completed_at.isoformat() if current.completed_at else None,
                    "standards": [
                        {
                            "standard_id": js.standard_id,
                            "status": js.status,
                            "questions_created": js.questions_created,
                            "error": js.error,
                            "avg_quality_score": js.avg_quality_score,
                            "quality_summary": js.quality_summary,
                        }
                        for js in current.job_standards
                    ] if current.job_standards else [],
                })
                yield f"data: {payload}\n\n"

                if current.status in terminal:
                    break

                await asyncio.sleep(2)
            finally:
                fresh_db.close()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/generation-jobs/{job_id}")
def cancel_generation_job(
    job_id: int,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Cancel a pending or running generation job."""
    service = QuestionGenerationJobService(db)
    try:
        job = service.cancel_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generation job {job_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return {"message": "Job cancelled"}


@router.post("/generation-jobs/{job_id}/retry", response_model=GenerationJobResponse)
def retry_failed_standards(
    job_id: int,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Create a new job retrying only the failed standards from a previous job."""
    service = QuestionGenerationJobService(db)
    try:
        original_job = service.get_job(job_id)
        if not original_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Generation job {job_id} not found"
            )

        new_job = service.retry_failed_standards(job_id)

        # Start the new job in the background using stored params
        background_tasks.add_task(
            QuestionGenerationJobService.run_job,
            job_id=new_job.id,
            question_type=new_job.question_type or "multiple_choice",
            model=new_job.model,
            timeout=new_job.timeout or 300,
            quality_mode=new_job.quality_mode,
            candidate_count=new_job.candidate_count,
            max_repair_attempts=new_job.max_repair_attempts,
            min_review_score=float(new_job.min_review_score or 0.75),
        )

        return new_job

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Question Insights ====================

@router.get("/question-insights")
def get_question_insights(
    subject_id: Optional[int] = None,
    grade_id: Optional[int] = None,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get insights about question coverage and student performance per domain."""
    admin_service = AdminService(db)
    return admin_service.get_question_insights(subject_id, grade_id)


@router.post("/smart-fill-suggestions")
def get_smart_fill_suggestions(
    request: SmartFillRequest,
    current_user: dict = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    """Get smart suggestions for question generation based on gaps and student data."""
    admin_service = AdminService(db)
    return admin_service.get_smart_fill_suggestions(
        subject_id=request.subject_id,
        grade_id=request.grade_id,
        fill_mode=request.fill_mode,
        max_standards=request.max_standards
    )


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
