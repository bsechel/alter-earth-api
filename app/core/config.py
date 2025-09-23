"""
Core configuration settings for Alter Earth API.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Settings
    app_name: str = "Alter Earth API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # Database Settings (Supabase)
    database_url: Optional[str] = None
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # AWS Cognito Settings
    cognito_region: Optional[str] = None
    cognito_user_pool_id: Optional[str] = None
    cognito_client_id: Optional[str] = None
    
    # Claude API Settings
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3-sonnet-20240229"
    
    # Redis Settings (for caching and background jobs)
    redis_url: str = "redis://localhost:6379"
    
    # Security Settings
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Settings
    allowed_origins: list = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # News API Settings
    news_api_sources: list = [
        "https://feeds.feedburner.com/EnvironmentalNews-ScienceDaily",
        "https://www.treehugger.com/feeds/all",
        "https://www.greentechmedia.com/rss"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency to get settings instance."""
    return settings