# Database Schema Overview

## Purpose

This database schema is designed to support a multi-user **Code Execution Platform** where each user can have multiple **sessions**, and each session contains a workspace made up of files and folders. The structure supports organizing user projects, managing workspace content, and enabling session-based isolation of workspaces.

---

## Tables and Relationships

### 1. `users`

- **Role:** Represents the registered users of the platform.
- **Key fields:**
  - `id`: Primary key, uniquely identifies a user.
  - `username`, `email`: Unique identifiers for user login and contact.
  - `password_hash`: Secured hashed password.
  - `is_reviewer`: Boolean flag indicating if the user can review code submissions.
  - `reviewer_level`: Integer (0-2) representing reviewer capability level:
    - 0: Regular user (not a reviewer)
    - 1: Junior reviewer (can review code submissions)
    - 2: Senior reviewer (can review code and mentor junior reviewers)
  - Timestamps: `created_at` and `updated_at` track user record lifecycle.

- **Notes:**
  User data is foundational. All sessions and workspace content relate back to a user through sessions. The reviewer system allows any user to self-promote to reviewer status for code review functionality.

---

### 2. `code_sessions`

- **Role:** Represents individual user sessions with containerized execution environments. Each session acts as an isolated workspace with its own Docker container.
- **Key fields:**
  - `id`: Primary key for the session (auto-increment).
  - `uuid`: Public-facing UUID identifier used for container management and frontend routing.
  - `user_id`: Foreign key linking to `users.id` (defaults to "anonymous" for guest sessions).
  - `name`: Optional label for the session for user organization.
  - `code`: Current code content in the session editor (default Python hello world).
  - `language`: Programming language (defaults to "python").
  - `is_active`: Boolean flag for session cleanup and container management.
  - Timestamps: `created_at` and `updated_at`.

- **Related table - `terminal_commands`:**
  - `id`: Primary key (auto-increment).
  - `session_id`: Foreign key to `code_sessions.id`.
  - `command`: The terminal command that was executed.
  - `output`: The output/response from the command execution.
  - `timestamp`: When the command was executed.
  - `success`: Boolean indicating if the command executed successfully.

- **Relationships:**
  - Each session belongs to one user or is anonymous (`user_id` FK).
  - Sessions isolate user workspace state, enabling multiple independent project workspaces per user.
  - Each session can have many terminal commands stored in history.
  - Each session can have many workspace items (files/folders).
  - Sessions can be submitted for code review via review requests.

- **Constraints:**
  - On user deletion, all their sessions cascade delete.
  - UUID must be unique for container identification.
  - Terminal command history cascades delete when session is removed.

---

### 3. `workspace_items`

- **Role:** Stores files and folders within a session's workspace, providing hierarchical file system structure.
- **Key fields:**
  - `id`: Primary key (auto-increment).
  - `session_id`: Foreign key referencing the session this item belongs to.
  - `parent_id`: Self-referential foreign key pointing to another `workspace_items.id` for nested folder structures.
  - `name`: Name of the file or folder.
  - `type`: Enum-like (`file` or `folder`).
  - `content`: Text content for files. `NULL` for folders.
  - `full_path`: Computed full path from root (e.g., "folder/subfolder/file.py").
  - `session_uuid`: Denormalized UUID from the session for faster container operations.
  - Timestamps: `created_at` and `updated_at`.

- **Relationships:**
  - Each workspace item belongs to one session (`session_id`).
  - Folder hierarchy is implemented via `parent_id` pointing to another item, allowing unlimited nesting.
  - Each item maintains a reference to its session's UUID for container sync operations.

- **Constraints:**
  - Deleting a session cascades and deletes all workspace items in that session.
  - Deleting a folder cascades and deletes all child items recursively.
  - Type is restricted to either `file` or `folder` via a CHECK constraint.
  - Full path is automatically calculated and stored for performance.

- **Indexes:**
  - Index on `(session_id, parent_id)` optimizes querying workspace items by session and parent folder.
  - Index on `session_uuid` for fast container file synchronization operations.

---

### 4. Review System

- **Role:** Complete code review workflow for workspaces.
- **Implementation:**
  - Uses `review_requests` table for review submissions
  - Uses `review_comments` table for line-by-line feedback
  - Uses `review_history` table for audit trail
  - Integrates with existing `users` table for reviewer status

#### Review Requests (`review_requests`)

- **Key fields:**
  - `id`: Primary key (auto-increment)
  - `session_id`: Foreign key referencing the workspace session being reviewed
  - `submitted_by`: Foreign key referencing the user who submitted for review
  - `assigned_to`: Foreign key referencing the assigned reviewer (nullable)
  - `title`: Review request title
  - `description`: Optional detailed description
  - `status`: Enum - 'pending', 'in_review', 'approved', 'rejected'
  - `priority`: Enum - 'low', 'medium', 'high', 'urgent'
  - Timestamps: `submitted_at`, `reviewed_at`, `created_at`, `updated_at`

#### Review Comments (`review_comments`)

- **Key fields:**
  - `id`: Primary key (auto-increment)
  - `review_request_id`: Foreign key referencing the review request
  - `commenter_id`: Foreign key referencing the user who made the comment
  - `workspace_item_id`: Foreign key referencing specific file (nullable for general comments)
  - `line_number`: Specific line number for inline comments (nullable)
  - `comment_text`: The actual comment content
  - `comment_type`: Enum - 'general', 'suggestion', 'issue', 'question', 'approval'
  - `is_resolved`: Boolean flag for comment resolution
  - Timestamps: `created_at`, `updated_at`

#### Review History (`review_history`)

- **Key fields:**
  - `id`: Primary key (auto-increment)
  - `review_request_id`: Foreign key referencing the review request
  - `changed_by`: Foreign key referencing the user who made the change
  - `old_status`: Previous status value
  - `new_status`: New status value
  - `change_description`: Optional description of the change
  - Timestamp: `created_at`

- **Key Features:**
  - **Complete Workflow:** pending → in_review → approved/rejected
  - **Line-by-line Comments:** Detailed feedback on specific code lines
  - **Priority System:** Support for different urgency levels
  - **Audit Trail:** Full history of review status changes
  - **Resolution Tracking:** Mark comments as resolved/unresolved

---

## How This Fits Into The Whole System

1. **User Management:**
   - Users register and login to the platform.
   - Each user's identity and authentication data are stored in the `users` table.
   - Users can self-promote to reviewer status to participate in code reviews.

2. **Sessions:**
   - When a user starts or switches a coding session, a `sessions` record is created or referenced.
   - Sessions isolate the user’s workspace and its files, allowing parallel projects or environments.

3. **Workspace Items:**
   - Files and folders belonging to a session are stored in `workspace_items`.
   - The hierarchy allows complex project structures.
   - Files hold the actual code/scripts/content, while folders organize the workspace.

4. **Data Integrity & Access Control:**
   - Foreign keys ensure workspace items belong to existing sessions, and sessions belong to existing users.
   - Cascading deletes clean up related data automatically.
   - Unique constraints prevent duplication of usernames and emails.

5. **Extensibility:**
   - Additional tables can be added later for features like permissions, version control, or file metadata.
   - The schema supports common queries for file listing, session switching, and user management efficiently.

---

## Summary

This schema models a robust foundation for a multi-user, session-based code execution platform with hierarchical workspace storage. The clear separation of users, sessions, and workspace items allows scalable management of projects and users while ensuring data consistency and integrity.