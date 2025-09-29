"""File synchronization service to keep container, filesystem, and database in sync."""

import asyncio
import os
from typing import Any, Optional

from app.services.container_manager import container_manager
from app.services.file_manager import FileManager


class FileSyncService:
    """Service to synchronize files between Docker container, local filesystem, and database."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.file_manager = FileManager(session_id)

    async def sync_from_container(self) -> dict[str, Any]:
        """Sync all files from Docker container to local filesystem and database."""
        try:
            if not container_manager.is_docker_available():
                return {"success": False, "error": "Docker not available"}

            # Get list of files in container
            container_files = await self._get_container_files()
            local_files = await self._get_local_files()

            sync_results: dict[str, list[str]] = {
                "synced_files": [],
                "new_files": [],
                "updated_files": [],
                "deleted_files": [],
                "errors": [],
            }

            # Sync files from container to local
            for file_path in container_files:
                try:
                    container_content = await self._get_container_file_content(
                        file_path
                    )
                    if container_content is not None:
                        local_exists = file_path in local_files

                        if local_exists:
                            # Check if file was modified
                            local_content = await self.file_manager.read_file(file_path)
                            if local_content != container_content:
                                # Update existing file
                                await self.file_manager.write_file(
                                    file_path, container_content
                                )
                                sync_results["updated_files"].append(file_path)
                        else:
                            # Create new file
                            await self.file_manager.write_file(
                                file_path, container_content
                            )
                            sync_results["new_files"].append(file_path)

                        sync_results["synced_files"].append(file_path)

                except Exception as e:
                    sync_results["errors"].append(
                        f"Error syncing {file_path}: {str(e)}"
                    )

            # Handle deleted files (exist locally but not in container)
            for file_path in local_files:
                if file_path not in container_files:
                    try:
                        await self.file_manager.delete_file(file_path)
                        sync_results["deleted_files"].append(file_path)
                    except Exception as e:
                        sync_results["errors"].append(
                            f"Error deleting {file_path}: {str(e)}"
                        )

            return {"success": True, "results": sync_results}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _get_container_files(self) -> set[str]:
        """Get list of all files in the container."""
        try:
            # Use find command to get all files recursively
            output, return_code = await container_manager.execute_command(
                self.session_id,
                "find /app -type f -name '*.py' -o -name '*.js' -o -name '*.txt' -o -name '*.json' -o -name '*.md' -o -name '*.csv' -o -name '*.dat' -o -name '*.html' -o -name '*.css' -o -name '*.ts' | sed 's|^/app/||' | grep -v '^$'",
            )

            if return_code == 0 and output.strip():
                return {
                    line.strip() for line in output.strip().split("\n") if line.strip()
                }
            return set()

        except Exception:
            return set()

    async def _get_local_files(self) -> set[str]:
        """Get list of all files in local filesystem."""
        try:
            files_data = await self.file_manager.list_files_structured("")
            files = set()

            def extract_files(items: list[dict[str, Any]], prefix: str = "") -> None:
                for item in items:
                    if item.get("type") == "file":
                        file_path = (
                            os.path.join(prefix, item["name"])
                            if prefix
                            else item["name"]
                        )
                        files.add(file_path)
                    elif item.get("type") == "directory" and "children" in item:
                        dir_path = (
                            os.path.join(prefix, item["name"])
                            if prefix
                            else item["name"]
                        )
                        extract_files(item["children"], dir_path)

            extract_files(files_data)
            return files

        except Exception:
            return set()

    async def _get_container_file_content(self, file_path: str) -> Optional[str]:
        """Get content of a file from the container."""
        try:
            output, return_code = await container_manager.execute_command(
                self.session_id, f"cat /app/{file_path}"
            )

            if return_code == 0:
                return output
            return None

        except Exception:
            return None

    async def sync_after_command(self, command: str) -> dict[str, Any]:
        """Sync files after a terminal command that might modify files."""
        # Commands that are likely to modify files
        file_modifying_commands = [
            "echo",
            "cat",
            "touch",
            "cp",
            "mv",
            "sed",
            "awk",
            "grep",
            "nano",
            "vi",
            "vim",
            "python",
            "node",
            "npm",
            "pip",
        ]

        # Check if command might modify files
        command_parts = command.strip().split()
        if not command_parts:
            return {"success": False, "error": "Empty command"}

        base_command = command_parts[0]
        has_redirect = ">" in command or ">>" in command

        # Sync if command might modify files or has redirection
        if base_command in file_modifying_commands or has_redirect:
            # Small delay to ensure file operations are complete
            await asyncio.sleep(0.1)
            return await self.sync_from_container()

        return {"success": True, "skipped": "Command unlikely to modify files"}


# Global instance
file_sync_service_cache: dict[str, FileSyncService] = {}


def get_file_sync_service(session_id: str) -> FileSyncService:
    """Get or create file sync service for a session."""
    if session_id not in file_sync_service_cache:
        file_sync_service_cache[session_id] = FileSyncService(session_id)
    return file_sync_service_cache[session_id]
