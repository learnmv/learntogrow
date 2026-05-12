from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, JSON, String, Text, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class ParentAssistantThread(Base):
    """Conversation thread for the parent assistant."""
    __tablename__ = "parent_assistant_threads"

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    title = Column(String(150))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    parent = relationship("User", foreign_keys=[parent_id])
    student = relationship("User", foreign_keys=[student_id])
    messages = relationship(
        "ParentAssistantMessage",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ParentAssistantMessage.created_at",
    )
    tool_calls = relationship(
        "ParentAssistantToolCall",
        back_populates="thread",
        cascade="all, delete-orphan",
        order_by="ParentAssistantToolCall.created_at",
    )


class ParentAssistantMessage(Base):
    """Persisted parent or assistant chat message."""
    __tablename__ = "parent_assistant_messages"
    __table_args__ = (
        CheckConstraint("role IN ('parent', 'assistant', 'system')", name="ck_parent_assistant_message_role"),
    )

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("parent_assistant_threads.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    thread = relationship("ParentAssistantThread", back_populates="messages")


class ParentAssistantToolCall(Base):
    """Audited tool call made by the parent assistant."""
    __tablename__ = "parent_assistant_tool_calls"
    __table_args__ = (
        CheckConstraint("status IN ('running', 'completed', 'failed')", name="ck_parent_assistant_tool_status"),
    )

    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey("parent_assistant_threads.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(Integer, ForeignKey("parent_assistant_messages.id", ondelete="SET NULL"))
    tool_name = Column(String(80), nullable=False)
    arguments = Column(JSON, nullable=False, default=dict)
    result = Column(JSON)
    status = Column(String(20), nullable=False, default="running")
    error = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP)

    thread = relationship("ParentAssistantThread", back_populates="tool_calls")
    message = relationship("ParentAssistantMessage")
