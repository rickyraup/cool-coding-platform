# Code Execution Platform Architecture

## Overview
A full-stack web platform that provides users with an isolated Python development environment featuring a code editor, terminal interface, and file management. The platform is deployed on Kubernetes with automatic horizontal scaling to support multiple concurrent users.

## System Architecture

```
┌────────────────────────────┐
│        Frontend            │
│    (Next.js 15 + React)    │
│                            │
│  ┌──────────────────────┐  │
│  │    Monaco Editor      │  │ Code editing with syntax highlighting
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │   xterm.js Terminal   │  │ Interactive terminal emulation
│  └──────────────────────┘  │
│  ┌──────────────────────┐  │
│  │  File Explorer Tree   │  │ Workspace file management
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │ HTTP API / WebSocket
             ▼
┌────────────────────────────┐
│    Kubernetes Cluster      │
│     (kind - local dev)     │
│                            │
│  ┌──────────────────────┐  │
│  │   LoadBalancer Svc    │  │ Distributes traffic to backend pods
│  └──────────┬───────────┘  │
│             │               │
│  ┌──────────▼───────────┐  │
│  │   Backend Pods (2-10) │  │ Horizontally scaled FastAPI instances
│  │   (FastAPI + Python)  │  │
│  │                       │  │
│  │  ┌─────────────────┐ │  │
│  │  │ Session Manager │ │  │ User session lifecycle
│  │  └─────────────────┘ │  │
│  │  ┌─────────────────┐ │  │
│  │  │ WebSocket Handler│ │  │ Real-time terminal I/O
│  │  └─────────────────┘ │  │
│  │  ┌─────────────────┐ │  │
│  │  │ K8s Pod Manager │ │  │ Creates/manages execution pods via K8s API
│  │  └─────────────────┘ │  │
│  │  ┌─────────────────┐ │  │
│  │  │ File Sync Logic │ │  │ Bidirectional DB ↔ Pod file sync
│  │  └─────────────────┘ │  │
│  │  ┌─────────────────┐ │  │
│  │  │ Auth Service    │ │  │ Simple username/password authentication
│  │  └─────────────────┘ │  │
│  └──────────┬───────────┘  │
│             │               │
│  ┌──────────▼───────────┐  │
│  │ Execution Pods (1/usr)│  │ Per-session Python environments
│  │  - Python 3.11        │  │
│  │  - Node.js 20         │  │
│  │  - pandas, scipy      │  │
│  │  - PVC storage (1Gi)  │  │
│  │  - Resource limits    │  │
│  └──────────────────────┘  │
│                            │
│  ┌──────────────────────┐  │
│  │ Horizontal Pod        │  │
│  │ Autoscaler (HPA)      │  │ Scales backend pods based on CPU/memory
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │ Database queries
             ▼
┌────────────────────────────┐
│     PostgreSQL Database    │
│      (Supabase/Local)      │
│                            │
│  - users                   │
│  - sessions (UUID-based)   │
│  - workspace_items         │
└────────────────────────────┘
```

## Key Components

### Frontend (Next.js 15)
- **Framework:** Next.js 15 with App Router + React 19
- **Language:** TypeScript with strict mode
- **Styling:** TailwindCSS v4
- **Editor:** Monaco Editor for code editing
- **Terminal:** xterm.js for terminal emulation
- **State Management:** React Context + custom hooks
- **Real-time:** WebSocket connection for terminal I/O

### Backend (FastAPI)
- **Framework:** FastAPI with async/await support
- **Language:** Python 3.9+ with type hints
- **Database:** PostgreSQL with custom connection pooling
- **Authentication:** Simple username/password with bcrypt
- **Orchestration:** Kubernetes for container management
- **WebSocket:** Real-time terminal communication
- **Background Tasks:** Pod lifecycle management via Kubernetes API
- **Code Quality:** Ruff (linting + formatting) + mypy (strict type checking)

### Database (PostgreSQL)
- **Users:** Authentication system
- **Sessions:** UUID-based session management
- **Workspace Items:** Hierarchical file/folder storage
- **Managed Service:** Supabase (production) or local PostgreSQL (development)

### Database Models Architecture
Models are organized into separate logical files for better maintainability:

**`backend/app/models/users.py`**
- User model with CRUD operations
- Password hashing with bcrypt
- Username/email lookup methods

**`backend/app/models/sessions.py`**
- CodeSession model with UUID-based identification
- Session lifecycle management
- User association and workspace tracking

**`backend/app/models/workspace_items.py`**
- WorkspaceItem model for files and folders
- Hierarchical structure with parent_id relationships
- Content storage and path resolution

**`backend/app/models/__init__.py`**
- Centralized model exports
- Backwards-compatible aliases

