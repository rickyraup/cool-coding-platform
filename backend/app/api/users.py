"""User management API endpoints."""

import bcrypt
from typing import Annotated, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ValidationError

from app.models.postgres_models import User
from app.schemas.postgres_schemas import (
    AuthResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)


router = APIRouter()


def hash_password(password: str) -> str:
    """Hash password using bcrypt with salt."""
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


@router.post(
    "/register", status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: UserCreate) -> AuthResponse:
    """Register a new user with comprehensive validation."""
    try:
        # Check if username already exists (case-insensitive)
        existing_user = User.get_by_username(user_data.username.lower())
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Check if email already exists
        existing_email = User.get_by_email(str(user_data.email))
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        new_user = User.create(
            username=user_data.username.lower(),  # Store username in lowercase
            email=str(user_data.email),
            password_hash=hashed_password,
        )

        # Convert to response format
        user_response = UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            created_at=new_user.created_at,
            updated_at=new_user.updated_at,
        )

        return AuthResponse(
            success=True,
            message="User registered successfully",
            user=user_response,
            data={"user_id": new_user.id},
        )

    except ValidationError as e:
        # Handle Pydantic validation errors
        error_messages = []
        for error in e.errors():
            field = error["loc"][-1] if error["loc"] else "field"
            message = error["msg"]
            error_messages.append(f"{field}: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="; ".join(error_messages),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e!s}",
        )


@router.post("/login")
async def login_user(login_data: UserLogin) -> AuthResponse:
    """Login user and return user info. Supports both username and email login."""
    try:
        # Try to find user by username first, then by email
        user = None
        identifier = login_data.username

        # Check if the identifier looks like an email
        if "@" in identifier:
            user = User.get_by_email(identifier)
        else:
            user = User.get_by_username(identifier)

        # If not found by email, try username (in case user typed username with @)
        if not user and "@" in identifier:
            user = User.get_by_username(identifier)

        # If not found by username, try email (in case user typed email without @)
        if not user and "@" not in identifier:
            user = User.get_by_email(identifier)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
            )

        # Convert to response format
        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return AuthResponse(
            success=True,
            message="Login successful",
            user=user_response,
            data={"user_id": user.id},
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {e!s}",
        )


@router.get("/{user_id}")
async def get_user(user_id: int) -> AuthResponse:
    """Get user by ID."""
    try:
        user = User.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found",
            )

        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return AuthResponse(
            success=True, message="User retrieved successfully", user=user_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {e!s}",
        )


@router.get("/username/{username}")
async def get_user_by_username(username: str) -> AuthResponse:
    """Get user by username."""
    try:
        user = User.get_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found",
            )

        user_response = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

        return AuthResponse(
            success=True, message="User retrieved successfully", user=user_response,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user: {e!s}",
        )

# Reviewer management endpoints
class ReviewerStatusUpdate(BaseModel):
    """Update reviewer status payload."""
    is_reviewer: bool = Field(..., description="Whether user should be a reviewer")
    reviewer_level: int = Field(1, ge=0, le=2, description="Reviewer level (0=regular, 1=junior, 2=senior)")


class UserListResponse(BaseModel):
    """User list response model."""
    success: bool
    data: list[UserResponse]
    total: int


# TODO: Add proper authentication and authorization checks
def get_current_user_id() -> int:
    """Get current user ID from session/token."""
    # Hardcoded for development - replace with actual auth
    return 5


@router.get("/reviewers")
async def get_reviewers() -> dict[str, Any]:
    """Get all reviewers - public endpoint for choosing reviewers."""
    try:
        reviewers = User.get_reviewers()

        reviewer_data = []
        for reviewer in reviewers:
            reviewer_data.append({
                "id": reviewer.id,
                "username": reviewer.username,
                "email": reviewer.email,
                "is_reviewer": reviewer.is_reviewer,
                "reviewer_level": reviewer.reviewer_level,
                "created_at": reviewer.created_at.isoformat() if reviewer.created_at else None,
                "updated_at": reviewer.updated_at.isoformat() if reviewer.updated_at else None,
            })

        return {
            "success": True,
            "data": reviewer_data,
            "total": len(reviewer_data)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch reviewers: {e!s}")


@router.get("/me")
async def get_current_user(
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> dict[str, Any]:
    """Get current user info."""
    try:
        user = User.get_by_id(current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_reviewer": user.is_reviewer,
            "reviewer_level": user.reviewer_level,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {e!s}")


@router.put("/me/reviewer-status")
async def toggle_my_reviewer_status(
    status_update: ReviewerStatusUpdate,
    current_user_id: Annotated[int, Depends(get_current_user_id)],
) -> dict[str, Any]:
    """Toggle current user's reviewer status - anyone can become a reviewer."""
    try:
        user = User.get_by_id(current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        success = user.update_reviewer_status(
            status_update.is_reviewer,
            status_update.reviewer_level
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to update reviewer status")

        action = "You are now a" if status_update.is_reviewer else "You are no longer a"
        level_text = ["regular user", "junior reviewer", "senior reviewer"][status_update.reviewer_level]

        return {
            "success": True,
            "message": f"{action} {level_text}",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_reviewer": user.is_reviewer,
                "reviewer_level": user.reviewer_level,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update reviewer status: {e!s}")
