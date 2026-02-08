"""
API endpoints for comments with threading support.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import selectinload
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
from app.schemas.comment import (
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentWithReplies,
    CommentTreeResponse,
    CommentAuthor,
)

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("", response_model=CommentResponse, status_code=201)
async def create_comment(
    post_id: UUID,
    comment_data: CommentCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new comment on a post or reply to an existing comment.

    - If parent_id is null, creates a top-level comment
    - If parent_id is set, creates a reply to that comment
    """
    # Verify post exists
    post_result = await session.execute(
        select(Post).where(Post.id == post_id)
    )
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Verify parent comment exists if specified
    if comment_data.parent_id:
        parent_result = await session.execute(
            select(Comment).where(
                and_(
                    Comment.id == comment_data.parent_id,
                    Comment.post_id == post_id  # Ensure parent is on same post
                )
            )
        )
        parent = parent_result.scalar_one_or_none()

        if not parent:
            raise HTTPException(
                status_code=404,
                detail="Parent comment not found or not on this post"
            )

    # Create comment
    comment = Comment(
        content=comment_data.content,
        user_id=current_user.id,
        post_id=post_id,
        parent_id=comment_data.parent_id,
    )
    session.add(comment)

    # Update post comment count
    post.comment_count += 1

    # Update user's comment count
    current_user.comment_count += 1

    await session.commit()
    await session.refresh(comment)

    # Build response with author info
    author = CommentAuthor(
        id=current_user.id,
        nickname=current_user.nickname,
        user_type=current_user.user_type.value,
        is_expert=current_user.is_expert,
    )

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        user_id=comment.user_id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        upvotes=comment.upvotes,
        downvotes=comment.downvotes,
        score=comment.score,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=author,
    )


@router.get("/post/{post_id}", response_model=CommentTreeResponse)
async def get_post_comments(
    post_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """
    Get all comments for a post as a threaded tree structure.

    Returns top-level comments with nested replies.
    """
    # Verify post exists
    post_result = await session.execute(
        select(Post).where(Post.id == post_id)
    )
    post = post_result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Get all comments for this post
    query = select(Comment).where(
        Comment.post_id == post_id
    ).options(
        selectinload(Comment.user)
    ).order_by(Comment.created_at)

    result = await session.execute(query)
    all_comments = result.scalars().all()

    # Build comment tree
    comment_tree = _build_comment_tree(all_comments)

    # Count top-level comments
    top_level_count = sum(1 for c in all_comments if c.parent_id is None)

    return CommentTreeResponse(
        post_id=post_id,
        total_comments=len(all_comments),
        top_level_count=top_level_count,
        comments=comment_tree,
    )


@router.get("/{comment_id}", response_model=CommentResponse)
async def get_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user),
):
    """Get a single comment by ID."""
    query = select(Comment).where(Comment.id == comment_id).options(
        selectinload(Comment.user)
    )

    result = await session.execute(query)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Build author info
    author = None
    if comment.user:
        author = CommentAuthor(
            id=comment.user.id,
            nickname=comment.user.nickname,
            user_type=comment.user.user_type.value,
            is_expert=comment.user.is_expert,
        )

    return CommentResponse(
        id=comment.id,
        content=comment.content if not comment.is_deleted else "[deleted]",
        user_id=comment.user_id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        upvotes=comment.upvotes,
        downvotes=comment.downvotes,
        score=comment.score,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=author,
    )


@router.put("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: UUID,
    update_data: CommentUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update a comment's content.

    Only the comment author can update it.
    """
    query = select(Comment).where(Comment.id == comment_id).options(
        selectinload(Comment.user)
    )

    result = await session.execute(query)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check ownership
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only edit your own comments"
        )

    # Can't edit deleted comments
    if comment.is_deleted:
        raise HTTPException(status_code=400, detail="Cannot edit deleted comment")

    # Update content
    comment.content = update_data.content
    comment.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(comment)

    author = CommentAuthor(
        id=current_user.id,
        nickname=current_user.nickname,
        user_type=current_user.user_type.value,
        is_expert=current_user.is_expert,
    )

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        user_id=comment.user_id,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        upvotes=comment.upvotes,
        downvotes=comment.downvotes,
        score=comment.score,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=author,
    )


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    comment_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete a comment.

    Only the comment author can delete it.
    Preserves thread structure by marking as deleted instead of removing.
    """
    query = select(Comment).where(Comment.id == comment_id)
    result = await session.execute(query)
    comment = result.scalar_one_or_none()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check ownership
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="You can only delete your own comments"
        )

    # Soft delete
    comment.is_deleted = True
    comment.content = "[deleted]"

    await session.commit()


def _build_comment_tree(comments: List[Comment]) -> List[CommentWithReplies]:
    """
    Build a nested comment tree from a flat list of comments.

    Args:
        comments: Flat list of all comments

    Returns:
        List of top-level comments with nested replies
    """
    # Create a mapping of comment_id -> comment data
    comment_map = {}

    for comment in comments:
        author = None
        if comment.user:
            author = CommentAuthor(
                id=comment.user.id,
                nickname=comment.user.nickname,
                user_type=comment.user.user_type.value,
                is_expert=comment.user.is_expert,
            )

        comment_with_replies = CommentWithReplies(
            id=comment.id,
            content=comment.content if not comment.is_deleted else "[deleted]",
            user_id=comment.user_id,
            post_id=comment.post_id,
            parent_id=comment.parent_id,
            upvotes=comment.upvotes,
            downvotes=comment.downvotes,
            score=comment.score,
            is_deleted=comment.is_deleted,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            author=author,
            replies=[],
            reply_count=0,
        )
        comment_map[comment.id] = comment_with_replies

    # Build tree structure
    top_level_comments = []

    for comment in comments:
        comment_data = comment_map[comment.id]

        if comment.parent_id is None:
            # Top-level comment
            top_level_comments.append(comment_data)
        else:
            # Reply - add to parent's replies
            if comment.parent_id in comment_map:
                parent = comment_map[comment.parent_id]
                parent.replies.append(comment_data)
                parent.reply_count += 1

    # Sort by score (best first) at each level
    def sort_comments(comment_list):
        comment_list.sort(key=lambda c: c.score, reverse=True)
        for comment in comment_list:
            if comment.replies:
                sort_comments(comment.replies)

    sort_comments(top_level_comments)

    return top_level_comments
