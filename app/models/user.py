"""
User model for storing user profiles linked to AWS Cognito.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class User(Base):
    """
    User profile model linked to AWS Cognito.
    
    Note: Authentication is handled by Cognito, this stores additional profile data.
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "alter_earth"}

    # Use UUID as primary key for better scalability
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Link to Cognito user (this is the key field)
    cognito_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic profile information
    email = Column(String(255), unique=True, nullable=False, index=True)
    nickname = Column(String(50), nullable=False, unique=True, index=True)
    bio = Column(Text, nullable=True)
    
    # Optional real name (user choice to share)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    show_real_name = Column(Boolean, default=False, nullable=False)
    
    # User role and permissions
    role = Column(String(20), nullable=False, default="member")  # member, expert, moderator, admin
    is_expert = Column(Boolean, default=False, nullable=False)
    
    # Expert-specific fields
    expertise_areas = Column(Text, nullable=True)  # JSON string of expertise areas
    institution = Column(String(200), nullable=True)
    website_url = Column(String(500), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Engagement metrics (for platform insights)
    post_count = Column(Integer, default=0, nullable=False)
    comment_count = Column(Integer, default=0, nullable=False)
    vote_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_active_at = Column(DateTime(timezone=True), nullable=True)

    @property
    def display_name(self):
        """Display name based on user preference."""
        if self.show_real_name and self.first_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.nickname
    
    @property
    def greeting_name(self):
        """Name for personalized greetings."""
        if self.show_real_name and self.first_name:
            return self.first_name
        return self.nickname

    def __repr__(self):
        return f"<User(id={self.id}, cognito_id={self.cognito_id}, email={self.email}, role={self.role})>"