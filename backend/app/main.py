"""
UnifyData.AI - FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base

# Import all models to register them with Base.metadata
from app.models.user import User
from app.models.organization import Organization
from app.models.data_source import DataSource
from app.models.document import Document, DocumentChunk
from app.models.conversation import Conversation, Message, UsageLog

# Import routers directly instead of using routes.py
from fastapi import APIRouter
from app.api.endpoints.auth import router as auth_router
from app.api.endpoints.onboarding import router as onboarding_router
from app.api.datasources import router as datasources_router

# Create API router
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding_router, prefix="/onboarding", tags=["Onboarding"])
api_router.include_router(datasources_router, prefix="/datasources", tags=["Data Sources"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("Starting UnifyData.AI API...")

    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created/verified")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug mode: {settings.DEBUG}")

    yield

    # Shutdown
    print("Shutting down UnifyData.AI API...")


# Create FastAPI application
app = FastAPI(
    title="UnifyData.AI API",
    description="Enterprise AI-powered unified search platform",
    version="0.1.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API routes
app.include_router(api_router, prefix="/api")

# Debug: Print all registered routes
print(f"Total app routes: {len(app.routes)}")
for route in app.routes:
    if hasattr(route, 'path'):
        print(f"  - {route.path}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "UnifyData.AI API",
        "version": "0.1.0",
        "status": "operational",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    if settings.DEBUG:
        raise exc

    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )
