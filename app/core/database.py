"""
Database configuration and connection setup for Supabase.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from app.core.config import settings

# Create declarative base for models
Base = declarative_base()

# Async database engine (recommended for FastAPI)
async_engine = None
async_session_maker = None

def create_async_database_engine():
    """Create async database engine for Supabase."""
    global async_engine, async_session_maker
    
    if not settings.database_url:
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Convert postgres:// to postgresql+asyncpg:// for async support
    database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    async_engine = create_async_engine(
        database_url,
        echo=settings.debug,  # Log SQL queries in debug mode
        pool_size=5,  # Reduced pool size for better compatibility
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before use
        # Fix for Supabase pooler - completely disable prepared statements
        connect_args={
            "prepared_statement_cache_size": 0,
            "statement_cache_size": 0,
        }
    )
    
    async_session_maker = async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    return async_engine

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    if not async_session_maker:
        create_async_database_engine()
    
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    if not async_engine:
        create_async_database_engine()
    
    async with async_engine.begin() as conn:
        # Import all models to ensure they're registered
        from app.models import user  # Only import models that exist
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """Close database connections."""
    if async_engine:
        await async_engine.dispose()