"""
Post models for the Reddit-like content system.
Includes Post (central table) and detail tables (AutomatedArticle, UserSubmission).
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, Text, ForeignKey, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class EntityType(str, enum.Enum):
    """Post entity type enumeration."""
    automated_article = "automated_article"
    user_submission = "user_submission"


class SubmissionType(str, enum.Enum):
    """User submission type enumeration."""
    text = "text"
    link = "link"


class Post(Base):
    """
    Central post table for all content types.
    Uses entity_type discriminator to link to detail tables.
    """
    __tablename__ = "posts"
    __table_args__ = {"schema": "alter_earth"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core fields
    title = Column(String(500), nullable=False, index=True)
    entity_type = Column(Enum(EntityType, name='entity_type', schema='alter_earth'), nullable=False, index=True)

    # Link to user (NOT NULL - use bot for automated content)
    user_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.users.id', ondelete='SET NULL'), nullable=False, index=True)

    # Community support (nullable for now, Phase 3 feature)
    community_id = Column(UUID(as_uuid=True), nullable=True)

    # Denormalized vote counts for performance
    upvotes = Column(Integer, nullable=False, default=0)
    downvotes = Column(Integer, nullable=False, default=0)
    score = Column(Integer, nullable=False, default=0, index=True)  # upvotes - downvotes
    hot_score = Column(Float, nullable=False, default=0.0, index=True)

    # Engagement metrics
    view_count = Column(Integer, nullable=False, default=0)
    comment_count = Column(Integer, nullable=False, default=0)

    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="posts")
    automated_article = relationship("AutomatedArticle", back_populates="post", uselist=False, cascade="all, delete-orphan")
    user_submission = relationship("UserSubmission", back_populates="post", uselist=False, cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title[:50]}...', type={self.entity_type}, score={self.score})>"


class AutomatedArticle(Base):
    """
    Detail table for automated news articles from RSS/API sources.
    One-to-one relationship with Post via post_id.
    """
    __tablename__ = "automated_articles"
    __table_args__ = {"schema": "alter_earth"}

    # Primary key is also foreign key to posts
    post_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.posts.id', ondelete='CASCADE'), primary_key=True)

    # Article content
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)  # Truncated snippet only (copyright compliance)
    url = Column(String(1000), nullable=False, unique=True, index=True)

    # Source information
    source_name = Column(String(200), nullable=False, index=True)
    source_url = Column(String(500), nullable=True)
    author = Column(String(200), nullable=True)

    # Categorization
    category = Column(String(100), nullable=True, index=True)
    tags = Column(Text, nullable=True)  # JSON array of tags

    # Publication info
    published_at = Column(DateTime(timezone=True), nullable=False, index=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # AI/Quality scoring
    relevance_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    accessibility_score = Column(Float, nullable=True)
    ai_summary = Column(Text, nullable=True)

    # Access information
    access_type = Column(String(20), nullable=False, default='free', index=True)
    paywall_detected_at = Column(DateTime(timezone=True), nullable=True)
    is_full_content = Column(Boolean, nullable=False, default=False)
    access_notes = Column(Text, nullable=True)

    # Content analysis
    word_count = Column(Integer, nullable=True)
    reading_time_minutes = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    post = relationship("Post", back_populates="automated_article")

    def __repr__(self):
        return f"<AutomatedArticle(post_id={self.post_id}, url='{self.url}', source='{self.source_name}')>"


class UserSubmission(Base):
    """
    Detail table for user-created posts (text or link).
    One-to-one relationship with Post via post_id.
    """
    __tablename__ = "user_submissions"
    __table_args__ = (
        CheckConstraint(
            "(submission_type = 'text' AND content IS NOT NULL) OR (submission_type = 'link' AND url IS NOT NULL)",
            name='check_submission_content'
        ),
        {"schema": "alter_earth"}
    )

    # Primary key is also foreign key to posts
    post_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.posts.id', ondelete='CASCADE'), primary_key=True)

    # Submission type
    submission_type = Column(Enum(SubmissionType, name='submission_type', schema='alter_earth'), nullable=False, index=True)

    # Content (for text posts)
    content = Column(Text, nullable=True)

    # URL (for link posts)
    url = Column(String(1000), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    post = relationship("Post", back_populates="user_submission")

    def __repr__(self):
        return f"<UserSubmission(post_id={self.post_id}, type={self.submission_type})>"
