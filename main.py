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

# Simple news router for testing
from fastapi import APIRouter
news_router = APIRouter()

@news_router.get("/")
async def get_news():
    return {"message": "News endpoint working", "articles": []}

@news_router.get("/test")
async def test_news():
    return {"status": "News API is working!"}

app.include_router(news_router, prefix="/api/v1/news", tags=["news"])

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