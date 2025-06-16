#!/usr/bin/env python3
"""
Simple test server to debug startup issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Starting test server...")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")

try:
    print("Importing FastAPI...")
    from fastapi import FastAPI
    print("✓ FastAPI imported successfully")
    
    print("Importing app module...")
    import app
    print("✓ App module imported successfully")
    
    print("Importing uvicorn...")
    import uvicorn
    print("✓ Uvicorn imported successfully")
    
    print("Creating test app...")
    test_app = FastAPI()
    
    @test_app.get("/")
    def read_root():
        return {"message": "Test server running"}
    
    print("Starting server on port 8000...")
    uvicorn.run(test_app, host="127.0.0.1", port=8000)
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc() 