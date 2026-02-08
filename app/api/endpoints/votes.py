"""
API endpoints for voting on posts and comments.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.vote import (
    VoteCreate,
    VoteResponse,
    VoteStatusResponse,
    VoteStatsResponse,
)
from app.services.voting import VotingService

router = APIRouter(prefix="/votes", tags=["votes"])


@router.post("/posts/{post_id}", response_model=VoteResponse, status_code=201)
async def vote_on_post(
    post_id: UUID,
    vote_data: VoteCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Vote on a post.

    - vote_value: 1 for upvote, -1 for downvote
    - If user already voted, updates the vote
    - Cannot vote on own posts
    - Vote weight is based on user's karma
    """
    voting_service = VotingService(session)

    try:
        vote, post = await voting_service.vote_on_post(
            user_id=current_user.id,
            post_id=post_id,
            vote_value=vote_data.vote_value
        )

        return VoteResponse(
            user_id=vote.user_id,
            post_id=vote.post_id,
            comment_id=vote.comment_id,
            vote_value=vote.vote_value,
            created_at=vote.created_at,
            updated_at=vote.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/posts/{post_id}", status_code=204)
async def remove_vote_from_post(
    post_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Remove vote from a post.

    Returns 204 even if vote didn't exist.
    """
    voting_service = VotingService(session)
    await voting_service.remove_vote_from_post(
        user_id=current_user.id,
        post_id=post_id
    )


@router.get("/posts/{post_id}/status", response_model=VoteStatusResponse)
async def get_post_vote_status(
    post_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Check if current user has voted on a post and what their vote is.
    """
    voting_service = VotingService(session)
    vote = await voting_service.get_user_vote(
        user_id=current_user.id,
        post_id=post_id
    )

    if vote:
        return VoteStatusResponse(
            has_voted=True,
            vote_value=vote.vote_value
        )
    else:
        return VoteStatusResponse(
            has_voted=False,
            vote_value=None
        )


@router.post("/comments/{comment_id}", response_model=VoteResponse, status_code=201)
async def vote_on_comment(
    comment_id: UUID,
    vote_data: VoteCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Vote on a comment.

    - vote_value: 1 for upvote, -1 for downvote
    - If user already voted, updates the vote
    - Cannot vote on own comments
    - Vote weight is based on user's karma
    """
    voting_service = VotingService(session)

    try:
        vote, comment = await voting_service.vote_on_comment(
            user_id=current_user.id,
            comment_id=comment_id,
            vote_value=vote_data.vote_value
        )

        return VoteResponse(
            user_id=vote.user_id,
            post_id=vote.post_id,
            comment_id=vote.comment_id,
            vote_value=vote.vote_value,
            created_at=vote.created_at,
            updated_at=vote.updated_at,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/comments/{comment_id}/status", response_model=VoteStatusResponse)
async def get_comment_vote_status(
    comment_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Check if current user has voted on a comment and what their vote is.
    """
    voting_service = VotingService(session)
    vote = await voting_service.get_user_vote(
        user_id=current_user.id,
        comment_id=comment_id
    )

    if vote:
        return VoteStatusResponse(
            has_voted=True,
            vote_value=vote.vote_value
        )
    else:
        return VoteStatusResponse(
            has_voted=False,
            vote_value=None
        )