### Infrastructure (Kubernetes)
- **Development:** kind (Kubernetes in Docker) for local development
- **Production:** DigitalOcean Kubernetes (DOKS) or similar
- **Execution Isolation:** Per-user Kubernetes pods
- **Backend Scaling:** Horizontal Pod Autoscaler (2-10 replicas)
- **Load Balancing:** Kubernetes LoadBalancer Service
- **Container Registry:** Docker Hub (rraup12/coding-platform-backend, rraup12/code-execution)
- **File Storage:** Database-backed with bidirectional pod sync

## Current System Features

### Authentication & Authorization
- **User Management:** Username/password authentication with bcrypt
- **Session Management:** Server-side session tracking with UUID identifiers
- **Access Control:** User-based workspace isolation

### Workspace Management
- **Session Isolation:** Each workspace gets unique Kubernetes pod with dedicated PVC
- **File Persistence:** Bidirectional sync between database and pod filesystems
- **Real-time Collaboration:** WebSocket-based terminal sharing
- **Pod Lifecycle:** Automatic creation, readiness checks, and cleanup
- **File Sync:** Automatic synchronization after file-modifying commands
- **Storage:** Database as single source of truth, synced to PVC-backed pod storage (1Gi per session)

### API Architecture
- **RESTful Design:** Standard HTTP methods for resource operations
- **WebSocket Integration:** Real-time terminal communication
- **Error Handling:** Consistent error response format
- **Type Safety:** Full TypeScript coverage on frontend, strict mypy on backend

### API Endpoints

**Users API** (`/api/users/`)
- `POST /register` - Create new user account
- `POST /login` - Authenticate user
- `GET /{user_id}` - Get user details

**Sessions API** (`/api/sessions/`)
- `GET /` - List user's sessions
- `POST /` - Create new session
- `GET /{session_uuid}` - Get session details

**Workspace API** (`/api/workspace/{session_uuid}/`)
- `GET /files` - List workspace files
- `GET /file/{filename}` - Get file content
- `POST /file/{filename}` - Save file content
- `DELETE /file/{filename}` - Delete file
- `GET /status` - Get workspace initialization status
- `POST /ensure-default` - Create default main.py if workspace is empty

**WebSocket** (`/ws`)
- Real-time terminal I/O
- Command execution in isolated pods
- Environment readiness notifications

## Security Considerations

### Pod Security
- **Process Isolation:** Each user session runs in separate Kubernetes pod
- **Resource Limits:** Memory (512Mi limit) and CPU (500m limit) per execution pod
- **Network Policies:** Isolated pod networking within Kubernetes
- **File System Isolation:** Each pod has dedicated PVC storage (1Gi)
- **Service Account:** Backend pods use RBAC-controlled service account for K8s API access

### Application Security
- **Input Validation:** All user inputs validated on backend
- **SQL Injection Prevention:** Parameterized queries throughout
- **XSS Protection:** Content sanitization on frontend
- **CORS Configuration:** Restricted to allowed origins
- **Command Execution:** All commands executed within isolated pods
- **Password Security:** bcrypt hashing with salt

### Data Protection
- **Session Security:** Secure session management with UUID tokens
- **Code Privacy:** User code only accessible to owner
- **Audit Logging:** Pod creation/deletion logged
- **Secret Management:** Database credentials stored in Kubernetes secrets or environment variables

## Performance Optimizations

### Pod Management
- **Lazy Loading:** Execution pods created only when workspace is accessed
- **Readiness Checks:** Backend waits for pod ready status before accepting commands
- **Background Cleanup:** Automated pod deletion when sessions end
- **Resource Monitoring:** Kubernetes metrics for pod CPU/memory usage

### Horizontal Scaling
- **Backend Autoscaling:** 2-10 replicas based on CPU (70%) and memory (80%) thresholds
- **Load Balancing:** Kubernetes Service distributes traffic across backend pods
- **Aggressive Scale-Up:** Doubles pods or adds 2 immediately under load
- **Conservative Scale-Down:** 5-minute stabilization, removes 50% or 1 pod gradually

### Frontend Performance
- **Code Splitting:** Route-based code splitting with Next.js
- **Optimistic Updates:** Immediate UI feedback for user actions
- **WebSocket Efficiency:** Minimal message overhead
- **Turbopack:** Fast Next.js bundler for development and production

### Database Performance
- **Connection Pooling:** Efficient database connection management
- **Query Optimization:** Indexed queries for common operations
- **Data Modeling:** Normalized schema with appropriate relationships

## Kubernetes Deployment Architecture

