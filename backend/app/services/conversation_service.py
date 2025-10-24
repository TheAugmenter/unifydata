"""
Conversation Service - Memory management for AI conversations
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, desc

from app.models import Conversation, Message, User
from app.services.search import search_service
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing AI conversations"""

    def __init__(self):
        """Initialize conversation service"""
        self.logger = logger

    async def create_conversation(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        title: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
    ) -> Conversation:
        """
        Create a new conversation

        Args:
            db: Database session
            user_id: User ID
            org_id: Organization ID
            title: Optional conversation title
            model: AI model to use

        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            org_id=org_id,
            title=title or "New Conversation",
            model=model,
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        self.logger.info(f"Created conversation {conversation.id} for user {user_id}")

        return conversation

    async def get_conversation(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> Optional[Conversation]:
        """
        Get a conversation by ID

        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (for access control)

        Returns:
            Conversation or None
        """
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        include_archived: bool = False,
    ) -> List[Conversation]:
        """
        List user's conversations

        Args:
            db: Database session
            user_id: User ID
            limit: Maximum number to return
            include_archived: Whether to include archived conversations

        Returns:
            List of conversations
        """
        query = select(Conversation).where(Conversation.user_id == user_id)

        if not include_archived:
            query = query.where(Conversation.is_archived == False)

        query = query.order_by(desc(Conversation.last_message_at)).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def add_message(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        model: Optional[str] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        context_documents: Optional[List[Dict[str, Any]]] = None,
        search_query: Optional[str] = None,
        response_time_ms: Optional[int] = None,
    ) -> Message:
        """
        Add a message to a conversation

        Args:
            db: Database session
            conversation_id: Conversation ID
            role: Message role (user or assistant)
            content: Message content
            model: AI model used (for assistant messages)
            tokens_input: Input tokens used
            tokens_output: Output tokens used
            context_documents: Documents used for context
            search_query: Search query used
            response_time_ms: Response time

        Returns:
            Created message
        """
        # Extract document IDs for storage
        doc_ids = None
        if context_documents:
            doc_ids = [doc.get("document_id") for doc in context_documents]

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            context_documents=doc_ids,
            search_query=search_query,
            response_time_ms=response_time_ms,
        )

        db.add(message)

        # Update conversation stats
        await db.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                message_count=Conversation.message_count + 1,
                total_tokens=Conversation.total_tokens + (tokens_input or 0) + (tokens_output or 0),
                last_message_at=datetime.utcnow(),
            )
        )

        await db.commit()
        await db.refresh(message)

        return message

    async def get_messages(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        limit: Optional[int] = None,
    ) -> List[Message]:
        """
        Get messages for a conversation

        Args:
            db: Database session
            conversation_id: Conversation ID
            limit: Optional limit

        Returns:
            List of messages (oldest first)
        """
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def ask_question(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        org_id: uuid.UUID,
        question: str,
        search_limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Ask a question in a conversation (non-streaming)

        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID
            org_id: Organization ID
            question: User's question
            search_limit: Number of documents to search for context

        Returns:
            Dict with answer and metadata
        """
        start_time = datetime.utcnow()

        # Get conversation
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found")

        # Search for relevant context
        search_results = await search_service.search(
            db=db,
            org_id=org_id,
            query=question,
            limit=search_limit,
            min_score=0.6,
        )

        context_documents = search_results["results"]

        # Get conversation history (last 10 messages for context)
        history_messages = await self.get_messages(db, conversation_id, limit=10)

        # Build messages array for Claude
        messages = []
        for msg in history_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Add current question
        messages.append({
            "role": "user",
            "content": question,
        })

        # Get AI response
        ai_response = await ai_service.chat(
            messages=messages,
            context_documents=context_documents,
            model=conversation.model,
            temperature=conversation.temperature,
        )

        # Calculate total response time
        total_response_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

        # Save user message
        await self.add_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=question,
        )

        # Save assistant message
        await self.add_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=ai_response["content"],
            model=ai_response["model"],
            tokens_input=ai_response["tokens_input"],
            tokens_output=ai_response["tokens_output"],
            context_documents=context_documents,
            search_query=question,
            response_time_ms=ai_response["response_time_ms"],
        )

        # Auto-generate title if this is the first question
        if conversation.message_count == 0:
            title = self._generate_title(question)
            await db.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(title=title)
            )
            await db.commit()

        return {
            "answer": ai_response["content"],
            "context_documents": context_documents,
            "model": ai_response["model"],
            "tokens_input": ai_response["tokens_input"],
            "tokens_output": ai_response["tokens_output"],
            "cost_usd": ai_response["cost_usd"],
            "response_time_ms": total_response_time_ms,
        }

    async def update_message_feedback(
        self,
        db: AsyncSession,
        message_id: uuid.UUID,
        thumbs_up: Optional[bool] = None,
        feedback_text: Optional[str] = None,
    ):
        """
        Update message feedback

        Args:
            db: Database session
            message_id: Message ID
            thumbs_up: Thumbs up/down
            feedback_text: Optional feedback text
        """
        await db.execute(
            update(Message)
            .where(Message.id == message_id)
            .values(
                thumbs_up=thumbs_up,
                feedback_text=feedback_text,
            )
        )
        await db.commit()

    async def archive_conversation(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        """Archive a conversation"""
        await db.execute(
            update(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
            .values(is_archived=True)
        )
        await db.commit()

    async def delete_conversation(
        self,
        db: AsyncSession,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
    ):
        """Delete a conversation and all its messages"""
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if conversation:
            await db.delete(conversation)
            await db.commit()

    def _generate_title(self, first_question: str, max_length: int = 50) -> str:
        """Generate conversation title from first question"""
        # Remove question mark and capitalize
        title = first_question.strip().rstrip("?")

        # Truncate if too long
        if len(title) > max_length:
            title = title[:max_length].rsplit(" ", 1)[0] + "..."

        return title


# Create singleton instance
conversation_service = ConversationService()
