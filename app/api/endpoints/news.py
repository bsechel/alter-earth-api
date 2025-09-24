"""
News API endpoints for environmental and conservation content.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from sqlalchemy.orm import selectinload

from app.core.database import get_async_session
from app.models.news import NewsArticle, NewsSource
from app.schemas.news import (
    NewsArticleResponse, 
    NewsArticleListResponse,
    NewsSourceResponse,
    NewsFilterParams
)

router = APIRouter()

@router.get("/articles", response_model=NewsArticleListResponse)
async def get_news_articles(
    category: Optional[str] = Query(None, description="Filter by category (climate-change, wildlife-conservation, etc.)"),
    source: Optional[str] = Query(None, description="Filter by news source name"),
    access_type: Optional[str] = Query("free", description="Filter by access type (free, paywall, registration)"),
    min_relevance: Optional[float] = Query(0.1, ge=0.0, le=1.0, description="Minimum relevance score (0.0-1.0)"),
    days_back: Optional[int] = Query(7, ge=1, le=365, description="Number of days back to search"),
    limit: int = Query(20, ge=1, le=100, description="Number of articles to return"),
    offset: int = Query(0, ge=0, description="Number of articles to skip"),
    search: Optional[str] = Query(None, description="Search in title and description"),
    featured_only: bool = Query(False, description="Show only featured articles"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get environmental news articles with conservation-focused filtering."""
    
    # Build query
    query = select(NewsArticle).where(NewsArticle.is_active == True)
    
    # Apply filters
    if category:
        query = query.where(NewsArticle.category == category)
    
    if source:
        query = query.where(NewsArticle.source_name.ilike(f"%{source}%"))
    
    if access_type and access_type != "all":
        query = query.where(NewsArticle.access_type == access_type)
    
    if min_relevance:
        query = query.where(NewsArticle.relevance_score >= min_relevance)
    
    if featured_only:
        query = query.where(NewsArticle.is_featured == True)
    
    # Date filter
    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.where(NewsArticle.published_at >= cutoff_date)
    
    # Search filter
    if search:
        search_filter = or_(
            NewsArticle.title.ilike(f"%{search}%"),
            NewsArticle.description.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    # Get total count for pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply ordering, limit, and offset
    query = query.order_by(desc(NewsArticle.published_at))
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return NewsArticleListResponse(
        articles=[NewsArticleResponse.model_validate(article) for article in articles],
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + limit) < total
    )

@router.get("/articles/{article_id}", response_model=NewsArticleResponse)
async def get_article(
    article_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific news article by ID."""
    
    query = select(NewsArticle).where(
        and_(
            NewsArticle.id == article_id,
            NewsArticle.is_active == True
        )
    )
    
    result = await db.execute(query)
    article = result.scalars().first()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Increment view count
    article.view_count += 1
    await db.commit()
    
    return NewsArticleResponse.model_validate(article)

@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_async_session)):
    """Get available news categories with article counts."""
    
    query = select(
        NewsArticle.category,
        func.count(NewsArticle.id).label('count')
    ).where(
        and_(
            NewsArticle.is_active == True,
            NewsArticle.category.isnot(None)
        )
    ).group_by(NewsArticle.category).order_by(desc('count'))
    
    result = await db.execute(query)
    categories = result.all()
    
    return {
        "categories": [
            {
                "name": cat.category,
                "count": cat.count,
                "display_name": cat.category.replace("-", " ").title()
            }
            for cat in categories
        ]
    }

@router.get("/sources", response_model=List[NewsSourceResponse])
async def get_news_sources(
    active_only: bool = Query(True, description="Show only active sources"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get available news sources."""
    
    query = select(NewsSource)
    
    if active_only:
        query = query.where(NewsSource.is_active == True)
    
    query = query.order_by(NewsSource.name)
    
    result = await db.execute(query)
    sources = result.scalars().all()
    
    return [NewsSourceResponse.model_validate(source) for source in sources]

@router.get("/featured", response_model=NewsArticleListResponse)
async def get_featured_articles(
    limit: int = Query(10, ge=1, le=50, description="Number of featured articles to return"),
    db: AsyncSession = Depends(get_async_session)
):
    """Get featured environmental news articles."""
    
    query = select(NewsArticle).where(
        and_(
            NewsArticle.is_featured == True,
            NewsArticle.is_active == True
        )
    ).order_by(desc(NewsArticle.published_at)).limit(limit)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return NewsArticleListResponse(
        articles=[NewsArticleResponse.model_validate(article) for article in articles],
        total=len(articles),
        limit=limit,
        offset=0,
        has_more=False
    )

@router.get("/conservation-highlights")
async def get_conservation_highlights(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_async_session)
):
    """Get top conservation and wildlife protection stories."""
    
    conservation_categories = [
        'wildlife-conservation', 
        'ecosystem-restoration', 
        'ocean-conservation'
    ]
    
    query = select(NewsArticle).where(
        and_(
            NewsArticle.category.in_(conservation_categories),
            NewsArticle.is_active == True,
            NewsArticle.relevance_score >= 0.5
        )
    ).order_by(
        desc(NewsArticle.relevance_score),
        desc(NewsArticle.published_at)
    ).limit(limit)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return {
        "conservation_highlights": [
            {
                "id": str(article.id),
                "title": article.title,
                "description": article.description[:200] + "..." if len(article.description) > 200 else article.description,
                "source": article.source_name,
                "category": article.category,
                "relevance_score": article.relevance_score,
                "published_at": article.published_at,
                "url": article.url,
                "reading_time": article.reading_time_minutes
            }
            for article in articles
        ]
    }

