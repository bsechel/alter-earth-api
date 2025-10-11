"""
Pydantic schemas for comments and comment threads.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ============================================
# Comment Schemas
# ============================================

class CommentCreate(BaseModel):
    """Schema for creating a comment."""
    content: str = Field(..., min_length=1, max_length=10000)
    parent_id: Optional[UUID] = Field(None, description="Parent comment ID for replies (null for top-level)")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "content": "This is a great article! Thanks for sharing.",
                    "parent_id": None  # Top-level comment
                },
                {
                    "content": "I agree with your point about ocean conservation.",
                    "parent_id": "550e8400-e29b-41d4-a716-446655440000"  # Reply
                }
            ]
        }
    )


class CommentUpdate(BaseModel):
    """Schema for updating a comment."""
    content: str = Field(..., min_length=1, max_length=10000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "content": "Updated comment content..."
            }
        }
    )


class CommentAuthor(BaseModel):
    """Simplified user info for comment author."""
    id: UUID
    nickname: str
    user_type: str
    is_expert: bool = False

    model_config = ConfigDict(from_attributes=True)


class CommentBase(BaseModel):
    """Base comment data."""
    id: UUID
    content: str
    user_id: UUID
    post_id: UUID
    parent_id: Optional[UUID]

    # Vote counts
    upvotes: int
    downvotes: int
    score: int

    # Status
    is_deleted: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentResponse(CommentBase):
    """Schema for comment in responses (includes author info)."""
    author: Optional[CommentAuthor] = None
    user_vote: Optional[int] = None  # Current user's vote (if authenticated)

    model_config = ConfigDict(from_attributes=True)


class CommentWithReplies(CommentResponse):
    """Schema for comment with nested replies (for building comment tree)."""
    replies: List['CommentWithReplies'] = []
    reply_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# Required for forward references
CommentWithReplies.model_rebuild()


class CommentTreeResponse(BaseModel):
    """Schema for complete comment tree on a post."""
    post_id: UUID
    total_comments: int
    top_level_count: int
    comments: List[CommentWithReplies]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "post_id": "550e8400-e29b-41d4-a716-446655440000",
                "total_comments": 15,
                "top_level_count": 5,
                "comments": []
            }
        }
    )


class CommentListResponse(BaseModel):
    """Paginated flat list of comments (for user profile, etc.)."""
    comments: List[CommentResponse]
    total: int
    page: int
    page_size: int
    has_more: bool
