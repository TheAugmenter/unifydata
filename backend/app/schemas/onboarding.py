"""
Onboarding Schemas
"""
from pydantic import BaseModel, Field


class OnboardingProgressUpdate(BaseModel):
    """Schema for updating onboarding progress"""
    onboarding_step: int = Field(..., ge=0, le=3, description="Current onboarding step (0-3)")
    onboarding_completed: bool = Field(default=False)


class OnboardingProgressResponse(BaseModel):
    """Schema for onboarding progress response"""
    onboarding_step: int
    onboarding_completed: bool
    message: str
