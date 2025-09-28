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

### 2. `sessions`

- **Role:** Represents individual user sessions. Each session acts as an isolated workspace environment.
- **Key fields:**
  - `id`: Primary key for the session.
  - `user_id`: Foreign key linking to `users.id`. This establishes ownership and enables multi-session management per user.
  - `name`: Optional label for the session.
  - Timestamps: `created_at` and `updated_at`.

- **Relationships:**  
  Each session belongs to one user (`user_id` FK). Sessions isolate user workspace state, enabling multiple independent project workspaces per user.

- **Constraints:**  
  On user deletion, all their sessions cascade delete.

---

### 3. `workspace_items`

- **Role:** Stores files and folders within a session’s workspace.
- **Key fields:**
  - `id`: Primary key.
  - `session_id`: Foreign key referencing the session this item belongs to.
  - `parent_id`: Self-referential foreign key pointing to another `workspace_items.id` for nested folder structures.
  - `name`: Name of the file or folder.
  - `type`: Enum-like (`file` or `folder`).
  - `content`: Text content for files. `NULL` for folders.
  - Timestamps: `created_at` and `updated_at`.

- **Relationships:**
  - Each workspace item belongs to one session (`session_id`).
  - Folder hierarchy is implemented via `parent_id` pointing to another item, allowing nesting of folders/files.

- **Constraints:**
  - Deleting a session cascades and deletes all workspace items in that session.
  - Deleting a folder cascades and deletes all child items.
  - Type is restricted to either `file` or `folder` via a CHECK constraint.

- **Indexes:**  
  Index on `(session_id, parent_id)` optimizes querying workspace items by session and parent folder.

---

### 4. Review System (User-Based)

- **Role:** Enables code review functionality through user reviewer status.
- **Implementation:**
  - Uses existing `users` table with `is_reviewer` and `reviewer_level` fields.
  - No separate review tables - review functionality is role-based.
  - Any user can self-promote to reviewer status through the frontend.

- **Key Features:**
  - **Self-Service Promotion:** Users can become reviewers without admin approval.
  - **Reviewer Levels:** Support for junior and senior reviewer distinctions.
  - **Flexible Assignment:** Users can choose any reviewer for their code submissions.

- **API Endpoints:**
  - `GET /api/users/reviewers` - Get all available reviewers
  - `GET /api/users/me` - Get current user info including reviewer status
  - `PUT /api/users/me/reviewer-status` - Toggle reviewer status and level

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