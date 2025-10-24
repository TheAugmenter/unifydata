"""
Data Source Model
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text, Integer, JSON, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class DataSource(Base):
    """Data Source model for connected integrations"""

    __tablename__ = "data_sources"

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
        nullable=False
    )

    # User who connected this source
    connected_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Source details
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="salesforce, slack, google_drive, notion, gmail"
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # Connection status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="connected",
        server_default="connected",
        comment="connected, disconnected, error, syncing"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # OAuth credentials (encrypted)
    access_token: Mapped[str | None] = mapped_column(Text)
    refresh_token: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Source-specific configuration
    config: Mapped[dict | None] = mapped_column(JSON)  # JSON configuration

    # Sync information
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_sync_status: Mapped[str | None] = mapped_column(
        String(50),
        comment="success, failed, in_progress"
    )
    last_sync_error: Mapped[str | None] = mapped_column(Text)
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_frequency: Mapped[int] = mapped_column(
        Integer,
        default=3600,
        server_default="3600",
        comment="Sync frequency in seconds (default: 1 hour)"
    )

    # Statistics
    total_documents: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    total_sync_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed_sync_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Timestamps
    connected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()")
    )
    disconnected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        return f"<DataSource(id={self.id}, type={self.source_type}, org_id={self.org_id})>"


class SyncLog(Base):
    """Sync Log model for tracking sync history"""

    __tablename__ = "sync_logs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Data source relationship
    data_source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="CASCADE"),
        nullable=False
    )

    # Sync details
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="in_progress, success, failed, cancelled"
    )
    sync_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="manual, automatic, initial"
    )

    # Progress
    documents_processed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    documents_added: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    documents_updated: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    documents_deleted: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    # Error information
    error_message: Mapped[str | None] = mapped_column(Text)
    error_details: Mapped[dict | None] = mapped_column(JSON)

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()")
    )

    def __repr__(self) -> str:
        return f"<SyncLog(id={self.id}, data_source_id={self.data_source_id}, status={self.status})>"
