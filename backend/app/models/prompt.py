"""Prompt template model for admin-editable LLM prompts."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class QuestionPrompt(Base):
    """Admin-editable prompt templates for question generation."""
    __tablename__ = "question_prompts"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<QuestionPrompt(id={self.id}, name='{self.name}')>"