# Users API

The Users API handles user authentication, profile management, and reviewer status management.

## Endpoints

### User Registration
**POST** `/api/users/register`

Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "data": {
    "user_id": 123
  }
}
```

### User Login
**POST** `/api/users/login`

Authenticate user and create session.

**Request Body:**
```json
{
  "username": "johndoe",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 123,
    "username": "johndoe",
    "email": "john@example.com",
    "is_reviewer": false,
    "reviewer_level": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "data": {
    "user_id": 123
  }
}
```

### Get Current User
**GET** `/api/users/me`

Get current authenticated user's profile.

**Response:**
```json
{
  "id": 123,
  "username": "johndoe",
  "email": "john@example.com",
  "is_reviewer": true,
  "reviewer_level": 2,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Toggle Reviewer Status
**PUT** `/api/users/me/reviewer-status`

Update current user's reviewer status (self-service promotion).

**Request Body:**
```json
{
  "is_reviewer": true,
  "reviewer_level": 2
}
```

**Response:**
```json
{
  "success": true,
  "message": "Reviewer status updated successfully",
  "user": {
    "id": 123,
    "username": "johndoe",
    "email": "john@example.com",
    "is_reviewer": true,
    "reviewer_level": 2,
    "updated_at": "2024-01-01T01:00:00Z"
  }
}
```

### Get Reviewers
**GET** `/api/users/reviewers`

Get list of all users with reviewer status.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "username": "johndoe",
      "email": "john@example.com",
      "is_reviewer": true,
      "reviewer_level": 2,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

## Authentication

Authentication is session-based. After successful login, the user session is maintained server-side.

## Reviewer Levels

- **Level 1**: Basic reviewer - can review simple code changes
- **Level 2**: Intermediate reviewer - can review moderate complexity changes
- **Level 3**: Senior reviewer - can review complex architectural changes
- **Level 4**: Lead reviewer - can review critical system changes

## Error Responses

### 400 Bad Request
```json
{
  "success": false,
  "message": "Invalid request data",
  "error": "Username already exists"
}
```

### 401 Unauthorized
```json
{
  "success": false,
  "message": "Authentication required",
  "error": "Please login to access this resource"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "message": "Insufficient permissions",
  "error": "User not authorized for this action"
}
```