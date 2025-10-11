"""
Scoring algorithms for posts and comments.
Implements Reddit-style ranking with hot, top, controversial, and rising algorithms.
"""

import math
from datetime import datetime, timezone
from typing import Union


class ScoringService:
    """Service for calculating post/comment scores and rankings."""

    # Reference epoch for hot score calculation (can be site launch date)
    # Using Jan 1, 2020 as default reference point
    EPOCH = datetime(2020, 1, 1, tzinfo=timezone.utc)

    @staticmethod
    def calculate_hot_score(
        upvotes: int,
        downvotes: int,
        created_at: datetime
    ) -> float:
        """
        Calculate Reddit-style hot score with time decay.

        Formula: log10(max(abs(score), 1)) * sign(score) + (created_at_epoch / 45000)

        This balances popularity with recency:
        - Popular posts get higher scores
        - Newer posts get a time boost
        - The first 10 upvotes matter more than the next 100

        Args:
            upvotes: Number of upvotes
            downvotes: Number of downvotes
            created_at: When the post was created

        Returns:
            Hot score (float) for ranking
        """
        score = upvotes - downvotes

        # Handle edge cases
        if score == 0:
            order = 0
        else:
            # log10(max(abs(score), 1)) ensures we never take log of 0
            # Multiply by sign to preserve negative scores
            order = math.log10(max(abs(score), 1)) * (1 if score > 0 else -1)

        # Time component - newer posts get boost
        # Ensure created_at has timezone info
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        seconds_since_epoch = (created_at - ScoringService.EPOCH).total_seconds()

        # 45000 seconds = 12.5 hours
        # This means a post loses ~1 point of ranking every 12.5 hours
        time_component = seconds_since_epoch / 45000

        return order + time_component

    @staticmethod
    def calculate_controversial_score(upvotes: int, downvotes: int) -> float:
        """
        Calculate controversy score.

        Posts are controversial when they have many votes but score near zero.
        Formula: (upvotes + downvotes) if abs(score) is low

        Args:
            upvotes: Number of upvotes
            downvotes: Number of downvotes

        Returns:
            Controversy score (higher = more controversial)
        """
        score = upvotes - downvotes
        total_votes = upvotes + downvotes

        if total_votes == 0:
            return 0.0

        # Controversial if close to 50/50 split
        # Balance is how close to 50/50 (0.0 = perfect balance, 1.0 = all one side)
        balance = abs(score) / total_votes

        # Return total votes weighted by how balanced it is
        # Less balance (closer to 50/50) = higher controversy
        return total_votes * (1 - balance)

    @staticmethod
    def calculate_rising_score(
        upvotes: int,
        downvotes: int,
        created_at: datetime,
        max_age_hours: float = 24.0
    ) -> float:
        """
        Calculate rising score for new posts gaining traction.

        Formula: score / (hours_since_creation + 2)^1.5

        Only considers posts less than max_age_hours old.

        Args:
            upvotes: Number of upvotes
            downvotes: Number of downvotes
            created_at: When the post was created
            max_age_hours: Maximum age to consider (default 24 hours)

        Returns:
            Rising score (0 if too old, otherwise velocity-based score)
        """
        score = upvotes - downvotes

        # Ensure created_at has timezone info
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        age = datetime.now(timezone.utc) - created_at
        hours_old = age.total_seconds() / 3600

        # Too old to be "rising"
        if hours_old > max_age_hours:
            return 0.0

        # Velocity calculation - score divided by time^1.5
        # The +2 prevents division by zero and gives very new posts a fair chance
        velocity = score / math.pow(hours_old + 2, 1.5)

        return max(velocity, 0.0)  # Don't return negative rising scores

    @staticmethod
    def calculate_vote_weight(karma: int) -> float:
        """
        Calculate vote weight based on user's karma.

        Formula: 1 + log10(karma + 1)

        This gives established users more influence, but with diminishing returns.

        Examples:
        - karma = 0: weight = 1.0
        - karma = 9: weight = 2.0
        - karma = 99: weight = 3.0
        - karma = 999: weight = 4.0

        Args:
            karma: User's total karma (post_karma + comment_karma)

        Returns:
            Vote weight multiplier (>= 1.0)
        """
        return 1.0 + math.log10(max(karma, 0) + 1)

    @staticmethod
    def fuzz_count(count: int, fuzz_percent: float = 0.1) -> int:
        """
        Apply fuzzing to vote counts to prevent vote manipulation detection.

        Args:
            count: Actual vote count
            fuzz_percent: Percentage to fuzz (default 10%)

        Returns:
            Fuzzed count (slightly randomized)
        """
        import random

        if count == 0:
            return 0

        # Add random noise within fuzz_percent
        fuzz_amount = int(count * fuzz_percent)
        if fuzz_amount == 0:
            fuzz_amount = 1

        return count + random.randint(-fuzz_amount, fuzz_amount)


# Convenience functions for direct use
def calculate_hot_score(upvotes: int, downvotes: int, created_at: datetime) -> float:
    """Calculate hot score for a post/comment."""
    return ScoringService.calculate_hot_score(upvotes, downvotes, created_at)


def calculate_controversial_score(upvotes: int, downvotes: int) -> float:
    """Calculate controversy score for a post/comment."""
    return ScoringService.calculate_controversial_score(upvotes, downvotes)


def calculate_rising_score(upvotes: int, downvotes: int, created_at: datetime) -> float:
    """Calculate rising score for a post."""
    return ScoringService.calculate_rising_score(upvotes, downvotes, created_at)


def calculate_vote_weight(karma: int) -> float:
    """Calculate vote weight based on karma."""
    return ScoringService.calculate_vote_weight(karma)
