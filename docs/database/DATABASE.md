# Database Schema Overview

## Purpose

This database schema supports a multi-user **Code Execution Platform** where each user can have multiple **sessions**, and each session contains a workspace made up of files and folders. The structure supports organizing user projects, managing workspace content, and enabling session-based isolation with dedicated Kubernetes pods for code execution.

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
│     created_at, updated_at (timestamp)                          │
│                                                                 │
│ REMOVED (cleanup): is_reviewer, reviewer_level                  │
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
│     code (text) [LEGACY - deprecated]  │                        │
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
└──────────────────────────────────────────────────────────────────┘
```

## Infrastructure Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     KUBERNETES CLUSTER                          │
│                                                                  │
│  Execution Pods (1 per active session)                          │
│  ┌────────────────┐  ┌────────────────┐                        │
│  │ exec-{uuid-1}  │  │ exec-{uuid-2}  │                        │
│  │ + PVC (1Gi)    │  │ + PVC (1Gi)    │                        │
│  └────────────────┘  └────────────────┘                        │
│          ▲                    ▲                                 │
│          │                    │                                 │
│          │ kubectl exec       │                                 │
│          └────────────────────┴─────────────┐                   │
│                                             │                   │
│  Backend Pods (2-10 replicas, auto-scaled)  │                   │
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

- **Role:** Represents registered users of the platform.
- **Key fields:**
  - `id`: Primary key, uniquely identifies a user.
  - `username`, `email`: Unique identifiers for user login and contact.
  - `password_hash`: Secured hashed password using bcrypt.
  - Timestamps: `created_at` and `updated_at` track user record lifecycle.

- **Notes:**
  - User data is foundational. All sessions and workspace content relate back to a user through sessions.
  - Review-related fields (`is_reviewer`, `reviewer_level`) were removed during platform cleanup - review/approval system was deprecated.

---

### 2. `sessions`

- **Role:** Represents individual user workspaces with isolated Kubernetes pod execution environments. Each session acts as a workspace with its own files, folders, and dedicated Kubernetes pod for code execution.

- **Key fields:**
  - `id`: Primary key for the session (auto-increment).
  - `uuid`: Public-facing UUID identifier used for Kubernetes pod naming (`exec-{uuid}`), WebSocket routing, and file synchronization.
  - `user_id`: Foreign key linking to `users.id`.
  - `name`: Optional descriptive label for the session.
  - `code`: **DEPRECATED** - Legacy field for monolithic code storage. Current code storage is via `workspace_items` table.
  - `language`: Programming language (defaults to "python").
  - `is_active`: Boolean flag for session lifecycle management.
  - Timestamps: `created_at` and `updated_at`.

- **Relationships:**
  - Each session belongs to one user (`user_id` FK).
  - Sessions isolate user workspace state, enabling multiple independent project workspaces per user.
  - Each session can have many workspace items (files/folders) via `workspace_items` table.
  - Each session gets a dedicated Kubernetes pod (created on-demand) in the `coding-platform` namespace.

- **Constraints:**
  - On user deletion, all their sessions cascade delete.
  - UUID must be unique for pod identification.
  - Session UUID is used as a foreign key in `workspace_items` for faster pod sync operations.

- **Infrastructure Integration:**
  - **Kubernetes Pod:** Each active session has a corresponding pod named `exec-{session.uuid}` in the coding-platform namespace.
  - **PersistentVolumeClaim (PVC):** Each pod has a 1Gi PVC named `workspace-{session.uuid}` mounted at `/app/`.
  - **File Sync:** Files from `workspace_items` table are synced to pod filesystem on session start.
  - **Bidirectional Sync:** File modifications in pod (via terminal commands) are automatically synced back to database.
  - **Pod Lifecycle:** Pods are created on-demand when sessions are activated and cleaned up when WebSocket connections close.

---

### 3. `workspace_items`

- **Role:** Stores files and folders within a session's workspace, providing hierarchical file system structure. This is the **primary storage** for all user code and files, synchronized bidirectionally with Kubernetes pod filesystems.

- **Key fields:**
  - `id`: Primary key (auto-increment).
  - `session_id`: Foreign key referencing the session this item belongs to (integer FK to `sessions.id`).
  - `parent_id`: Self-referential foreign key pointing to another `workspace_items.id` for nested folder structures.
  - `name`: Name of the file or folder (e.g., "main.py", "src").
  - `type`: Enum (`file` or `folder`).
  - `content`: Text content for files. `NULL` for folders. **This is the source of truth for file contents.**
  - `full_path`: Computed full path from root (e.g., "src/main.py"). Used for pod filesystem operations.
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
  - **DB → Pod (Load):** When a session starts, all workspace items are written to pod at `/app/{name}`.
  - **Pod → DB (Sync):** After terminal commands that modify files (touch, echo, python, etc.), pod filesystem is scanned and changes are written back to workspace_items.
  - **Sync Triggers:** File-modifying commands detected in `backend/app/websockets/handlers.py` trigger automatic sync.
  - **Conflict Resolution:** Database is the source of truth. Pod changes overwrite database on sync.

---

## Database Operations

### User Operations

```python
# Create user
User.create(
    username="alice",
    email="alice@example.com",
    password_hash=hash_password("secure_password")
)

