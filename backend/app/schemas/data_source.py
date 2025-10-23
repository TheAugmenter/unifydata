"""
Data Source Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class DataSourceBase(BaseModel):
    """Base data source schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class DataSourceCreate(DataSourceBase):
    """Schema for creating a data source"""
    source_type: str = Field(
        ...,
        description="Type of data source (salesforce, slack, google_drive, notion, gmail)"
    )


class DataSourceUpdate(BaseModel):
    """Schema for updating a data source"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DataSourceResponse(DataSourceBase):
    """Schema for data source response"""
    id: uuid.UUID
    org_id: uuid.UUID
    connected_by_user_id: Optional[uuid.UUID]
    source_type: str
    status: str
    is_active: bool
    last_sync_at: Optional[datetime]
    last_sync_status: Optional[str]
    next_sync_at: Optional[datetime]
    sync_frequency: int
    total_documents: int
    total_sync_count: int
    failed_sync_count: int
    connected_at: datetime
    disconnected_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DataSourceListResponse(BaseModel):
    """Schema for list of data sources"""
    data_sources: list[DataSourceResponse]
    total: int


class SyncTriggerResponse(BaseModel):
    """Schema for sync trigger response"""
    message: str
    sync_log_id: uuid.UUID
    data_source_id: uuid.UUID


class SyncLogResponse(BaseModel):
    """Schema for sync log response"""
    id: uuid.UUID
    data_source_id: uuid.UUID
    status: str
    sync_type: str
    documents_processed: int
    documents_added: int
    documents_updated: int
    documents_deleted: int
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class SyncLogListResponse(BaseModel):
    """Schema for list of sync logs"""
    sync_logs: list[SyncLogResponse]
    total: int
