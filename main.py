"""
Alter Earth API - Technology for Ecological Conservation
A FastAPI backend platform dedicated to ecological conservation, sustainability, 
and leveraging technology and AI for environmental good.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

from app.core.config import settings
from app.core.database import create_async_database_engine
from app.api.endpoints import users, news

# Initialize FastAPI app with settings
app = FastAPI(
    title=settings.app_name,
    description="A community platform for ecological conservation, sustainability advocacy, and using AI for environmental good",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(users.router, prefix="/api/v1")

# Simple test endpoint for database connection
@app.get("/test-db")
async def test_database_connection():
    try:
        from app.core.database import get_async_session
        from sqlalchemy import text
        async for session in get_async_session():
            # Simple query to test connection and schema
            result = await session.execute(text("SELECT 1"))
            count_result = await session.execute(text("SELECT COUNT(*) FROM alter_earth.news_articles"))
            return {
                "status": "Database connected", 
                "test_result": result.scalar(),
                "news_articles_count": count_result.scalar()
            }
    except Exception as e:
        return {"status": "Database error", "error": str(e)}

app.include_router(news.router, prefix="/api/v1/news", tags=["news"])

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    create_async_database_engine()

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "description": "A community platform dedicated to ecological conservation and sustainability",
        "mission": "Building community around ecological conservation, sustainability advocacy, and using AI for environmental good",
        "version": settings.app_version,
        "docs": "/docs",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "alter-earth-api"
    }

@app.get("/api/v1/info")
async def api_info():
    """API information endpoint."""
    return {
        "api_version": "v1",
        "features": [
            "User Authentication (AWS Cognito)",
            "Content Management (Posts, Articles, Comments)",
            "AI-Powered Content Curation (Claude API)",
            "Real-time Updates",
            "Background Processing"
        ],
        "status": "development"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)