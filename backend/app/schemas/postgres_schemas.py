"""Pydantic schemas for PostgreSQL models."""

import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# Base response models
class BaseResponse(BaseModel):
    success: bool
    message: str


class BaseDataResponse(BaseResponse):
    data: Optional[dict] = None


# User schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            msg = "Username can only contain letters, numbers, hyphens, and underscores"
            raise ValueError(msg)
        return v.lower()  # Store username in lowercase for consistency

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
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
    id: int
    username: str
    email: str
    created_at: datetime
    updated_at: datetime


class UserLogin(BaseModel):
    username: str
    password: str


# Session schemas
class SessionCreate(BaseModel):
    user_id: int
    name: Optional[str] = None


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None


class SessionResponse(BaseModel):
    id: str  # Use UUID as public identifier (was internal int ID)
    user_id: int
    name: Optional[str]
    code: str
    language: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseResponse):
    data: list[SessionResponse]
    count: int


class SessionDetailResponse(BaseResponse):
    data: SessionResponse


# Workspace Item schemas
class WorkspaceItemCreate(BaseModel):
    session_id: int
    parent_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(file|folder)$")
    content: Optional[str] = None


class WorkspaceItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None


class WorkspaceItemResponse(BaseModel):
    id: int
    session_id: int
    parent_id: Optional[int]
    name: str
    type: str
    content: Optional[str]
    created_at: datetime
    updated_at: datetime
    full_path: Optional[str] = None


class WorkspaceItemListResponse(BaseResponse):
    data: list[WorkspaceItemResponse]
    count: int


class WorkspaceItemDetailResponse(BaseResponse):
    data: WorkspaceItemResponse


# File operations schemas
class FileOperationRequest(BaseModel):
    action: str = Field(
        ...,
        pattern="^(create_file|create_folder|read|write|rename|delete|list)$",
    )
    path: str
    content: Optional[str] = None
    new_name: Optional[str] = None


# Workspace tree structure for nested display
class WorkspaceTreeItem(BaseModel):
    id: int
    name: str
    type: str
    full_path: str
    children: Optional[list["WorkspaceTreeItem"]] = None


class WorkspaceTreeResponse(BaseResponse):
    data: list[WorkspaceTreeItem]


# Update forward reference
WorkspaceTreeItem.model_rebuild()


# Authentication schemas
class AuthResponse(BaseResponse):
    data: dict = Field(default_factory=dict)
    user: Optional[UserResponse] = None
    token: Optional[str] = None


# Combined session with workspace
class SessionWithWorkspaceResponse(BaseResponse):
    session: SessionResponse
    workspace_items: list[WorkspaceItemResponse]
    workspace_tree: list[WorkspaceTreeItem]
