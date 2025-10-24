"""
Semantic Search Service
AI-powered search across all connected data sources
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models import Document, DocumentChunk
from app.services.embeddings import embeddings_service
from app.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)


class SearchService:
    """Service for semantic search across documents"""

    def __init__(self):
        """Initialize search service"""
        self.logger = logger

    async def search(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        query: str,
        limit: int = 10,
        source_types: Optional[List[str]] = None,
        min_score: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Perform semantic search across documents

        Args:
            db: Database session
            org_id: Organization ID (for multi-tenancy)
            query: Search query text
            limit: Maximum number of results
            source_types: Optional filter by source types (e.g., ["salesforce", "slack"])
            min_score: Minimum similarity score (0-1)

        Returns:
            Dict with search results
        """
        start_time = datetime.utcnow()

        self.logger.info(
            f"Searching for: '{query}' (org: {org_id}, limit: {limit}, "
            f"sources: {source_types or 'all'})"
        )

        # Create query embedding
        embedding_result = await embeddings_service.create_embedding(query)
        query_vector = embedding_result["embedding"]

        # Build Pinecone filter
        filter_metadata = {}
        if source_types:
            filter_metadata["source_type"] = {"$in": source_types}

        # Search Pinecone
        namespace = str(org_id)  # Use org_id as namespace
        matches = await pinecone_service.query(
            query_vector=query_vector,
            top_k=limit * 2,  # Get more results for filtering
            namespace=namespace,
            filter_metadata=filter_metadata if filter_metadata else None,
            include_metadata=True,
        )

        # Filter by score
        filtered_matches = [
            match for match in matches
            if match["score"] >= min_score
        ][:limit]

        # Get full document details from database
        results = []
        for match in filtered_matches:
            metadata = match["metadata"]
            document_id = uuid.UUID(metadata["document_id"])

            # Get document from database
            result = await db.execute(
                select(Document).where(
                    and_(
                        Document.id == document_id,
                        Document.org_id == org_id,
                        Document.is_deleted == False,
                    )
                )
            )
            document = result.scalar_one_or_none()

            if not document:
                continue

            # Format result
            results.append({
                "document_id": str(document.id),
                "title": document.title,
                "content": document.content,
                "content_preview": self._create_preview(
                    document.content,
                    metadata.get("content", ""),
                    max_length=300
                ),
                "source_type": document.source_type,
                "url": document.url,
                "score": match["score"],
                "chunk_index": metadata.get("chunk_index", 0),
                "created_at": document.source_created_at or document.created_at,
                "metadata": document.source_metadata or {},
            })

        # Calculate search time
        search_time = (datetime.utcnow() - start_time).total_seconds()

        self.logger.info(
            f"Found {len(results)} results in {search_time:.2f}s "
            f"(query: '{query[:50]}...')"
        )

        return {
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_time_seconds": search_time,
            "filters": {
                "source_types": source_types,
                "min_score": min_score,
            },
        }

    async def search_with_ai_summary(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        query: str,
        limit: int = 10,
        source_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Perform search and generate AI summary of results

        Args:
            db: Database session
            org_id: Organization ID
            query: Search query
            limit: Maximum results
            source_types: Optional source type filter

        Returns:
            Dict with search results and AI summary
        """
        # Perform search
        search_results = await self.search(
            db=db,
            org_id=org_id,
            query=query,
            limit=limit,
            source_types=source_types,
        )

        # TODO: Generate AI summary using Anthropic Claude
        # This would use the search results to create a summary
        ai_summary = {
            "summary": "AI summary not yet implemented",
            "sources_count": len(search_results["results"]),
            "confidence": "high",
        }

        return {
            **search_results,
            "ai_summary": ai_summary,
        }

    def _create_preview(
        self,
        full_content: str,
        chunk_content: str,
        max_length: int = 300
    ) -> str:
        """
        Create content preview, prioritizing the matching chunk

        Args:
            full_content: Full document content
            chunk_content: Matching chunk content
            max_length: Maximum preview length

        Returns:
            Preview text
        """
        # Use chunk content if available and not too long
        if chunk_content and len(chunk_content) <= max_length:
            return chunk_content

        # Otherwise, use beginning of full content
        if len(full_content) <= max_length:
            return full_content

        # Truncate and add ellipsis
        return full_content[:max_length].rsplit(" ", 1)[0] + "..."

    async def get_search_suggestions(
        self,
        db: AsyncSession,
        org_id: uuid.UUID,
        partial_query: str,
        limit: int = 5,
    ) -> List[str]:
        """
        Get search query suggestions based on partial input

        Args:
            db: Database session
            org_id: Organization ID
            partial_query: Partial search query
            limit: Maximum suggestions

        Returns:
            List of suggested queries
        """
        # TODO: Implement intelligent query suggestions
        # This could use:
        # - Common searches by the organization
        # - Document titles and content
        # - Search history

        # For now, return empty list
        return []

    async def get_related_documents(
        self,
        db: AsyncSession,
        document_id: uuid.UUID,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Get documents related to a specific document

        Args:
            db: Database session
            document_id: Document ID to find related docs for
            limit: Maximum results

        Returns:
            List of related documents
        """
        # Get the document
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            return []

        # Use document content as query
        query_text = document.title + "\n" + document.content[:1000]

        # Search for similar documents
        search_results = await self.search(
            db=db,
            org_id=document.org_id,
            query=query_text,
            limit=limit + 1,  # +1 because original doc will be in results
            min_score=0.6,
        )

        # Filter out the original document
        related = [
            result for result in search_results["results"]
            if result["document_id"] != str(document_id)
        ][:limit]

        return related


# Create singleton instance
search_service = SearchService()
