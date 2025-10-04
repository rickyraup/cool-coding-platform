"""User model and database operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.postgres import get_db


@dataclass
class User:
    """User model matching PostgreSQL schema."""

    id: Optional[int] = None
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        username: str,
        email: str,
        password_hash: str,
    ) -> "User":
        """Create a new user."""
        db = get_db()

        query = """
            INSERT INTO code_editor_project.users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """
        user_id = db.execute_insert(query, (username, email, password_hash))
        assert user_id is not None, "Failed to create user"
        user = cls.get_by_id(user_id)
        assert user is not None, "Failed to retrieve created user"
        return user

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional["User"]:
        """Get user by ID."""
        db = get_db()
        query = """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM code_editor_project.users
            WHERE id = %s
        """
        result = db.execute_one(query, (user_id,))
        if result:
            return cls(
                id=result["id"],
                username=result["username"],
                email=result["email"],
                password_hash=result["password_hash"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_by_username(cls, username: str) -> Optional["User"]:
        """Get user by username."""
        db = get_db()
        query = """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM code_editor_project.users
            WHERE username = %s
        """
        result = db.execute_one(query, (username,))
        if result:
            return cls(
                id=result["id"],
                username=result["username"],
                email=result["email"],
                password_hash=result["password_hash"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_by_email(cls, email: str) -> Optional["User"]:
        """Get user by email."""
        db = get_db()
        query = """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM code_editor_project.users
            WHERE email = %s
        """
        result = db.execute_one(query, (email,))
        if result:
            return cls(
                id=result["id"],
                username=result["username"],
                email=result["email"],
                password_hash=result["password_hash"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_all_users(cls) -> list["User"]:
        """Get all users."""
        db = get_db()
        query = """
            SELECT id, username, email, password_hash, created_at, updated_at
            FROM code_editor_project.users
            ORDER BY created_at DESC
        """
        results = db.execute_query(query)
        return [
            cls(
                id=row["id"],
                username=row["username"],
                email=row["email"],
                password_hash=row["password_hash"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]