# Get user by username
user = User.get_by_username("alice")

# Get user by email
user = User.get_by_email("alice@example.com")
```

### Session Operations

```python
# Create session
session = CodeSession.create(
    user_id=user.id,
    name="My Python Project",
    language="python"
)

# Get session by UUID
session = CodeSession.get_by_uuid("550e8400-e29b-41d4-a716-446655440000")

# Get all sessions for a user
sessions = CodeSession.get_by_user_id(user.id)

# Update session
session.update(name="Updated Project Name")

# Delete session (cascades to workspace_items)
session.delete()
```

### Workspace Item Operations

```python
# Create file
file = WorkspaceItem.create(
    session_id=session.id,
    name="main.py",
    item_type="file",
    content="print('Hello, World!')",
    parent_id=None
)

# Create folder
folder = WorkspaceItem.create(
    session_id=session.id,
    name="src",
    item_type="folder",
    parent_id=None
)

# Create nested file
nested_file = WorkspaceItem.create(
    session_id=session.id,
    name="utils.py",
    item_type="file",
    content="def helper(): pass",
    parent_id=folder.id
)

# Get all items for a session
items = WorkspaceItem.get_all_by_session(session.id)

# Update file content
file.update_content("print('Updated code')")

# Delete item (cascades to children)
folder.delete()
```

---

## File Synchronization Flow

### Session Start (DB → Pod)

1. User opens a workspace session in frontend
2. WebSocket connection established to backend
3. Backend creates or retrieves Kubernetes pod `exec-{session.uuid}`
4. All `workspace_items` for session are read from database
5. Files are written to pod filesystem at `/app/{full_path}`
6. Pod is ready for terminal commands

### Command Execution (Pod → DB)

1. User types command in terminal (e.g., `echo "test" > file.txt`)
2. Command executed in pod via `kubectl exec`
3. After command completion, `sync_pod_changes_to_database()` is triggered
4. Pod filesystem is scanned with `find /app -type f`
5. File contents read with `cat /app/{filename}`
6. Database `workspace_items` table is updated with new/modified files
7. Deleted files removed from database

### Manual Save (Editor → DB → Pod)

1. User edits file in Monaco editor and saves (Ctrl+S)
2. File content sent to backend via WebSocket
3. Database `workspace_items` updated with new content
4. Content synced to pod filesystem at `/app/{filename}`
5. Pod now has latest code for execution

---

## Performance Considerations

### Denormalization

- `session_uuid` stored in `workspace_items` to avoid JOINs during pod sync
- `full_path` pre-computed and stored for faster filesystem operations
- Pod file sync reads directly from `workspace_items` without joining `sessions`

### Indexes

- `sessions.uuid` - UNIQUE index for fast pod lookup
- `workspace_items(session_id, parent_id)` - Composite index for folder navigation
- `workspace_items(session_uuid)` - Index for fast pod sync queries
- `workspace_items(full_path)` - Index for file path lookups

### Caching

- Active Kubernetes pod sessions cached in-memory (`container_manager.active_sessions`)
- File manager maintains workspace directory cache at `/tmp/coding_platform_sessions/workspace_{uuid}`

---

## Security

### Authentication & Authorization

- Passwords hashed with bcrypt (10 rounds)
- Users can only access their own sessions
- Session UUIDs are random and unpredictable
- Kubernetes pods isolated per session (no cross-session access)

### Data Isolation

- Each session has dedicated Kubernetes pod (process isolation)
- Each pod has dedicated PersistentVolumeClaim (storage isolation)
- RBAC limits backend service account to pod/PVC management only
- No direct database access from execution pods

### Input Validation

- SQL injection prevented by parameterized queries
- File paths validated to prevent directory traversal
- Kubernetes pod names validated (alphanumeric + hyphens only)
- Content size limits enforced (files, folder depth, etc.)

---

## Deployment

### Database Setup

```sql
-- Create database
CREATE DATABASE coolcoding;

