"""
API Dependencies
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token

    Usage:
        @router.get("/me")
        async def get_me(current_user: User = Depends(get_current_user)):
            return current_user
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_token",
                "message": "Authorization header is missing",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid authentication scheme")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token_format",
                "message": "Invalid authorization header format. Expected 'Bearer <token>'",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid or expired token",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check token type
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token_type",
                "message": "Invalid token type. Access token required.",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid token payload",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "user_not_found",
                "message": "User not found",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "user_inactive",
                "message": "User account is inactive",
            },
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "user_inactive",
                "message": "User account is inactive",
            },
        )
    return current_user


async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require admin role"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "insufficient_permissions",
                "message": "Admin privileges required",
            },
        )
    return current_user
