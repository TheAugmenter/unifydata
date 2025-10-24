"""
Organization Model
"""
from datetime import datetime
from typing import List
from sqlalchemy import String, DateTime, Integer, Boolean, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Organization(Base):
    """Organization/Company model"""

    __tablename__ = "organizations"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Organization details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))

    # Subscription
    plan: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="trial",
        server_default="trial"
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    subscription_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="trialing",
        server_default="trialing"
    )

    # Limits
    max_users: Mapped[int] = mapped_column(Integer, default=5, server_default="5")
    max_data_sources: Mapped[int] = mapped_column(
        Integer,
        default=3,
        server_default="3"
    )
    monthly_search_limit: Mapped[int] = mapped_column(
        Integer,
        default=1000,
        server_default="1000"
    )

    # Usage tracking
    current_users: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    current_data_sources: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0"
    )
    searches_this_month: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0"
    )

    # Settings
    settings: Mapped[dict | None] = mapped_column(Text)  # JSON stored as text
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

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

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="organization",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, plan={self.plan})>"