-- Create tables (see table SQL files in docs/database/tables/)
\i docs/database/tables/users.sql
\i docs/database/tables/sessions.sql
\i docs/database/tables/workspace_items.sql
```

### Connection

```env
DATABASE_URL=postgresql://user:password@host:port/coolcoding
```

### Migrations

Database schema changes are currently managed manually. Future enhancement: use Alembic for migrations.

---

---

## Future Schema Improvements

### 1. `users` Table Enhancements

**Current Limitations:**
- No user roles/permissions system (all users have equal access)
- No email verification tracking
- No account status flags (active, suspended, deleted)
- No user preferences storage (theme, editor settings, etc.)
- No rate limiting metadata

**Proposed Improvements:**
```sql
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN account_status VARCHAR(20) DEFAULT 'active';  -- active, suspended, deleted
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
ALTER TABLE users ADD COLUMN preferences JSONB;  -- Editor settings, theme, etc.
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user';  -- user, admin, premium
```

**Benefits:**
- Enable tiered access (free, premium, admin)
- Track user engagement and activity
- Store user preferences for better UX
- Support account lifecycle management

---

### 2. `sessions` Table Enhancements

**Current Limitations:**
- `code` field is deprecated but still exists (bloat)
- No session sharing/collaboration support
- No session templates or forking
- No execution limits tracking (CPU time, memory usage)
- No session visibility control (public/private)
- Missing last_accessed_at for better idle cleanup

**Proposed Improvements:**
```sql
ALTER TABLE sessions DROP COLUMN code;  -- Remove deprecated field
ALTER TABLE sessions ADD COLUMN last_accessed_at TIMESTAMP;
ALTER TABLE sessions ADD COLUMN visibility VARCHAR(10) DEFAULT 'private';  -- private, public, shared
ALTER TABLE sessions ADD COLUMN forked_from_session_id INT REFERENCES sessions(id);
ALTER TABLE sessions ADD COLUMN execution_stats JSONB;  -- CPU time, memory, command count
ALTER TABLE sessions ADD COLUMN description TEXT;
ALTER TABLE sessions ADD COLUMN tags TEXT[];  -- For categorization
```

**Benefits:**
- Clean up deprecated storage (reduce DB size)
- Enable session sharing and templates
- Track resource usage per session
- Better session discovery and organization
- More accurate idle session detection

**Migration Strategy:**
```sql
-- Migrate any remaining code to workspace_items before dropping
UPDATE workspace_items
SET content = sessions.code
WHERE workspace_items.session_id = sessions.id
  AND workspace_items.name = 'script.py'
  AND sessions.code IS NOT NULL;

