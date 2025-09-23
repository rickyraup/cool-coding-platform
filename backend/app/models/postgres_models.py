"""PostgreSQL data models and database operations."""

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
    def create(cls, username: str, email: str, password_hash: str) -> "User":
        """Create a new user."""
        db = get_db()
        query = """
            INSERT INTO code_editor_project.users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """
        user_id = db.execute_insert(query, (username, email, password_hash))
        return cls.get_by_id(user_id)

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


@dataclass
class CodeSession:
    """Code session model matching PostgreSQL schema."""

    id: Optional[int] = None
    user_id: int = 0
    name: Optional[str] = None
    code: str = '# Write your Python code here\nprint("Hello, World!")'
    language: str = "python"
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(cls, user_id: int, name: Optional[str] = None, code: Optional[str] = None) -> "CodeSession":
        """Create a new session."""
        db = get_db()
        query = """
            INSERT INTO code_editor_project.sessions (user_id, name, code, language, is_active)
            VALUES (%s, %s, %s, %s, %s)
        """
        default_code = code or '# Write your Python code here\nprint("Hello, World!")'
        session_id = db.execute_insert(query, (user_id, name, default_code, "python", True))
        return cls.get_by_id(session_id)

    @classmethod
    def get_by_id(cls, session_id: int) -> Optional["CodeSession"]:
        """Get session by ID."""
        db = get_db()
        query = """
            SELECT id, user_id, name, code, language, is_active, created_at, updated_at
            FROM code_editor_project.sessions
            WHERE id = %s
        """
        result = db.execute_one(query, (session_id,))
        if result:
            return cls(
                id=result["id"],
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
            SELECT id, user_id, name, code, language, is_active, created_at, updated_at
            FROM code_editor_project.sessions
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """
        results = db.execute_query(query, (user_id,))
        return [
            cls(
                id=row["id"],
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

    def update(self, name: Optional[str] = None, code: Optional[str] = None, 
               language: Optional[str] = None, is_active: Optional[bool] = None) -> bool:
        """Update session fields."""
        if not self.id:
            return False
        
        # Build dynamic update query
        updates = []
        params = []
        
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


@dataclass
class WorkspaceItem:
    """Workspace item model matching PostgreSQL schema."""

    id: Optional[int] = None
    session_id: int = 0
    parent_id: Optional[int] = None
    name: str = ""
    type: str = ""  # 'file' or 'folder'
    content: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def create(
        cls,
        session_id: int,
        name: str,
        item_type: str,
        parent_id: Optional[int] = None,
        content: Optional[str] = None,
    ) -> "WorkspaceItem":
        """Create a new workspace item."""
        if item_type not in ["file", "folder"]:
            msg = "Type must be 'file' or 'folder'"
            raise ValueError(msg)

        db = get_db()
        query = """
            INSERT INTO code_editor_project.workspace_items (session_id, parent_id, name, type, content)
            VALUES (%s, %s, %s, %s, %s)
        """
        item_id = db.execute_insert(
            query, (session_id, parent_id, name, item_type, content),
        )
        return cls.get_by_id(item_id)

    @classmethod
    def get_by_id(cls, item_id: int) -> Optional["WorkspaceItem"]:
        """Get workspace item by ID."""
        db = get_db()
        query = """
            SELECT id, session_id, parent_id, name, type, content, created_at, updated_at
            FROM code_editor_project.workspace_items
            WHERE id = %s
        """
        result = db.execute_one(query, (item_id,))
        if result:
            return cls(
                id=result["id"],
                session_id=result["session_id"],
                parent_id=result["parent_id"],
                name=result["name"],
                type=result["type"],
                content=result["content"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        return None

    @classmethod
    def get_by_session_and_parent(
        cls, session_id: int, parent_id: Optional[int] = None,
    ) -> list["WorkspaceItem"]:
        """Get all items in a session/folder."""
        db = get_db()
        query = """
            SELECT id, session_id, parent_id, name, type, content, created_at, updated_at
            FROM code_editor_project.workspace_items
            WHERE session_id = %s AND parent_id IS %s
            ORDER BY type DESC, name ASC
        """
        # Handle NULL parent_id comparison
        if parent_id is None:
            query = query.replace("IS %s", "IS NULL")
            params = (session_id,)
        else:
            query = query.replace("IS %s", "= %s")
            params = (session_id, parent_id)

        results = db.execute_query(query, params)
        return [
            cls(
                id=row["id"],
                session_id=row["session_id"],
                parent_id=row["parent_id"],
                name=row["name"],
                type=row["type"],
                content=row["content"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]

    @classmethod
    def get_all_by_session(cls, session_id: int) -> list["WorkspaceItem"]:
        """Get all workspace items for a session."""
        db = get_db()
        query = """
            SELECT id, session_id, parent_id, name, type, content, created_at, updated_at
            FROM code_editor_project.workspace_items
            WHERE session_id = %s
            ORDER BY parent_id NULLS FIRST, type DESC, name ASC
        """
        results = db.execute_query(query, (session_id,))
        return [
            cls(
                id=row["id"],
                session_id=row["session_id"],
                parent_id=row["parent_id"],
                name=row["name"],
                type=row["type"],
                content=row["content"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in results
        ]

    def update_content(self, content: str) -> bool:
        """Update file content."""
        if not self.id or self.type != "file":
            return False
        db = get_db()
        query = """
            UPDATE code_editor_project.workspace_items
            SET content = %s, updated_at = NOW()
            WHERE id = %s
        """
        affected = db.execute_update(query, (content, self.id))
        if affected > 0:
            self.content = content
            return True
        return False

    def rename(self, new_name: str) -> bool:
        """Rename workspace item."""
        if not self.id:
            return False
        db = get_db()
        query = """
            UPDATE code_editor_project.workspace_items
            SET name = %s, updated_at = NOW()
            WHERE id = %s
        """
        affected = db.execute_update(query, (new_name, self.id))
        if affected > 0:
            self.name = new_name
            return True
        return False

    def delete(self) -> bool:
        """Delete workspace item (cascades to children)."""
        if not self.id:
            return False
        db = get_db()
        query = """
            DELETE FROM code_editor_project.workspace_items
            WHERE id = %s
        """
        affected = db.execute_update(query, (self.id,))
        return affected > 0

    def get_full_path(self) -> str:
        """Get the full path of this item from root."""
        if not self.parent_id:
            return self.name

        # Get parent item
        parent = WorkspaceItem.get_by_id(self.parent_id)
        if parent:
            return f"{parent.get_full_path()}/{self.name}"
        return self.name
