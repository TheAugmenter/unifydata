"""
Onboarding Endpoints
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.schemas.onboarding import OnboardingProgressUpdate, OnboardingProgressResponse
from app.api.dependencies import get_current_user


router = APIRouter()


@router.get(
    "/progress",
    response_model=OnboardingProgressResponse,
    summary="Get onboarding progress",
    description="Get current user's onboarding progress",
)
async def get_onboarding_progress(
    current_user: User = Depends(get_current_user),
):
    """
    Get onboarding progress for current user

    Returns:
        - onboarding_step: Current step (0-3)
        - onboarding_completed: Whether onboarding is complete
    """
    return OnboardingProgressResponse(
        onboarding_step=current_user.onboarding_step,
        onboarding_completed=current_user.onboarding_completed,
        message="Onboarding progress retrieved successfully"
    )


@router.put(
    "/progress",
    response_model=OnboardingProgressResponse,
    summary="Update onboarding progress",
    description="Update current user's onboarding progress",
)
async def update_onboarding_progress(
    progress: OnboardingProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update onboarding progress for current user

    Steps:
    - 0: Welcome tour (intro to platform)
    - 1: Connect first data source
    - 2: First search tutorial
    - 3: Onboarding complete

    Args:
        progress: New onboarding progress
    """
    # Update user's onboarding progress
    current_user.onboarding_step = progress.onboarding_step
    current_user.onboarding_completed = progress.onboarding_completed

    await db.commit()
    await db.refresh(current_user)

    return OnboardingProgressResponse(
        onboarding_step=current_user.onboarding_step,
        onboarding_completed=current_user.onboarding_completed,
        message="Onboarding progress updated successfully"
    )


@router.post(
    "/skip",
    response_model=OnboardingProgressResponse,
    summary="Skip onboarding",
    description="Mark onboarding as completed and skip remaining steps",
)
async def skip_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Skip onboarding for current user

    Sets onboarding_completed to True and step to 3
    """
    current_user.onboarding_step = 3
    current_user.onboarding_completed = True

    await db.commit()
    await db.refresh(current_user)

    return OnboardingProgressResponse(
        onboarding_step=current_user.onboarding_step,
        onboarding_completed=current_user.onboarding_completed,
        message="Onboarding skipped successfully"
    )


@router.post(
    "/complete",
    response_model=OnboardingProgressResponse,
    summary="Complete onboarding",
    description="Mark onboarding as completed",
)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete onboarding for current user

    Sets onboarding_completed to True
    """
    current_user.onboarding_completed = True
    current_user.onboarding_step = 3

    await db.commit()
    await db.refresh(current_user)

    return OnboardingProgressResponse(
        onboarding_step=current_user.onboarding_step,
        onboarding_completed=current_user.onboarding_completed,
        message="Onboarding completed successfully"
    )