### Cluster Configuration
- **Development:** kind cluster (local Kubernetes)
- **Production:** DigitalOcean Kubernetes (DOKS) or similar
- **Node Pool:** Configurable based on environment

### Backend Deployment
**File:** `backend/k8s/04-backend.yaml`

**Deployment Spec:**
- **Replicas:** 2 minimum (HPA managed)
- **Container Image:** rraup12/coding-platform-backend:latest
- **Resources per pod:**
  - CPU Request: 250m, Limit: 1000m
  - Memory Request: 512Mi, Limit: 1Gi
- **Health Checks:**
  - Liveness: HTTP /api/health/ (30s delay, 10s period)
  - Readiness: HTTP /api/health/ (10s delay, 5s period)
- **Service Account:** backend-sa (with RBAC for pod management)

**Service:**
- **Type:** LoadBalancer
- **Port:** 80 → 8002 (container port)
- **Load Distribution:** Round-robin across backend pods

### Horizontal Pod Autoscaler (HPA)
**File:** `backend/k8s/05-hpa.yaml`

**Configuration:**
- **Target:** backend deployment
- **Replicas:** 2 min, 10 max
- **Metrics:**
  - CPU: 70% average utilization
  - Memory: 80% average utilization
- **Scale-Up Behavior:**
  - Policy: Max(2 pods, 100% of current)
  - Stabilization: None (immediate)
- **Scale-Down Behavior:**
  - Policy: Min(1 pod, 50% of current)
  - Stabilization: 300 seconds (5 minutes)

### Execution Pod Management
**Managed by:** `backend/app/services/kubernetes_client.py` + `backend/app/services/container_manager.py`

**Pod Specification:**
- **Name:** pod-{random_hash}
- **Image:** rraup12/code-execution:latest
  - Base: Python 3.11
  - Includes: Node.js 20, pandas, scipy, numpy
- **Resources:**
  - CPU Request: 200m, Limit: 500m
  - Memory Request: 256Mi, Limit: 512Mi
- **Storage:** 1Gi PersistentVolumeClaim per session (files synced to/from database)
- **Lifecycle:**
  1. Created when user opens workspace
  2. Waits for "Running" and "Ready" status
  3. Files synced from database to pod
  4. Accepts terminal commands via WebSocket
  5. Files synced back to database after modifications
  6. Deleted when session ends or user disconnects

### File Synchronization
**Service:** `backend/app/api/workspace_files.py` + `backend/app/services/workspace_loader.py`

**Database → Pod (on session start):**
1. Query workspace_items for session
2. For each file/folder: create in pod filesystem using tar
3. Write file contents to /app directory
4. Maintain directory structure

**Pod → Database (on file save):**
1. API receives file content from frontend
2. Update workspace_items in database
3. Sync to pod's /app directory using tar
4. Both database and pod stay in sync

**Key Features:**
- Database is single source of truth
- Files persist across pod restarts
- Real-time sync on file save/delete
- Support for nested directories

### Deployment Process

**Build & Push Images:**
```bash
# Using the provided script
cd backend
./build-and-push.sh

# Or manually
docker buildx build --platform linux/amd64,linux/arm64 \
  -t rraup12/coding-platform-backend:latest -f Dockerfile.backend --push .

docker buildx build --platform linux/amd64,linux/arm64 \
  -t rraup12/code-execution:latest -f Dockerfile --push .
```

**Deploy to Kubernetes:**
```bash
# Apply all configurations
kubectl apply -f backend/k8s/

# Verify deployment
kubectl rollout status deployment/backend -n coding-platform
kubectl get hpa -n coding-platform
kubectl get pods -n coding-platform
```

**Monitor Scaling:**
```bash
# Watch HPA metrics
kubectl get hpa -n coding-platform --watch

# Watch pod scaling
kubectl get pods -n coding-platform -l app=backend --watch

# Watch execution pods
kubectl get pods -n default --watch
```

### Development URLs
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8002/api/
- **WebSocket:** ws://localhost:8002/ws
- **Health Check:** http://localhost:8002/api/health/

### Production URLs
- **Backend API:** http://<loadbalancer-ip>/api/
- **WebSocket:** ws://<loadbalancer-ip>/ws
- **Health Check:** http://<loadbalancer-ip>/api/health/

## Code Quality & CI/CD

### Linting & Formatting
- **Backend:** Ruff for linting and formatting (configured in `backend/ruff.toml`)
- **Frontend:** ESLint for TypeScript/React (configured in `frontend/eslint.config.js`)

### Type Checking
- **Backend:** mypy in strict mode (configured in `backend/mypy.ini`)
- **Frontend:** TypeScript strict mode

