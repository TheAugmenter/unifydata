"""
Organization Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class OrganizationBase(BaseModel):
    """Base organization schema"""
    name: str = Field(..., min_length=1, max_length=255)
    website: Optional[str] = Field(None, max_length=255)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""
    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logo_url: Optional[str] = None
    website: Optional[str] = Field(None, max_length=255)


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""
    id: uuid.UUID
    slug: str
    logo_url: Optional[str] = None
    plan: str
    trial_ends_at: Optional[datetime] = None
    subscription_status: str
    max_users: int
    max_data_sources: int
    monthly_search_limit: int
    current_users: int
    current_data_sources: int
    searches_this_month: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
