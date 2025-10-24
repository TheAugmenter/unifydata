"""
Search API Endpoints
"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import User
from app.api.auth import get_current_active_user
from app.services.search import search_service

router = APIRouter()


# Request/Response Models
class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Maximum number of results")
    source_types: Optional[List[str]] = Field(None, description="Filter by source types")
    min_score: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class SearchResultItem(BaseModel):
    """Single search result"""
    document_id: str
    title: str
    content_preview: str
    source_type: str
    url: Optional[str]
    score: float
    chunk_index: int
    created_at: str
    metadata: dict


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    results: List[SearchResultItem]
    total_results: int
    search_time_seconds: float
    filters: dict


class SearchWithSummaryResponse(SearchResponse):
    """Search response with AI summary"""
    ai_summary: dict


class RelatedDocumentsResponse(BaseModel):
    """Related documents response"""
    document_id: str
    related_documents: List[SearchResultItem]
    total_results: int


# Endpoints
@router.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search across all connected data sources using semantic search

    This endpoint performs AI-powered semantic search across all documents
    from your connected data sources (Salesforce, Slack, Google Drive, etc.).
    """
    try:
        results = await search_service.search(
            db=db,
            org_id=current_user.org_id,
            query=request.query,
            limit=request.limit,
            source_types=request.source_types,
            min_score=request.min_score,
        )

        return SearchResponse(**results)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/search/with-summary", response_model=SearchWithSummaryResponse)
async def search_with_summary(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Search with AI-generated summary of results

    Performs semantic search and generates an AI summary of the findings.
    """
    try:
        results = await search_service.search_with_ai_summary(
            db=db,
            org_id=current_user.org_id,
            query=request.query,
            limit=request.limit,
            source_types=request.source_types,
        )

        return SearchWithSummaryResponse(**results)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search with summary failed: {str(e)}"
        )


@router.get("/search/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Partial query"),
    limit: int = Query(5, ge=1, le=20, description="Maximum suggestions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get search query suggestions based on partial input

    Returns suggested search queries as the user types.
    """
    try:
        suggestions = await search_service.get_search_suggestions(
            db=db,
            org_id=current_user.org_id,
            partial_query=q,
            limit=limit,
        )

        return {
            "suggestions": suggestions,
            "total": len(suggestions),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.get("/documents/{document_id}/related", response_model=RelatedDocumentsResponse)
async def get_related_documents(
    document_id: UUID,
    limit: int = Query(5, ge=1, le=20, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get documents related to a specific document

    Returns documents that are semantically similar to the specified document.
    """
    try:
        related = await search_service.get_related_documents(
            db=db,
            document_id=document_id,
            limit=limit,
        )

        return RelatedDocumentsResponse(
            document_id=str(document_id),
            related_documents=related,
            total_results=len(related),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get related documents: {str(e)}"
        )
