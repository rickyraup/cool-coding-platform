# Kubernetes Deployment Guide - Quick Start

This guide will help you deploy the Code Execution Platform on Kubernetes with proper pod isolation for 10 users.

## What You Get

- ✅ **Backend API** - FastAPI application managing sessions
- ✅ **PostgreSQL Database** - Stores user data and workspaces
- ✅ **Dynamic Execution Pods** - Isolated Python environments per user session
- ✅ **Automatic Cleanup** - Idle pods are cleaned up automatically
- ✅ **Resource Limits** - Prevents resource exhaustion

## Prerequisites

1. **Kubernetes Cluster** - Choose one:
   - **DigitalOcean Kubernetes** (Recommended): $12/month
   - **Google Cloud GKE**: ~$25-40/month
   - **Local testing**: kind (free)

2. **Tools Installed**:
   ```bash
   # kubectl
   brew install kubectl

   # Docker
   brew install --cask docker

   # Optional: DigitalOcean CLI
   brew install doctl
   ```

3. **Docker Hub Account** (free): https://hub.docker.com/signup

## Step-by-Step Deployment

### Option A: DigitalOcean (Recommended for Production)

#### 1. Create Cluster
```bash
# Install CLI
brew install doctl

# Login
doctl auth init

# Create cluster (~5 minutes)
doctl kubernetes cluster create coding-platform \
  --region nyc1 \
  --node-pool "name=workers;size=s-2vcpu-2gb;count=1" \
  --wait

# Verify connection
kubectl get nodes
```

#### 2. Build and Push Docker Images
```bash
cd backend

# Run the build script (enter your Docker Hub username when prompted)
./build-and-push.sh

# This will:
# - Build backend image
# - Build executor image (with pandas, scipy, numpy)
# - Push both to Docker Hub
```

#### 3. Update Configuration
```bash
# Update with your Docker Hub username
DOCKER_USERNAME="your-dockerhub-username"

sed -i '' "s|your-dockerhub-username|$DOCKER_USERNAME|g" k8s/04-backend.yaml
sed -i '' "s|your-dockerhub-username|$DOCKER_USERNAME|g" k8s/03-backend-config.yaml

# Update CORS with your Vercel frontend URL
# Edit k8s/03-backend-config.yaml and add your frontend URL
```

#### 4. Deploy to Kubernetes
```bash
# Run deployment script
cd k8s
./deploy.sh

# This will:
# - Create namespace
# - Set up RBAC permissions
# - Deploy PostgreSQL
# - Deploy backend
# - Show you the external IP
```

#### 5. Get Backend URL
```bash
# Wait for LoadBalancer IP (may take 1-2 minutes)
kubectl get svc backend -n coding-platform --watch

# Once you see an EXTERNAL-IP, press Ctrl+C
BACKEND_IP=$(kubectl get svc backend -n coding-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Backend URL: http://$BACKEND_IP"
```

#### 6. Test the Deployment
```bash
# Health check
curl http://$BACKEND_IP/api/health/

# Create test session
curl -X POST http://$BACKEND_IP/api/postgres_sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "name": "Test Session"}'

# Watch execution pods being created
kubectl get pods -n coding-platform --watch
```

#### 7. Update Vercel Frontend
```bash
# In your Vercel dashboard, set environment variable:
NEXT_PUBLIC_API_URL=http://YOUR_BACKEND_IP
```

---

### Option B: Local Testing with kind

Perfect for testing before deploying to production:

```bash
# 1. Create local cluster
kind create cluster --name test-cluster

# 2. Build images (no push needed for local testing)
cd backend
docker build -f Dockerfile.backend -t coding-platform-backend:latest .
docker build -f Dockerfile.executor -t coding-platform-executor:latest .

# 3. Load images into kind
kind load docker-image coding-platform-backend:latest --name test-cluster
kind load docker-image coding-platform-executor:latest --name test-cluster

# 4. Update k8s manifests for local images
sed -i '' 's|your-dockerhub-username/||g' k8s/04-backend.yaml
sed -i '' 's|your-dockerhub-username/||g' k8s/03-backend-config.yaml
sed -i '' 's|imagePullPolicy: Always|imagePullPolicy: Never|g' k8s/04-backend.yaml

# 5. Deploy
cd k8s
kubectl apply -f .

# 6. Forward port to access locally
kubectl port-forward -n coding-platform svc/backend 8002:80

# 7. Test
curl http://localhost:8002/api/health/
```

