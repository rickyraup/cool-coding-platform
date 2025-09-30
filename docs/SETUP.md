# Code Execution Platform - Setup Guide

## Prerequisites

### Local Development
- **Node.js:** 18+ (for frontend)
- **Python:** 3.9+ (for backend)
- **PostgreSQL:** 14+ (database)
- **Git:** For version control

### Kubernetes Deployment (Production)
- **Kubernetes Cluster:** DigitalOcean Kubernetes (DOKS) or similar
- **kubectl:** Kubernetes CLI tool
- **Docker:** For building and pushing images
- **Docker Hub Account:** For container registry
- **PostgreSQL:** Managed database (DigitalOcean, AWS RDS, etc.)

## Architecture Overview

The platform uses different execution environments:
- **Local Development**: Docker containers for code execution (optional)
- **Production**: Kubernetes pods for code execution (required)

### Production Infrastructure
- **Backend**: 2-10 FastAPI pods (horizontally scaled)
- **Execution Pods**: 1 per active user session
- **Database**: PostgreSQL (managed service)
- **Load Balancer**: Kubernetes LoadBalancer service
- **Autoscaling**: HPA for backend, cluster autoscaler for nodes

---

## Local Development Setup

### Environment Setup

## Backend Setup

### 1. Database Setup
```bash
# Install PostgreSQL (macOS with Homebrew)
brew install postgresql
brew services start postgresql

# Create database and user
createdb coolcoding
createuser -s coolcoding_user
```

### 2. Backend Installation
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Database Migration
```bash
# Run migrations to set up database schema
python -m app.core.database
```

### 4. Start Backend Server
```bash
# Development mode
python -m app.main

# The API will be available at http://localhost:8002
```

## Frontend Setup

### 1. Frontend Installation
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API URL
```

### 2. Start Development Server
```bash
# Development mode with Turbopack
npm run dev

# The app will be available at http://localhost:3000
```

## Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://coolcoding_user:password@localhost/coolcoding
ENVIRONMENT=development
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8002
```

## Development Workflow

### 1. Start Services
```bash
# Terminal 1: Database
brew services start postgresql

# Terminal 2: Backend
cd backend && source venv/bin/activate && python -m app.main

# Terminal 3: Frontend
cd frontend && npm run dev
```

### 2. Access Application
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8002
- **API Docs:** http://localhost:8002/docs

## Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```

### Frontend Linting
```bash
cd frontend
npm run lint
npm run type-check
```

## Docker Setup (Optional)

### Container-based Development
```bash
# Build and run with Docker Compose
docker-compose up --build

# For testing with isolated database
docker-compose -f docker-compose.test.yml up --build
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running
   - Verify database credentials in .env
   - Check if database exists

2. **Port Conflicts**
   - Backend default: 8002
   - Frontend default: 3000
   - Change ports in configuration if needed

3. **Docker Issues**
   - Ensure Docker daemon is running
   - Check container logs for errors
   - Verify file permissions for volumes

### Logs and Debugging
- **Backend logs:** Check console output
- **Frontend logs:** Check browser console
- **Database logs:** Check PostgreSQL logs
- **Container logs:** `docker logs <container_name>`

## Kubernetes Production Deployment

### 1. Prerequisites
```bash
# Install kubectl
brew install kubectl  # macOS
# Or follow: https://kubernetes.io/docs/tasks/tools/

# Set up DigitalOcean CLI (optional)
brew install doctl
doctl auth init

# Install Docker with buildx for multi-platform builds
docker buildx create --use
```

### 2. Database Setup
Create a managed PostgreSQL database:
```bash
# DigitalOcean example
doctl databases create coolcoding-db --engine pg --version 14 --region nyc1

# Get connection details
doctl databases connection coolcoding-db
```

### 3. Build and Push Container Images
```bash
# Backend image
cd backend
docker buildx build --platform linux/amd64,linux/arm64 \
  -t <your-dockerhub-username>/coding-platform-backend:latest \
  --push .

# Execution environment image
cd execution-image
docker buildx build --platform linux/amd64,linux/arm64 \
  -t <your-dockerhub-username>/code-execution:latest \
  --push .
```

### 4. Create Kubernetes Cluster
```bash
# DigitalOcean Kubernetes
doctl kubernetes cluster create coolcoding-cluster \
  --region nyc1 \
  --node-pool "name=pool-2vcpu;size=s-2vcpu-2gb;count=3;auto-scale=true;min-nodes=3;max-nodes=7"