### Pre-commit Hooks
Configured in `backend/.pre-commit-config.yaml`:
- Trailing whitespace removal
- YAML/TOML validation
- Ruff linting and formatting
- mypy type checking

### GitHub Actions
Automated code quality checks on PRs and pushes (`.github/workflows/code_checks.yaml`):
- Backend: Ruff lint, Ruff format, mypy strict
- Frontend: ESLint, TypeScript type check

## Project Structure

```
cool-coding-platform/
├── frontend/                    # Next.js 15 frontend
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom React hooks
│   │   └── services/           # API client, WebSocket
│   ├── eslint.config.js        # ESLint configuration
│   ├── tsconfig.json           # TypeScript config
│   └── package.json
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/                # API endpoints
│   │   │   ├── health.py       # Health check endpoint
│   │   │   ├── users.py        # User management
│   │   │   ├── sessions.py     # Session management
│   │   │   └── workspace_files.py  # File operations
│   │   ├── models/             # Database models (organized)
│   │   │   ├── users.py        # User model
│   │   │   ├── sessions.py     # Session model
│   │   │   ├── workspace_items.py  # File/folder model
│   │   │   └── __init__.py     # Model exports
│   │   ├── schemas/            # Pydantic schemas (organized)
│   │   │   ├── base.py         # Base response schemas
│   │   │   ├── users.py        # User schemas
│   │   │   ├── sessions.py     # Session schemas
│   │   │   ├── workspace.py    # Workspace schemas
│   │   │   └── __init__.py     # Schema exports
│   │   ├── services/           # Business logic
│   │   │   ├── container_manager.py    # Pod lifecycle
│   │   │   ├── kubernetes_client.py    # K8s API client
│   │   │   ├── file_manager.py         # File operations
│   │   │   ├── workspace_loader.py     # File sync
│   │   │   └── background_tasks.py     # Cleanup tasks
│   │   ├── websockets/         # WebSocket handlers
│   │   │   ├── manager.py      # Connection management
│   │   │   └── handlers.py     # Message handling
│   │   ├── core/               # Core utilities
│   │   │   └── postgres.py     # Database connection
│   │   └── main.py             # FastAPI app + WebSocket endpoint
│   ├── k8s/                    # Kubernetes manifests
│   │   ├── 01-namespace.yaml
│   │   ├── 02-rbac.yaml
│   │   ├── 03-backend-config.yaml
│   │   ├── 04-backend.yaml
│   │   └── 05-hpa.yaml
│   ├── tests/                  # Pytest tests
│   ├── mypy.ini               # mypy strict config
│   ├── ruff.toml              # Ruff linter/formatter config
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile.backend     # Backend container
│
├── docs/                       # Documentation
│   ├── architecture/
│   │   └── ARCHITECTURE.md    # This file
│   ├── api/                   # API documentation
│   └── database/              # Database schema docs
│
├── .github/
│   └── workflows/
│       └── code_checks.yaml   # CI/CD pipeline
│
└── CLAUDE.md                  # Project context for Claude Code
```

## Recent Architecture Changes

### Model Reorganization (October 2024)
- Split monolithic `postgres_models.py` into logical separate files
- Models now organized by domain: `users.py`, `sessions.py`, `workspace_items.py`
- Improved maintainability and code organization
- Backwards-compatible imports via `__init__.py`

### Schema Reorganization (October 2024)
- Split schemas into domain-specific files
- Base schemas extracted to `base.py`
- Domain schemas: `users.py`, `sessions.py`, `workspace.py`
- Cleaner imports and better organization

### Code Cleanup (October 2024)
- Removed review/approval system (not in current scope)
- Removed dead code execution subprocess feature
- Removed reviewer management system
- Simplified authentication to basic username/password
- Cleaned up empty exception handlers
- Extracted helper functions to reduce duplication

### CI/CD Improvements (October 2024)
- Updated GitHub Actions to use Ruff instead of Black/Flake8
- Added mypy strict type checking to CI pipeline
- Added frontend ESLint and TypeScript checks
- Separate jobs for backend and frontend validation

## Future Enhancements

### Potential Features
- Multi-language support (currently Python + Node.js)
- Collaborative editing (multiple users in same workspace)
- Workspace templates and starter projects
- Package management UI (pip, npm)
- Larger storage volumes (currently 1Gi PVC per session)
- User workspace quotas and limits
- Admin dashboard for user/session management

### Infrastructure Improvements
- Production deployment to cloud Kubernetes (DOKS, EKS, GKE)
- HTTPS/TLS termination with Let's Encrypt
- Ingress controller for better routing
- Monitoring and alerting (Prometheus + Grafana)
- Log aggregation (ELK stack or similar)
- Automated backups for database
- Disaster recovery procedures
