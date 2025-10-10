"""
Voting service for managing votes on posts and comments.
Handles vote creation, updates, and karma calculation with proper transaction management.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, Tuple
from datetime import datetime

from app.models.vote import Vote
from app.models.post import Post
from app.models.comment import Comment
from app.models.user import User
from app.services.scoring import calculate_hot_score, calculate_vote_weight


class VotingService:
    """Service for handling votes on posts and comments."""

    def __init__(self, session: AsyncSession):
        """
        Initialize voting service.

        Args:
            session: Async database session
        """
        self.session = session

    async def vote_on_post(
        self,
        user_id: UUID,
        post_id: UUID,
        vote_value: int
    ) -> Tuple[Vote, Post]:
        """
        Cast or update a vote on a post.

        This handles the complete voting workflow:
        1. Check if user already voted
        2. Create or update vote
        3. Update denormalized counts on post
        4. Update post owner's karma
        5. Recalculate hot_score

        Args:
            user_id: ID of user casting vote
            post_id: ID of post being voted on
            vote_value: 1 for upvote, -1 for downvote

        Returns:
            Tuple of (Vote, Post)

        Raises:
            ValueError: If post not found or user tries to vote on own post
        """
        # Validate vote_value
        if vote_value not in (1, -1):
            raise ValueError("vote_value must be 1 or -1")

        # Get post with user relationship
        post_result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .where(Post.id == post_id)
        )
        post = post_result.scalar_one_or_none()

        if not post:
            raise ValueError(f"Post {post_id} not found")

        # Prevent self-voting
        if post.user_id == user_id:
            raise ValueError("Cannot vote on your own post")

        # Get voter for karma calculation
        voter_result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        voter = voter_result.scalar_one_or_none()

        if not voter:
            raise ValueError(f"User {user_id} not found")

        # Calculate vote weight based on voter's karma
        total_karma = voter.post_karma + voter.comment_karma
        vote_weight = calculate_vote_weight(total_karma)

        # Check for existing vote
        existing_vote_result = await self.session.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == user_id,
                    Vote.post_id == post_id
                )
            )
        )
        existing_vote = existing_vote_result.scalar_one_or_none()

        if existing_vote:
            # Vote already exists - update it
            old_value = existing_vote.vote_value

            if old_value == vote_value:
                # Same vote - no change needed
                return existing_vote, post

            # Update vote value
            existing_vote.vote_value = vote_value
            existing_vote.updated_at = datetime.utcnow()

            # Update denormalized counts (remove old, add new)
            self._update_post_counts(post, -old_value, vote_value, vote_weight)

            # Update post owner's karma
            if post.user:
                self._update_user_post_karma(post.user, -old_value, vote_value, vote_weight)

            vote = existing_vote

        else:
            # Create new vote
            vote = Vote(
                user_id=user_id,
                post_id=post_id,
                vote_value=vote_value
            )
            self.session.add(vote)

            # Update denormalized counts
            self._update_post_counts(post, 0, vote_value, vote_weight)

            # Update post owner's karma
            if post.user:
                self._update_user_post_karma(post.user, 0, vote_value, vote_weight)

        # Recalculate hot_score
        post.hot_score = calculate_hot_score(post.upvotes, post.downvotes, post.created_at)

        # Commit transaction
        await self.session.commit()
        await self.session.refresh(post)
        await self.session.refresh(vote)

        return vote, post

    async def remove_vote_from_post(
        self,
        user_id: UUID,
        post_id: UUID
    ) -> Optional[Post]:
        """
        Remove a user's vote from a post.

        Args:
            user_id: ID of user removing vote
            post_id: ID of post

        Returns:
            Updated Post or None if vote didn't exist
        """
        # Get existing vote
        vote_result = await self.session.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == user_id,
                    Vote.post_id == post_id
                )
            )
        )
        vote = vote_result.scalar_one_or_none()

        if not vote:
            return None

        # Get post with user
        post_result = await self.session.execute(
            select(Post)
            .options(selectinload(Post.user))
            .where(Post.id == post_id)
        )
        post = post_result.scalar_one()

        # Get voter for weight calculation
        voter_result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        voter = voter_result.scalar_one()

        total_karma = voter.post_karma + voter.comment_karma
        vote_weight = calculate_vote_weight(total_karma)

        # Remove vote effects
        self._update_post_counts(post, vote.vote_value, 0, vote_weight)

        if post.user:
            self._update_user_post_karma(post.user, vote.vote_value, 0, vote_weight)

        # Recalculate hot_score
        post.hot_score = calculate_hot_score(post.upvotes, post.downvotes, post.created_at)

        # Delete vote
        await self.session.delete(vote)
        await self.session.commit()
        await self.session.refresh(post)

        return post

    async def vote_on_comment(
        self,
        user_id: UUID,
        comment_id: UUID,
        vote_value: int
    ) -> Tuple[Vote, Comment]:
        """
        Cast or update a vote on a comment.

        Similar to vote_on_post but for comments.

        Args:
            user_id: ID of user casting vote
            comment_id: ID of comment being voted on
            vote_value: 1 for upvote, -1 for downvote

        Returns:
            Tuple of (Vote, Comment)
        """
        if vote_value not in (1, -1):
            raise ValueError("vote_value must be 1 or -1")

        # Get comment with user
        comment_result = await self.session.execute(
            select(Comment)
            .options(selectinload(Comment.user))
            .where(Comment.id == comment_id)
        )
        comment = comment_result.scalar_one_or_none()

        if not comment:
            raise ValueError(f"Comment {comment_id} not found")

        # Prevent self-voting
        if comment.user_id == user_id:
            raise ValueError("Cannot vote on your own comment")

        # Get voter
        voter_result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        voter = voter_result.scalar_one_or_none()

        if not voter:
            raise ValueError(f"User {user_id} not found")

        total_karma = voter.post_karma + voter.comment_karma
        vote_weight = calculate_vote_weight(total_karma)

        # Check for existing vote
        existing_vote_result = await self.session.execute(
            select(Vote).where(
                and_(
                    Vote.user_id == user_id,
                    Vote.comment_id == comment_id
                )
            )
        )
        existing_vote = existing_vote_result.scalar_one_or_none()

        if existing_vote:
            old_value = existing_vote.vote_value

            if old_value == vote_value:
                return existing_vote, comment

            existing_vote.vote_value = vote_value
            existing_vote.updated_at = datetime.utcnow()

            self._update_comment_counts(comment, -old_value, vote_value, vote_weight)

            if comment.user:
                self._update_user_comment_karma(comment.user, -old_value, vote_value, vote_weight)

            vote = existing_vote

        else:
            vote = Vote(
                user_id=user_id,
                comment_id=comment_id,
                vote_value=vote_value
            )
            self.session.add(vote)

            self._update_comment_counts(comment, 0, vote_value, vote_weight)

            if comment.user:
                self._update_user_comment_karma(comment.user, 0, vote_value, vote_weight)

        await self.session.commit()
        await self.session.refresh(comment)
        await self.session.refresh(vote)

        return vote, comment

    async def get_user_vote(
        self,
        user_id: UUID,
        post_id: Optional[UUID] = None,
        comment_id: Optional[UUID] = None
    ) -> Optional[Vote]:
        """
        Get a user's vote on a post or comment.

        Args:
            user_id: ID of user
            post_id: ID of post (if voting on post)
            comment_id: ID of comment (if voting on comment)

        Returns:
            Vote or None if user hasn't voted
        """
        if post_id:
            result = await self.session.execute(
                select(Vote).where(
                    and_(
                        Vote.user_id == user_id,
                        Vote.post_id == post_id
                    )
                )
            )
        elif comment_id:
            result = await self.session.execute(
                select(Vote).where(
                    and_(
                        Vote.user_id == user_id,
                        Vote.comment_id == comment_id
                    )
                )
            )
        else:
            raise ValueError("Must provide either post_id or comment_id")

        return result.scalar_one_or_none()

    @staticmethod
    def _update_post_counts(post: Post, old_value: int, new_value: int, weight: float):
        """Update denormalized vote counts on a post."""
        # Remove old vote effects
        if old_value == 1:
            post.upvotes -= int(weight)
        elif old_value == -1:
            post.downvotes -= int(weight)

        # Add new vote effects
        if new_value == 1:
            post.upvotes += int(weight)
        elif new_value == -1:
            post.downvotes += int(weight)

        # Update score
        post.score = post.upvotes - post.downvotes

    @staticmethod
    def _update_comment_counts(comment: Comment, old_value: int, new_value: int, weight: float):
        """Update denormalized vote counts on a comment."""
        # Remove old vote effects
        if old_value == 1:
            comment.upvotes -= int(weight)
        elif old_value == -1:
            comment.downvotes -= int(weight)

        # Add new vote effects
        if new_value == 1:
            comment.upvotes += int(weight)
        elif new_value == -1:
            comment.downvotes += int(weight)

        # Update score
        comment.score = comment.upvotes - comment.downvotes

    @staticmethod
    def _update_user_post_karma(user: User, old_value: int, new_value: int, weight: float):
        """Update user's post karma."""
        karma_change = (new_value - old_value) * int(weight)
        user.post_karma = max(0, user.post_karma + karma_change)

    @staticmethod
    def _update_user_comment_karma(user: User, old_value: int, new_value: int, weight: float):
        """Update user's comment karma."""
        karma_change = (new_value - old_value) * int(weight)
        user.comment_karma = max(0, user.comment_karma + karma_change)