# Connect kubectl to cluster
doctl kubernetes cluster kubeconfig save coolcoding-cluster
```

### 5. Configure Kubernetes Resources
Update `backend/k8s/` files with your values:

**00-namespace.yaml** - Already configured

**01-secrets.yaml**
```yaml
stringData:
  DATABASE_URL: "postgresql://user:pass@host:port/db"
```

**02-configmap.yaml**
```yaml
data:
  KUBERNETES_NAMESPACE: "default"
  EXECUTION_IMAGE: "<your-dockerhub-username>/code-execution:latest"
  CORS_ORIGINS: "https://your-frontend-domain.com"
```

**03-backend.yaml**
```yaml
image: <your-dockerhub-username>/coding-platform-backend:latest
```

### 6. Deploy to Kubernetes
```bash
# Apply all Kubernetes configurations
kubectl apply -f backend/k8s/

# Wait for backend to be ready
kubectl rollout status deployment/backend -n coding-platform

# Check pod status
kubectl get pods -n coding-platform

# Get LoadBalancer IP
kubectl get svc backend -n coding-platform
```

### 7. Verify Deployment
```bash
# Check HPA status
kubectl get hpa -n coding-platform

# View logs
kubectl logs -l app=backend -n coding-platform --tail=50

# Test health endpoint
curl http://<LOADBALANCER-IP>/api/health/
```

### 8. Frontend Deployment
Update frontend environment variables:
```env
NEXT_PUBLIC_API_URL=http://<LOADBALANCER-IP>
NEXT_PUBLIC_WS_URL=ws://<LOADBALANCER-IP>
```

Build and deploy frontend (Vercel, Netlify, etc.):
```bash
cd frontend
npm run build
# Deploy to your hosting platform
```

### Production Environment Variables

**Backend (Kubernetes Secrets & ConfigMaps)**:
```yaml
# Secrets (01-secrets.yaml)
DATABASE_URL: postgresql://user:pass@host:port/db

# ConfigMap (02-configmap.yaml)
KUBERNETES_NAMESPACE: default
EXECUTION_IMAGE: your-dockerhub/code-execution:latest
CORS_ORIGINS: https://your-domain.com
FASTAPI_ENV: production
```

**Frontend (.env.production)**:
```env
NEXT_PUBLIC_API_URL=http://<LOADBALANCER-IP>
NEXT_PUBLIC_WS_URL=ws://<LOADBALANCER-IP>
```

### Scaling and Monitoring

**Monitor Scaling**:
```bash
# Watch HPA metrics
kubectl get hpa -n coding-platform --watch

# Watch pod scaling
kubectl get pods -n coding-platform -l app=backend --watch

# Check node scaling
kubectl get nodes --watch

# View resource usage
kubectl top nodes
kubectl top pods -n coding-platform
```

**Adjust Scaling**:
```bash
# Manually scale backend
kubectl scale deployment backend --replicas=5 -n coding-platform

# Update HPA thresholds
kubectl edit hpa backend-hpa -n coding-platform
```

### Security Considerations
- **Database**: Use managed database with SSL/TLS
- **Secrets**: Store sensitive data in Kubernetes secrets
- **RBAC**: Backend uses service account with limited permissions
- **Network**: Configure network policies if needed
- **Images**: Use private registry or trusted public images
- **Resource Limits**: Pods have CPU/memory limits to prevent abuse
- **Updates**: Use rolling updates for zero-downtime deployments

## Additional Resources

### 📚 Documentation
- **[API Documentation](http://localhost:8002/docs)** - Interactive API docs (when running)
- **[Complete API Reference](./api/README.md)** - Comprehensive API documentation
- **[Architecture Overview](./architecture/ARCHITECTURE.md)** - System design and components
- **[Database Schema](./database/DATABASE.md)** - Data models and relationships
- **[Feature Guide](./FEATURES.md)** - Detailed feature descriptions
- **[Deployment Guide](./deployment/README.md)** - Production deployment strategies

### 🔌 API References
- **[Reviews API](./api/reviews.md)** - Code review system endpoints
- **[Users API](./api/users.md)** - User management and authentication
- **[Workspace API](./api/workspace.md)** - File and session operations
- **[WebSocket API](./api/websocket.md)** - Real-time terminal communication