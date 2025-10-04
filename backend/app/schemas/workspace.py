"""Workspace-related Pydantic schemas."""

from pydantic import BaseModel


class FileContentRequest(BaseModel):
    """Request model for saving file content."""

    content: str


class FileResponse(BaseModel):
    """Response model for file data."""

    name: str
    type: str  # 'file' or 'directory'
    path: str


class FileContentResponse(BaseModel):
    """Response model for file content."""

    name: str
    path: str
    content: str
