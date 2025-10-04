# Workspace API

The Workspace API provides file management and workspace operations for the code execution environment. Each workspace runs in an isolated Kubernetes pod with persistent storage, allowing users to create, edit, and manage files that are synchronized bidirectionally with the PostgreSQL database.

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

Gracefully shutdown workspace and clean up Kubernetes pod and PVC.

**Response:**
```json
{
  "success": true,
  "message": "Workspace shutdown completed",
  "workspace_id": "uuid-string",
  "session_id": "session-id",
  "active_connections": 0,
  "pod_deleted": true,
  "pvc_deleted": true
}
```

## Workspace Infrastructure

### Kubernetes Pod Lifecycle
Each workspace is backed by a dedicated Kubernetes pod:

1. **Pod Creation**: When user opens workspace → `exec-{session_uuid}` pod created
2. **File Loading**: Files from `workspace_items` table synced to pod at `/app/workspace/`
3. **Interactive Session**: User executes commands via WebSocket → `kubectl exec`
4. **File Sync**: Changes in pod automatically synced back to database
5. **Pod Cleanup**: When workspace closes → Pod and PVC deleted, files remain in DB

### Pod Specifications
- **Name**: `exec-{session_uuid}`
- **Image**: `rraup12/code-execution:latest`
- **Resources**:
  - CPU Request: 200m, Limit: 500m
  - Memory Request: 256Mi, Limit: 512Mi
- **Storage**: 1Gi PersistentVolumeClaim mounted at `/app/workspace/`
- **Namespace**: `coding-platform`

### File Synchronization
- **Direction**: Bidirectional (DB ↔ Pod)
- **Trigger**: Automatic after file-modifying commands (touch, echo, python, pip, etc.)
- **Implementation**: `backend/app/websockets/handlers.py` (sync_pod_changes_to_database function)
- **Scope**: All files in `/app/workspace/` directory

### Workspace Status
Workspace can have the following statuses:
- `initializing` - Pod is being created
- `loading_files` - Files being synced from database to pod
- `ready` - Pod is ready, files loaded, terminal available
- `error` - Pod creation or file sync failed
- `terminated` - Pod has been deleted