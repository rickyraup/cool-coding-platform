"""Workspace item model and database operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.postgres import get_db


@dataclass
class WorkspaceItem:
    """Workspace item model matching PostgreSQL schema."""

    id: Optional[int] = None
    session_id: Optional[int] = None
    parent_id: Optional[int] = None
    name: str = ""
    type: str = ""  # 'file' or 'folder'
    content: Optional[str] = None
    full_path: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    session_uuid: Optional[str] = None

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

        # Get the session to retrieve its UUID
        from app.models.sessions import CodeSession

        session = CodeSession.get_by_id(session_id)
        if not session:
            msg = f"Session {session_id} not found"
            raise ValueError(msg)

        # Calculate full_path
        full_path = name
        if parent_id:
            parent = cls.get_by_id(parent_id)
            if parent and parent.full_path:
                full_path = f"{parent.full_path}/{name}"

        db = get_db()
        query = """
            INSERT INTO code_editor_project.workspace_items (session_id, parent_id, name, type, content, full_path, session_uuid)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        item_id = db.execute_insert(
            query,
            (session_id, parent_id, name, item_type, content, full_path, session.uuid),
        )
        assert item_id is not None, "Failed to create workspace item"
        item = cls.get_by_id(item_id)
        assert item is not None, "Failed to retrieve created workspace item"
        return item

    @classmethod
    def get_by_id(cls, item_id: int) -> Optional["WorkspaceItem"]:
        """Get workspace item by ID."""
        db = get_db()
        query = """
            SELECT id, session_id, parent_id, name, type, content, full_path, created_at, updated_at, session_uuid
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
                full_path=result["full_path"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
                session_uuid=result["session_uuid"],
            )
        return None

    @classmethod
    def get_by_session_and_parent(
        cls,
        session_id: int,
        parent_id: Optional[int] = None,
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
        params: tuple[int, ...]
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
            SELECT id, session_id, parent_id, name, type, content, full_path, created_at, updated_at, session_uuid
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
                full_path=row["full_path"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                session_uuid=row["session_uuid"],
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
        # Use the stored full_path if available
        if self.full_path:
            return self.full_path

        # Fallback to calculated path for backwards compatibility
        if not self.parent_id:
            return self.name

        # Get parent item
        parent = WorkspaceItem.get_by_id(self.parent_id)
        if parent:
            return f"{parent.get_full_path()}/{self.name}"
        return self.name
