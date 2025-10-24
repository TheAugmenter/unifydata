"""
Document Model for storing parsed content
"""
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, JSON, BigInteger
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Document(Base):
    """Document model for storing parsed content from data sources"""

    __tablename__ = "documents"

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
        nullable=False,
        index=True
    )

    # Organization relationship (denormalized for faster queries)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Document identification
    external_id: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="External ID from the source (e.g., file ID, message ID)"
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="salesforce, slack, google_drive, notion, gmail"
    )

    # Document metadata
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="document, email, message, page, file"
    )
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_extension: Mapped[str | None] = mapped_column(String(50))

    # URLs and paths
    url: Mapped[str | None] = mapped_column(Text, comment="URL to access the document")
    file_path: Mapped[str | None] = mapped_column(Text, comment="Path in the source system")

    # Size and statistics
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    word_count: Mapped[int | None] = mapped_column(Integer)
    char_count: Mapped[int | None] = mapped_column(Integer)

    # Vector embedding
    embedding_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("pending"),
        comment="pending, processing, completed, failed"
    )
    vector_id: Mapped[str | None] = mapped_column(
        String(500),
        comment="ID of the vector in Pinecone"
    )
    embedding_model: Mapped[str | None] = mapped_column(
        String(100),
        comment="Model used for embeddings (e.g., text-embedding-ada-002)"
    )
    embedding_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Source-specific metadata
    source_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        comment="Additional metadata from the source (author, tags, etc.)"
    )

    # Document timestamps from source
    source_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Processing status
    parse_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("pending"),
        comment="pending, processing, completed, failed"
    )
    parse_error: Mapped[str | None] = mapped_column(Text)

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        server_default=text("false"),
        comment="Soft delete flag"
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Timestamps
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
        return f"<Document(id={self.id}, title={self.title[:50]}, source={self.source_type})>"


class DocumentChunk(Base):
    """Document chunks for better vector search (split large documents)"""

    __tablename__ = "document_chunks"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Document relationship
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Chunk details
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Index of the chunk in the document (0-based)"
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False)

    # Vector embedding
    vector_id: Mapped[str | None] = mapped_column(
        String(500),
        comment="ID of the vector in Pinecone"
    )
    embedding_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        server_default=text("pending"),
        comment="pending, processing, completed, failed"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        server_default=text("now()")
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id}, chunk={self.chunk_index})>"
