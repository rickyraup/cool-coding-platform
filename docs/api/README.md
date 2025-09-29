# API Documentation

This directory contains the complete API documentation for the Code Execution Platform.

## API Overview

The Code Execution Platform provides a RESTful API built with FastAPI, offering comprehensive backend services for a web-based development environment with integrated terminal functionality, user management, and code review systems.

**Base URL**: `http://localhost:8001` (development)

**API Documentation**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## API Structure

### Core Services
- **[Health](./health.md)** - Health check endpoints
- **[Users](./users.md)** - User authentication and management
- **[Sessions](./sessions.md)** - Session management (legacy and PostgreSQL)
- **[Workspace](./workspace.md)** - Workspace operations and file management
- **[Reviews](./reviews.md)** - Code review system
- **[WebSocket](./websocket.md)** - Real-time terminal communication

### Authentication

The API uses session-based authentication with user IDs. Most endpoints require authentication.

```http
# Example authenticated request
GET /api/users/me
Content-Type: application/json
```

### Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Handling

Error responses include appropriate HTTP status codes and detailed error messages:

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error information",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## API Endpoints by Category

### Health & Status
- `GET /` - Root endpoint
- `GET /api/health/` - Health check

### User Management
- `POST /api/users/register` - User registration
- `POST /api/users/login` - User login
- `GET /api/users/me` - Get current user
- `PUT /api/users/me/reviewer-status` - Toggle reviewer status
- `GET /api/users/reviewers` - List reviewers

### Session Management
- `POST /api/sessions/` - Create session (legacy)
- `GET /api/sessions/{session_id}` - Get session (legacy)
- `POST /api/postgres_sessions/` - Create PostgreSQL session
- `GET /api/postgres_sessions/{session_id}` - Get PostgreSQL session

### Workspace Operations
- `GET /api/workspace/{workspace_id}/files` - List workspace files
- `POST /api/workspace/{workspace_id}/files` - Create file
- `GET /api/workspace/{workspace_id}/files/{file_path}` - Get file content
- `PUT /api/workspace/{workspace_id}/files/{file_path}` - Update file content
- `DELETE /api/workspace/{workspace_id}/files/{file_path}` - Delete file
- `GET /api/workspace/{workspace_id}/status` - Get workspace status
- `POST /api/workspace/{workspace_id}/ensure-defaults` - Ensure default files

### Session Workspace
- `GET /api/session_workspace/{session_id}` - Get session with workspace
- `POST /api/session_workspace/{session_id}/files/{filename}` - Update file content

### Code Review System
- `POST /api/reviews/` - Create review request
- `GET /api/reviews/` - List review requests
- `GET /api/reviews/{review_id}` - Get review request
- `PUT /api/reviews/{review_id}` - Update review request
- `PUT /api/reviews/{review_id}/status` - Update review status
- `GET /api/reviews/session/{session_id}/status` - Get review status for session
- `GET /api/reviews/stats/overview` - Get review statistics

### Workspace Management
- `POST /workspace/{workspace_id}/shutdown` - Shutdown workspace

### WebSocket
- `WS /ws` - WebSocket endpoint for real-time terminal communication

## Rate Limiting

Currently, no rate limiting is implemented, but it may be added in future versions.

## Versioning

The API is currently version 1.0.0. Future versions will maintain backward compatibility where possible.

## CORS Configuration

The API allows cross-origin requests from:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://localhost:3002`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`
- `http://127.0.0.1:3002`

## Security

- All sensitive operations require authentication
- Input validation on all endpoints
- CORS protection
- Error messages don't expose sensitive information

## Testing

Use the interactive API documentation at `/docs` to test endpoints directly, or use tools like Postman or curl.

Example with curl:
```bash
# Health check
curl -X GET "http://localhost:8001/api/health/"

# Get current user (requires authentication)
curl -X GET "http://localhost:8001/api/users/me" \
  -H "Content-Type: application/json"
```