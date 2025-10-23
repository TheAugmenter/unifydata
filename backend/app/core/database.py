"""
Database Configuration and Session Management
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Base class for models
class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
