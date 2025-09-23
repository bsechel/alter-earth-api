"""
Alter Earth API - Sustainable Community Platform
A FastAPI backend for ecological conservation and green technology discussions.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Alter Earth API",
    description="A sustainable community platform with AI-powered content curation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Alter Earth API",
        "description": "Sustainable community platform with AI-powered content curation",
        "version": "0.1.0",
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