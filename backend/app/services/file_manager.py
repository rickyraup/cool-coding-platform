import os
import shutil
from typing import List, Dict, Any

import aiofiles


class FileManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_dir = os.path.join("/tmp", "coding_platform_sessions", session_id)
        self.max_file_size = 1024 * 1024  # 1MB max file size

        # Create session directory if it doesn't exist
        os.makedirs(self.session_dir, exist_ok=True)

        # Allowed file extensions for security
        self.allowed_extensions = {".py", ".txt", ".md", ".json", ".csv", ".dat", ".js", ".ts", ".html", ".css"}

    def _validate_path(self, file_path: str, is_directory: bool = False) -> str:
        """Validate and sanitize file path to prevent directory traversal"""
        # Normalize the path and remove any directory traversal attempts
        file_path = os.path.normpath(file_path)
        
        # Remove leading slashes and ensure no parent directory references
        file_path = file_path.lstrip('/')
        if '..' in file_path:
            raise ValueError("Parent directory references are not allowed")

        # For files, check file extension on the filename (not the path)
        if not is_directory:
            filename = os.path.basename(file_path)
            _, ext = os.path.splitext(filename)
            if ext and ext not in self.allowed_extensions:
                raise ValueError(f"File extension '{ext}' is not allowed")

        # Return full path within session directory
        full_path = os.path.join(self.session_dir, file_path)
        
        # Ensure the path is still within the session directory
        if not full_path.startswith(self.session_dir):
            raise ValueError("Path is outside of allowed directory")
            
        return full_path

    async def write_file(self, file_path: str, content: str) -> bool:
        """Write content to a file"""
        try:
            full_path = self._validate_path(file_path)

            # Check content size
            if len(content.encode("utf-8")) > self.max_file_size:
                raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)

            return True

        except Exception as e:
            raise Exception(f"Failed to write file: {e!s}")

    async def read_file(self, file_path: str) -> str:
        """Read content from a file"""
        try:
            full_path = self._validate_path(file_path)

            if not os.path.exists(full_path):
                raise FileNotFoundError(f"File '{file_path}' not found")

            # Check file size before reading
            file_size = os.path.getsize(full_path)
            if file_size > self.max_file_size:
                raise ValueError("File size exceeds maximum allowed size")

            async with aiofiles.open(full_path, encoding="utf-8") as f:
                content = await f.read()

            return content

        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to read file: {e!s}")

    async def list_files_structured(self, directory: str = "") -> List[Dict[str, Any]]:
        """List files in the session directory or subdirectory with structured data"""
        try:
            if directory:
                # Validate subdirectory path using our validation method
                search_dir = self._validate_path(directory, is_directory=True)
                path_prefix = directory + "/" if not directory.endswith("/") else directory
            else:
                search_dir = self.session_dir
                path_prefix = ""

            if not os.path.exists(search_dir):
                return []

            files = []
            for item in os.listdir(search_dir):
                item_path = os.path.join(search_dir, item)
                
                if os.path.isfile(item_path):
                    # Check if file extension is allowed
                    _, ext = os.path.splitext(item)
                    if ext in self.allowed_extensions or ext == "":  # Allow files without extensions
                        files.append({
                            "name": item,
                            "type": "file",
                            "path": path_prefix + item
                        })
                elif os.path.isdir(item_path):
                    files.append({
                        "name": item,
                        "type": "directory", 
                        "path": path_prefix + item
                    })

            # Sort with directories first, then files
            files.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
            return files

        except Exception as e:
            raise Exception(f"Failed to list files: {e!s}")

    async def list_files(self, directory: str = "") -> List[str]:
        """List files in the session directory or subdirectory"""
        try:
            if directory:
                # Validate subdirectory path
                directory = os.path.basename(directory)
                search_dir = os.path.join(self.session_dir, directory)
            else:
                search_dir = self.session_dir

            if not os.path.exists(search_dir):
                return []

            files = []
            for item in os.listdir(search_dir):
                item_path = os.path.join(search_dir, item)

                if os.path.isfile(item_path):
                    # Check if file extension is allowed
                    _, ext = os.path.splitext(item)
                    if ext in self.allowed_extensions:
                        files.append(item)
                elif os.path.isdir(item_path):
                    files.append(f"{item}/")

            return sorted(files)

        except Exception as e:
            raise Exception(f"Failed to list files: {e!s}")

    async def delete_file(self, file_path: str) -> bool:
        """Delete a file or directory"""
        try:
            # Try as directory first, then as file
            try:
                full_path = self._validate_path(file_path, is_directory=True)
            except ValueError:
                full_path = self._validate_path(file_path, is_directory=False)

            if not os.path.exists(full_path):
                raise FileNotFoundError(f"File '{file_path}' not found")

            if os.path.isfile(full_path):
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path)
            
            return True

        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to delete file: {e!s}")

    async def create_directory(self, dir_path: str) -> bool:
        """Create a new directory"""
        try:
            full_path = self._validate_path(dir_path, is_directory=True)
            
            if os.path.exists(full_path):
                raise ValueError(f"Directory '{dir_path}' already exists")
            
            os.makedirs(full_path, exist_ok=True)
            return True
            
        except Exception as e:
            raise Exception(f"Failed to create directory: {e!s}")

    async def create_file(self, file_path: str, content: str = "") -> bool:
        """Create a new file with optional content"""
        try:
            full_path = self._validate_path(file_path, is_directory=False)
            
            if os.path.exists(full_path):
                raise ValueError(f"File '{file_path}' already exists")
            
            # Create directory structure if needed
            dir_path = os.path.dirname(full_path)
            if dir_path and dir_path != self.session_dir:
                os.makedirs(dir_path, exist_ok=True)
            
            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(content)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to create file: {e!s}")

    async def file_exists(self, file_path: str) -> bool:
        """Check if a file exists"""
        try:
            full_path = self._validate_path(file_path)
            return os.path.exists(full_path)
        except:
            return False

    async def get_file_info(self, file_path: str) -> dict:
        """Get file information"""
        try:
            full_path = self._validate_path(file_path)

            if not os.path.exists(full_path):
                raise FileNotFoundError(f"File '{file_path}' not found")

            stat = os.stat(full_path)

            return {
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_file": os.path.isfile(full_path),
                "extension": os.path.splitext(file_path)[1],
            }

        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to get file info: {e!s}")

    def cleanup_session(self):
        """Clean up the entire session directory"""
        try:
            if os.path.exists(self.session_dir):
                shutil.rmtree(self.session_dir)
        except Exception as e:
            print(f"Error cleaning up session {self.session_id}: {e}")

    def get_session_size(self) -> int:
        """Get total size of all files in session"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(self.session_dir):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
        except Exception:
            pass

        return total_size
