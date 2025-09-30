# Database Schema Overview

## Purpose

This database schema is designed to support a multi-user **Code Execution Platform** where each user can have multiple **sessions**, and each session contains a workspace made up of files and folders. The structure supports organizing user projects, managing workspace content, and enabling session-based isolation of workspaces.

---

## Database Schema Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USERS TABLE                             │
├─────────────────────────────────────────────────────────────────┤
│ PK  id (int)                                                    │
│     username (varchar) UNIQUE                                   │
│     email (varchar) UNIQUE                                      │
│     password_hash (varchar)                                     │
│     is_reviewer (boolean)                                       │
│     reviewer_level (int) 0-4                                    │
│     created_at, updated_at (timestamp)                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ 1:N (user owns many sessions)
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│                       SESSIONS TABLE                            │
├─────────────────────────────────────────────────────────────────┤
│ PK  id (int)                                                    │
│     uuid (uuid) UNIQUE  ◄─────────────┐                        │
│ FK  user_id → users.id                 │                        │
│     name (varchar)                     │                        │
│     code (text) [LEGACY]               │                        │
│     language (varchar)                 │                        │
│     is_active (boolean)                │                        │
│     created_at, updated_at             │                        │
└──────────────────┬─────────────────────┼─────────────────────────┘
                   │                     │
                   │ 1:N                 │ denormalized for speed
                   │                     │
┌──────────────────▼─────────────────────┼─────────────────────────┐
│                  WORKSPACE_ITEMS TABLE │                         │
├────────────────────────────────────────┼─────────────────────────┤
│ PK  id (int)                           │                         │
│ FK  session_id → sessions.id           │                         │
│ FK  parent_id → workspace_items.id (SELF-REF for hierarchy)     │
│     session_uuid (uuid) ◄──────────────┘                         │
│     name (varchar)                                               │
│     type (enum: file|folder)                                     │
│     content (text, NULL for folders)                             │
│     full_path (varchar, computed)                                │
│     created_at, updated_at (timestamp)                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────┐            │
│  │  Hierarchy Example:                             │            │
│  │    root (parent_id=NULL)                        │            │
│  │    ├─ src (parent_id=root.id)                   │            │
│  │    │  ├─ main.py (parent_id=src.id)             │            │
│  │    │  └─ utils.py (parent_id=src.id)            │            │
│  │    └─ README.md (parent_id=root.id)             │            │
│  └─────────────────────────────────────────────────┘            │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   │ Referenced by review comments
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│                   REVIEW_REQUESTS TABLE                         │
├─────────────────────────────────────────────────────────────────┤
│ PK  id (int)                                                    │
│ FK  session_id → sessions.uuid (string FK, not int!)           │
│ FK  submitted_by → users.id                                     │
│ FK  assigned_to → users.id (nullable)                           │
│     title (varchar)                                             │
│     description (text)                                          │
│     status (enum: pending|in_review|approved|rejected)          │
│     priority (enum: low|medium|high|urgent)                     │
│     submitted_at, reviewed_at (timestamp)                       │
│     created_at, updated_at (timestamp)                          │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ 1:N (one review → many comments)
                   │
┌──────────────────▼──────────────────────────────────────────────┐
│                   REVIEW_COMMENTS TABLE                         │
├─────────────────────────────────────────────────────────────────┤
│ PK  id (int)                                                    │
│ FK  review_request_id → review_requests.id                      │
│ FK  commenter_id → users.id                                     │
│ FK  workspace_item_id → workspace_items.id (nullable)           │
│     line_number (int, nullable)                                 │
│     comment_text (text)                                         │
│     comment_type (enum: general|suggestion|issue|question|...)  │
│     is_resolved (boolean)                                       │
│     created_at, updated_at (timestamp)                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   REVIEW_HISTORY TABLE                          │
├─────────────────────────────────────────────────────────────────┤
│ PK  id (int)                                                    │
│ FK  review_request_id → review_requests.id                      │
│ FK  changed_by → users.id                                       │
│     old_status (varchar)                                        │
│     new_status (varchar)                                        │
│     change_description (text)                                   │
│     created_at (timestamp)                                      │
└─────────────────────────────────────────────────────────────────┘
```

## Kubernetes Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                          │
│  ┌──────────────┐  ┌──────────────────┐  ┌─────────────────┐   │
│  │    users     │  │    sessions      │  │ workspace_items │   │
│  │              │  │  uuid: abc-123   │  │ content: code   │   │
│  └──────────────┘  └──────────────────┘  └─────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ File Sync Service
                           │ (bidirectional)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│              Kubernetes Cluster (DOKS)                          │
│                                                                 │
│  Pod: exec-abc-123                                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Container: rraup12/code-execution:latest              │    │
│  │  ┌──────────────────────────────────────────────────┐  │    │
│  │  │  /app/workspace/                                  │  │    │
│  │  │    ├─ main.py  (synced from workspace_items)      │  │    │
│  │  │    ├─ utils.py (synced from workspace_items)      │  │    │
│  │  │    └─ data.txt (synced from workspace_items)      │  │    │
│  │  └──────────────────────────────────────────────────┘  │    │
│  │                                                          │    │
│  │  Mounted PVC: workspace-abc-123 (1Gi)                   │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Backend Pods (2-10 replicas)                                  │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐              │
│  │ backend-1  │  │ backend-2  │  │ backend-N  │              │
│  └────────────┘  └────────────┘  └────────────┘              │
│         │                │                │                    │
│         └────────────────┴────────────────┘                    │
│                          │                                     │
│                 LoadBalancer Service                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ WebSocket / HTTP
                          │
                  ┌───────▼────────┐
                  │  Frontend      │
                  │  (Next.js)     │
                  └────────────────┘
```

