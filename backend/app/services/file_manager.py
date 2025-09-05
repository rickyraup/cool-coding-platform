import os
import aiofiles
from typing import List, Optional
import shutil
from pathlib import Path

class FileManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.session_dir = os.path.join("/tmp", "code_platform", session_id)
        self.max_file_size = 1024 * 1024  # 1MB max file size
        
        # Create session directory if it doesn't exist
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Allowed file extensions for security
        self.allowed_extensions = {'.py', '.txt', '.md', '.json', '.csv', '.dat'}
    
    def _validate_path(self, file_path: str) -> str:
        """Validate and sanitize file path to prevent directory traversal"""
        
        # Remove any directory traversal attempts
        file_path = os.path.basename(file_path)
        
        # Check file extension
        _, ext = os.path.splitext(file_path)
        if ext not in self.allowed_extensions:
            raise ValueError(f"File extension '{ext}' is not allowed")
        
        # Return full path within session directory
        return os.path.join(self.session_dir, file_path)
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write content to a file"""
        
        try:
            full_path = self._validate_path(file_path)
            
            # Check content size
            if len(content.encode('utf-8')) > self.max_file_size:
                raise ValueError(f"File size exceeds maximum allowed size of {self.max_file_size} bytes")
            
            async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            return True
            
        except Exception as e:
            raise Exception(f"Failed to write file: {str(e)}")
    
    async def read_file(self, file_path: str) -> str:
        """Read content from a file"""
        
        try:
            full_path = self._validate_path(file_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"File '{file_path}' not found")
            
            # Check file size before reading
            file_size = os.path.getsize(full_path)
            if file_size > self.max_file_size:
                raise ValueError(f"File size exceeds maximum allowed size")
            
            async with aiofiles.open(full_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            return content
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")
    
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
            raise Exception(f"Failed to list files: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file"""
        
        try:
            full_path = self._validate_path(file_path)
            
            if not os.path.exists(full_path):
                raise FileNotFoundError(f"File '{file_path}' not found")
            
            os.remove(full_path)
            return True
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
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
                "extension": os.path.splitext(file_path)[1]
            }
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Failed to get file info: {str(e)}")
    
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