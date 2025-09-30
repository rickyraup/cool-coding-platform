# Code Execution Platform Architecture

## Overview
A full-stack web platform that provides users with an isolated Python development environment featuring a code editor, terminal interface, file management, and code review system. The platform is deployed on Kubernetes with automatic horizontal scaling to support multiple concurrent users.

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
│  ┌──────────────────────┐  │
│  │  Code Review System   │  │ Review workflow + workspace review
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │ HTTP API / WebSocket
             ▼
┌────────────────────────────┐
│    Kubernetes Cluster      │
│   (DigitalOcean DOKS)      │
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
│  │  │ File Sync Svc   │ │  │ Bidirectional DB ↔ Pod file sync
│  │  └─────────────────┘ │  │
│  │  ┌─────────────────┐ │  │
│  │  │ Auth Service    │ │  │ Authentication + reviewer system
│  │  └─────────────────┘ │  │
│  │  ┌─────────────────┐ │  │
│  │  │ Review Service  │ │  │ Code review management
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
│                            │
│  ┌──────────────────────┐  │
│  │ Cluster Autoscaler    │  │ Adds/removes nodes as needed
│  └──────────────────────┘  │
└────────────┬───────────────┘
             │ Database queries
             ▼
┌────────────────────────────┐
│     PostgreSQL Database    │
│   (Managed DigitalOcean)   │
│                            │
│  - users (with reviewer    │
│    level fields)           │
│  - sessions (UUID-based)   │
│  - workspace_items         │
│  - review_requests         │
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
- **Authentication:** Simple username/password (extensible)
- **Orchestration:** Kubernetes for container management
- **WebSocket:** Real-time terminal communication
- **Background Tasks:** Pod lifecycle management via Kubernetes API

### Database (PostgreSQL)
- **Users:** Authentication + reviewer system
- **Sessions:** UUID-based session management
- **Workspace Items:** Hierarchical file storage
- **Review Requests:** Code review workflow
- **Managed Service:** DigitalOcean Managed PostgreSQL

### Infrastructure (Kubernetes on DigitalOcean)
- **Cluster:** DigitalOcean Kubernetes (DOKS)
- **Nodes:** s-2vcpu-2gb droplets (1.9 cores, 1.96Gi each)
- **Node Scaling:** Cluster Autoscaler (3-7 nodes)
- **Execution Isolation:** Per-user Kubernetes pods with PVCs
- **Backend Scaling:** Horizontal Pod Autoscaler (2-10 replicas)
- **Load Balancing:** Kubernetes LoadBalancer Service
- **Container Registry:** Docker Hub (rraup12/coding-platform-backend, rraup12/code-execution)
- **File Storage:** Database-backed with bidirectional pod sync

## Current System Features

### Code Review System
- **Review Workflow:** Submit workspaces for review with priority levels
- **Status Tracking:** pending → in_review → approved/rejected
- **Reviewer Management:** Self-service reviewer promotion system
- **Review Interface:** Dedicated review workspace with read-only code view

### Authentication & Authorization
- **User Management:** Username/password authentication
- **Session Management:** Server-side session tracking
- **Reviewer System:** Multi-level reviewer permissions (Level 1-4)
- **Access Control:** Role-based access to review functions

### Workspace Management
- **Session Isolation:** Each workspace gets unique Kubernetes pod with PVC
- **File Persistence:** Bidirectional sync between database and pod filesystems
- **Real-time Collaboration:** WebSocket-based terminal sharing
- **Pod Lifecycle:** Automatic creation, readiness checks, and cleanup
- **File Sync:** Automatic synchronization after file-modifying commands
- **Storage:** 1Gi PersistentVolumeClaim per execution pod

### API Architecture
- **RESTful Design:** Standard HTTP methods for resource operations
- **WebSocket Integration:** Real-time terminal communication
- **Error Handling:** Consistent error response format
- **Type Safety:** Full TypeScript coverage on frontend

## Security Considerations

### Pod Security
- **Process Isolation:** Each user session runs in separate Kubernetes pod
- **Resource Limits:** Memory (512Mi limit) and CPU (500m limit) per execution pod
- **Network Policies:** Isolated pod networking within Kubernetes
- **File System Isolation:** Each pod has dedicated PVC, no host access
- **Service Account:** Backend pods use RBAC-controlled service account for K8s API access

### Application Security
- **Input Validation:** All user inputs validated on backend
- **SQL Injection Prevention:** Parameterized queries throughout
- **XSS Protection:** Content sanitization on frontend
- **CORS Configuration:** Restricted to allowed origins
- **Command Execution:** All commands executed within isolated pods

### Data Protection
- **Session Security:** Secure session management
- **Code Privacy:** User code only accessible to owner and assigned reviewers
- **Audit Logging:** Pod creation/deletion and review actions logged
- **Data Encryption:** Sensitive data encrypted at rest
- **Secret Management:** Database credentials stored in Kubernetes secrets

## Performance Optimizations

### Pod Management
- **Lazy Loading:** Execution pods created only when workspace is accessed
- **Readiness Checks:** Backend waits for pod ready status before accepting commands
- **Background Cleanup:** Automated pod deletion when sessions end
- **Resource Monitoring:** Kubernetes metrics for pod CPU/memory usage
- **PVC Persistence:** Reusable storage volumes for session continuity

