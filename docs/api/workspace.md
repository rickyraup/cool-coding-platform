# Workspace API

The Workspace API provides file management and workspace operations for the code execution environment.

## File Operations

### List Files
**GET** `/api/workspace/{workspace_id}/files`

List all files in the workspace.

**Response:**
```json
[
  {
    "name": "main.py",
    "path": "main.py",
    "type": "file",
    "size": 1024,
    "modified": "2024-01-01T00:00:00Z"
  }
]
```

### Get File Content
**GET** `/api/workspace/{workspace_id}/files/{file_path}`

Get content of a specific file.

**Response:**
```json
{
  "path": "main.py",
  "content": "print('Hello World')",
  "size": 20,
  "modified": "2024-01-01T00:00:00Z"
}
```

### Update File Content
**PUT** `/api/workspace/{workspace_id}/files/{file_path}`

Update or create file content.

**Request Body:**
```json
{
  "content": "print('Updated content')"
}
```

**Response:**
```json
{
  "success": true,
  "message": "File updated successfully",
  "path": "main.py",
  "size": 25
}
```

### Delete File
**DELETE** `/api/workspace/{workspace_id}/files/{file_path}`

Delete a file from the workspace.

**Response:**
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

## Workspace Operations

### Get Workspace Status
**GET** `/api/workspace/{workspace_id}/status`

Get current status of the workspace.

**Response:**
```json
{
  "status": "ready",
  "initialized": true,
  "message": "Workspace is ready",
  "file_count": 3
}
```

### Ensure Default Files
**POST** `/api/workspace/{workspace_id}/ensure-defaults`

Ensure workspace has required default files.

**Response:**
```json
{
  "success": true,
  "message": "Default files ensured",
  "files_created": ["main.py", "requirements.txt"]
}
```

### Shutdown Workspace
**POST** `/workspace/{workspace_id}/shutdown`

Gracefully shutdown workspace and clean up container.

**Response:**
```json
{
  "success": true,
  "message": "Workspace shutdown completed",
  "workspace_id": "uuid-string",
  "session_id": "session-id",
  "active_connections": 0,
  "container_cleaned": true
}
```