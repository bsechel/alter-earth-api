"""
Vote model for the voting system.
Tracks user votes on posts and comments.
"""

from sqlalchemy import Column, DateTime, SmallInteger, ForeignKey, CheckConstraint, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Vote(Base):
    """
    User votes on posts and comments.
    A user can vote once per post or comment (enforced by unique constraints).
    """
    __tablename__ = "votes"
    __table_args__ = (
        # Ensure vote is for either post OR comment, not both
        CheckConstraint(
            "(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)",
            name='check_vote_target'
        ),
        # Ensure vote value is valid
        CheckConstraint(
            "vote_value IN (1, -1)",
            name='check_vote_value'
        ),
        # Composite primary key
        PrimaryKeyConstraint('user_id', 'post_id', 'comment_id'),
        {"schema": "alter_earth"}
    )

    # User who cast the vote
    user_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.users.id', ondelete='CASCADE'), nullable=False, index=True)

    # Either post_id or comment_id must be set (not both)
    post_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.posts.id', ondelete='CASCADE'), nullable=True)
    comment_id = Column(UUID(as_uuid=True), ForeignKey('alter_earth.comments.id', ondelete='CASCADE'), nullable=True)

    # Vote value: 1 for upvote, -1 for downvote
    vote_value = Column(SmallInteger, nullable=False)

    # Timestamps (track when votes change)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="votes")
    post = relationship("Post", back_populates="votes")
    comment = relationship("Comment", back_populates="votes")

    @property
    def is_upvote(self):
        """Check if this is an upvote."""
        return self.vote_value == 1

    @property
    def is_downvote(self):
        """Check if this is a downvote."""
        return self.vote_value == -1

    def __repr__(self):
        target = f"post={self.post_id}" if self.post_id else f"comment={self.comment_id}"
        vote_type = "↑" if self.is_upvote else "↓"
        return f"<Vote(user={self.user_id}, {target}, {vote_type})>"