---

## Monitoring & Maintenance

### Check Status
```bash
# View all pods
kubectl get pods -n coding-platform

# View services
kubectl get svc -n coding-platform

# Check resource usage
kubectl top pods -n coding-platform
kubectl top nodes
```

### View Logs
```bash
# Backend logs
kubectl logs -f -l app=backend -n coding-platform

# PostgreSQL logs
kubectl logs -f -l app=postgres -n coding-platform

# Execution pod logs (replace POD_NAME)
kubectl logs -f session-POD_NAME -n coding-platform

# All logs
kubectl logs -f --all-containers=true -n coding-platform
```

### Common Commands
```bash
# Restart backend
kubectl rollout restart deployment/backend -n coding-platform

# Scale backend
kubectl scale deployment backend -n coding-platform --replicas=2

# Delete old execution pods
kubectl delete pods -l app=session-pod -n coding-platform

# Update backend image
kubectl set image deployment/backend backend=YOUR_USERNAME/coding-platform-backend:latest -n coding-platform
```

---

## Troubleshooting

### Problem: Backend pod not starting
```bash
# Check events
kubectl describe pod -l app=backend -n coding-platform

# Common fixes:
# - Wrong image name: Update k8s/04-backend.yaml
# - Database not ready: Wait for postgres pod to be ready
# - Wrong credentials: Check k8s/03-backend-config.yaml
```

### Problem: Execution pods not creating
```bash
# Check backend logs for errors
kubectl logs -f -l app=backend -n coding-platform | grep -i "pod\|kubernetes"

# Verify RBAC permissions
kubectl get rolebinding backend-pod-manager -n coding-platform

# Common fixes:
# - Wrong service account: Check k8s/01-rbac.yaml
# - Wrong namespace: Check KUBERNETES_NAMESPACE in config
# - Wrong image: Check EXECUTION_IMAGE in config
```

### Problem: Can't connect to backend
```bash
# Check LoadBalancer status
kubectl get svc backend -n coding-platform

# If pending too long (DigitalOcean should be < 2 mins):
kubectl describe svc backend -n coding-platform

# For local testing, use port-forward:
kubectl port-forward -n coding-platform svc/backend 8002:80
```

---

## Costs

### DigitalOcean (Recommended)
- **Cluster**: $12/month (1 node, 2GB RAM)
- **LoadBalancer**: $12/month (automatically created)
- **Total**: ~$24/month for 10 users

### Google Cloud GKE
- **Autopilot**: ~$25-40/month (pay per pod usage)
- **Free tier**: $300 credit for first 90 days

### Optimization Tips
- Start with 1 node, scale up as needed
- Use node autoscaling for burst traffic
- Your code already cleans up idle pods (saves resources)

---

## Next Steps

1. ✅ Deploy backend to Kubernetes
2. ✅ Update Vercel environment variables
3. Test creating sessions from your frontend
4. Monitor resource usage
5. Set up automated backups (see k8s/README.md)
6. Enable HTTPS with cert-manager (production)

---

## Getting Help

- **Kubernetes Issues**: Check `kubectl logs` and `kubectl describe`
- **Backend Issues**: Check backend logs in Kubernetes
- **Detailed Guide**: See `backend/k8s/README.md`
- **DigitalOcean Docs**: https://docs.digitalocean.com/products/kubernetes/

---

## Quick Reference

```bash
# Deploy everything
cd backend/k8s && ./deploy.sh

# Update backend
kubectl set image deployment/backend backend=YOUR_IMAGE -n coding-platform

# View logs
kubectl logs -f -l app=backend -n coding-platform

# Delete everything
kubectl delete namespace coding-platform

# Get backend URL
kubectl get svc backend -n coding-platform
```

Good luck with your deployment! 🚀