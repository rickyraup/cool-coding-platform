"""User management API endpoints."""

import hashlib

from fastapi import APIRouter, HTTPException, status

from app.models.postgres_models import User
from app.schemas.postgres_schemas import (
    AuthResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)


router = APIRouter()


def hash_password(password: str) -> str:
    """Hash password using SHA256 (simple implementation)."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed


@router.post(
    "/register", status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: UserCreate) -> AuthResponse:
    """Register a new user."""
    try:
        # Check if username already exists
        existing_user = User.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )

        # Check if email already exists
        existing_email = User.get_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists",
            )

        # Hash password and create user
        hashed_password = hash_password(user_data.password)
        new_user = User.create(
            username=user_data.username,
            email=user_data.email,
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e!s}",
        )


@router.post("/login")
async def login_user(login_data: UserLogin) -> AuthResponse:
    """Login user and return user info."""
    try:
        # Find user by username
        user = User.get_by_username(login_data.username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
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