---

## Tables and Relationships

### 1. `users`

- **Role:** Represents the registered users of the platform.
- **Key fields:**
  - `id`: Primary key, uniquely identifies a user.
  - `username`, `email`: Unique identifiers for user login and contact.
  - `password_hash`: Secured hashed password.
  - `is_reviewer`: Boolean flag indicating if the user can review code submissions.
  - `reviewer_level`: Integer (0-4) representing reviewer capability level:
    - 0: Regular user (not a reviewer)
    - 1: Level 1 reviewer (basic review capabilities)
    - 2: Level 2 reviewer (intermediate review capabilities)
    - 3: Level 3 reviewer (advanced review capabilities)
    - 4: Level 4 reviewer (expert reviewer with full access)
  - Timestamps: `created_at` and `updated_at` track user record lifecycle.

- **Notes:**
  User data is foundational. All sessions and workspace content relate back to a user through sessions. The reviewer system allows any user to self-promote to reviewer status for code review functionality.

---

### 2. `sessions` (formerly `code_sessions`)

- **Role:** Represents individual user workspaces with isolated Kubernetes pod execution environments. Each session acts as a workspace with its own files, folders, and dedicated Kubernetes pod for code execution.
- **Key fields:**
  - `id`: Primary key for the session (auto-increment).
  - `uuid`: Public-facing UUID identifier used for Kubernetes pod naming, WebSocket routing, and file synchronization (format: `exec-{uuid}`).
  - `user_id`: Foreign key linking to `users.id`.
  - `name`: Optional descriptive label for the session for user organization.
  - `code`: Legacy field - current code content in the session editor (default Python hello world). Note: Primary code storage is now via `workspace_items`.
  - `language`: Programming language (defaults to "python").
  - `is_active`: Boolean flag for session lifecycle management.
  - Timestamps: `created_at` and `updated_at`.

- **Relationships:**
  - Each session belongs to one user (`user_id` FK).
  - Sessions isolate user workspace state, enabling multiple independent project workspaces per user.
  - Each session can have many workspace items (files/folders) via `workspace_items` table.
  - Sessions can be submitted for code review via `review_requests` table.
  - Each session gets a dedicated Kubernetes pod (created on-demand) in the `default` namespace.

- **Constraints:**
  - On user deletion, all their sessions cascade delete.
  - UUID must be unique for pod identification.
  - Session UUID is used as a foreign key in `workspace_items` for faster pod sync operations.

- **Infrastructure Integration:**
  - **Kubernetes Pod:** Each active session has a corresponding pod named `exec-{session.uuid}` in the default namespace.
  - **PersistentVolumeClaim (PVC):** Each pod has a 1Gi PVC named `workspace-{session.uuid}` mounted at `/app/workspace/`.
  - **File Sync:** Files from `workspace_items` table are synced to pod filesystem on session start.
  - **Bidirectional Sync:** File modifications in pod (via terminal commands) are automatically synced back to database.

---

### 3. `workspace_items`

- **Role:** Stores files and folders within a session's workspace, providing hierarchical file system structure. This is the primary storage for all user code and files, synchronized bidirectionally with Kubernetes pod filesystems.
- **Key fields:**
  - `id`: Primary key (auto-increment).
  - `session_id`: Foreign key referencing the session this item belongs to (integer FK to `sessions.id`).
  - `parent_id`: Self-referential foreign key pointing to another `workspace_items.id` for nested folder structures.
  - `name`: Name of the file or folder (e.g., "main.py", "src").
  - `type`: Enum-like (`file` or `folder`).
  - `content`: Text content for files. `NULL` for folders. This is the source of truth for file contents.
  - `full_path`: Computed full path from root (e.g., "folder/subfolder/file.py"). Used for pod filesystem operations.
  - `session_uuid`: Denormalized UUID from the session for faster pod sync operations without JOINs.
  - Timestamps: `created_at` and `updated_at`.

