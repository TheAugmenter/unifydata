"""
User Schemas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
import uuid
import re


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=255)

    @validator("password")
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    job_title: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=50)
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: uuid.UUID
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None
    job_title: Optional[str] = None
    role: str
    org_id: uuid.UUID
    is_email_verified: bool
    onboarding_completed: bool
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @validator("new_password")
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v
