"""
Pydantic schemas for news API responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class NewsArticleResponse(BaseModel):
    """Response schema for a news article."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    title: str
    description: Optional[str] = None
    content: Optional[str] = None
    url: str
    source_name: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    published_at: datetime
    scraped_at: datetime
    access_type: str = "free"
    is_full_content: bool = True
    access_notes: Optional[str] = None
    relevance_score: Optional[float] = None
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    view_count: int = 0
    share_count: int = 0
    is_featured: bool = False

class NewsArticleListResponse(BaseModel):
    """Response schema for a list of news articles with pagination."""
    articles: List[NewsArticleResponse]
    total: int
    limit: int
    offset: int
    has_more: bool

class NewsSourceResponse(BaseModel):
    """Response schema for a news source."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    name: str
    description: Optional[str] = None
    url: str
    source_type: str
    category_focus: Optional[str] = None
    typical_access_type: str = "free"
    language: str = "en"
    country: Optional[str] = None
    is_active: bool = True
    last_fetch_at: Optional[datetime] = None
    last_fetch_success: bool = True
    total_articles_fetched: int = 0
    average_relevance_score: Optional[float] = None
    free_content_percentage: Optional[float] = None

class NewsFilterParams(BaseModel):
    """Parameters for filtering news articles."""
    category: Optional[str] = Field(None, description="Filter by category")
    source: Optional[str] = Field(None, description="Filter by source name")
    access_type: Optional[str] = Field("free", description="Filter by access type")
    min_relevance: Optional[float] = Field(0.1, ge=0.0, le=1.0)
    days_back: Optional[int] = Field(7, ge=1, le=365)
    search: Optional[str] = Field(None, description="Search query")
    featured_only: bool = Field(False, description="Show only featured articles")

class CategoryStats(BaseModel):
    """Statistics for a news category."""
    name: str
    count: int
    display_name: str

class NewsStatsResponse(BaseModel):
    """Response schema for news statistics."""
    total_articles: int
    recent_articles_7_days: int
    active_sources: int
    average_relevance_score: float
    access_type_distribution: dict
    last_updated: str