"""
Pydantic schemas for posts and related content types.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


# Enums for API
class EntityTypeEnum(str, Enum):
    """Post entity type for API responses."""
    automated_article = "automated_article"
    user_submission = "user_submission"


class SubmissionTypeEnum(str, Enum):
    """User submission type for API requests/responses."""
    text = "text"
    link = "link"


class SortOption(str, Enum):
    """Post sorting options."""
    hot = "hot"
    top = "top"
    new = "new"
    controversial = "controversial"
    rising = "rising"


class TimePeriod(str, Enum):
    """Time period for 'top' sorting."""
    hour = "hour"
    day = "day"
    week = "week"
    month = "month"
    year = "year"
    all = "all"


# ============================================
# User Submission Schemas
# ============================================

class UserSubmissionCreate(BaseModel):
    """Schema for creating a user submission."""
    title: str = Field(..., min_length=1, max_length=500)
    submission_type: SubmissionTypeEnum
    content: Optional[str] = Field(None, min_length=1)  # For text posts
    url: Optional[str] = Field(None, max_length=1000)  # For link posts

    @field_validator('content')
    @classmethod
    def validate_text_post(cls, v, info):
        """Ensure text posts have content."""
        if info.data.get('submission_type') == SubmissionTypeEnum.text and not v:
            raise ValueError('Text posts must have content')
        return v

    @field_validator('url')
    @classmethod
    def validate_link_post(cls, v, info):
        """Ensure link posts have URL."""
        if info.data.get('submission_type') == SubmissionTypeEnum.link and not v:
            raise ValueError('Link posts must have a URL')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "title": "Why we need to protect ocean ecosystems",
                    "submission_type": "text",
                    "content": "Ocean ecosystems are facing unprecedented threats..."
                },
                {
                    "title": "New study on coral reef restoration",
                    "submission_type": "link",
                    "url": "https://example.com/coral-study"
                }
            ]
        }
    )


class UserSubmissionResponse(BaseModel):
    """Schema for user submission in responses."""
    post_id: UUID
    submission_type: SubmissionTypeEnum
    content: Optional[str]
    url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Automated Article Schemas
# ============================================

class AutomatedArticleResponse(BaseModel):
    """Schema for automated article in responses."""
    post_id: UUID
    description: Optional[str]
    content: Optional[str]  # Snippet only
    url: str
    source_name: str
    source_url: Optional[str]
    author: Optional[str]
    category: Optional[str]
    tags: Optional[str]
    published_at: datetime
    scraped_at: datetime
    relevance_score: Optional[float]
    quality_score: Optional[float]
    ai_summary: Optional[str]
    access_type: str
    word_count: Optional[int]
    reading_time_minutes: Optional[int]

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Post Schemas
# ============================================

class PostBase(BaseModel):
    """Base post schema with common fields."""
    title: str = Field(..., min_length=1, max_length=500)


class PostResponse(BaseModel):
    """Schema for post in API responses."""
    id: UUID
    title: str
    entity_type: EntityTypeEnum
    user_id: UUID
    community_id: Optional[UUID]

    # Vote counts
    upvotes: int
    downvotes: int
    score: int
    hot_score: float

    # Engagement
    view_count: int
    comment_count: int

    # Status
    is_active: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Detail data (one will be populated based on entity_type)
    automated_article: Optional[AutomatedArticleResponse] = None
    user_submission: Optional[UserSubmissionResponse] = None

    # User info (simplified)
    user_nickname: Optional[str] = None
    user_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostListItem(BaseModel):
    """Simplified post schema for list views (feed)."""
    id: UUID
    title: str
    entity_type: EntityTypeEnum
    user_id: UUID

    # Vote counts
    score: int
    upvotes: int
    downvotes: int

    # Engagement
    comment_count: int

    # Timestamps
    created_at: datetime

    # Preview content based on type
    preview_text: Optional[str] = None  # First 200 chars of content/description
    preview_url: Optional[str] = None  # For links and articles
    source_name: Optional[str] = None  # For automated articles

    # User info
    user_nickname: Optional[str] = None
    user_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    """Paginated list of posts."""
    posts: list[PostListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


# ============================================
# Query Schemas
# ============================================

class PostQueryParams(BaseModel):
    """Query parameters for post listing."""
    sort: SortOption = Field(default=SortOption.hot)
    time_period: TimePeriod = Field(default=TimePeriod.day)  # Only used for 'top' sort
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=100)
    community_id: Optional[UUID] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sort": "hot",
                "time_period": "day",
                "page": 1,
                "page_size": 25
            }
        }
    )
