from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric, TIMESTAMP, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Question(Base):
    """Generated questions with metadata and optional GeoGebra diagrams."""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    standard_id = Column(Integer, ForeignKey("standards.id", ondelete="CASCADE"), nullable=False)

    # Core question content
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False, default="multiple_choice")
    options = Column(JSON)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text)

    # Metadata
    difficulty = Column(Numeric(3, 2))
    requires_diagram = Column(Boolean, default=False)
    applet_type = Column(String(20))
    geogebra_commands = Column(JSON)
    applet_config = Column(JSON)
    generation_signature = Column(JSON)
    math_spec = Column(JSON)
    semantic_hash = Column(String(128))
    quality_score = Column(Numeric(4, 3))

    # Tracking
    created_at = Column(TIMESTAMP, default=datetime.utcnow, server_default=func.now())
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now())
    generated_by = Column(String(100))
    is_active = Column(Boolean, default=True)

    # Relationships
    standard = relationship("Standard", backref="questions")
