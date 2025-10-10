"""
Authentication endpoints for AWS Cognito integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_async_session
from app.core.auth import cognito_auth, get_or_create_user_profile, get_current_user
from app.models.user import User
from app.models.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


class TokenExchangeRequest(BaseModel):
    code: str
    redirect_uri: str = "http://localhost:3000/auth/callback"


class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    token_type: str
    expires_in: int
    user: UserResponse


@router.post("/exchange", response_model=TokenResponse)
async def exchange_authorization_code(
    request: TokenExchangeRequest,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Exchange authorization code for JWT tokens and create/sync user profile.
    
    This endpoint is called by the frontend after successful Cognito authentication.
    It handles both new user registration and existing user login.
    """
    try:
        # Exchange code for tokens with Cognito
        tokens = await cognito_auth.exchange_code_for_tokens(
            code=request.code,
            redirect_uri=request.redirect_uri
        )
        
        # Verify and decode the ID token to get user info
        user_info = await cognito_auth.verify_token(tokens['id_token'])
        
        # Create or get existing user profile
        user = await get_or_create_user_profile(user_info, session)
        
        # Return tokens and user info
        return TokenResponse(
            access_token=tokens['access_token'],
            id_token=tokens['id_token'],
            token_type=tokens.get('token_type', 'Bearer'),
            expires_in=tokens.get('expires_in', 3600),
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    Standard endpoint following Reddit/GitHub pattern.
    """
    return current_user