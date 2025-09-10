#!/usr/bin/env python3

import sys
import traceback

try:
    print("Starting server test...")
    
    # Test imports
    print("Testing imports...")
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    print("✓ FastAPI imports successful")
    
    # Test database connection
    print("Testing database connection...")
    from services.database import DatabaseService
    db_service = DatabaseService()
    print("✓ Database service created")
    
    # Test app creation
    print("Testing app creation...")
    app = FastAPI(title="Test API")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    print("✓ CORS middleware added")
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "Test successful"}
    
    print("✓ Test endpoint created")
    print("✓ All tests passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("Full traceback:")
    traceback.print_exc()
    sys.exit(1)


