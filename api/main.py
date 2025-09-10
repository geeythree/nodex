"""
Vercel-compatible FastAPI entry point for SecureAI backend.
This file adapts the main application to work with Vercel's serverless functions.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from agentcrews.mediator.hackathon_backend import app
except ImportError as e:
    # Fallback for deployment issues
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    app = FastAPI(title="SecureAI API", version="1.0.0")
    
    @app.get("/")
    async def root():
        return {"message": "SecureAI API is running", "error": f"Import error: {str(e)}"}
    
    @app.get("/health")
    async def health():
        return {"status": "degraded", "message": "Running in fallback mode", "import_error": str(e)}

# Vercel entry point
def handler(request):
    """Vercel serverless function handler."""
    return app(request)

# For local development compatibility
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)