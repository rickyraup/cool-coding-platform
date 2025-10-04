"""Session-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.schemas.base import BaseResponse


class SessionCreate(BaseModel):
    """Schema for session creation."""

    user_id: int
    name: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for session data in responses."""

    id: str  # Use UUID as public identifier (was internal int ID)
    user_id: int
    name: Optional[str]
    code: str
    language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseResponse):
    """Schema for list of sessions response."""

    data: list[SessionResponse]
    count: int


class SessionDetailResponse(BaseResponse):
    """Schema for single session detail response."""

    data: SessionResponse
