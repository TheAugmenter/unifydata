"""
API Router Configuration
"""
from fastapi import APIRouter

from app.api.endpoints import auth, onboarding
from app.api import datasources

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(datasources.router, prefix="/datasources", tags=["Data Sources"])
