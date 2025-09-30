# Kubernetes Deployment Guide

This directory contains Kubernetes manifests for deploying the Code Execution Platform with proper pod isolation.

## Architecture

- **Backend Pod**: FastAPI application that manages user sessions and creates execution pods
- **PostgreSQL Pod**: Database for storing user data, sessions, and workspace files
- **Execution Pods**: Dynamically created Python pods for each user session (created by backend)

## Prerequisites

1. **Kubernetes Cluster** (one of):
   - DigitalOcean Kubernetes (DOKS) - $12/month
   - Google Kubernetes Engine (GKE)
   - Local testing: kind or minikube

2. **kubectl** CLI installed and configured

3. **Docker Hub account** (or other container registry)

4. **Docker** installed locally

## Quick Start

### 1. Build and Push Docker Images

```bash
# Build backend image
cd backend
docker build -f Dockerfile.backend -t YOUR_DOCKERHUB_USERNAME/coding-platform-backend:latest .
docker push YOUR_DOCKERHUB_USERNAME/coding-platform-backend:latest

# Build executor image (for user pods)
docker build -f Dockerfile.executor -t YOUR_DOCKERHUB_USERNAME/coding-platform-executor:latest .
docker push YOUR_DOCKERHUB_USERNAME/coding-platform-executor:latest
```

### 2. Update Configuration

Edit `k8s/03-backend-config.yaml`:
- Update `CORS_ORIGINS` with your Vercel frontend URL
- Update `EXECUTION_IMAGE` with your executor image name

Edit `k8s/04-backend.yaml`:
- Update `image:` with your backend image name

Edit `k8s/02-postgres.yaml`:
- Change `POSTGRES_PASSWORD` in production!

### 3. Deploy to Kubernetes

```bash
# Apply all manifests in order
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-rbac.yaml
kubectl apply -f k8s/02-postgres.yaml
kubectl apply -f k8s/03-backend-config.yaml
kubectl apply -f k8s/04-backend.yaml

# Or deploy all at once
kubectl apply -f k8s/
```

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n coding-platform

# Check services
kubectl get svc -n coding-platform

# Get backend external IP
kubectl get svc backend -n coding-platform

# Watch pod creation
kubectl get pods -n coding-platform --watch

# Check logs
kubectl logs -f deployment/backend -n coding-platform
kubectl logs -f deployment/postgres -n coding-platform
```

### 5. Test Pod Creation

```bash
# Get backend external IP
BACKEND_IP=$(kubectl get svc backend -n coding-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Create a test session
curl -X POST http://$BACKEND_IP/api/postgres_sessions/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "name": "Test Session"}'

# Watch execution pods being created
kubectl get pods -n coding-platform --watch
```

## Configuration

### Environment Variables

All configuration is in `k8s/03-backend-config.yaml`:

| Variable | Description | Default |
|----------|-------------|---------|
| `KUBERNETES_NAMESPACE` | Namespace for execution pods | `coding-platform` |
| `EXECUTION_IMAGE` | Docker image for execution pods | `python:3.11-slim` |
| `CORS_ORIGINS` | Allowed frontend origins | Update this! |
| `DATABASE_URL` | PostgreSQL connection string | Set in secret |

### Secrets

Update passwords in `k8s/02-postgres.yaml` and `k8s/03-backend-config.yaml` before deploying to production!

```bash
# Generate a secure password
openssl rand -base64 32
```

## Scaling

### Scale Backend

```bash
# Scale to 2 replicas
kubectl scale deployment backend -n coding-platform --replicas=2
```

### Scale Nodes

```bash
# DigitalOcean
doctl kubernetes cluster node-pool create coding-platform \
  --name workers \
  --size s-2vcpu-2gb \
  --count 2

# GKE
gcloud container clusters resize coding-platform --num-nodes=2
```

## Monitoring

### Check Resource Usage

```bash
# Pod resource usage
kubectl top pods -n coding-platform

# Node resource usage
kubectl top nodes

# Describe backend pod
kubectl describe pod -l app=backend -n coding-platform
```

### View Logs

```bash
# Backend logs
kubectl logs -f -l app=backend -n coding-platform

# User execution pod logs (replace POD_NAME)
kubectl logs -f session-POD_NAME -n coding-platform

# Stream logs from all pods
kubectl logs -f --all-containers=true -l app=backend -n coding-platform
```

## Troubleshooting

### Backend Pod Not Starting

```bash
# Check events
kubectl describe pod -l app=backend -n coding-platform

# Check logs
kubectl logs -l app=backend -n coding-platform

# Common issues:
# - Image pull errors: Check Docker Hub credentials
# - Database connection: Check postgres service is running
```

### Execution Pods Not Creating

```bash
# Check backend has proper RBAC permissions
kubectl get rolebinding backend-pod-manager -n coding-platform

# Check service account
kubectl get sa backend-sa -n coding-platform

# Check backend logs for errors
kubectl logs -f -l app=backend -n coding-platform | grep -i "kubernetes"
```

### Database Connection Issues

```bash
# Check postgres is running
kubectl get pods -l app=postgres -n coding-platform

# Test connection from backend pod
kubectl exec -it deployment/backend -n coding-platform -- \
  python -c "import psycopg2; psycopg2.connect('postgresql://postgres:PASSWORD@postgres:5432/coding_platform')"
```

## Cleanup

### Delete Everything

```bash
# Delete all resources
kubectl delete namespace coding-platform

# Or delete individually
kubectl delete -f k8s/
```

### Delete Only Execution Pods

```bash
# Delete all session pods
kubectl delete pods -l app=session-pod -n coding-platform

# Delete specific session pod
kubectl delete pod session-POD_NAME -n coding-platform
```

## Production Recommendations

1. **Use Managed Database**: Instead of in-cluster PostgreSQL, use:
   - DigitalOcean Managed Database
   - Google Cloud SQL
   - AWS RDS

2. **Use Container Registry**: Push images to private registry:
   - Google Container Registry (GCR)
   - AWS ECR
   - DigitalOcean Container Registry

3. **Enable TLS**: Use cert-manager for automatic HTTPS certificates

4. **Set Resource Limits**: Update resource requests/limits based on usage

5. **Enable Monitoring**: Install Prometheus + Grafana for metrics

6. **Backup Database**: Set up automated PostgreSQL backups

7. **Use Secrets Management**: Use external secrets operator or vault

## Cost Optimization

For 10 users:
- Start with 1 node (2GB RAM, 2 vCPU)
- Set pod resource limits to prevent over-provisioning
- Use node autoscaling if usage is bursty
- Clean up idle execution pods (your code already does this)

## Support

- Check backend logs: `kubectl logs -f -l app=backend -n coding-platform`
- Check GitHub issues: https://github.com/your-repo/issues
- Review Kubernetes docs: https://kubernetes.io/docs/