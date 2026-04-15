"""Pydantic schemas for prompt template API."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PromptResponse(BaseModel):
    """Response schema for prompt template."""
    id: int
    name: str
    content: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptUpdate(BaseModel):
    """Request schema for updating a prompt template."""
    content: str
    description: Optional[str] = None


class PromptPlaceholder(BaseModel):
    """Information about a placeholder in a prompt template."""
    placeholder: str
    description: str
    example: str


class PromptPlaceholdersResponse(BaseModel):
    """Response with available placeholders for prompt templates."""
    placeholders: list[PromptPlaceholder]