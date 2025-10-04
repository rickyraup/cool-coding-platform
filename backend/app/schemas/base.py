"""Base Pydantic schemas."""

from typing import Any, Optional

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """Base response model for all API responses."""

    success: bool
    message: str


class BaseDataResponse(BaseResponse):
    """Base response model with optional data field."""

    data: Optional[dict[str, Any]] = None
