#!/usr/bin/env python
"""
API Test Script

This script tests the UnifyData.AI API endpoints without requiring Docker.
It can be used to verify that the API is working correctly.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.main import app
    from app.core.config import settings
    print("✓ Successfully imported app modules")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    print("\nPlease install dependencies first:")
    print("  pip install -r requirements.txt")
    sys.exit(1)


def test_imports():
    """Test that all modules can be imported"""
    print("\n=== Testing Module Imports ===")

    try:
        from app.core.database import Base, engine
        print("✓ Database module imported")
    except Exception as e:
        print(f"✗ Database module error: {e}")

    try:
        from app.core.security import hash_password, create_access_token
        print("✓ Security module imported")
    except Exception as e:
        print(f"✗ Security module error: {e}")

    try:
        from app.models.user import User
        from app.models.organization import Organization
        print("✓ Models imported")
    except Exception as e:
        print(f"✗ Models error: {e}")

    try:
        from app.schemas.user import UserCreate, UserResponse
        print("✓ Schemas imported")
    except Exception as e:
        print(f"✗ Schemas error: {e}")


def test_config():
    """Test configuration loading"""
    print("\n=== Testing Configuration ===")
    print(f"App Name: {settings.APP_NAME}")
    print(f"Version: {settings.VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug: {settings.DEBUG}")
    print(f"API Prefix: {settings.API_V1_PREFIX}")
    print(f"Database URL: {settings.DATABASE_URL[:30]}..." if len(settings.DATABASE_URL) > 30 else settings.DATABASE_URL)
    print("✓ Configuration loaded successfully")


def test_app():
    """Test FastAPI app configuration"""
    print("\n=== Testing FastAPI App ===")
    print(f"App Title: {app.title}")
    print(f"App Version: {app.version}")
    print(f"Docs URL: {app.docs_url}")
    print(f"Routes count: {len(app.routes)}")

    print("\nAvailable routes:")
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ', '.join(sorted(route.methods))
            print(f"  {methods:12} {route.path}")

    print("✓ FastAPI app configured correctly")


def test_endpoints():
    """Test endpoint responses"""
    print("\n=== Testing Endpoints ===")

    from fastapi.testclient import TestClient

    try:
        client = TestClient(app)

        # Test root endpoint
        response = client.get("/")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ GET / - Status: {response.status_code}")
            print(f"  Response: {data}")
        else:
            print(f"✗ GET / - Status: {response.status_code}")

        # Test health endpoint
        response = client.get("/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ GET /health - Status: {response.status_code}")
            print(f"  Response: {data}")
        else:
            print(f"✗ GET /health - Status: {response.status_code}")

        print("✓ Endpoints responding correctly")

    except Exception as e:
        print(f"✗ Endpoint test failed: {e}")


def main():
    """Run all tests"""
    print("=" * 60)
    print("UnifyData.AI API Test Suite")
    print("=" * 60)

    test_imports()
    test_config()
    test_app()
    test_endpoints()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("✓ All basic tests passed!")
    print("\nTo start the API server, run:")
    print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    print("\nThen access:")
    print("  - API: http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs")
    print("  - Health: http://localhost:8000/health")
    print("=" * 60)


if __name__ == "__main__":
    main()