-- Then drop the column
ALTER TABLE sessions DROP COLUMN code;
```

---

### 3. `workspace_items` Table Enhancements

**Current Limitations:**
- No file size tracking (potential storage abuse)
- No version history or change tracking
- No file locking for concurrent edits
- Missing file metadata (permissions, last modified by, etc.)
- No search/indexing on file content
- `full_path` computed but not enforced at DB level
- Parent/child integrity not enforced with constraints

**Proposed Improvements:**
```sql
-- Add file size tracking
ALTER TABLE workspace_items ADD COLUMN file_size_bytes INT;

-- Add metadata
ALTER TABLE workspace_items ADD COLUMN last_modified_by INT REFERENCES users(id);
ALTER TABLE workspace_items ADD COLUMN is_readonly BOOLEAN DEFAULT FALSE;
ALTER TABLE workspace_items ADD COLUMN mime_type VARCHAR(100);

-- Full-text search on content
CREATE INDEX idx_workspace_content_search ON workspace_items
USING GIN(to_tsvector('english', content));

-- Enforce unique names per parent
CREATE UNIQUE INDEX idx_workspace_unique_name_per_parent
ON workspace_items(session_id, COALESCE(parent_id, 0), name);

-- Add version tracking (future: separate table)
ALTER TABLE workspace_items ADD COLUMN version INT DEFAULT 1;
```

**Proposed: New `workspace_item_versions` Table**
```sql
CREATE TABLE workspace_item_versions (
    id SERIAL PRIMARY KEY,
    workspace_item_id INT NOT NULL REFERENCES workspace_items(id) ON DELETE CASCADE,
    version INT NOT NULL,
    content TEXT,
    modified_by INT REFERENCES users(id),
    modified_at TIMESTAMP DEFAULT NOW(),
    change_description VARCHAR(500),
    UNIQUE(workspace_item_id, version)
);
```

**Benefits:**
- Prevent storage abuse with size limits
- Enable version control and rollback
- Support collaborative editing
- Improve search and file discovery
- Better data integrity with constraints

---

### 4. Additional Tables for Future Features

**`session_collaborators` - Multi-user Sessions**
```sql
CREATE TABLE session_collaborators (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(20) NOT NULL,  -- viewer, editor, admin
    invited_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, user_id)
);
```

**`execution_logs` - Command History & Audit Trail**
```sql
CREATE TABLE execution_logs (
    id SERIAL PRIMARY KEY,
    session_id INT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id),
    command TEXT NOT NULL,
    exit_code INT,
    output TEXT,
    execution_time_ms INT,
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_execution_logs_session ON execution_logs(session_id, executed_at DESC);
```

**`session_templates` - Shareable Starting Points**
```sql
CREATE TABLE session_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INT REFERENCES users(id),
    language VARCHAR(50),
    is_public BOOLEAN DEFAULT FALSE,
    use_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE template_files (
    id SERIAL PRIMARY KEY,
    template_id INT NOT NULL REFERENCES session_templates(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    content TEXT,
    path VARCHAR(500)
);
```

---

### Migration Path

1. **Phase 1: Non-breaking Additions** (Immediate)
   - Add new columns with defaults
   - Add indexes for performance
   - Backfill data as needed

2. **Phase 2: Data Cleanup** (After validation)
   - Migrate `sessions.code` to workspace_items
   - Drop deprecated `code` column
   - Clean up orphaned records

3. **Phase 3: New Features** (Future releases)
   - Add collaborators table
   - Implement version history
   - Add execution logs
   - Create template system

4. **Phase 4: Migration Tool** (Long-term)
   - Implement Alembic for automated migrations
   - Version control all schema changes
   - Rollback support

---

## Related Documentation

- [User API Documentation](../api/users.md)
- [Workspace API Documentation](../api/workspace.md)
- [WebSocket API Documentation](../api/websocket.md)
- [Architecture Overview](../architecture/ARCHITECTURE.md)
- [Kubernetes Deployment](../../backend/k8s/README.md)
