"""
Vercel-compatible FastAPI entry point for SecureAI backend.
Python 3.12 compatible version with enhanced error handling.
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_minimal_app():
    """Create a minimal FastAPI app for testing deployment."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(title="SecureAI API", version="1.0.0")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify your frontend domain
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        return {
            "message": "SecureAI API is running",
            "status": "online",
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform
        }
    
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "service": "SecureAI Backend",
            "environment": "production"
        }
    
    @app.post("/api/interpret")
    async def interpret_fallback(data: Dict[str, Any]):
        return {
            "error": "Full AI functionality not loaded",
            "message": "Basic API is working, but AI features need full deployment",
            "received": data
        }
    
    return app

# Try to import the full application, fall back to minimal if needed
try:
    from agentcrews.mediator.hackathon_backend import app
    print("✅ Successfully loaded full SecureAI application")
except ImportError as e:
    print(f"⚠️ Falling back to minimal app due to import error: {str(e)}")
    app = create_minimal_app()
except Exception as e:
    print(f"⚠️ Unexpected error, using minimal app: {str(e)}")
    app = create_minimal_app()

# Vercel entry point
def handler(request):
    """Vercel serverless function handler."""
    return app(request)

# For local development compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)