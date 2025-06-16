#!/usr/bin/env python3
"""
Simple startup script for the AI Recommendation Engine FastAPI server.
"""

import uvicorn
from app import app

if __name__ == "__main__":
    print("🚀 Starting AI Recommendation Engine Backend...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔄 Auto-reload enabled for development")
    print("-" * 50)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 