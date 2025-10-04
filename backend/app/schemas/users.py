"""User-related Pydantic schemas."""

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import BaseResponse


class UserCreate(BaseModel):
    """Schema for user registration."""

    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            msg = "Username can only contain letters, numbers, hyphens, and underscores"
            raise ValueError(msg)
        return v.lower()  # Store username in lowercase for consistency

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            msg = "Password must be at least 8 characters long"
            raise ValueError(msg)
        if not re.search(r"[a-z]", v):
            msg = "Password must contain at least one lowercase letter"
            raise ValueError(msg)
        if not re.search(r"[A-Z]", v):
            msg = "Password must contain at least one uppercase letter"
            raise ValueError(msg)
        if not re.search(r"\d", v):
            msg = "Password must contain at least one number"
            raise ValueError(msg)
        if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>?]', v):
            msg = "Password must contain at least one special character"
            raise ValueError(msg)
        return v


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class AuthResponse(BaseResponse):
    """Schema for authentication responses."""

    data: dict[str, Any] = Field(default_factory=dict)
    user: Optional[UserResponse] = None
