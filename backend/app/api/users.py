"""User management API endpoints."""

import bcrypt
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError

from app.models.users import User
from app.schemas import (
    AuthResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

router = APIRouter()


def user_to_response(user: User) -> UserResponse:
    """Convert User model to UserResponse schema."""
    assert user.id is not None
    assert user.created_at is not None
    assert user.updated_at is not None
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


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
    "/register",
    status_code=status.HTTP_201_CREATED,
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
        user_response = user_to_response(new_user)

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
        # Try to find user by username or email
        identifier = login_data.username
        user = User.get_by_username(identifier) or User.get_by_email(identifier)

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
        user_response = user_to_response(user)

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
