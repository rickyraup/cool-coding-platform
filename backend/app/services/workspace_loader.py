"""Service for loading workspace files/folders from PostgreSQL into containers."""

import logging
import os
from typing import Optional

from app.models.sessions import CodeSession
from app.models.workspace_items import WorkspaceItem
from app.services.container_manager import container_manager

logger = logging.getLogger(__name__)


class WorkspaceLoaderService:
    """Service for loading workspace data into container sessions."""

    def __init__(self) -> None:
        self.sessions_dir = "/tmp/coding_platform_sessions"

    async def load_workspace_into_container(self, session_id: int) -> bool:
        """Load workspace items from database into container session."""
        try:
            # Get session from database
            session = CodeSession.get_by_id(session_id)
            if not session:
                logger.error(f"Session {session_id} not found in database")
                return False

            # Get all workspace items for this session
            workspace_items = WorkspaceItem.get_all_by_session(session_id)
            if not workspace_items:
                logger.info(f"No workspace items found for session {session_id}")
                return True  # Empty workspace is valid

            # Find container session by workspace ID (new user-aware session system)
            active_session_id = container_manager.find_session_by_workspace_id(
                str(session_id),
            )
            if not active_session_id:
                # Fallback: create new session (should not normally happen)
                container_session = await container_manager.get_or_create_session(
                    str(session_id),
                )
                working_dir = container_session.working_dir
            else:
                container_session = container_manager.active_sessions[active_session_id]
                working_dir = container_session.working_dir

            # Create workspace structure
            await self._create_workspace_structure(workspace_items, working_dir)

            logger.info(f"Successfully loaded workspace for session {session_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to load workspace for session {session_id}: {e}")
            return False

    async def _create_workspace_structure(
        self,
        workspace_items: list[WorkspaceItem],
        base_dir: str,
    ) -> None:
        """Create the file/folder structure in the container working directory."""
        # Sort items to ensure folders are created before files
        items_by_path = {}
        for item in workspace_items:
            full_path = item.get_full_path()
            items_by_path[full_path] = item

        # Sort by path depth to ensure parent folders are created first
        sorted_paths = sorted(items_by_path.keys(), key=lambda x: (x.count("/"), x))

        for path in sorted_paths:
            item = items_by_path[path]
            full_path = os.path.join(base_dir, path.lstrip("/"))

            if item.type == "folder":
                await self._create_folder(full_path)
            elif item.type == "file":
                await self._create_file(full_path, item.content or "")

    async def _create_folder(self, folder_path: str) -> None:
        """Create a folder in the filesystem."""
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            logger.exception(f"Failed to create folder {folder_path}: {e}")
            raise

    async def _create_file(self, file_path: str, content: str) -> None:
        """Create a file with content in the filesystem."""
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            # Write file content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            logger.exception(f"Failed to create file {file_path}: {e}")
            raise

    async def save_workspace_from_container(self, session_id: int) -> bool:
        """Save current container workspace state back to database."""
        try:
            # Get session from database
            session = CodeSession.get_by_id(session_id)
            if not session:
                logger.error(f"Session {session_id} not found in database")
                return False

            # Find container session by workspace ID (new user-aware session system)
            active_session_id = container_manager.find_session_by_workspace_id(
                str(session_id),
            )
            if not active_session_id:
                logger.error(f"No active container session for workspace {session_id}")
                return False

            container_session = container_manager.active_sessions[active_session_id]
            working_dir = container_session.working_dir

            # Clear existing workspace items for this session
            existing_items = WorkspaceItem.get_all_by_session(session_id)
            for item in existing_items:
                item.delete()

            # Scan and save current workspace structure
            await self._scan_and_save_workspace(session_id, working_dir)

            logger.info(f"Successfully saved workspace for session {session_id}")
            return True

        except Exception as e:
            logger.exception(f"Failed to save workspace for session {session_id}: {e}")
            return False

    async def _scan_and_save_workspace(
        self,
        session_id: int,
        base_dir: str,
        parent_id: Optional[int] = None,
        current_path: str = "",
    ) -> Optional[list[WorkspaceItem]]:
        """Recursively scan directory and save items to database."""
        try:
            if not os.path.exists(base_dir):
                return None

            items = []
            for item_name in os.listdir(base_dir):
                # Skip hidden files and system files
                if item_name.startswith("."):
                    continue

                item_path = os.path.join(base_dir, item_name)
                relative_path = (
                    os.path.join(current_path, item_name) if current_path else item_name
                )

                if os.path.isdir(item_path):
                    # Create folder item
                    folder_item = WorkspaceItem.create(
                        session_id=session_id,
                        parent_id=parent_id,
                        name=item_name,
                        item_type="folder",
                        content=None,
                    )
                    items.append(folder_item)

                    # Recursively process subdirectory
                    await self._scan_and_save_workspace(
                        session_id=session_id,
                        base_dir=item_path,
                        parent_id=folder_item.id,
                        current_path=relative_path,
                    )

                elif os.path.isfile(item_path):
                    # Read file content
                    try:
                        with open(item_path, encoding="utf-8") as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        # Handle binary files
                        logger.warning(f"Skipping binary file: {item_path}")
                        continue
                    except Exception as e:
                        logger.warning(f"Could not read file {item_path}: {e}")
                        content = ""

                    # Create file item
                    file_item = WorkspaceItem.create(
                        session_id=session_id,
                        parent_id=parent_id,
                        name=item_name,
                        item_type="file",
                        content=content,
                    )
                    items.append(file_item)

            return items

        except Exception as e:
            logger.exception(f"Failed to scan directory {base_dir}: {e}")
            raise


# Global instance
workspace_loader = WorkspaceLoaderService()
