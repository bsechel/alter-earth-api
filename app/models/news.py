"""
News article model for storing curated environmental news.
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class NewsArticle(Base):
    """
    News article model for environmental and sustainability news.
    """
    __tablename__ = "news_articles"
    __table_args__ = {"schema": "alter_earth"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Article content
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    
    # Source information
    source_name = Column(String(200), nullable=False, index=True)
    source_url = Column(String(500), nullable=True)
    author = Column(String(200), nullable=True)
    
    # Access and paywall information
    access_type = Column(String(20), default='free', nullable=False, index=True)  # 'free', 'paywall', 'subscription', 'registration'
    paywall_detected_at = Column(DateTime(timezone=True), nullable=True)
    is_full_content = Column(Boolean, default=True, nullable=False)  # vs just preview/snippet
    access_notes = Column(Text, nullable=True)  # Additional access information
    
    # Categorization
    category = Column(String(100), nullable=True, index=True)  # e.g., "renewable-energy", "climate-change"
    tags = Column(Text, nullable=True)  # JSON array of tags
    
    # Publication info
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Quality and relevance scoring (for AI integration later)
    relevance_score = Column(Float, nullable=True)  # 0.0 to 1.0
    quality_score = Column(Float, nullable=True)    # 0.0 to 1.0
    accessibility_score = Column(Float, nullable=True)  # Bonus for free, accessible content
    ai_summary = Column(Text, nullable=True)        # AI-generated summary
    
    # Content status
    is_featured = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Engagement metrics (for future use)
    view_count = Column(Integer, default=0, nullable=False)
    share_count = Column(Integer, default=0, nullable=False)
    
    # Content analysis
    word_count = Column(Integer, nullable=True)
    reading_time_minutes = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title='{self.title[:50]}...', source='{self.source_name}', access='{self.access_type}')>"


class NewsSource(Base):
    """
    News source configuration for RSS feeds and APIs.
    """
    __tablename__ = "news_sources"
    __table_args__ = {"schema": "alter_earth"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source information
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(500), nullable=False)
    rss_url = Column(String(500), nullable=True)
    api_endpoint = Column(String(500), nullable=True)
    
    # Configuration
    source_type = Column(String(50), nullable=False)  # 'rss', 'api', 'scraper'
    category_focus = Column(String(100), nullable=True)  # Primary focus area
    language = Column(String(10), default='en', nullable=False)
    country = Column(String(10), nullable=True)
    
    # Access characteristics
    typical_access_type = Column(String(20), default='free', nullable=False)  # What this source usually provides
    paywall_frequency = Column(Float, nullable=True)  # 0.0 to 1.0 - how often articles are paywalled
    access_reliability = Column(Float, default=1.0, nullable=False)  # How reliable free access is
    
    # Fetching configuration
    fetch_frequency_hours = Column(Integer, default=6, nullable=False)  # How often to check
    max_articles_per_fetch = Column(Integer, default=20, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    last_fetch_at = Column(DateTime(timezone=True), nullable=True)
    last_fetch_success = Column(Boolean, default=True, nullable=False)
    last_error_message = Column(Text, nullable=True)
    
    # Quality metrics
    total_articles_fetched = Column(Integer, default=0, nullable=False)
    average_relevance_score = Column(Float, nullable=True)
    free_content_percentage = Column(Float, nullable=True)  # Track how much content is actually free
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<NewsSource(id={self.id}, name='{self.name}', type='{self.source_type}', access='{self.typical_access_type}')>"