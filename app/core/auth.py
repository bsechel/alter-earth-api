"""
AWS Cognito authentication service for JWT token validation.
"""

import requests
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.config import settings
from app.core.database import get_async_session
from app.models.user import User

security = HTTPBearer()


class CognitoAuth:
    """AWS Cognito JWT token validation service."""
    
    def __init__(self):
        self.region = settings.cognito_region
        self.user_pool_id = settings.cognito_user_pool_id
        self.client_id = settings.cognito_client_id
        self.jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
        self._jwks = None
    
    async def get_jwks(self):
        """Fetch JSON Web Key Set from Cognito."""
        if not self._jwks:
            response = requests.get(self.jwks_url)
            response.raise_for_status()
            self._jwks = response.json()
        return self._jwks
    
    async def verify_token(self, token: str) -> dict:
        """
        Verify JWT token with Cognito public keys.
        Returns decoded token payload.
        """
        try:
            # Get signing keys
            jwks = await self.get_jwks()
            
            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')
            
            # Find the matching key
            key = None
            for jwk in jwks['keys']:
                if jwk['kid'] == kid:
                    key = jwk
                    break
            
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find matching key"
                )
            
            # Verify and decode token
            payload = jwt.decode(
                token,
                key,
                algorithms=['RS256'],
                audience=self.client_id,
                issuer=f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}",
                options={"verify_at_hash": False}  # Skip at_hash verification for ID tokens
            )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
    
    async def exchange_code_for_tokens(self, code: str, redirect_uri: str) -> dict:
        """
        Exchange authorization code for access/ID tokens.
        """
        token_url = f"https://{settings.cognito_domain}/oauth2/token"
        
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': code,
            'redirect_uri': redirect_uri
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = requests.post(token_url, data=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Token exchange failed: {str(e)}"
            )


# Global auth instance
cognito_auth = CognitoAuth()


async def get_current_user(
    token: str = Depends(security),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    """
    Dependency to get current user from JWT token.
    Validates token and returns user from database.
    """
    try:
        # Verify token and extract user info
        payload = await cognito_auth.verify_token(token.credentials)
        cognito_id = payload['sub']
        
        # Get user from database
        result = await session.execute(
            select(User).where(User.cognito_id == cognito_id)
        )
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User profile not found. Please complete registration."
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def generate_unique_nickname(base_nickname: str, session: AsyncSession) -> str:
    """
    Generate a unique nickname by appending numbers if needed.
    """
    # Clean up the base nickname
    base_nickname = base_nickname.replace(' ', '').lower()
    
    # Check if base nickname is available
    result = await session.execute(
        select(User).where(User.nickname == base_nickname)
    )
    if not result.scalars().first():
        return base_nickname
    
    # Try with numbers
    for i in range(1, 1000):
        candidate = f"{base_nickname}{i}"
        result = await session.execute(
            select(User).where(User.nickname == candidate)
        )
        if not result.scalars().first():
            return candidate
    
    # Fallback: use random suffix
    import random
    return f"{base_nickname}{random.randint(1000, 9999)}"


async def get_or_create_user_profile(user_info: dict, session: AsyncSession) -> User:
    """
    Get existing user or create new profile from Cognito user info.
    Creates a temporary nickname that user can change later.
    """
    cognito_id = user_info['sub']
    
    # Check if user already exists
    result = await session.execute(
        select(User).where(User.cognito_id == cognito_id)
    )
    existing_user = result.scalars().first()
    
    if existing_user:
        return existing_user
    
    # Extract optional name information
    first_name = user_info.get('given_name')
    last_name = user_info.get('family_name')
    
    # If no names from Cognito, try parsing 'name' field
    if not first_name and not last_name:
        full_name = user_info.get('name', '')
        if full_name:
            name_parts = full_name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else None
    
    # Generate initial nickname from available info
    if first_name:
        base_nickname = first_name
    else:
        # Use email prefix as fallback
        base_nickname = user_info['email'].split('@')[0]
    
    # Ensure nickname is unique
    nickname = await generate_unique_nickname(base_nickname, session)
    
    # Create new user
    new_user = User(
        cognito_id=cognito_id,
        email=user_info['email'],
        nickname=nickname,
        first_name=first_name,
        last_name=last_name,
        is_verified=user_info.get('email_verified', False)
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user