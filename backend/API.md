# Code Execution Platform API Documentation

Version: 1.0.0

Base URL: `http://localhost:8000` (development)

## Table of Contents

- [Authentication](#authentication)
- [Health Check Endpoints](#health-check-endpoints)
- [User Management](#user-management)
- [Session Management](#session-management)
- [Workspace File Operations](#workspace-file-operations)
- [Workspace Management](#workspace-management)
- [WebSocket API](#websocket-api)
- [Error Responses](#error-responses)
- [Data Models](#data-models)

---

## Authentication

Currently, the API uses user_id-based authentication. Future versions will implement JWT tokens.

**Authorization Header**: Not implemented yet
**Query Parameter**: `user_id` for session access control

---

## Health Check Endpoints

### GET /api/health/

Basic health check endpoint.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T12:00:00Z",
  "uptime": 1728000000,
  "environment": "production",
  "version": "1.0.0",
  "message": "FastAPI server is running"
}
```

### GET /api/health/detailed

Detailed health check with system metrics.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-04T12:00:00Z",
  "uptime": 1728000000,
  "environment": "production",
  "version": "1.0.0",
  "system": {
    "memory": {
      "used": 2048.50,
      "total": 8192.00,
      "percent": 25.0,
      "unit": "MB"
    },
    "cpu": {
      "usage_percent": 15.5,
      "count": 8
    },
    "platform": "posix"
  },
  "message": "Detailed FastAPI server health information"
}
```

---

## User Management

### POST /api/users/register

Register a new user.

**Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Validation Rules**:
- Username: 3-50 characters, alphanumeric + underscores, case-insensitive
- Email: Valid email format
- Password: Minimum 8 characters

**Response** (201 Created):
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2025-10-04T12:00:00Z",
    "updated_at": "2025-10-04T12:00:00Z"
  },
  "data": {
    "user_id": 1
  }
}
```

**Errors**:
- `400 Bad Request`: Username/email already exists, validation errors
- `500 Internal Server Error`: Server error

### POST /api/users/login

Login user with username/email and password.

**Request Body**:
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

Note: `username` field accepts both username and email.

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2025-10-04T12:00:00Z",
    "updated_at": "2025-10-04T12:00:00Z"
  },
  "data": {
    "user_id": 1
  }
}
```

**Errors**:
- `401 Unauthorized`: Invalid credentials
- `500 Internal Server Error`: Server error

---

## Session Management

### GET /api/sessions/

Get sessions, optionally filtered by user.

**Query Parameters**:
- `user_id` (optional): Filter sessions by user ID
- `skip` (optional, default: 0): Pagination offset
- `limit` (optional, default: 100): Maximum results

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Retrieved 2 sessions",
  "data": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "user_id": 1,
      "name": "My Python Project",
      "code": "print('Hello, World!')",
      "language": "python",
      "is_active": true,
      "created_at": "2025-10-04T12:00:00Z",
      "updated_at": "2025-10-04T12:30:00Z"
    }
  ],
  "count": 2
}
```

### POST /api/sessions/

Create a new session.

**Request Body**:
```json
{
  "user_id": 1,
  "name": "My Python Project"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "message": "Session created successfully",
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_id": 1,
    "name": "My Python Project",
    "code": "",
    "language": "python",
    "is_active": true,
    "created_at": "2025-10-04T12:00:00Z",
    "updated_at": "2025-10-04T12:00:00Z"
  }
}
```

Note: A default `script.py` file is automatically created in the workspace.

**Errors**:
- `404 Not Found`: User not found
- `500 Internal Server Error`: Server error

### GET /api/sessions/{session_uuid}

Get a specific session by UUID.

**Path Parameters**:
- `session_uuid`: Session UUID

**Query Parameters**:
- `user_id` (required): User ID for authorization

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Session retrieved successfully",
  "data": {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "user_id": 1,
    "name": "My Python Project",
    "code": "print('Hello, World!')",
    "language": "python",
    "is_active": true,
    "created_at": "2025-10-04T12:00:00Z",
    "updated_at": "2025-10-04T12:30:00Z"
  }
}
```

**Errors**:
- `403 Forbidden`: User doesn't have access to this session
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Server error

---

## Workspace File Operations

### GET /api/workspace/{session_uuid}/files

List all files and folders in a workspace.

**Path Parameters**:
- `session_uuid`: Session UUID

**Response** (200 OK):
```json
[
  {
    "name": "script.py",
    "type": "file",
    "path": "script.py"
  },
  {
    "name": "utils",
    "type": "folder",
    "path": "utils"
  },
  {
    "name": "helper.py",
    "type": "file",
    "path": "utils/helper.py"
  }
]
```

Note: Returns empty array `[]` for new workspaces with no files.

### GET /api/workspace/{session_uuid}/file/{filename:path}

Get content of a specific file.

**Path Parameters**:
- `session_uuid`: Session UUID
- `filename`: File path (can include directories, e.g., `utils/helper.py`)

**Response** (200 OK):
```json
{
  "name": "script.py",
  "path": "script.py",
  "content": "print('Hello, World!')\n"
}
```

**Errors**:
- `404 Not Found`: Session or file not found
- `500 Internal Server Error`: Server error

### POST /api/workspace/{session_uuid}/file/{filename:path}

Create or update a file.

**Path Parameters**:
- `session_uuid`: Session UUID
- `filename`: File path (can include directories)

**Request Body**:
```json
{
  "content": "print('Updated content!')\n"
}
```

**Response** (200 OK):
```json
{
  "message": "File script.py updated successfully",
  "file": {
    "name": "script.py",
    "path": "script.py",
    "content": "print('Updated content!')\n"
  }
}
```

**Errors**:
- `404 Not Found`: Session not found
- `500 Internal Server Error`: Server error

### DELETE /api/workspace/{session_uuid}/file/{filename:path}

Delete a file.

**Path Parameters**:
- `session_uuid`: Session UUID
- `filename`: File path

**Response** (200 OK):
```json
{
  "message": "File script.py deleted successfully"
}
```

**Errors**:
- `404 Not Found`: Session or file not found
- `500 Internal Server Error`: Server error

### GET /api/workspace/{session_uuid}/status

Get workspace initialization status.

**Path Parameters**:
- `session_uuid`: Session UUID

**Response** (200 OK):
```json
{
  "status": "ready",
  "message": "Workspace is ready",
  "initialized": true,
  "filesystem_synced": true,
  "file_count": 3,
  "container_ready": true
}
```

**Possible Status Values**:
- `ready`: Workspace is initialized and ready
- `initializing`: Container is being created
- `empty`: Workspace has no files
- `not_found`: Session not found
- `error`: Error occurred

### POST /api/workspace/{session_uuid}/ensure-default

Ensure workspace has default files (creates `main.py` if empty).

**Path Parameters**:
- `session_uuid`: Session UUID

**Response** (200 OK):
```json
{
  "message": "Created default main.py file",
  "files_created": ["main.py"],
  "file": {
    "name": "main.py",
    "path": "main.py",
    "content": "# Welcome to your coding session!\nprint('Hello, World!')\n"
  }
}
```

Or if workspace already has files:
```json
{
  "message": "Workspace already has files, no defaults created",
  "files_created": []
}
```

---

## Workspace Management

### POST /workspace/{workspace_id}/shutdown

Gracefully shutdown a workspace and cleanup its container.

**Path Parameters**:
- `workspace_id`: Workspace UUID

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Workspace a1b2c3d4-e5f6-7890-abcd-ef1234567890 shutdown completed",
  "workspace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "session_id": "user_1_ws_a1b2c3d4_1728000000_abc123",
  "active_connections": 0,
  "container_cleaned": true
}
```

Or if no active session:
```json
{
  "success": true,
  "message": "No active session found for workspace a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "workspace_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

## WebSocket API

### WS /ws?user_id={user_id}

Real-time terminal communication endpoint.

**Query Parameters**:
- `user_id` (optional): User ID for session tracking

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?user_id=1');
```

**Initial Connection Response**:
```json
{
  "type": "connection_established",
  "message": "WebSocket connected successfully",
  "timestamp": "2025-10-04T12:00:00Z"
}
```

### Message Types

#### Terminal Input

Send terminal commands to execute.

**Client → Server**:
```json
{
  "type": "terminal_input",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "input": "ls -la\n"
}
```

**Server → Client** (Output):
```json
{
  "type": "terminal_output",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "output": "total 16\ndrwxr-xr-x 3 user user 4096 Oct 4 12:00 .\n...",
  "timestamp": "2025-10-04T12:00:01Z"
}
```

#### File Operations via Terminal

**Touch File**:
```json
{
  "type": "touch",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "test.py"
}
```

**Response**:
```json
{
  "type": "touch_response",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "success": true,
  "filename": "test.py",
  "message": "File 'test.py' created successfully"
}
```

**Remove File**:
```json
{
  "type": "rm",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "test.py"
}
```

**Response**:
```json
{
  "type": "rm_response",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "success": true,
  "filename": "test.py",
  "message": "File 'test.py' removed successfully"
}
```

**Sync Files**:
```json
{
  "type": "sync_files",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Response**:
```json
{
  "type": "sync_response",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "success": true,
  "message": "Files synced to container"
}
```

#### Pod Status Updates

**Pod Ready Notification** (Server → Client):
```json
{
  "type": "pod_ready",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-10-04T12:00:05Z"
}
```

**Progress Updates** (Server → Client):
```json
{
  "type": "terminal_output",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "output": "⏳ Initializing environment... (10s)",
  "timestamp": "2025-10-04T12:00:05Z"
}
```

**Clear Progress** (Server → Client):
```json
{
  "type": "terminal_clear_progress",
  "sessionId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "timestamp": "2025-10-04T12:00:15Z"
}
```

---

## Error Responses

All endpoints follow a consistent error response format:

### 400 Bad Request
```json
{
  "detail": "Username already exists"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid username/email or password"
}
```

### 403 Forbidden
```json
{
  "detail": "Access denied: You don't have permission to access this session"
}
```

### 404 Not Found
```json
{
  "detail": "Session not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to create session: <error message>"
}
```

---

## Data Models

### User
```typescript
{
  id: number;
  username: string;        // 3-50 chars, lowercase
  email: string;
  created_at: string;      // ISO 8601 timestamp
  updated_at: string;      // ISO 8601 timestamp
}
```

### Session
```typescript
{
  id: string;              // UUID
  user_id: number;
  name: string;            // Session name
  code: string;            // Legacy field (empty string)
  language: string;        // Default: "python"
  is_active: boolean;      // Default: true
  created_at: string;      // ISO 8601 timestamp
  updated_at: string;      // ISO 8601 timestamp
}
```

### File/Folder (WorkspaceItem)
```typescript
{
  name: string;            // Filename or folder name
  type: "file" | "folder";
  path: string;            // Full path from workspace root
  content?: string;        // Only for files
}
```

---

## Rate Limits

Currently no rate limiting is implemented. This will be added in future versions.

---

## CORS Configuration

CORS origins are configured via the `CORS_ORIGINS` environment variable:
```
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Default: `http://localhost:3000,http://127.0.0.1:3000`

---

## Development & Testing

### Interactive API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Testing with curl

**Health Check**:
```bash
curl http://localhost:8000/api/health/
```

**Register User**:
```bash
curl -X POST http://localhost:8000/api/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}'
```

**Create Session**:
```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"name":"Test Session"}'
```

**Get Files**:
```bash
curl http://localhost:8000/api/workspace/{session_uuid}/files
```

---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- User registration and login
- Session management with UUID-based identification
- Workspace file operations
- WebSocket terminal communication
- Kubernetes pod-based code execution
- PostgreSQL persistence

### Removed Features
- Code review system (removed in cleanup)
- Guest user support (removed in cleanup)

---

## Future Enhancements

- [ ] JWT-based authentication
- [ ] Rate limiting
- [ ] WebSocket authentication
- [ ] Session sharing between users
- [ ] File upload/download endpoints
- [ ] Code execution metrics and analytics
- [ ] Session templates
