"""
User management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List
from uuid import UUID

from app.core.database import get_async_session
from app.core.auth import get_current_user
from app.models.user import User
from app.models.schemas import UserCreate, UserUpdate, UserResponse, UserPublic, ErrorResponse
import asyncpg

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Create a new user profile.
    
    This endpoint creates a user profile linked to a Cognito user ID.
    Authentication should be handled by Cognito before calling this endpoint.
    """
    try:
        # Create new user instance
        new_user = User(
            cognito_id=user_data.cognito_id,
            email=user_data.email,
            display_name=user_data.display_name,
            bio=user_data.bio,
            role=user_data.role,
            is_expert=user_data.is_expert,
            expertise_areas=user_data.expertise_areas,
            institution=user_data.institution,
            website_url=user_data.website_url
        )
        
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        
        return new_user
        
    except Exception as e:
        await session.rollback()
        if "unique constraint" in str(e).lower():
            if "cognito_id" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this Cognito ID already exists"
                )
            elif "email" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by ID."""
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/cognito/{cognito_id}", response_model=UserResponse)
async def get_user_by_cognito_id(
    cognito_id: str,
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by Cognito ID."""
    result = await session.execute(select(User).where(User.cognito_id == cognito_id))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/", response_model=List[UserPublic])
async def list_users(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session)
):
    """
    List users with pagination.
    
    Returns public user information only.
    """
    if limit > 100:
        limit = 100  # Prevent excessive queries
    
    result = await session.execute(
        select(User)
        .where(User.is_active == True)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    users = result.scalars().all()
    
    return users


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """Update user information. Users can only update their own profiles."""
    # Check if user is trying to update their own profile
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    user = current_user  # Use the authenticated user
    
    # Update only provided fields
    update_data = user_update.model_dump(exclude_unset=True)
    if update_data:
        for field, value in update_data.items():
            setattr(user, field, value)
        
        try:
            await session.commit()
            await session.refresh(user)
            return user
            
        except Exception as e:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
    
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Deactivate user account. Users can only deactivate their own accounts.
    """
    # Check if user is trying to deactivate their own account
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only deactivate your own account"
        )
    
    current_user.is_active = False
    
    try:
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.get("/experts/", response_model=List[UserPublic])
async def list_experts(
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_async_session)
):
    """List expert users."""
    if limit > 50:
        limit = 50
    
    result = await session.execute(
        select(User)
        .where(User.is_expert == True, User.is_active == True)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    experts = result.scalars().all()
    
    return experts