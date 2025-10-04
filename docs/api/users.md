# Users API

The Users API handles user authentication and profile management.

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

**Validation Rules:**
- `username`: 3-20 characters, alphanumeric with hyphens/underscores only
- `email`: Valid email format
- `password`: 8-128 characters, must include uppercase, lowercase, digit, and special character

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
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Authentication

Authentication is session-based. After successful login, the user session is maintained server-side.

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