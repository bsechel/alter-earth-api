"""
Pydantic schemas for the voting system.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


# ============================================
# Vote Schemas
# ============================================

class VoteCreate(BaseModel):
    """Schema for creating or updating a vote."""
    vote_value: Literal[1, -1] = Field(..., description="1 for upvote, -1 for downvote")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"vote_value": 1},  # Upvote
                {"vote_value": -1}  # Downvote
            ]
        }
    )


class VoteResponse(BaseModel):
    """Schema for vote in responses."""
    user_id: UUID
    post_id: Optional[UUID] = None
    comment_id: Optional[UUID] = None
    vote_value: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoteStatusResponse(BaseModel):
    """Schema for checking user's vote status on an item."""
    has_voted: bool
    vote_value: Optional[int] = None  # 1, -1, or None if not voted

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"has_voted": True, "vote_value": 1},
                {"has_voted": False, "vote_value": None}
            ]
        }
    )


class VoteStatsResponse(BaseModel):
    """Schema for vote statistics on an item."""
    upvotes: int
    downvotes: int
    score: int  # upvotes - downvotes
    user_vote: Optional[int] = None  # Current user's vote (if authenticated)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "upvotes": 42,
                "downvotes": 3,
                "score": 39,
                "user_vote": 1
            }
        }
    )
