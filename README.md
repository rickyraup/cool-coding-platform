# Code Execution Platform

A modern web-based development environment that provides users with isolated Python and Node.js development environments featuring a code editor, terminal interface, file management, and collaborative code review system. Built on Kubernetes with horizontal autoscaling to support multiple concurrent users.

![Platform Demo](https://img.shields.io/badge/Status-Production%20Ready-green)
![Tech Stack](https://img.shields.io/badge/Stack-Next.js%20%2B%20FastAPI-blue)
![Python](https://img.shields.io/badge/Python-3.11%2B-brightgreen)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Enabled-326CE5)
![Node.js](https://img.shields.io/badge/Node.js-20-339933)

## 🚀 Features

### Core Development Environment
- **🖥️ Monaco Code Editor**: Full-featured editor with syntax highlighting, IntelliSense, and autocomplete
- **📟 Interactive Terminal**: Real-time terminal emulation with xterm.js supporting all standard commands
- **📁 File Management**: Create, edit, and organize files in a hierarchical workspace structure
- **💾 Session Persistence**: Multiple isolated sessions per user with PostgreSQL-backed storage
- **🔒 Secure Execution**: Kubernetes pod-based isolation with dedicated resources per session
- **🐍 Python 3.11+**: Pre-installed with pandas, scipy, numpy, and pip package management
- **📦 Node.js 20**: Full npm ecosystem with package installation support

### Advanced Features
- **👥 User Management**: Registration, authentication, and profile management
- **📝 Code Review System**: Submit code for review with priority levels and reviewer assignment
- **🏆 Reviewer Levels**: Five-level reviewer system (0-4) with self-service promotion
- **🔄 Real-time Sync**: WebSocket-based live updates and bidirectional file synchronization
- **☸️ Kubernetes Pods**: Dedicated execution pod per active session with 1Gi storage

### Security & Performance
- **🛡️ Sandboxed Execution**: Each session runs in an isolated Kubernetes pod
- **⚡ Horizontal Autoscaling**: 2-10 backend pods scale based on CPU (70%) and memory (80%)
- **📈 Cluster Autoscaling**: 3-7 nodes added automatically based on demand
- **🔐 Resource Limits**: CPU (500m), memory (512Mi) per execution pod
- **📊 High Availability**: Load-balanced backend with zero-downtime deployments
- **🚀 Scalability**: Supports 10-40+ concurrent users with current configuration

## 🏗️ Architecture

### Frontend (Next.js 15)
- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript with strict mode
- **Styling**: TailwindCSS v4
- **Editor**: Monaco Editor
- **Terminal**: xterm.js with full TTY support
- **State**: React Context + custom hooks

### Backend (FastAPI on Kubernetes)
- **Framework**: FastAPI with async/await
- **Language**: Python 3.9+ with type hints
- **Database**: PostgreSQL (DigitalOcean Managed Database)
- **Orchestration**: Kubernetes (DOKS) with kubectl integration
- **WebSocket**: Real-time terminal communication via kubectl exec
- **Scaling**: Horizontal Pod Autoscaler (HPA) for backend pods
- **Load Balancing**: Kubernetes LoadBalancer service

### Infrastructure
- **Kubernetes Cluster**: DigitalOcean Kubernetes (DOKS)
- **Backend Pods**: 2-10 replicas (horizontally scaled)
- **Execution Pods**: 1 per active user session
- **Storage**: PersistentVolumeClaims (1Gi per session)
- **Container Registry**: Docker Hub
- **Database**: Managed PostgreSQL with connection pooling

### Database Schema
- **Users**: Authentication + 5-level reviewer system
- **Sessions**: UUID-based workspace management
- **Workspace Items**: Hierarchical file storage with bidirectional sync
- **Review Requests**: Code review workflow with comments
- **Review History**: Audit trail for review changes

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Next.js 15 + React 19 | Modern web framework with SSR |
| **Backend** | FastAPI + Python 3.11 | High-performance async API |
| **Database** | PostgreSQL (Managed) | Reliable relational database |
| **Orchestration** | Kubernetes (DOKS) | Container orchestration & scaling |
| **Editor** | Monaco Editor | VS Code-like editing experience |
| **Terminal** | xterm.js | Full terminal emulation |
| **Styling** | TailwindCSS v4 | Utility-first CSS framework |
| **Isolation** | Kubernetes Pods | Per-session execution environments |
| **Real-time** | WebSocket + kubectl exec | Live terminal communication |
| **Storage** | PersistentVolumeClaims | Persistent workspace storage |
| **Scaling** | HPA + Cluster Autoscaler | Automatic horizontal scaling |
| **Registry** | Docker Hub | Container image hosting |

## 📁 Project Structure

```
├── frontend/                    # Next.js frontend application
│   ├── src/
│   │   ├── app/                # App Router pages and layouts
│   │   ├── components/         # React components
│   │   ├── contexts/           # React contexts (Auth, App state)
│   │   ├── hooks/              # Custom React hooks
│   │   └── services/           # API service layer
│   ├── public/                 # Static assets
│   └── package.json            # Frontend dependencies
├── backend/                     # FastAPI backend service
│   ├── app/
│   │   ├── api/                # REST API endpoints
│   │   ├── core/               # Core utilities (database, settings)
│   │   ├── models/             # Database models
│   │   ├── schemas/            # Pydantic request/response schemas
│   │   ├── services/           # Business logic services
│   │   │   ├── kubernetes_client.py  # K8s pod management
│   │   │   └── file_sync.py          # DB ↔ Pod file sync
│   │   ├── websockets/         # WebSocket handlers
│   │   └── main.py             # FastAPI application entry point
│   ├── k8s/                    # Kubernetes manifests
│   │   ├── 00-namespace.yaml  # Namespace definition
│   │   ├── 01-secrets.yaml    # Database credentials
│   │   ├── 02-configmap.yaml  # Configuration
│   │   ├── 03-backend.yaml    # Backend deployment & service
│   │   └── 04-hpa.yaml        # Horizontal Pod Autoscaler
│   ├── execution-image/        # Execution pod Dockerfile
│   ├── tests/                  # Comprehensive test suite
│   └── requirements.txt        # Python dependencies
├── docs/                        # Project documentation
│   ├── SETUP.md                # Complete setup guide
│   ├── FEATURES.md             # Detailed feature documentation
│   ├── api/                    # API documentation
│   │   ├── README.md           # API overview
│   │   ├── reviews.md          # Review system API
│   │   ├── users.md            # User management API
│   │   ├── workspace.md        # Workspace operations API
│   │   └── websocket.md        # WebSocket API
│   ├── architecture/           # Architecture documentation
│   │   └── ARCHITECTURE.md     # System design and components
│   ├── database/               # Database documentation
│   │   └── DATABASE.md         # Schema design and models
│   └── deployment/             # Deployment guides
│       └── README.md           # Production deployment guide
└── README.md                   # This file
```

## 🚦 Quick Start

### Local Development Prerequisites
- **Node.js** 18+ (for frontend)
- **Python** 3.9+ (for backend)
- **PostgreSQL** 14+ (database)

### Kubernetes Deployment Prerequisites
- **kubectl** (Kubernetes CLI)
- **Docker** with buildx (for multi-platform builds)
- **Kubernetes Cluster** (DigitalOcean, AWS EKS, GCP GKE, etc.)
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
python -m app.main
```

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with API URL

# Start development server
npm run dev
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs
- **WebSocket**: ws://localhost:8002/api/terminal/ws/{session_id}

## ☸️ Kubernetes Deployment

### Quick Deploy to Kubernetes
```bash
# 1. Build and push images
docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/coding-platform-backend:latest --push backend/

docker buildx build --platform linux/amd64,linux/arm64 \
  -t your-username/code-execution:latest --push backend/execution-image/

# 2. Update Kubernetes manifests with your values
# Edit backend/k8s/01-secrets.yaml (database URL)
# Edit backend/k8s/02-configmap.yaml (execution image)
# Edit backend/k8s/03-backend.yaml (backend image)

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

# View logs
kubectl logs -l app=backend -n coding-platform --tail=50
```

See **[Complete Setup Guide](docs/SETUP.md)** for detailed deployment instructions.

## 📚 Documentation

### 🚀 Getting Started
- **[Setup Guide](docs/SETUP.md)** - Complete installation and configuration
- **[Features](docs/FEATURES.md)** - Detailed feature documentation
- **[Deployment Guide](docs/deployment/README.md)** - Production deployment strategies

### 🏗️ Technical Reference
- **[Architecture](docs/architecture/ARCHITECTURE.md)** - System design and components
- **[Database](docs/database/DATABASE.md)** - Schema design and data models
- **[API Documentation](docs/api/README.md)** - Complete API reference

### 🔌 API Endpoints
- **[Reviews API](docs/api/reviews.md)** - Code review system endpoints
- **[Users API](docs/api/users.md)** - User management and authentication
- **[Workspace API](docs/api/workspace.md)** - File and session operations
- **[WebSocket API](docs/api/websocket.md)** - Real-time terminal communication

## 🔧 Development

### Running Tests
```bash
# Backend tests
cd backend
venv/bin/python -m pytest tests/ -v

# Frontend linting
cd frontend
npm run lint
npm run type-check
```

### Database Setup
```bash
# Create PostgreSQL database
createdb coolcoding
createuser -s coolcoding_user

# Run migrations (automatic on startup)
python -m app.main
```

## 🔒 Security Features

- **Pod Isolation**: Each session runs in a separate Kubernetes pod with dedicated resources
- **Resource Limits**: CPU (500m), memory (512Mi) per execution pod
- **RBAC**: Backend uses service account with limited Kubernetes API permissions
- **Input Validation**: Comprehensive sanitization of all inputs
- **Path Protection**: Prevention of directory traversal attacks
- **Session Isolation**: User data completely separated in database and pods
- **File System Isolation**: Each pod has dedicated PVC, no host access
- **Network Security**: Kubernetes network policies (configurable)

## 🌟 Key Workflows

### Basic Development Session
1. User registers/logs in to the platform
2. Creates a new workspace session
3. Backend creates dedicated Kubernetes pod for the session
4. Files from PostgreSQL are synced to pod filesystem
5. User writes Python/Node.js code in Monaco editor
6. Executes commands in terminal (runs in pod via kubectl exec)
7. File changes automatically synced back to database
8. Session state persists in PostgreSQL
9. Pod is cleaned up when session ends

### Code Review Process
1. Developer completes code in session
2. Submits code for review with description and priority
3. Available reviewers can claim and review submissions
4. Reviewers examine workspace files and provide line-level feedback
5. Developers receive review comments and can iterate
6. Code is approved or rejected with documented history

### Reviewer System
1. Any user can self-promote to reviewer status (Levels 1-4)
2. Five reviewer levels: 0 (regular), 1 (basic), 2 (intermediate), 3 (advanced), 4 (expert)
3. Reviewers are listed and discoverable
4. Higher-level reviewers can handle more complex reviews
5. Review statistics tracked for accountability

## 🚀 Deployment

### Production Architecture
The platform is designed for Kubernetes deployment with the following components:

**Infrastructure**:
- **Kubernetes Cluster**: DigitalOcean Kubernetes (DOKS), AWS EKS, or GCP GKE
- **Backend**: 2-10 FastAPI pods with horizontal autoscaling
- **Execution Pods**: 1 per active user session (on-demand)
- **Database**: Managed PostgreSQL (DigitalOcean, AWS RDS, Supabase)
- **Load Balancer**: Kubernetes LoadBalancer service
- **Container Registry**: Docker Hub or private registry

**Deployment Targets**:
- **Frontend**: Vercel, Netlify, or Cloudflare Pages
- **Backend**: Kubernetes cluster with HPA
- **Database**: Managed PostgreSQL service

### Scaling Configuration
- **Backend Pods**: Auto-scale 2-10 based on CPU (70%) and memory (80%)
- **Cluster Nodes**: Auto-scale 3-7 based on pod scheduling needs
- **Execution Pods**: Created on-demand, 1 per active session
- **Capacity**: Current config supports 10-40+ concurrent users

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

---

**Built with ❤️ using Next.js, FastAPI, and modern web technologies**