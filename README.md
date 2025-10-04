# Code Execution Platform

A modern web-based development environment that provides users with isolated Python development environments featuring a Monaco code editor, real-time terminal interface, and persistent file management. Built on Kubernetes with horizontal autoscaling to support multiple concurrent users.

## ⚠️ Security Notice

**Important**: The original database URL was accidentally leaked in the git history. The database password has been changed. If you have an old `.env` file, please update it with the new credentials.

![Platform Demo](https://img.shields.io/badge/Status-Production%20Ready-green)
![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%2B%20FastAPI-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Enabled-326CE5)
![Node.js](https://img.shields.io/badge/Node.js-20-339933)
![Type Safety](https://img.shields.io/badge/mypy-100%25%20strict-blue)
![Code Quality](https://img.shields.io/badge/ruff-compliant-brightgreen)

## 🎉 Recent Updates

**Architecture Refactoring & Code Cleanup** (October 2024)
- ✅ **Model Organization**: Split monolithic `postgres_models.py` into logical files (`users.py`, `sessions.py`, `workspace_items.py`)
- ✅ **Schema Organization**: Separated Pydantic schemas by domain (`base.py`, `users.py`, `sessions.py`, `workspace.py`)
- ✅ **100% Type Safety**: Achieved zero mypy errors in strict mode
- ✅ **Code Quality**: Ruff linting and formatting, ESLint for frontend
- ✅ **Removed Unused Features**: Eliminated review/approval system and dead code
- ✅ **CI/CD Improvements**: GitHub Actions with Ruff, mypy strict, ESLint, and TypeScript checks
- ✅ **Simplified Authentication**: Streamlined to basic username/password with bcrypt
- ✅ **Refactored Core**: Cleaned up exception handlers, extracted helper functions, reduced duplication

## 🚀 Features

### Core Development Environment
- **🖥️ Monaco Code Editor**: Full-featured editor with syntax highlighting, IntelliSense, and autocomplete
- **📟 Interactive Terminal**: Real-time terminal emulation with xterm.js supporting all standard bash commands
- **📁 File Management**: Create, edit, delete, and organize files in a hierarchical workspace structure
- **💾 Session Persistence**: Multiple isolated sessions per user with PostgreSQL-backed storage
- **🔒 Secure Execution**: Kubernetes pod-based isolation with dedicated resources per session
- **🐍 Python 3.11+**: Pre-installed with pandas, scipy, numpy, and pip package management
- **📦 Full Terminal Access**: Complete bash environment in isolated pods

### Advanced Features
- **👥 User Management**: Registration, authentication, and profile management
- **🔄 Real-time Sync**: WebSocket-based live updates and bidirectional file synchronization (DB ↔ Pod ↔ Editor)
- **☸️ Kubernetes Pods**: Dedicated execution pod per active session with ephemeral storage
- **🔌 WebSocket Communication**: Real-time terminal I/O via WebSocket + kubectl exec integration
- **📂 Workspace Files API**: RESTful API for file operations with automatic pod synchronization

### Security & Performance
- **🛡️ Sandboxed Execution**: Each session runs in an isolated Kubernetes pod
- **⚡ Horizontal Autoscaling**: 2-10 backend pods scale based on CPU (70%) and memory (80%)
- **🔐 Resource Limits**: CPU (500m), memory (512Mi) per execution pod
- **📊 High Availability**: Load-balanced backend with zero-downtime deployments
- **🚀 Scalability**: Supports 10+ concurrent users with current configuration

## 🏗️ Architecture

### Frontend (Next.js 15)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript with strict mode
- **Styling**: TailwindCSS v4
- **Editor**: Monaco Editor
- **Terminal**: xterm.js with full TTY support
- **State**: React Context + custom hooks
- **Code Quality**: ESLint with Next.js recommended config

### Backend (FastAPI on Kubernetes)
- **Framework**: FastAPI with async/await
- **Language**: Python 3.9+ with strict type hints (100% mypy strict mode compliance)
- **Database**: PostgreSQL (Supabase/local) with connection pooling
- **Orchestration**: Kubernetes with kubectl integration
- **WebSocket**: Real-time terminal communication via kubectl exec
- **Code Quality**: Ruff linter + formatter, mypy strict (0 errors)
- **Testing**: pytest with API and integration tests
- **Background Tasks**: Automated pod cleanup (idle sessions every 60s, startup cleanup)
- **Scaling**: Horizontal Pod Autoscaler (HPA) for backend pods
- **Load Balancing**: Kubernetes LoadBalancer service

### Infrastructure
- **Development**: kind (Kubernetes in Docker) for local development
- **Production**: DigitalOcean Kubernetes (DOKS) or similar
- **Backend Pods**: 2-10 replicas (horizontally scaled)
- **Execution Pods**: 1 per active user session
- **Storage**: Database as single source of truth, synced to ephemeral pod storage
- **Container Registry**: Docker Hub
- **Database**: Managed PostgreSQL with connection pooling

### Database Schema
Models organized into logical separate files for better maintainability:

- **users** (`backend/app/models/users.py`): User authentication and profile management
  - Fields: id, username, email, password_hash, created_at, updated_at

- **sessions** (`backend/app/models/sessions.py`): UUID-based workspace/session management
  - Fields: id, uuid, user_id, name, code, language, is_active, created_at, updated_at

- **workspace_items** (`backend/app/models/workspace_items.py`): Hierarchical file/folder storage with bidirectional sync
  - Fields: id, session_id, parent_id, name, type, content, full_path, created_at, updated_at

### Background Services
- **Startup Cleanup**: Removes orphaned Kubernetes pods from previous server crashes (runs once on startup)
- **Idle Session Cleanup**: Automatically removes idle sessions (30min timeout) and expired sessions (2hr max lifetime) - runs every 60 seconds

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 15 + React 19 | Modern web framework with SSR |
| **Backend** | FastAPI + Python 3.11 | High-performance async API |
| **Database** | PostgreSQL (Managed) | Reliable relational database |
| **Orchestration** | Kubernetes (kind/DOKS) | Container orchestration & scaling |
| **Editor** | Monaco Editor | VS Code-like editing experience |
| **Terminal** | xterm.js | Full terminal emulation |
| **Styling** | TailwindCSS v4 | Utility-first CSS framework |
| **Isolation** | Kubernetes Pods | Per-session execution environments |
| **Real-time** | WebSocket + kubectl exec | Live terminal communication |
| **Storage** | Database + Pod Sync | Database as single source of truth |
| **Scaling** | HPA | Automatic horizontal scaling |
| **Registry** | Docker Hub | Container image hosting |

## 📁 Project Structure

```
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/                # App Router pages and layouts
│   │   ├── components/         # React components
│   │   ├── contexts/           # React contexts (Auth, App state)
│   │   ├── hooks/              # Custom React hooks
│   │   └── services/           # API client, WebSocket
│   ├── public/                 # Static assets
│   ├── eslint.config.js        # ESLint configuration
│   ├── tsconfig.json           # TypeScript config
│   └── package.json            # Frontend dependencies
│
├── backend/                     # FastAPI backend service
│   ├── app/
│   │   ├── api/                # REST API endpoints
│   │   │   ├── health.py       # Health check endpoint
│   │   │   ├── users.py        # User management
│   │   │   ├── sessions.py     # Session management
│   │   │   └── workspace_files.py  # File operations
│   │   ├── models/             # Database models (organized by domain)
│   │   │   ├── users.py        # User model
│   │   │   ├── sessions.py     # CodeSession model
│   │   │   ├── workspace_items.py  # WorkspaceItem model
│   │   │   └── __init__.py     # Model exports
│   │   ├── schemas/            # Pydantic schemas (organized by domain)
│   │   │   ├── base.py         # Base response schemas
│   │   │   ├── users.py        # User schemas
│   │   │   ├── sessions.py     # Session schemas
│   │   │   ├── workspace.py    # Workspace schemas
│   │   │   └── __init__.py     # Schema exports
│   │   ├── services/           # Business logic services
│   │   │   ├── kubernetes_client.py    # K8s pod management
│   │   │   ├── container_manager.py    # Session & pod lifecycle
│   │   │   ├── background_tasks.py     # Automated cleanup tasks
│   │   │   ├── workspace_loader.py     # DB ↔ Pod file sync
│   │   │   └── file_manager.py         # File operations
│   │   ├── websockets/         # WebSocket handlers
│   │   │   ├── manager.py      # Connection management
│   │   │   └── handlers.py     # Message handling
│   │   ├── core/               # Core utilities
│   │   │   └── postgres.py     # Database connection
│   │   └── main.py             # FastAPI app + WebSocket endpoint
│   ├── k8s/                    # Kubernetes manifests
│   │   ├── 01-namespace.yaml  # Namespace definition
│   │   ├── 02-rbac.yaml       # Service account & RBAC
│   │   ├── 03-backend-config.yaml  # ConfigMap
│   │   ├── 04-backend.yaml    # Backend deployment & service
│   │   └── 05-hpa.yaml        # Horizontal Pod Autoscaler
│   ├── tests/                  # Comprehensive test suite
│   ├── mypy.ini               # mypy strict configuration
│   ├── ruff.toml              # Ruff linter/formatter config
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Execution pod image
│   └── Dockerfile.backend     # Backend pod image
│
├── docs/                        # Project documentation
│   ├── SETUP.md                # Complete setup guide
│   ├── FEATURES.md             # Detailed feature documentation
│   ├── api/                    # API documentation
│   │   ├── README.md           # API overview
│   │   ├── users.md            # User management API
│   │   ├── workspace.md        # Workspace operations API
│   │   └── websocket.md        # WebSocket API
│   ├── architecture/           # Architecture documentation
│   │   └── ARCHITECTURE.md     # System design and components
│   ├── database/               # Database documentation
│   │   └── DATABASE.md         # Schema design and models
│   └── deployment/             # Deployment guides
│       └── README.md           # Production deployment guide
│
├── .github/
│   └── workflows/
│       └── code_checks.yaml   # CI/CD (Ruff, mypy, ESLint, TypeScript)
│
├── CLAUDE.md                  # Project context for Claude Code
└── README.md                  # This file
```

## 🚦 Quick Start

### Local Development Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.9+ (for backend)
- **PostgreSQL** 14+ (database)
- **kubectl** (for Kubernetes)
- **kind** (for local Kubernetes cluster)

### Kubernetes Deployment Prerequisites
- **kubectl** (Kubernetes CLI)
- **Docker** with buildx (for multi-platform builds)
- **Kubernetes Cluster** (kind for local, DigitalOcean/AWS/GCP for production)
- **Managed PostgreSQL** (recommended for production)

### 1. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with API URL (http://localhost:8002)

# Start development server
npm run dev
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs
- **WebSocket**: ws://localhost:8002/ws

## ☸️ Kubernetes Deployment

### Quick Deploy to Kubernetes
```bash
# 1. Build and push images using the provided script
cd backend
./build-and-push.sh

# Or manually:
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/coding-platform-backend:latest -f Dockerfile.backend --push .

docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/code-execution:latest -f Dockerfile --push .

# 2. Update Kubernetes manifests with your values
# Edit backend/k8s/03-backend-config.yaml (execution image, CORS origins)
# Edit backend/k8s/04-backend.yaml (backend image)
# Create backend/k8s/03-backend-secrets.yaml from example (database URL)

# 3. Deploy to cluster
kubectl apply -f backend/k8s/

# 4. Wait for deployment
kubectl rollout status deployment/backend -n coding-platform

# 5. Get LoadBalancer IP
kubectl get svc backend -n coding-platform
```

### Monitoring Deployment
```bash
# Check HPA status
kubectl get hpa -n coding-platform

# Watch pod scaling
kubectl get pods -n coding-platform --watch

# Watch execution pods
kubectl get pods -n default --watch

# View logs
kubectl logs -l app=backend -n coding-platform --tail=50
```

See **[Complete Setup Guide](docs/SETUP.md)** for detailed deployment instructions.

## 📚 API Endpoints

### REST API
- **POST** `/api/users/register` - Register new user
- **POST** `/api/users/login` - User authentication
- **GET** `/api/users/{user_id}` - Get user details
- **POST** `/api/sessions/` - Create new workspace session
- **GET** `/api/sessions/{session_uuid}` - Get session details (requires user_id param)
- **GET** `/api/sessions/` - List user sessions
- **GET** `/api/workspace/{session_uuid}/files` - List workspace files
- **GET** `/api/workspace/{session_uuid}/file/{filename}` - Get file content
- **POST** `/api/workspace/{session_uuid}/file/{filename}` - Save file content
- **DELETE** `/api/workspace/{session_uuid}/file/{filename}` - Delete file
- **GET** `/api/workspace/{session_uuid}/status` - Get workspace initialization status
- **POST** `/api/workspace/{session_uuid}/ensure-default` - Create default main.py if empty

### WebSocket API
- **WS** `/ws` - Real-time terminal communication
  - `terminal_input` - Execute terminal commands in isolated pod
  - `pod_ready` - Notification when execution pod is ready
  - `terminal_output` - Command output from pod
  - `terminal_clear_progress` - Clear progress messages

See **[API Documentation](http://localhost:8002/docs)** (FastAPI auto-generated) for full details.

## 🔧 Development

### Code Quality & Testing
```bash
# Backend type checking (100% strict mode compliance - 0 errors)
cd backend
venv/bin/mypy app --strict --show-error-codes --no-error-summary

# Backend linting and formatting
cd backend
venv/bin/ruff check .
venv/bin/ruff format .

# Backend tests
cd backend
venv/bin/pytest tests/ -v

# Frontend linting
cd frontend
npm run lint

# Frontend type checking
cd frontend
npx tsc --noEmit
```

### Pre-commit Hooks
The backend includes pre-commit hooks (`.pre-commit-config.yaml`):
```bash
cd backend
pip install pre-commit
pre-commit install
```

This runs automatically on git commit:
- Trailing whitespace removal
- YAML/TOML validation
- Ruff linting and formatting
- mypy type checking

### Database Setup
The backend uses PostgreSQL with automatic schema initialization on startup. No manual migrations required - just configure your `DATABASE_URL` environment variable with a valid PostgreSQL connection string.

## 🔒 Security Features

- **Pod Isolation**: Each session runs in a separate Kubernetes pod with dedicated resources
- **Resource Limits**: CPU (500m), memory (512Mi) per execution pod
- **RBAC**: Backend uses service account with limited Kubernetes API permissions
- **Input Validation**: Comprehensive sanitization and pattern matching
- **Session Isolation**: User data completely separated in database and pods
- **File System Isolation**: Each pod has dedicated ephemeral storage, restricted to /app directory
- **Automatic Cleanup**: Idle sessions cleaned up after 30 minutes, max 2 hour lifetime
- **Network Security**: Kubernetes network policies (configurable)
- **Password Security**: bcrypt hashing with salt
- **SQL Injection Prevention**: Parameterized queries throughout
- **CORS Configuration**: Restricted to allowed origins

## 🌟 Key Workflows

### Basic Development Session
1. User registers/logs in to the platform
2. Creates a new workspace session (default `script.py` created in database)
3. Backend creates dedicated Kubernetes pod for the session
4. Files from PostgreSQL are synced to pod filesystem automatically
5. User writes Python code in Monaco editor
6. File saved in editor → Updates database → Syncs to pod
7. Executes commands in terminal (runs in pod via `kubectl exec` via WebSocket)
8. Session state persists in PostgreSQL (sessions + workspace_items tables)
9. Pod is cleaned up when:
   - WebSocket disconnects and no other connections exist
   - Session is idle for 30+ minutes (background cleanup task)
   - Session exceeds 2 hour maximum lifetime

## 🚀 Deployment

### Production Architecture
The platform is designed for Kubernetes deployment with the following components:

**Infrastructure**:
- **Kubernetes Cluster**: kind (local), DigitalOcean Kubernetes (DOKS), AWS EKS, or GCP GKE
- **Backend**: 2-10 FastAPI pods with horizontal autoscaling
- **Execution Pods**: 1 per active user session (on-demand)
- **Database**: Managed PostgreSQL (Supabase, AWS RDS, DigitalOcean)
- **Load Balancer**: Kubernetes LoadBalancer service
- **Container Registry**: Docker Hub or private registry

**Deployment Targets**:
- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **Backend**: Kubernetes cluster with HPA
- **Database**: Managed PostgreSQL service

### Scaling Configuration
- **Backend Pods**: Auto-scale 2-10 based on CPU (70%) and memory (80%)
- **Execution Pods**: Created on-demand, 1 per active session
- **Capacity**: Current config supports 10+ concurrent users

### Environment Configuration
- Configure managed database connection string
- Set up CORS for frontend domain
- Configure Kubernetes secrets for sensitive data
- Update execution pod image in ConfigMap
- Set resource limits in pod specifications

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Quality Standards
- Backend: Ruff linting, mypy strict mode (100% compliance)
- Frontend: ESLint, TypeScript strict mode
- All PRs must pass CI checks (see `.github/workflows/code_checks.yaml`)

---

**Built with ❤️ using Next.js, FastAPI, and Kubernetes**
