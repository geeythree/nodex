#!/usr/bin/env python3
"""
SecureAI Mediator Agent Startup Script
Production-ready Mediator agent with voice integration and React Flow management
"""

import os
import sys
import asyncio
from pathlib import Path
import uvicorn
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables
load_dotenv()

def check_environment():
    """Check required environment variables"""
    required_vars = [
        "OPENAI_API_KEY"
    ]
    
    optional_vars = [
        ("CREWAI_MODEL", "gpt-4o")
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file")
        return False
    
    print("✅ Required environment variables configured")
    
    # Check optional variables
    for var, default in optional_vars:
        if not os.getenv(var):
            print(f"ℹ️  {var} not set, using default: {default}")
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import crewai
        import openai
        import yaml
        import loguru
        import pydantic
        print("✅ Core dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def main():
    """Main startup function"""
    print("🚀 Starting SecureAI Mediator Agent...")
    print("=" * 50)
    
    # Check environment and dependencies
    if not check_environment():
        sys.exit(1)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Import and configure logging
    from agentcrews.mediator.logging_config import structured_logger
    print("✅ Logging configured")
    
    # Start the API server
    print("🌐 Starting API server...")
    print("📡 Real-time progress tracking enabled")
    print("🖼️  Image-to-workflow processing (GPT-4o Vision)")
    print("📝 Text-to-workflow processing (CrewAI + GPT-4o)")
    print("📊 React Flow diagram management active")
    print("🔒 Domain-specific compliance enforcement enabled")
    print("=" * 50)
    
    try:
        # Configure reload settings to avoid watching unnecessary files
        reload_enabled = os.getenv("RELOAD", "true").lower() == "true"
        
        uvicorn.run(
            "agentcrews.mediator.hackathon_backend:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8000)),
            reload=reload_enabled,
            reload_dirs=["agentcrews"] if reload_enabled else None,
            reload_excludes=[
                "env/*",
                ".env",
                "venv/*", 
                ".venv/*",
                "__pycache__/*",
                "*.pyc",
                "*.pyo",
                "*.pyd",
                ".git/*",
                ".pytest_cache/*",
                "node_modules/*",
                "frontend/node_modules/*",
                "*.log",
                ".DS_Store"
            ] if reload_enabled else None,
            log_level=os.getenv("LOG_LEVEL", "info").lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
