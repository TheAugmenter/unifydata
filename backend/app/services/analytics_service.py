"""
Analytics Service - Usage tracking and insights
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.sql import extract

from app.models import UsageLog, Conversation, Message, DataSource, Document

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking usage and generating analytics"""

    def __init__(self):
        """Initialize analytics service"""
        self.logger = logger

    async def log_event(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        event_type: str,
        user_id: Optional[uuid.UUID] = None,
        event_subtype: Optional[str] = None,
        event_metadata: Optional[Dict[str, Any]] = None,
        model_used: Optional[str] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        cost_usd: Optional[float] = None,
        response_time_ms: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> UsageLog:
        """
        Log a usage event

        Args:
            db: Database session
            org_id: Organization ID
            event_type: Type of event (search, chat, sync, etc.)
            user_id: Optional user ID
            event_subtype: Optional event subtype
            event_metadata: Optional event metadata
            model_used: AI model used
            tokens_input: Input tokens
            tokens_output: Output tokens
            cost_usd: Cost in USD
            response_time_ms: Response time in milliseconds
            status: Event status (success, error, timeout)
            error_message: Optional error message

        Returns:
            Created UsageLog
        """
        usage_log = UsageLog(
            org_id=org_id,
            user_id=user_id,
            event_type=event_type,
            event_subtype=event_subtype,
            event_metadata=event_metadata,
            model_used=model_used,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            status=status,
            error_message=error_message,
        )

        db.add(usage_log)
        await db.commit()
        await db.refresh(usage_log)

        return usage_log

    async def get_dashboard_stats(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get dashboard statistics for an organization

        Args:
            db: Database session
            org_id: Organization ID
            days: Number of days to look back

        Returns:
            Dict with dashboard stats
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        # Total conversations
        total_convos_result = await db.execute(
            select(func.count(Conversation.id)).where(
                and_(
                    Conversation.org_id == org_id,
                    Conversation.created_at >= since_date,
                )
            )
        )
        total_conversations = total_convos_result.scalar() or 0

        # Total messages
        total_messages_result = await db.execute(
            select(func.count(Message.id))
            .join(Conversation)
            .where(
                and_(
                    Conversation.org_id == org_id,
                    Message.created_at >= since_date,
                )
            )
        )
        total_messages = total_messages_result.scalar() or 0

        # Total tokens used
        tokens_result = await db.execute(
            select(
                func.coalesce(func.sum(Message.tokens_input), 0).label("total_input"),
                func.coalesce(func.sum(Message.tokens_output), 0).label("total_output"),
            )
            .join(Conversation)
            .where(
                and_(
                    Conversation.org_id == org_id,
                    Message.created_at >= since_date,
                    Message.role == "assistant",
                )
            )
        )
        tokens_row = tokens_result.one()
        total_tokens_input = int(tokens_row.total_input)
        total_tokens_output = int(tokens_row.total_output)

        # Total cost (estimate from usage logs)
        cost_result = await db.execute(
            select(func.coalesce(func.sum(UsageLog.cost_usd), 0)).where(
                and_(
                    UsageLog.org_id == org_id,
                    UsageLog.created_at >= since_date,
                )
            )
        )
        total_cost = float(cost_result.scalar() or 0.0)

        # Total searches
        searches_result = await db.execute(
            select(func.count(UsageLog.id)).where(
                and_(
                    UsageLog.org_id == org_id,
                    UsageLog.event_type == "search",
                    UsageLog.created_at >= since_date,
                )
            )
        )
        total_searches = searches_result.scalar() or 0

        # Total synced documents
        docs_result = await db.execute(
            select(func.count(Document.id))
            .join(DataSource)
            .where(
                and_(
                    DataSource.org_id == org_id,
                    Document.created_at >= since_date,
                )
            )
        )
        total_documents = docs_result.scalar() or 0

        # Connected data sources
        sources_result = await db.execute(
            select(func.count(DataSource.id)).where(
                and_(
                    DataSource.org_id == org_id,
                    DataSource.is_active == True,
                )
            )
        )
        total_data_sources = sources_result.scalar() or 0

        # Average response time
        avg_time_result = await db.execute(
            select(func.avg(Message.response_time_ms))
            .join(Conversation)
            .where(
                and_(
                    Conversation.org_id == org_id,
                    Message.created_at >= since_date,
                    Message.role == "assistant",
                    Message.response_time_ms.is_not(None),
                )
            )
        )
        avg_response_time = int(avg_time_result.scalar() or 0)

        return {
            "period_days": days,
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_searches": total_searches,
            "total_documents": total_documents,
            "total_data_sources": total_data_sources,
            "tokens": {
                "input": total_tokens_input,
                "output": total_tokens_output,
                "total": total_tokens_input + total_tokens_output,
            },
            "total_cost_usd": round(total_cost, 2),
            "avg_response_time_ms": avg_response_time,
        }

    async def get_usage_over_time(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        event_type: Optional[str] = None,
        days: int = 30,
        interval: str = "day",
    ) -> List[Dict[str, Any]]:
        """
        Get usage over time for charts

        Args:
            db: Database session
            org_id: Organization ID
            event_type: Optional event type filter
            days: Number of days to look back
            interval: Time interval (day, week, month)

        Returns:
            List of usage data points
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        # Build query
        query = select(
            func.date_trunc(interval, UsageLog.created_at).label("period"),
            func.count(UsageLog.id).label("count"),
            func.coalesce(func.sum(UsageLog.cost_usd), 0).label("cost"),
            func.coalesce(func.sum(UsageLog.tokens_input), 0).label("tokens_input"),
            func.coalesce(func.sum(UsageLog.tokens_output), 0).label("tokens_output"),
        ).where(
            and_(
                UsageLog.org_id == org_id,
                UsageLog.created_at >= since_date,
            )
        )

        if event_type:
            query = query.where(UsageLog.event_type == event_type)

        query = query.group_by("period").order_by("period")

        result = await db.execute(query)
        rows = result.all()

        return [
            {
                "period": row.period.isoformat() if row.period else None,
                "count": row.count,
                "cost_usd": float(row.cost),
                "tokens_input": int(row.tokens_input),
                "tokens_output": int(row.tokens_output),
            }
            for row in rows
        ]

    async def get_top_models_used(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        days: int = 30,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get top AI models used

        Args:
            db: Database session
            org_id: Organization ID
            days: Number of days to look back
            limit: Maximum results

        Returns:
            List of model usage stats
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                Message.model,
                func.count(Message.id).label("usage_count"),
                func.coalesce(func.sum(Message.tokens_input), 0).label("total_input"),
                func.coalesce(func.sum(Message.tokens_output), 0).label("total_output"),
            )
            .join(Conversation)
            .where(
                and_(
                    Conversation.org_id == org_id,
                    Message.created_at >= since_date,
                    Message.role == "assistant",
                    Message.model.is_not(None),
                )
            )
            .group_by(Message.model)
            .order_by(desc("usage_count"))
            .limit(limit)
        )

        rows = result.all()

        return [
            {
                "model": row.model,
                "usage_count": row.usage_count,
                "tokens_input": int(row.total_input),
                "tokens_output": int(row.total_output),
                "tokens_total": int(row.total_input) + int(row.total_output),
            }
            for row in rows
        ]

    async def get_event_type_breakdown(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """
        Get breakdown of events by type

        Args:
            db: Database session
            org_id: Organization ID
            days: Number of days to look back

        Returns:
            List of event type stats
        """
        since_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                UsageLog.event_type,
                func.count(UsageLog.id).label("count"),
                func.coalesce(func.sum(UsageLog.cost_usd), 0).label("total_cost"),
            )
            .where(
                and_(
                    UsageLog.org_id == org_id,
                    UsageLog.created_at >= since_date,
                )
            )
            .group_by(UsageLog.event_type)
            .order_by(desc("count"))
        )

        rows = result.all()

        return [
            {
                "event_type": row.event_type,
                "count": row.count,
                "cost_usd": float(row.total_cost),
            }
            for row in rows
        ]


# Create singleton instance
analytics_service = AnalyticsService()
