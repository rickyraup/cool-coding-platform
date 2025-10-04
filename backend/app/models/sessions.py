"""Code session model and database operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.core.postgres import get_db


@dataclass
class CodeSession:
    """Code session model matching PostgreSQL schema."""

    id: Optional[int] = None
    uuid: Optional[str] = None  # Public-facing UUID
    user_id: int = 0
    name: Optional[str] = None
    code: str = '# Write your Python code here\nprint("Hello, World!")'
    language: str = "python"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        user_id: int,
        name: Optional[str] = None,
        code: Optional[str] = None,
    ) -> "CodeSession":
        """Create a new session."""
        db = get_db()
        query = """
            INSERT INTO code_editor_project.sessions (user_id, name, code, language, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """
        default_code = code or '# Write your Python code here\nprint("Hello, World!")'
        session_id = db.execute_insert(
            query,
            (user_id, name, default_code, "python", True),
        )
        assert session_id is not None, "Failed to create session"
        session = cls.get_by_id(session_id)
        assert session is not None, "Failed to retrieve created session"
        return session

    @classmethod
    def get_by_id(cls, session_id: int) -> Optional["CodeSession"]:
        """Get session by ID."""
        db = get_db()
        query = """
            SELECT id, uuid, user_id, name, code, language, is_active, created_at, updated_at
            FROM code_editor_project.sessions
            WHERE id = %s
        """
        result = db.execute_one(query, (session_id,))
        if result:
            return cls(
                id=result["id"],
                uuid=result["uuid"],
                user_id=result["user_id"],
                name=result["name"],
                code=result["code"],
                language=result["language"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_by_uuid(cls, session_uuid: str) -> Optional["CodeSession"]:
        """Get session by UUID (public-facing identifier)."""
        db = get_db()
        query = """
            SELECT id, uuid, user_id, name, code, language, is_active, created_at, updated_at
            FROM code_editor_project.sessions
            WHERE uuid = %s
        """
        result = db.execute_one(query, (session_uuid,))
        if result:
            return cls(
                id=result["id"],
                uuid=result["uuid"],
                user_id=result["user_id"],
                name=result["name"],
                code=result["code"],
                language=result["language"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_by_user_id(cls, user_id: int) -> list["CodeSession"]:
        """Get all sessions for a user."""
        db = get_db()
        query = """
            SELECT id, uuid, user_id, name, code, language, is_active, created_at, updated_at
            FROM code_editor_project.sessions
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """
        results = db.execute_query(query, (user_id,))
        return [
            cls(
                id=row["id"],
                uuid=row["uuid"],
                user_id=row["user_id"],
                name=row["name"],
                code=row["code"],
                language=row["language"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]

    def update_name(self, name: str) -> bool:
        """Update session name."""
        if not self.id:
            return False
        db = get_db()
        query = """
            UPDATE code_editor_project.sessions
            SET name = %s, updated_at = NOW()
            WHERE id = %s
        """
        affected = db.execute_update(query, (name, self.id))
        if affected > 0:
            self.name = name
            return True
        return False

    def update(
        self,
        name: Optional[str] = None,
        code: Optional[str] = None,
        language: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """Update session fields."""
        if not self.id:
            return False

        # Build dynamic update query
        updates: list[str] = []
        params: list[Any] = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)
        if code is not None:
            updates.append("code = %s")
            params.append(code)
        if language is not None:
            updates.append("language = %s")
            params.append(language)
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if not updates:
            return True  # Nothing to update

        updates.append("updated_at = NOW()")
        params.append(self.id)

        db = get_db()
        query = f"""
            UPDATE code_editor_project.sessions
            SET {', '.join(updates)}
            WHERE id = %s
        """
        affected = db.execute_update(query, tuple(params))

        if affected > 0:
            # Update local fields
            if name is not None:
                self.name = name
            if code is not None:
                self.code = code
            if language is not None:
                self.language = language
            if is_active is not None:
                self.is_active = is_active
            return True
        return False

    def delete(self) -> bool:
        """Delete session and all associated workspace items."""
        if not self.id:
            return False
        db = get_db()
        query = """
            DELETE FROM code_editor_project.sessions
            WHERE id = %s
        """
        affected = db.execute_update(query, (self.id,))
        return affected > 0
