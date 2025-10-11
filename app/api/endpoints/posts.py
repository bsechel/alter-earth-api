"""
API endpoints for posts (list, get, create user submissions).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from typing import Optional
from datetime import datetime, timezone, timedelta
from uuid import UUID

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.post import Post, UserSubmission, AutomatedArticle, EntityType, SubmissionType
from app.schemas.post import (
    PostResponse,
    PostListItem,
    PostListResponse,
    PostQueryParams,
    UserSubmissionCreate,
    SortOption,
    TimePeriod,
)
from app.services.scoring import calculate_hot_score

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=PostListResponse)
async def list_posts(
    sort: SortOption = Query(default=SortOption.hot),
    time_period: TimePeriod = Query(default=TimePeriod.day),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    community_id: Optional[UUID] = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
):
    """
    List posts with sorting and pagination.

    Supports multiple sort options:
    - hot: Reddit-style hot ranking (default)
    - top: Highest score in time period
    - new: Most recent first
    - controversial: Most debated
    - rising: Trending among new posts
    """
    # Build base query
    query = select(Post).where(Post.is_active == True)

    # Filter by community if specified
    if community_id:
        query = query.where(Post.community_id == community_id)

    # Apply sorting
    if sort == SortOption.hot:
        query = query.order_by(desc(Post.hot_score))

    elif sort == SortOption.top:
        # Filter by time period for "top"
        if time_period != TimePeriod.all:
            cutoff = _get_time_cutoff(time_period)
            query = query.where(Post.created_at >= cutoff)
        query = query.order_by(desc(Post.score))

    elif sort == SortOption.new:
        query = query.order_by(desc(Post.created_at))

    elif sort == SortOption.controversial:
        # Controversial = high vote count, low score
        # We'll calculate this in Python for now (could optimize with DB function)
        query = query.where(
            and_(
                Post.upvotes + Post.downvotes > 10,  # Minimum activity
                func.abs(Post.score) < (Post.upvotes + Post.downvotes) * 0.3  # Balanced
            )
        ).order_by(desc(Post.upvotes + Post.downvotes))

    elif sort == SortOption.rising:
        # Rising = new posts (< 24h) with good score
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        query = query.where(
            and_(
                Post.created_at >= cutoff,
                Post.score > 0
            )
        ).order_by(desc(Post.score / func.extract('epoch', func.now() - Post.created_at)))

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    # Load posts with relationships
    query = query.options(
        selectinload(Post.user),
        selectinload(Post.automated_article),
        selectinload(Post.user_submission)
    )

    result = await session.execute(query)
    posts = result.scalars().all()

    # Convert to list items
    post_items = []
    for post in posts:
        # Build preview based on entity type
        preview_text = None
        preview_url = None
        source_name = None

        if post.entity_type == EntityType.automated_article and post.automated_article:
            article = post.automated_article
            preview_text = article.description or article.content
            if preview_text and len(preview_text) > 200:
                preview_text = preview_text[:200] + "..."
            preview_url = article.url
            source_name = article.source_name

        elif post.entity_type == EntityType.user_submission and post.user_submission:
            submission = post.user_submission
            if submission.submission_type == SubmissionType.text:
                preview_text = submission.content
                if preview_text and len(preview_text) > 200:
                    preview_text = preview_text[:200] + "..."
            elif submission.submission_type == SubmissionType.link:
                preview_url = submission.url

        post_item = PostListItem(
            id=post.id,
            title=post.title,
            entity_type=post.entity_type.value,
            user_id=post.user_id,
            score=post.score,
            upvotes=post.upvotes,
            downvotes=post.downvotes,
            comment_count=post.comment_count,
            created_at=post.created_at,
            preview_text=preview_text,
            preview_url=preview_url,
            source_name=source_name,
            user_nickname=post.user.nickname if post.user else None,
            user_type=post.user.user_type.value if post.user else None,
        )
        post_items.append(post_item)

    return PostListResponse(
        posts=post_items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(offset + page_size) < total
    )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get a single post by ID with full details."""
    query = select(Post).where(Post.id == post_id).options(
        selectinload(Post.user),
        selectinload(Post.automated_article),
        selectinload(Post.user_submission)
    )

    result = await session.execute(query)
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Increment view count
    post.view_count += 1
    await session.commit()

    # Build response
    response_data = {
        "id": post.id,
        "title": post.title,
        "entity_type": post.entity_type.value,
        "user_id": post.user_id,
        "community_id": post.community_id,
        "upvotes": post.upvotes,
        "downvotes": post.downvotes,
        "score": post.score,
        "hot_score": post.hot_score,
        "view_count": post.view_count,
        "comment_count": post.comment_count,
        "is_active": post.is_active,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "user_nickname": post.user.nickname if post.user else None,
        "user_type": post.user.user_type.value if post.user else None,
    }

    # Add detail data based on entity type
    if post.entity_type == EntityType.automated_article and post.automated_article:
        response_data["automated_article"] = post.automated_article

    elif post.entity_type == EntityType.user_submission and post.user_submission:
        response_data["user_submission"] = post.user_submission

    return PostResponse(**response_data)


@router.post("", response_model=PostResponse, status_code=201)
async def create_user_submission(
    submission: UserSubmissionCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new user submission (text or link post).

    Requires authentication.
    """
    # Create the post
    post = Post(
        title=submission.title,
        entity_type=EntityType.user_submission,
        user_id=current_user.id,
        hot_score=calculate_hot_score(0, 0, datetime.now(timezone.utc))
    )
    session.add(post)
    await session.flush()  # Get post.id

    # Create the user submission detail
    user_submission = UserSubmission(
        post_id=post.id,
        submission_type=submission.submission_type.value,
        content=submission.content,
        url=submission.url
    )
    session.add(user_submission)

    # Update user's post count
    current_user.post_count += 1

    await session.commit()
    await session.refresh(post)
    await session.refresh(user_submission)

    # Build response
    response_data = {
        "id": post.id,
        "title": post.title,
        "entity_type": post.entity_type.value,
        "user_id": post.user_id,
        "community_id": post.community_id,
        "upvotes": post.upvotes,
        "downvotes": post.downvotes,
        "score": post.score,
        "hot_score": post.hot_score,
        "view_count": post.view_count,
        "comment_count": post.comment_count,
        "is_active": post.is_active,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "user_submission": user_submission,
        "user_nickname": current_user.nickname,
        "user_type": current_user.user_type.value,
    }

    return PostResponse(**response_data)


def _get_time_cutoff(time_period: TimePeriod) -> datetime:
    """Get cutoff datetime for time period filter."""
    now = datetime.now(timezone.utc)

    if time_period == TimePeriod.hour:
        return now - timedelta(hours=1)
    elif time_period == TimePeriod.day:
        return now - timedelta(days=1)
    elif time_period == TimePeriod.week:
        return now - timedelta(weeks=1)
    elif time_period == TimePeriod.month:
        return now - timedelta(days=30)
    elif time_period == TimePeriod.year:
        return now - timedelta(days=365)
    else:  # all
        return datetime.min.replace(tzinfo=timezone.utc)
