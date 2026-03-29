from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.services.questions import QuestionService
from app.schemas.questions import QuestionGenerateRequest, QuestionResponse

router = APIRouter(prefix="/questions", tags=["questions"])


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
            model=request.model
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
