"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    display_name: str = Field(..., min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    role: str = Field(default="member", pattern="^(member|expert|moderator|admin)$")
    is_expert: bool = False
    expertise_areas: Optional[str] = Field(None, max_length=500)
    institution: Optional[str] = Field(None, max_length=200)
    website_url: Optional[str] = Field(None, max_length=500)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    cognito_id: str = Field(..., min_length=1, max_length=255)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "cognito_id": "cognito-user-12345",
                "email": "john.doe@example.com",
                "display_name": "John Doe",
                "bio": "Environmental scientist passionate about sustainability",
                "role": "member",
                "is_expert": False,
                "expertise_areas": "renewable energy, carbon sequestration",
                "institution": "University of California",
                "website_url": "https://johndoe.example.com"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    bio: Optional[str] = Field(None, max_length=1000)
    expertise_areas: Optional[str] = Field(None, max_length=500)
    institution: Optional[str] = Field(None, max_length=200)
    website_url: Optional[str] = Field(None, max_length=500)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "Dr. John Doe",
                "bio": "Senior Environmental Scientist with 15 years of experience",
                "expertise_areas": "renewable energy, carbon capture, sustainable agriculture",
                "institution": "Stanford Environmental Institute"
            }
        }
    )


class UserResponse(UserBase):
    """Schema for user response data."""
    id: UUID
    cognito_id: str
    is_active: bool
    is_verified: bool
    post_count: int
    comment_count: int
    vote_count: int
    created_at: datetime
    updated_at: datetime
    last_active_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Public user schema (limited information for general display)."""
    id: UUID
    display_name: str
    bio: Optional[str]
    is_expert: bool
    expertise_areas: Optional[str]
    institution: Optional[str]
    website_url: Optional[str]
    post_count: int
    comment_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserStats(BaseModel):
    """User engagement statistics."""
    total_posts: int
    total_comments: int
    total_votes: int
    expert_articles: Optional[int] = 0
    member_since: datetime
    last_active: Optional[datetime]


# Error response schemas
class ErrorResponse(BaseModel):
    """Standard error response schema."""
    detail: str
    error_code: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "User not found",
                "error_code": "USER_NOT_FOUND"
            }
        }
    )


class ValidationErrorResponse(BaseModel):
    """Validation error response schema."""
    detail: str
    errors: list[dict]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Validation error",
                "errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "type": "value_error"
                    }
                ]
            }
        }
    )