@router.get("/climate-focus")
async def get_climate_focus_articles(
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_async_session)
):
    """Get top climate change and environmental policy stories."""
    
    climate_categories = [
        'climate-change',
        'environmental-policy', 
        'renewable-energy'
    ]
    
    query = select(NewsArticle).where(
        and_(
            NewsArticle.category.in_(climate_categories),
            NewsArticle.is_active == True,
            NewsArticle.relevance_score >= 0.5
        )
    ).order_by(
        desc(NewsArticle.relevance_score),
        desc(NewsArticle.published_at)
    ).limit(limit)
    
    result = await db.execute(query)
    articles = result.scalars().all()
    
    return {
        "climate_focus": [
            {
                "id": str(article.id),
                "title": article.title,
                "description": article.description[:200] + "..." if len(article.description) > 200 else article.description,
                "source": article.source_name,
                "category": article.category,
                "relevance_score": article.relevance_score,
                "published_at": article.published_at,
                "url": article.url,
                "reading_time": article.reading_time_minutes
            }
            for article in articles
        ]
    }

@router.get("/stats")
async def get_news_stats(db: AsyncSession = Depends(get_async_session)):
    """Get news collection statistics."""
    
    # Total articles
    total_query = select(func.count(NewsArticle.id)).where(NewsArticle.is_active == True)
    total_result = await db.execute(total_query)
    total_articles = total_result.scalar()
    
    # Articles by access type
    access_query = select(
        NewsArticle.access_type,
        func.count(NewsArticle.id).label('count')
    ).where(NewsArticle.is_active == True).group_by(NewsArticle.access_type)
    access_result = await db.execute(access_query)
    access_stats = {row.access_type: row.count for row in access_result.all()}
    
    # Recent articles (last 7 days)
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    recent_query = select(func.count(NewsArticle.id)).where(
        and_(
            NewsArticle.is_active == True,
            NewsArticle.published_at >= recent_cutoff
        )
    )
    recent_result = await db.execute(recent_query)
    recent_articles = recent_result.scalar()
    
    # Average relevance score
    avg_relevance_query = select(func.avg(NewsArticle.relevance_score)).where(
        NewsArticle.is_active == True
    )
    avg_relevance_result = await db.execute(avg_relevance_query)
    avg_relevance = avg_relevance_result.scalar() or 0
    
    # Active sources
    sources_query = select(func.count(NewsSource.id)).where(NewsSource.is_active == True)
    sources_result = await db.execute(sources_query)
    active_sources = sources_result.scalar()
    
    return {
        "total_articles": total_articles,
        "recent_articles_7_days": recent_articles,
        "active_sources": active_sources,
        "average_relevance_score": round(float(avg_relevance), 3),
        "access_type_distribution": access_stats,
        "last_updated": datetime.utcnow().isoformat()
    }