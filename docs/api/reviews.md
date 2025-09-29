# Reviews API

The Reviews API provides comprehensive code review functionality, allowing users to submit workspaces for review and reviewers to manage the review process.

## Endpoints

### Create Review Request
**POST** `/api/reviews/`

Submit a workspace for code review.

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "title": "Review Title",
  "description": "Optional description",
  "priority": "medium"
}
```

**Parameters:**
- `session_id` (string, required): UUID of the workspace session
- `title` (string, required): Title for the review request
- `description` (string, optional): Detailed description of what to review
- `priority` (string, optional): Priority level - "low", "medium", "high", "urgent" (default: "medium")

**Response:**
```json
{
  "success": true,
  "message": "Review request created successfully",
  "data": {
    "id": 1,
    "session_id": "uuid-string",
    "title": "Review Title",
    "description": "Optional description",
    "priority": "medium",
    "status": "pending",
    "submitted_by": 123,
    "assigned_to": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "reviewed_at": null
  }
}
```

### Get Review Requests
**GET** `/api/reviews/`

List review requests with optional filtering.

**Query Parameters:**
- `assigned_to` (integer, optional): Filter by assigned reviewer user ID
- `status` (string, optional): Filter by status - "pending", "in_review", "approved", "rejected", "requires_changes"
- `submitted_by` (integer, optional): Filter by submitter user ID

**Response:**
```json
{
  "success": true,
  "message": "Success",
  "data": [
    {
      "id": 1,
      "session_id": "uuid-string",
      "title": "Review Title",
      "status": "pending",
      "priority": "medium",
      "submitted_by": 123,
      "assigned_to": 456,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

### Get Single Review Request
**GET** `/api/reviews/{review_id}`

Get details of a specific review request.

**Path Parameters:**
- `review_id` (integer, required): ID of the review request

**Response:**
```json
{
  "success": true,
  "message": "Success",
  "data": {
    "id": 1,
    "session_id": "uuid-string",
    "title": "Review Title",
    "description": "Detailed description",
    "priority": "medium",
    "status": "in_review",
    "submitted_by": 123,
    "assigned_to": 456,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "reviewed_at": "2024-01-01T01:00:00Z"
  }
}
```

### Update Review Request
**PUT** `/api/reviews/{review_id}`

Update a review request (title, description, priority).

**Path Parameters:**
- `review_id` (integer, required): ID of the review request

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "priority": "high"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Review request updated successfully",
  "data": {
    "id": 1,
    "title": "Updated Title",
    "description": "Updated description",
    "priority": "high",
    "updated_at": "2024-01-01T02:00:00Z"
  }
}
```

### Update Review Status
**PUT** `/api/reviews/{review_id}/status`

Update the status of a review request (for reviewers).

**Path Parameters:**
- `review_id` (integer, required): ID of the review request

**Request Body:**
```json
{
  "status": "approved"
}
```

**Parameters:**
- `status` (string, required): New status - "pending", "in_review", "approved", "rejected", "requires_changes"

**Response:**
```json
{
  "success": true,
  "message": "Review status updated successfully",
  "data": {
    "id": 1,
    "status": "approved",
    "reviewed_at": "2024-01-01T03:00:00Z",
    "updated_at": "2024-01-01T03:00:00Z"
  }
}
```

### Get Review Status for Session
**GET** `/api/reviews/session/{session_id}/status`

Get review status information for a specific workspace session.

**Path Parameters:**
- `session_id` (string, required): UUID of the workspace session

**Response:**
```json
{
  "reviewRequest": {
    "id": 1,
    "session_id": "uuid-string",
    "title": "Review Title",
    "status": "in_review",
    "priority": "medium",
    "submitted_by": 123,
    "assigned_to": 456,
    "created_at": "2024-01-01T00:00:00Z"
  },
  "isReviewer": true,
  "canSubmitForReview": false
}
```

**Response Fields:**
- `reviewRequest` (object|null): Review request details if exists
- `isReviewer` (boolean): Whether current user is assigned as reviewer
- `canSubmitForReview` (boolean): Whether current user can submit this session for review

### Get Review Statistics
**GET** `/api/reviews/stats/overview`

Get overview statistics for the review system.

**Response:**
```json
{
  "total_pending": 5,
  "total_in_review": 3,
  "total_approved": 15,
  "total_rejected": 2,
  "my_pending_reviews": 2,
  "my_assigned_reviews": 1
}
```

**Response Fields:**
- `total_pending` (integer): Total pending review requests
- `total_in_review` (integer): Total reviews currently in progress
- `total_approved` (integer): Total approved reviews
- `total_rejected` (integer): Total rejected reviews
- `my_pending_reviews` (integer): Current user's pending submissions
- `my_assigned_reviews` (integer): Reviews assigned to current user

## Review Status Flow

The review system follows this status flow:

1. **pending** - Initial state when review is submitted
2. **in_review** - Review is being actively reviewed
3. **approved** - Review has been approved
4. **rejected** - Review has been rejected
5. **requires_changes** - Review needs changes before approval

## Priority Levels

- **low** - Non-urgent review
- **medium** - Standard priority (default)
- **high** - Important review
- **urgent** - Critical review requiring immediate attention

## Authentication

All review endpoints require user authentication. The current user's ID is used for permission checks and ownership validation.

## Error Responses

### 404 Not Found
```json
{
  "success": false,
  "message": "Review request not found",
  "error": "No review request found with ID: 123"
}
```

### 403 Forbidden
```json
{
  "success": false,
  "message": "Insufficient permissions",
  "error": "You are not authorized to perform this action"
}
```

### 400 Bad Request
```json
{
  "success": false,
  "message": "Invalid request data",
  "error": "Status must be one of: pending, in_review, approved, rejected, requires_changes"
}
```

## Usage Examples

### Submit a workspace for review
```bash
curl -X POST "http://localhost:8001/api/reviews/" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Python function optimization",
    "description": "Please review the optimization of the calculate_performance function",
    "priority": "high"
  }'
```

### Approve a review
```bash
curl -X PUT "http://localhost:8001/api/reviews/1/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved"}'
```

### Get reviews assigned to me
```bash
curl -X GET "http://localhost:8001/api/reviews/?assigned_to=456" \
  -H "Content-Type: application/json"
```