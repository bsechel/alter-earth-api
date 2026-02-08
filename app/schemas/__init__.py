"""
Schemas package for API request/response validation.
"""

# Post schemas
from app.schemas.post import (
    EntityTypeEnum,
    SubmissionTypeEnum,
    SortOption,
    TimePeriod,
    UserSubmissionCreate,
    UserSubmissionResponse,
    AutomatedArticleResponse,
    PostResponse,
    PostListItem,
    PostListResponse,
    PostQueryParams,
)

# Comment schemas
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentAuthor,
    CommentResponse,
    CommentWithReplies,
    CommentTreeResponse,
    CommentListResponse,
)

# Vote schemas
from app.schemas.vote import (
    VoteCreate,
    VoteResponse,
    VoteStatusResponse,
    VoteStatsResponse,
)

__all__ = [
    # Post schemas
    "EntityTypeEnum",
    "SubmissionTypeEnum",
    "SortOption",
    "TimePeriod",
    "UserSubmissionCreate",
    "UserSubmissionResponse",
    "AutomatedArticleResponse",
    "PostResponse",
    "PostListItem",
    "PostListResponse",
    "PostQueryParams",

    # Comment schemas
    "CommentCreate",
    "CommentUpdate",
    "CommentAuthor",
    "CommentResponse",
    "CommentWithReplies",
    "CommentTreeResponse",
    "CommentListResponse",

    # Vote schemas
    "VoteCreate",
    "VoteResponse",
    "VoteStatusResponse",
    "VoteStatsResponse",
]
