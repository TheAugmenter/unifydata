"""
Analytics API Endpoints - Usage tracking and insights
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.api.dependencies import get_current_user
from app.services.analytics_service import analytics_service

router = APIRouter()


# Response Models
class DashboardStatsResponse(BaseModel):
    """Dashboard statistics response"""
    period_days: int
    total_conversations: int
    total_messages: int
    total_searches: int
    total_documents: int
    total_data_sources: int
    tokens: dict
    total_cost_usd: float
    avg_response_time_ms: int


class UsageDataPoint(BaseModel):
    """Usage data point for charts"""
    period: str
    count: int
    cost_usd: float
    tokens_input: int
    tokens_output: int


class ModelUsageStats(BaseModel):
    """Model usage statistics"""
    model: str
    usage_count: int
    tokens_input: int
    tokens_output: int
    tokens_total: int


class EventTypeStats(BaseModel):
    """Event type statistics"""
    event_type: str
    count: int
    cost_usd: float


# Endpoints
@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get dashboard statistics for the organization

    Returns key metrics for the specified time period:
    - Total conversations, messages, searches
    - Token usage and costs
    - Average response time
    - Connected data sources and documents
    """
    try:
        stats = await analytics_service.get_dashboard_stats(
            db=db,
            org_id=current_user.org_id,
            days=days,
        )

        return DashboardStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get("/usage-over-time", response_model=List[UsageDataPoint])
async def get_usage_over_time(
    days: int = Query(30, ge=1, le=365),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    interval: str = Query("day", regex="^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get usage over time for charts

    Returns time-series data for visualizing usage patterns:
    - Event counts
    - Cost accumulation
    - Token usage trends
    """
    try:
        data = await analytics_service.get_usage_over_time(
            db=db,
            org_id=current_user.org_id,
            event_type=event_type,
            days=days,
            interval=interval,
        )

        return [UsageDataPoint(**point) for point in data]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get usage over time: {str(e)}"
        )


@router.get("/models", response_model=List[ModelUsageStats])
async def get_top_models_used(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get top AI models used

    Returns statistics for the most frequently used AI models:
    - Usage count
    - Token consumption
    - Cost breakdown
    """
    try:
        models = await analytics_service.get_top_models_used(
            db=db,
            org_id=current_user.org_id,
            days=days,
            limit=limit,
        )

        return [ModelUsageStats(**model) for model in models]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get model usage: {str(e)}"
        )


@router.get("/events", response_model=List[EventTypeStats])
async def get_event_type_breakdown(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get breakdown of events by type

    Returns statistics for different event types:
    - search, chat, sync, etc.
    - Event counts
    - Associated costs
    """
    try:
        events = await analytics_service.get_event_type_breakdown(
            db=db,
            org_id=current_user.org_id,
            days=days,
        )

        return [EventTypeStats(**event) for event in events]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get event breakdown: {str(e)}"
        )


@router.get("/export")
async def export_analytics_data(
    days: int = Query(30, ge=1, le=365),
    format: str = Query("csv", regex="^(csv|json)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export analytics data

    Returns raw analytics data in CSV or JSON format for further analysis.
    """
    # TODO: Implement CSV/JSON export
    # This would query UsageLog and format as CSV or JSON
    raise HTTPException(
        status_code=501,
        detail="Export functionality not yet implemented"
    )
