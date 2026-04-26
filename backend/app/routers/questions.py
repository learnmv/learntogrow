from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional

from app.dependencies import get_db
from app.services.questions import QuestionService
from app.schemas.questions import (
    QuestionGenerateRequest,
    QuestionResponse,
    QuestionDBResponse
)
from app.services.adaptive import get_next_adaptive_question, update_theta_after_answer
from app.models import AnsweredQuestion, Question, Standard, Domain, StudentDomainAbility
from app.routers.auth import get_current_user, require_role

router = APIRouter(prefix="/questions", tags=["questions"])
security = HTTPBearer(auto_error=False)


@router.get("/adaptive", response_model=QuestionDBResponse)
def get_adaptive_question(
    domain_id: int = Query(..., description="Domain ID for adaptive question selection"),
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Serve the next question adaptively based on the student's current ability.

    - **domain_id**: The curriculum domain to pull a question from

    Algorithm:
    1. Fetches the student's theta (ability score) for this domain.
    2. Selects the active question with difficulty closest to theta.
    3. Excludes questions the student has already answered.
    """
    question = get_next_adaptive_question(
        db=db,
        student_id=current_user["user_id"],
        domain_id=domain_id,
    )
    if not question:
        raise HTTPException(
            status_code=404,
            detail="No active questions available for this domain. Please contact your teacher or try again later."
        )
    return question


@router.post("/generate", response_model=QuestionResponse)
def generate_question(
    request: QuestionGenerateRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a question using Ollama based on a curriculum standard.

    - **standard_id**: The ID of the curriculum standard to base the question on
    - **difficulty**: Optional override for difficulty (0-1, where 0=easy, 1=hard)
    - **question_type**: Type of question (multiple_choice, open_ended)
    - **custom_prompt**: Optional custom prompt to override the default template
    - **model**: Optional Ollama model override
    """
    service = QuestionService(db)

    try:
        result = service.generate_question(
            standard_id=request.standard_id,
            difficulty=request.difficulty,
            question_type=request.question_type,
            custom_prompt=request.custom_prompt,
            model=request.model,
            timeout=request.timeout
        )
        return result

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating question: {str(e)}")


@router.get("/standard/{standard_id}", response_model=List[QuestionDBResponse])
def get_questions_by_standard(
    standard_id: int,
    limit: Optional[int] = Query(None, ge=1, le=100, description="Maximum number of questions to return"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Fetch active questions for a specific standard.

    If the requester is an authenticated student, questions they have already
    answered will be excluded to avoid repetition.
    """
    student_id = None

    # Try to extract student identity from token (optional auth)
    if credentials:
        try:
            current_user = get_current_user(credentials, db)
            if current_user.get("role") == "student":
                student_id = current_user["user_id"]
        except HTTPException:
            pass  # Not authenticated or invalid token — return all questions

    service = QuestionService(db)
    questions = service.get_questions_by_standard(standard_id, limit=limit, student_id=student_id)
    return questions


@router.post("/answer", status_code=status.HTTP_201_CREATED)
def record_answer(
    data: dict,
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """
    Record that a student answered a question.

    Also recalculates the student's adaptive ability score (theta) for
    the question's domain.

    - **question_id**: The ID of the question answered
    - **selected_answer**: The answer the student selected
    - **is_correct**: Whether the answer is correct
    """
    question_id = data.get("question_id")
    selected_answer = data.get("selected_answer")
    is_correct = data.get("is_correct")

    if question_id is None or is_correct is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="question_id and is_correct are required"
        )

    # Verify the question exists
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found"
        )

    # Use INSERT ... ON CONFLICT DO NOTHING to avoid duplicates
    from sqlalchemy.dialects.postgresql import insert
    stmt = insert(AnsweredQuestion).values(
        student_id=current_user["user_id"],
        question_id=question_id,
        standard_id=question.standard_id,
        selected_answer=selected_answer,
        is_correct=is_correct,
    ).on_conflict_do_nothing(
        constraint='answered_questions_student_id_question_id_key'
    )
    db.execute(stmt)

    # Update adaptive ability (theta) — wrapped so answer recording never fails because of this
    try:
        std = db.query(Standard).filter(Standard.id == question.standard_id).first()
        if std:
            theta_result = update_theta_after_answer(
                db=db,
                student_id=current_user["user_id"],
                domain_id=std.domain_id,
                question_id=question_id,
                is_correct=is_correct,
            )
        else:
            theta_result = {"updated": False, "reason": "Standard not found"}
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Theta update failed after answer for student {current_user['user_id']}: {exc}")
        theta_result = {"updated": False, "reason": str(exc)}

    db.commit()

    return {
        "message": "Answer recorded successfully",
        "adaptive": theta_result,
    }


@router.get("/adaptive-domain", response_model=dict)
def get_adaptive_domain_summary(
    domain_id: int = Query(..., description="Domain ID"),
    current_user: dict = Depends(require_role(["student"])),
    db: Session = Depends(get_db)
):
    """Return the student's current theta and domain stats."""
    ability_record = db.query(StudentDomainAbility).filter(
        StudentDomainAbility.student_id == current_user["user_id"],
        StudentDomainAbility.domain_id == domain_id,
    ).first()

    domain = db.query(Domain).filter(Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    theta = float(ability_record.theta) if ability_record else 0.35
    questions_attempted = ability_record.questions_attempted if ability_record else 0
    correct_streak = ability_record.correct_streak if ability_record else 0

    return {
        "domain_id": domain_id,
        "domain_name": domain.name,
        "theta": theta,
        "questions_attempted": questions_attempted,
        "correct_streak": correct_streak,
    }