### Horizontal Scaling
- **Backend Autoscaling:** 2-10 replicas based on CPU (70%) and memory (80%) thresholds
- **Load Balancing:** Kubernetes Service distributes traffic across backend pods
- **Cluster Autoscaling:** 3-7 nodes added/removed based on pod scheduling needs
- **Aggressive Scale-Up:** Doubles pods or adds 2 immediately under load
- **Conservative Scale-Down:** 5-minute stabilization, removes 50% or 1 pod gradually
- **Capacity Planning:** Current setup supports 10-40+ concurrent users

### Frontend Performance
- **Code Splitting:** Route-based code splitting with Next.js
- **Caching:** API response caching for static data
- **Optimistic Updates:** Immediate UI feedback for user actions
- **WebSocket Efficiency:** Minimal message overhead

### Database Performance
- **Connection Pooling:** Efficient database connection management
- **Query Optimization:** Indexed queries for common operations
- **Data Modeling:** Normalized schema with appropriate relationships
- **Managed Service:** DigitalOcean managed PostgreSQL with automatic backups

## Kubernetes Deployment Architecture

### Cluster Configuration
- **Provider:** DigitalOcean Kubernetes (DOKS)
- **Region:** Configurable (currently using US regions)
- **Node Pool:** s-2vcpu-2gb droplets
  - CPU: 2 vCPUs (1.9 cores allocatable)
  - Memory: 2GB RAM (1.96Gi allocatable)
  - Nodes: 3-7 (managed by Cluster Autoscaler)

### Backend Deployment
**File:** `backend/k8s/03-backend.yaml`

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
**File:** `backend/k8s/04-hpa.yaml`

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

**How It Works:**
1. Metrics Server collects CPU/memory data from pods
2. HPA calculates average utilization across all backend pods
3. If avg CPU > 70% OR avg memory > 80%: scale up immediately
4. If utilization drops: wait 5 minutes, then scale down gradually
5. Never goes below 2 replicas or above 10 replicas

### Execution Pod Management
**Managed by:** `backend/app/services/kubernetes_client.py`

**Pod Specification:**
- **Name:** exec-{session_id}
- **Image:** rraup12/code-execution:latest
  - Base: Python 3.11
  - Includes: Node.js 20, pandas, scipy, numpy
- **Resources:**
  - CPU Request: 200m, Limit: 500m
  - Memory Request: 256Mi, Limit: 512Mi
- **Storage:** 1Gi PersistentVolumeClaim per pod
- **Lifecycle:**
  1. Created when user opens workspace
  2. Waits for "Running" and "Ready" status
  3. Files synced from database to pod
  4. Accepts terminal commands via WebSocket
  5. Files synced back to database after modifications
  6. Deleted when session ends or user disconnects

### Cluster Autoscaling
**Managed by:** DigitalOcean Cluster Autoscaler

**Behavior:**
- Monitors unschedulable pods (insufficient node resources)
- Adds new nodes when pods are pending due to resource constraints
- Removes unused nodes after sustained low utilization
- Respects min (3) and max (7) node limits

**Example Scaling Scenario:**
1. 10 users → 10 execution pods + 2 backend pods = ~2.5 CPU, 3.5Gi
2. Fits on 3 nodes (5.7 CPU, 5.88Gi available)
3. 30 users → 30 execution pods + 4 backend pods = ~7 CPU, 9Gi
4. Cluster autoscaler adds nodes 4, 5, 6 (21 CPU, 17.6Gi total)
5. All pods scheduled successfully

### File Synchronization
**Service:** `backend/app/services/file_sync.py`

**Database → Pod (on session start):**
1. Query workspace_items for session
2. For each file/folder: create in pod filesystem
3. Use kubectl exec to write file contents
4. Maintain directory structure

**Pod → Database (after commands):**
1. Detect file-modifying commands (touch, echo, python, etc.)
2. List all files in pod workspace using kubectl exec
3. Read file contents from pod
4. Update or create workspace_items in database
5. Mark files as modified with timestamp

**Synced Commands:**
- touch, echo, cat, cp, mv, rm
- python, pip, node, npm
- git, wget, curl
- nano, vim (if used)
- Any command with >, >>, tee

### Deployment Process
**Build & Push Images:**
```bash
# Backend
docker buildx build --platform linux/amd64,linux/arm64 \
  -t rraup12/coding-platform-backend:latest --push backend/

# Execution environment
docker buildx build --platform linux/amd64,linux/arm64 \
  -t rraup12/code-execution:latest --push backend/execution-image/
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

# Check node scaling
kubectl get nodes --watch
```

### Production URLs
- **Backend API:** http://<loadbalancer-ip>/api/
- **WebSocket:** ws://<loadbalancer-ip>/api/terminal/ws/{session_id}
- **Health Check:** http://<loadbalancer-ip>/api/health/

### Capacity Planning
See `CAPACITY-ANALYSIS.md` for detailed resource calculations:
- **10 users:** Runs on 3 nodes comfortably (~50% utilization)
- **50 users:** Requires 7+ nodes (hits current cluster max)
- **Scaling limit:** ~40 users with current config (7 node max)
- **Recommended:** Increase cluster max to 10 nodes for 50+ users
