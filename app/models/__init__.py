"""
Models package for Alter Earth API.
"""

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User, UserType
from app.models.news import NewsArticle, NewsSource
from app.models.post import Post, AutomatedArticle, UserSubmission, EntityType, SubmissionType
from app.models.comment import Comment
from app.models.vote import Vote

__all__ = [
    # User models
    "User",
    "UserType",

    # News models (legacy)
    "NewsArticle",
    "NewsSource",

    # Post models (Phase 2)
    "Post",
    "AutomatedArticle",
    "UserSubmission",
    "EntityType",
    "SubmissionType",

    # Comment model
    "Comment",

    # Vote model
    "Vote",
]
