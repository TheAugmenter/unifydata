"""
Chat API Endpoints - AI Q&A with Claude
"""
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.models import User
from app.api.dependencies import get_current_user
from app.services.conversation_service import conversation_service
from app.services.ai_service import ai_service
from app.services.analytics_service import analytics_service

router = APIRouter()


# Request/Response Models
class CreateConversationRequest(BaseModel):
    """Create conversation request"""
    title: Optional[str] = Field(None, description="Conversation title")
    model: str = Field("claude-3-5-sonnet-20241022", description="AI model to use")


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: str
    title: str
    model: str
    temperature: float
    message_count: int
    total_tokens: int
    is_archived: bool
    last_message_at: Optional[str]
    created_at: str


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    role: str
    content: str
    model: Optional[str]
    tokens_input: Optional[int]
    tokens_output: Optional[int]
    context_documents: Optional[List[str]]
    thumbs_up: Optional[bool]
    created_at: str


class AskQuestionRequest(BaseModel):
    """Ask question request"""
    question: str = Field(..., min_length=1, max_length=5000)
    search_limit: int = Field(5, ge=1, le=20, description="Number of context documents")


class AskQuestionResponse(BaseModel):
    """Ask question response"""
    answer: str
    context_documents: List[dict]
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    response_time_ms: int


class MessageFeedbackRequest(BaseModel):
    """Message feedback request"""
    thumbs_up: Optional[bool] = None
    feedback_text: Optional[str] = Field(None, max_length=1000)


class ModelInfoResponse(BaseModel):
    """Model information response"""
    id: str
    name: str
    max_tokens: int
    cost_input_per_1m: float
    cost_output_per_1m: float
    best_for: str


# Endpoints
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new conversation"""
    try:
        conversation = await conversation_service.create_conversation(
            db=db,
            user_id=current_user.id,
            org_id=current_user.org_id,
            title=request.title,
            model=request.model,
        )

        # Log event
        await analytics_service.log_event(
            db=db,
            org_id=current_user.org_id,
            user_id=current_user.id,
            event_type="chat",
            event_subtype="conversation_created",
        )

        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            model=conversation.model,
            temperature=conversation.temperature,
            message_count=conversation.message_count,
            total_tokens=conversation.total_tokens,
            is_archived=conversation.is_archived,
            last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
            created_at=conversation.created_at.isoformat(),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    include_archived: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's conversations"""
    try:
        conversations = await conversation_service.list_conversations(
            db=db,
            user_id=current_user.id,
            limit=limit,
            include_archived=include_archived,
        )

        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                model=conv.model,
                temperature=conv.temperature,
                message_count=conv.message_count,
                total_tokens=conv.total_tokens,
                is_archived=conv.is_archived,
                last_message_at=conv.last_message_at.isoformat() if conv.last_message_at else None,
                created_at=conv.created_at.isoformat(),
            )
            for conv in conversations
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversation details"""
    conversation = await conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationResponse(
        id=str(conversation.id),
        title=conversation.title,
        model=conversation.model,
        temperature=conversation.temperature,
        message_count=conversation.message_count,
        total_tokens=conversation.total_tokens,
        is_archived=conversation.is_archived,
        last_message_at=conversation.last_message_at.isoformat() if conversation.last_message_at else None,
        created_at=conversation.created_at.isoformat(),
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a conversation"""
    try:
        await conversation_service.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

        return {"message": "Conversation deleted successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")


@router.post("/conversations/{conversation_id}/archive")
async def archive_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Archive a conversation"""
    try:
        await conversation_service.archive_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

        return {"message": "Conversation archived successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to archive conversation: {str(e)}")


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: UUID,
    limit: Optional[int] = Query(None, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get messages for a conversation"""
    # Verify access
    conversation = await conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        messages = await conversation_service.get_messages(
            db=db,
            conversation_id=conversation_id,
            limit=limit,
        )

        return [
            MessageResponse(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                model=msg.model,
                tokens_input=msg.tokens_input,
                tokens_output=msg.tokens_output,
                context_documents=msg.context_documents,
                thumbs_up=msg.thumbs_up,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")


@router.post("/conversations/{conversation_id}/messages", response_model=AskQuestionResponse)
async def ask_question(
    conversation_id: UUID,
    request: AskQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question in a conversation (non-streaming)"""
    try:
        result = await conversation_service.ask_question(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            org_id=current_user.org_id,
            question=request.question,
            search_limit=request.search_limit,
        )

        # Log event
        await analytics_service.log_event(
            db=db,
            org_id=current_user.org_id,
            user_id=current_user.id,
            event_type="chat",
            event_subtype="question_asked",
            model_used=result["model"],
            tokens_input=result["tokens_input"],
            tokens_output=result["tokens_output"],
            cost_usd=result["cost_usd"],
            response_time_ms=result["response_time_ms"],
        )

        return AskQuestionResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Log error
        await analytics_service.log_event(
            db=db,
            org_id=current_user.org_id,
            user_id=current_user.id,
            event_type="chat",
            event_subtype="question_asked",
            status="error",
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to ask question: {str(e)}")


@router.post("/conversations/{conversation_id}/messages/stream")
async def ask_question_stream(
    conversation_id: UUID,
    request: AskQuestionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question with streaming response"""
    # Note: Streaming implementation requires more complex async handling
    # For MVP, we'll use non-streaming endpoint
    # TODO: Implement proper streaming with Server-Sent Events (SSE)
    raise HTTPException(
        status_code=501,
        detail="Streaming not yet implemented. Use POST /messages for now."
    )


@router.put("/messages/{message_id}/feedback")
async def update_message_feedback(
    message_id: UUID,
    request: MessageFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update message feedback (thumbs up/down)"""
    try:
        await conversation_service.update_message_feedback(
            db=db,
            message_id=message_id,
            thumbs_up=request.thumbs_up,
            feedback_text=request.feedback_text,
        )

        return {"message": "Feedback updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update feedback: {str(e)}")


@router.get("/models", response_model=List[ModelInfoResponse])
async def list_models():
    """List available AI models"""
    models = ai_service.list_models()

    return [ModelInfoResponse(**model) for model in models]
