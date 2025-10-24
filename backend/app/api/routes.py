"""
API Router Configuration
"""
from fastapi import APIRouter

# Import routers
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.onboarding import router as onboarding_router
from app.api.datasources import router as datasources_router
from app.api.search import router as search_router
from app.api.chat import router as chat_router
from app.api.analytics import router as analytics_router

# Create main API router
api_router = APIRouter()

# Include all sub-routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding_router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(datasources_router, prefix="/datasources", tags=["Data Sources"])
api_router.include_router(search_router, prefix="/search", tags=["Search"])
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])

print(f"API Router initialized with {len(api_router.routes)} routes")
