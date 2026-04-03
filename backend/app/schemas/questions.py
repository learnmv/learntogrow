from pydantic import BaseModel, Field
from typing import Optional, List

from app.prompts import AppletType


class QuestionGenerateRequest(BaseModel):
    """Request body for generating a question."""
    standard_id: int = Field(..., description="ID of the curriculum standard")
    difficulty: Optional[float] = Field(
        None, ge=0, le=1,
        description="Override difficulty (0=easy, 1=hard). Uses standard's difficulty if not provided."
    )
    question_type: str = Field(
        default="multiple_choice",
        description="Type of question: multiple_choice, open_ended, etc."
    )
    custom_prompt: Optional[str] = Field(
        None,
        description="Optional custom prompt to override the default template"
    )
    model: Optional[str] = Field(
        None,
        description="Optional model override (defaults to OLLAMA_MODEL env var)"
    )


class QuestionResponse(BaseModel):
    """Response containing a generated question."""
    question: str = Field(..., description="The question text")
    options: Optional[List[str]] = Field(
        None,
        description="Multiple choice options (if applicable)"
    )
    answer: str = Field(..., description="The correct answer")
    explanation: Optional[str] = Field(
        None,
        description="Explanation of the answer"
    )
    standard_code: str = Field(..., description="Code of the standard used")
    difficulty: float = Field(..., description="Difficulty level of the question")
    question_type: str = Field(..., description="Type of question generated")
    requires_diagram: Optional[bool] = Field(
        None,
        description="Whether this question includes a GeoGebra diagram"
    )
    applet_type: Optional[AppletType] = Field(
        None,
        description="GeoGebra applet type if requires_diagram is True"
    )
    geogebra_commands: Optional[List[str]] = Field(
        None,
        description="GeoGebra commands to create the diagram"
    )
    applet_config: Optional[dict] = Field(
        None,
        description="GeoGebra applet configuration"
    )

    class Config:
        from_attributes = True