- **Relationships:**
  - Each workspace item belongs to one session (`session_id` → `sessions.id`).
  - Folder hierarchy is implemented via `parent_id` pointing to another item, allowing unlimited nesting.
  - Each item maintains a reference to its session's UUID for fast pod sync operations.
  - When files are modified in a Kubernetes pod (via terminal commands), changes are synced back to this table.

- **Constraints:**
  - Deleting a session cascades and deletes all workspace items in that session.
  - Deleting a folder cascades and deletes all child items recursively.
  - Type is restricted to either `file` or `folder` via a CHECK constraint.
  - Full path is automatically calculated and stored for performance.
  - Names within the same parent folder must be unique (enforced by application logic).

- **Indexes:**
  - Index on `(session_id, parent_id)` optimizes querying workspace items by session and parent folder.
  - Index on `session_uuid` for fast pod file synchronization operations.
  - Index on `full_path` for efficient file lookup during sync operations.

- **File Synchronization:**
  - **DB → Pod (Load):** When a session starts, all workspace items are written to pod at `/app/workspace/{full_path}`.
  - **Pod → DB (Sync):** After terminal commands that modify files (touch, echo, python, etc.), pod filesystem is scanned and changes are written back to workspace_items.
  - **Sync Service:** `backend/app/services/file_sync.py` handles bidirectional synchronization.
  - **Command Detection:** `backend/app/websockets/handlers.py` detects file-modifying commands and triggers sync.

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

### 1. User Management
- Users register and login to the platform.
- Each user's identity and authentication data are stored in the `users` table.
- Users can self-promote to reviewer status to participate in code reviews.
- Reviewer levels (0-4) determine access to review features.

### 2. Session & Workspace Flow
1. **Session Creation:** User creates a new workspace → `sessions` record created with unique UUID.
2. **Pod Creation:** When user opens workspace → Backend creates Kubernetes pod named `exec-{session.uuid}`.
3. **File Loading:** Files from `workspace_items` table are synced to pod filesystem at `/app/workspace/`.
4. **Interactive Terminal:** User sends commands via WebSocket → Commands executed in pod via `kubectl exec`.
5. **File Modification:** User runs commands that modify files (python, touch, echo, etc.).
6. **Sync Back:** Backend detects file-modifying commands → Scans pod filesystem → Updates `workspace_items` table.
7. **Session End:** User closes workspace → Pod and PVC are deleted → Files remain in database.

### 3. Code Review Integration
- Users submit workspaces for review via `review_requests` table.
- Reviewers access read-only versions of sessions to provide feedback.
- Comments can reference specific files via `workspace_item_id` foreign key.
- Review history tracked in `review_history` for audit trail.

### 4. Data Integrity & Access Control
- **Foreign Keys:** Workspace items → sessions → users (cascading relationships).
- **Cascading Deletes:** Deleting session removes all workspace items and review requests.
- **Unique Constraints:** Session UUIDs must be unique for pod identification.
- **Indexes:** Optimized for common queries (file listing, session lookup, review filtering).

### 5. Infrastructure Integration (Kubernetes)
- **Database ↔ Kubernetes Pods:** Bidirectional file synchronization.
- **PersistentVolumeClaims:** Each session gets 1Gi storage volume.
- **Resource Isolation:** Each session runs in separate pod (CPU: 500m, Memory: 512Mi limits).
- **Scalability:** Backend pods (2-10 replicas) and cluster nodes (3-7) scale based on load.
- **Service Discovery:** Session UUID used consistently across DB, pods, and WebSocket connections.

### 6. Performance Optimizations
- **Denormalized Fields:** `session_uuid` in workspace_items for fast lookups without JOINs.
- **Full Path Storage:** Pre-computed paths for efficient file operations.
- **Indexes:** Strategic indexes on frequently queried columns (session_id, parent_id, session_uuid).
- **Connection Pooling:** Database connection pool for high-concurrency operations.

### 7. Extensibility
- Schema supports future features:
  - Version control (git integration via additional tables)
  - File sharing and collaboration (permissions table)
  - Workspace templates (template storage)
  - Analytics and usage tracking (metrics tables)

---

## Summary

This schema provides a robust foundation for a **Kubernetes-based, multi-user code execution platform** with:
- **Hierarchical workspace storage** for files and folders
- **Bidirectional file synchronization** between PostgreSQL and Kubernetes pods
- **Comprehensive code review system** with line-level comments and status tracking
- **Multi-level reviewer permissions** (0-4 levels)
- **Scalable infrastructure** supporting 10-40+ concurrent users with autoscaling
- **Strong data integrity** with cascading relationships and constraints

The separation of users → sessions → workspace_items, combined with Kubernetes orchestration, enables scalable management of isolated development environments while maintaining data consistency and high availability.