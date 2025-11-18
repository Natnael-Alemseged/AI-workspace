"""Web search integration API routes."""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.users_complete import get_current_user as current_active_user
from app.db import get_async_session
from app.models.user import User
from app.models.web_search import WebSearchEngine, WebSearchQuery
from app.services.integrations.composio_service import composio_service

router = APIRouter(prefix="/search", tags=["search"])


# Request/Response Models
class SearchConnectionRequest(BaseModel):
    """Request to connect search engine account."""
    redirect_url: Optional[str] = "http://localhost:8002/api/search/callback"


class SearchConnectionResponse(BaseModel):
    """Response with search connection details."""
    connection_url: str
    entity_id: str
    status: str


class WebSearchRequest(BaseModel):
    """Request to perform a web search."""
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    num_results: int = Field(default=10, ge=1, le=50, description="Number of results to return")
    engine: WebSearchEngine = Field(default=WebSearchEngine.SERPAPI, description="Search engine to use")
    save_to_db: bool = Field(default=True, description="Whether to save search results to database")


class WebSearchResponse(BaseModel):
    """Response with search results."""
    query: str
    engine: str
    results: list
    count: int
    search_id: Optional[str] = None


class SearchHistoryResponse(BaseModel):
    """Response with search history."""
    searches: list
    total: int
    page: int
    page_size: int


@router.post("/connect", response_model=SearchConnectionResponse)
async def connect_search_engine(
    request: SearchConnectionRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Initiate search engine OAuth connection for the current user.
    
    This endpoint returns a URL that the user should visit to authorize
    search engine access. After authorization, they'll be redirected to the callback URL.
    """
    try:
        entity_id = str(user.id)
        
        logger.info(f"Initiating search engine connection for user {entity_id}")
        
        connection = await composio_service.connect_user_account(
            entity_id=entity_id,
            app_name="SERPAPI",
            redirect_url=request.redirect_url
        )
        
        return SearchConnectionResponse(
            connection_url=connection.get("redirectUrl", ""),
            entity_id=entity_id,
            status="pending"
        )
        
    except Exception as e:
        logger.error(f"Error connecting search engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate search engine connection: {str(e)}"
        )


@router.get("/callback")
async def search_callback(
    code: str,
    state: Optional[str] = None,
    user: User = Depends(current_active_user)
):
    """
    Handle OAuth callback from search engine.
    
    This endpoint is called by Composio after the user authorizes search engine access.
    """
    try:
        logger.info(f"Search engine OAuth callback received for user {user.id}")
        
        return {
            "status": "success",
            "message": "Search engine connected successfully",
            "user_id": str(user.id)
        }
        
    except Exception as e:
        logger.error(f"Error in search callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete search engine connection: {str(e)}"
        )


@router.get("/status")
async def get_search_status(
    user: User = Depends(current_active_user)
):
    """
    Check if search engine is connected for the current user.
    """
    try:
        entity_id = str(user.id)
        
        # Get connected accounts
        accounts = await composio_service.get_connected_accounts(entity_id)
        
        search_connected = any(
            acc.get("appName") in ["serpapi", "bing"] for acc in accounts
        )
        
        return {
            "connected": search_connected,
            "entity_id": entity_id,
            "accounts": accounts
        }
        
    except Exception as e:
        logger.error(f"Error checking search status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check search status: {str(e)}"
        )


@router.post("/query", response_model=WebSearchResponse)
async def perform_web_search(
    request: WebSearchRequest,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Perform a web search using the configured search engine.
    
    This endpoint executes a web search and optionally saves the results to the database.
    
    Example queries:
    - "Python FastAPI tutorial"
    - "latest AI news"
    - "weather in New York"
    """
    try:
        entity_id = str(user.id)
        
        logger.info(f"Performing web search for user {entity_id}: {request.query}")
        
        # Execute web search
        result = await composio_service.execute_web_search(
            entity_id=entity_id,
            query=request.query,
            num_results=request.num_results
        )
        
        # Extract results from the response
        search_results = result.get("data", {})
        organic_results = search_results.get("organic_results", [])
        
        search_id = None
        
        # Save to database if requested
        if request.save_to_db:
            search_query = WebSearchQuery(
                id=uuid.uuid4(),
                user_id=user.id,
                query=request.query,
                engine=request.engine,
                raw_results=search_results,
                created_at=datetime.utcnow()
            )
            
            session.add(search_query)
            await session.commit()
            await session.refresh(search_query)
            
            search_id = str(search_query.id)
            logger.info(f"Saved search results to database with ID: {search_id}")
        
        return WebSearchResponse(
            query=request.query,
            engine=request.engine.value,
            results=organic_results,
            count=len(organic_results),
            search_id=search_id
        )
        
    except Exception as e:
        logger.error(f"Error performing web search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform web search: {str(e)}"
        )


@router.get("/history", response_model=SearchHistoryResponse)
async def get_search_history(
    page: int = 1,
    page_size: int = 20,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get search history for the current user.
    
    Returns paginated list of previous searches with their results.
    """
    try:
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Query search history
        stmt = (
            select(WebSearchQuery)
            .where(WebSearchQuery.user_id == user.id)
            .order_by(WebSearchQuery.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await session.execute(stmt)
        searches = result.scalars().all()
        
        # Count total searches
        count_stmt = select(WebSearchQuery).where(WebSearchQuery.user_id == user.id)
        count_result = await session.execute(count_stmt)
        total = len(count_result.scalars().all())
        
        # Format response
        search_list = [
            {
                "id": str(search.id),
                "query": search.query,
                "engine": search.engine.value,
                "created_at": search.created_at.isoformat(),
                "results_count": len(search.raw_results.get("organic_results", [])) if search.raw_results else 0
            }
            for search in searches
        ]
        
        return SearchHistoryResponse(
            searches=search_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Error getting search history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search history: {str(e)}"
        )


@router.get("/history/{search_id}")
async def get_search_details(
    search_id: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Get detailed results for a specific search.
    
    Returns the full search results including all metadata.
    """
    try:
        # Query specific search
        stmt = (
            select(WebSearchQuery)
            .where(
                WebSearchQuery.id == uuid.UUID(search_id),
                WebSearchQuery.user_id == user.id
            )
        )
        
        result = await session.execute(stmt)
        search = result.scalar_one_or_none()
        
        if not search:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Search not found"
            )
        
        return {
            "id": str(search.id),
            "query": search.query,
            "engine": search.engine.value,
            "created_at": search.created_at.isoformat(),
            "raw_results": search.raw_results,
            "summary": search.summary
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid search ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search details: {str(e)}"
        )


@router.get("/tools")
async def get_search_tools(
    user: User = Depends(current_active_user)
):
    """
    Get available search tools for the current user.
    
    This returns all search actions that can be performed via Composio.
    """
    try:
        entity_id = str(user.id)
        
        tools = await composio_service.get_web_search_tools(entity_id)
        
        return {
            "status": "success",
            "tools": tools,
            "count": len(tools)
        }
        
    except Exception as e:
        logger.error(f"Error getting search tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search tools: {str(e)}"
        )