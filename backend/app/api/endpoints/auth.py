"""
Authentication Endpoints
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.models.organization import Organization
from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.schemas.organization import OrganizationResponse
from app.schemas.auth import TokenResponse, TokenRefresh
from app.core.config import settings


router = APIRouter()


def generate_org_slug(name: str) -> str:
    """Generate URL-friendly organization slug"""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


@router.post(
    "/register",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user and organization",
    description="Creates a new user account and organization. Automatically creates admin user with trial plan.",
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register new user and create organization

    Flow:
    1. Check if email already exists
    2. Create organization with trial plan
    3. Create admin user
    4. Generate JWT tokens
    5. Return user, organization, and tokens
    """

    # Check if user already exists
    result = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "email_already_exists",
                "message": "An account with this email already exists. Please log in or use a different email.",
            }
        )

    # Parse full name
    name_parts = user_data.full_name.strip().split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else None

    # Generate organization slug
    base_slug = generate_org_slug(user_data.company_name)
    slug = base_slug
    counter = 1

    # Ensure unique slug
    while True:
        result = await db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        if not result.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    # Create organization
    trial_end_date = datetime.utcnow() + timedelta(days=14)
    organization = Organization(
        name=user_data.company_name,
        slug=slug,
        plan="trial",
        trial_ends_at=trial_end_date,
        subscription_status="trialing",
        max_users=5,
        max_data_sources=3,
        monthly_search_limit=1000,
        current_users=1,  # First user
    )

    db.add(organization)
    await db.flush()  # Flush to get organization ID

    # Create user
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        first_name=first_name,
        last_name=last_name,
        role="admin",  # First user is always admin
        org_id=organization.id,
        is_email_verified=False,
        onboarding_completed=False,
        onboarding_step=0,
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(organization)

    # Generate tokens
    token_data = {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id),
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({
        "user_id": str(user.id),
        "email": user.email,
    })

    # Return response
    return {
        "user": UserResponse.model_validate(user),
        "organization": OrganizationResponse.model_validate(organization),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    }


@router.post(
    "/login",
    response_model=dict,
    summary="User login",
    description="Authenticate user with email and password",
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return tokens

    Flow:
    1. Find user by email
    2. Verify password
    3. Check account status (locked, inactive)
    4. Update last login time
    5. Generate tokens
    """

    # Find user
    result = await db.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_credentials",
                "message": "Invalid email or password.",
            }
        )

    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "account_locked",
                "message": f"Account is temporarily locked due to too many failed login attempts. Try again in {remaining_minutes} minutes.",
            }
        )

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "account_locked",
                    "message": "Account has been locked due to too many failed login attempts. Try again in 30 minutes.",
                }
            )

        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_credentials",
                "message": "Invalid email or password.",
            }
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "account_inactive",
                "message": "Your account has been deactivated. Please contact support.",
            }
        )

    # Reset failed login attempts and update last login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    # Load organization
    result = await db.execute(
        select(Organization).where(Organization.id == user.org_id)
    )
    organization = result.scalar_one()

    # Generate tokens
    token_data = {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id),
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({
        "user_id": str(user.id),
        "email": user.email,
    })

    return {
        "user": UserResponse.model_validate(user),
        "organization": OrganizationResponse.model_validate(organization),
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    }


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token",
)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token

    Flow:
    1. Decode and validate refresh token
    2. Find user
    3. Generate new access token
    4. Return new tokens
    """

    # Decode refresh token
    payload = decode_token(token_data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid or expired refresh token.",
            }
        )

    user_id = payload.get("user_id")

    # Find user
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "message": "Invalid or expired refresh token.",
            }
        )

    # Generate new tokens
    token_payload = {
        "user_id": str(user.id),
        "email": user.email,
        "role": user.role,
        "org_id": str(user.org_id),
    }

    access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token({
        "user_id": str(user.id),
        "email": user.email,
    })

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# Dependency for protected routes
async def get_current_user(
    token: str = Depends(lambda: None),  # Will be replaced with proper OAuth2 header
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user from JWT token

    This is a dependency that can be used in protected routes to get the current user.
    """
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi import Request

    # For now, we'll extract token from Authorization header manually
    # In production, use OAuth2PasswordBearer

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # This is a simplified version - in production use proper OAuth2
    # For now, datasources endpoints will work without auth for testing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication not implemented for datasources yet - use for testing only"
    )
