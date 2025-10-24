"""
Conversation and Message Models for AI Q&A
"""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, JSON, Boolean, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Conversation(Base):
    """Conversation model for AI Q&A sessions"""

    __tablename__ = "conversations"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Organization relationship
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # User who created the conversation
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Conversation details
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Auto-generated or user-provided title"
    )

    # Settings
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="claude-3-5-sonnet-20241022",
        comment="AI model used for this conversation"
    )

    temperature: Mapped[float] = mapped_column(
        default=0.7,
        comment="Temperature for AI responses (0.0-1.0)"
    )

    # Statistics
    message_count: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))

    # Status
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    # Timestamps
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
        onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title[:50]})>"


class Message(Base):
    """Message model for conversation messages"""

    __tablename__ = "messages"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Conversation relationship
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message details
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="user or assistant"
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    # AI metadata (for assistant messages)
    model: Mapped[str | None] = mapped_column(String(100))
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)

    # Context used (for assistant messages)
    context_documents: Mapped[list | None] = mapped_column(
        JSON,
        comment="List of document IDs used for context"
    )

    search_query: Mapped[str | None] = mapped_column(
        Text,
        comment="Search query used to retrieve context"
    )

    # Response metadata
    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        comment="Time taken to generate response (ms)"
    )

    # Feedback
    thumbs_up: Mapped[bool | None] = mapped_column(Boolean)
    feedback_text: Mapped[str | None] = mapped_column(Text)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()")
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"


class UsageLog(Base):
    """Usage tracking for analytics"""

    __tablename__ = "usage_logs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Organization relationship
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # User relationship
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="search, chat, sync, etc."
    )

    event_subtype: Mapped[str | None] = mapped_column(
        String(100),
        comment="Specific action within event type"
    )

    # Metadata
    event_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Additional event data"
    )

    # AI usage
    model_used: Mapped[str | None] = mapped_column(String(100))
    tokens_input: Mapped[int | None] = mapped_column(Integer)
    tokens_output: Mapped[int | None] = mapped_column(Integer)

    # Cost tracking (optional)
    cost_usd: Mapped[float | None] = mapped_column(
        comment="Estimated cost in USD"
    )

    # Performance
    response_time_ms: Mapped[int | None] = mapped_column(Integer)

    # Success/failure
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="success",
        comment="success, error, timeout"
    )

    error_message: Mapped[str | None] = mapped_column(Text)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()"),
        index=True
    )

    def __repr__(self) -> str:
        return f"<UsageLog(id={self.id}, event_type={self.event_type}, org_id={self.org_id})>"
