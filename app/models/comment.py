"""
Comment model for the commenting system.
Supports threaded comments with parent/child relationships.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Comment(Base):
    """
    User comments on posts with threading support.
    Supports unlimited nesting via parent_id self-reference.
    """
    __tablename__ = "comments"
    __table_args__ = {"schema": "alter_earth"}

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Comment content
    content = Column(Text, nullable=False)

    # Who created this comment
    user_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.users.id', ondelete='SET NULL'), nullable=False, index=True)

    # Which post this comment belongs to
    post_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.posts.id', ondelete='CASCADE'), nullable=False, index=True)

    # Parent comment for threading (NULL for top-level comments)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.comments.id', ondelete='CASCADE'), nullable=True, index=True)

    # Denormalized vote counts for performance
    upvotes = Column(Integer, nullable=False, default=0)
    downvotes = Column(Integer, nullable=False, default=0)
    score = Column(Integer, nullable=False, default=0, index=True)  # upvotes - downvotes

    # Soft delete flag (preserves thread structure)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")
    votes = relationship("Vote", back_populates="comment", cascade="all, delete-orphan")

    # Self-referential relationship for threading
    parent = relationship("Comment", remote_side=[id], back_populates="replies")
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")

    @property
    def is_top_level(self):
        """Check if this is a top-level comment (no parent)."""
        return self.parent_id is None

    @property
    def depth(self):
        """Calculate the depth of this comment in the thread."""
        depth = 0
        parent = self.parent
        while parent:
            depth += 1
            parent = parent.parent
        return depth

    def __repr__(self):
        deleted = " [DELETED]" if self.is_deleted else ""
        return f"<Comment(id={self.id}, post_id={self.post_id}, score={self.score}, depth={self.depth}{deleted})>"
