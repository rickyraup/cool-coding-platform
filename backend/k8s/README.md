# Kubernetes Deployment Guide

Complete deployment configuration for the Code Execution Platform on Kubernetes.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment Steps](#deployment-steps)
- [Configuration Files](#configuration-files)
- [Auto-Scaling](#auto-scaling)
- [Secret Management](#secret-management)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured with cluster access
- Metrics Server installed (for HPA auto-scaling)
- Ingress controller (if using 07-ingress.yaml)

## Quick Start

```bash
# 1. Create namespace
kubectl apply -f 01-namespace.yaml

# 2. Set up RBAC
kubectl apply -f 02-rbac.yaml

# 3. Create ConfigMap
kubectl apply -f 03-backend-config.yaml

# 4. Create Secrets (IMPORTANT: Do this before deploying!)
kubectl create secret generic backend-secret \
  --from-literal=DATABASE_URL='postgresql://user:password@host:port/dbname' \
  --namespace=coding-platform

# 5. Deploy backend
kubectl apply -f 04-backend.yaml

# 6. Set up auto-scaling
kubectl apply -f 05-hpa.yaml

# 7. (Optional) Let's Encrypt for TLS
kubectl apply -f 06-letsencrypt.yaml

# 8. (Optional) Ingress for external access
kubectl apply -f 07-ingress.yaml
```

## Deployment Steps

### Step 1: Create Namespace

```bash
kubectl apply -f 01-namespace.yaml
```

Creates the `coding-platform` namespace for resource isolation.

### Step 2: Set Up RBAC

```bash
kubectl apply -f 02-rbac.yaml
```

Creates:
- Service account `backend-sa`
- Role with permissions to manage pods and PVCs
- RoleBinding to associate them

### Step 3: Create ConfigMap

```bash
kubectl apply -f 03-backend-config.yaml
```

Non-sensitive configuration:
- Kubernetes namespace
- Execution container image
- CORS origins
- Environment (production/development)

### Step 4: Create Secrets

**NEVER commit actual secrets to version control!**

#### Option A: Using kubectl (Recommended for Production)

```bash
kubectl create secret generic backend-secret \
  --from-literal=DATABASE_URL='your-actual-connection-string' \
  --namespace=coding-platform
```

#### Option B: Using Secret File (Local Development)

```bash
# Copy example and edit
cp 03-backend-secrets.yaml.example 03-backend-secrets.yaml
# Edit with actual values
nano 03-backend-secrets.yaml
# Apply
kubectl apply -f 03-backend-secrets.yaml
```

#### Option C: External Secret Management (Production Best Practice)

Use AWS Secrets Manager, HashiCorp Vault, Azure Key Vault, or Google Secret Manager with External Secrets Operator.

Example with External Secrets Operator:
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: backend-secret
  namespace: coding-platform
spec:
  secretStoreRef:
    name: aws-secretsmanager
    kind: SecretStore
  target:
    name: backend-secret
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: coding-platform/database-url
```

### Step 5: Deploy Backend Application

```bash
kubectl apply -f 04-backend.yaml
```

Deploys:
- **Deployment**: 2 backend pods (min replicas for high availability)
- **Service**: LoadBalancer exposing port 80 → 8002

**Resource Limits per Pod**:
- CPU: 250m request, 1000m limit
- Memory: 512Mi request, 1Gi limit

**Health Checks**:
- Liveness probe: `/api/health/` every 10s
- Readiness probe: `/api/health/` every 5s

### Step 6: Set Up Horizontal Pod Autoscaler

```bash
kubectl apply -f 05-hpa.yaml
```

**Auto-scaling Configuration**:
- **Min replicas**: 2 (maintains 2 pods for redundancy)
- **Max replicas**: 10 (scales up to 10 under heavy load)
- **CPU threshold**: 70% average utilization
- **Memory threshold**: 80% average utilization

**Scaling Behavior**:
- **Scale Up**: Immediate, doubles pods or adds 2 (whichever is more)
- **Scale Down**: 5-minute stabilization, removes 50% or 1 pod (whichever is less)

### Step 7: Let's Encrypt (Optional)

```bash
kubectl apply -f 06-letsencrypt.yaml
```

Sets up automatic TLS certificate issuance via Let's Encrypt.

### Step 8: Ingress (Optional)

```bash
kubectl apply -f 07-ingress.yaml
```

Configures external access rules for the backend service.

## Configuration Files

| File | Purpose | Required |
|------|---------|----------|
| `01-namespace.yaml` | Creates `coding-platform` namespace | ✅ Yes |
| `02-rbac.yaml` | Service account + permissions for pod/PVC management | ✅ Yes |
| `03-backend-config.yaml` | Non-sensitive configuration (ConfigMap) | ✅ Yes |
| `03-backend-secrets.yaml.example` | Secret template - DO NOT commit with real values | 📝 Template |
| `04-backend.yaml` | Backend Deployment + Service (2 initial replicas) | ✅ Yes |
| `05-hpa.yaml` | Horizontal Pod Autoscaler (2-10 pods) | ✅ Yes |
| `06-letsencrypt.yaml` | Let's Encrypt certificate issuer | ⚙️ Optional |
| `07-ingress.yaml` | Ingress rules for external access | ⚙️ Optional |

## Auto-Scaling

### How It Works

The platform automatically scales based on resource utilization:

1. **User 1-2 connect** → 2 backend pods handle requests
2. **Users 3-10 connect** → Load increases across pods
3. **CPU > 70% or Memory > 80%** → HPA triggers scale-up
4. **New pods added** → Load distributed across 4, 6, 8, or 10 pods
5. **Load decreases** → After 5min stabilization, HPA scales down
6. **Maintains minimum 2 pods** → For high availability

### Capacity Planning

**Current setup handles**:
- 2-20 simultaneous users with baseline config
- Can burst to 100+ users (scales to 10 pods)
- High availability (2+ pods always running)

### Testing Auto-Scaling

```bash
# Watch HPA status
kubectl get hpa backend-hpa -n coding-platform -w

# Monitor pod scaling
kubectl get pods -n coding-platform -l app=backend -w

# Check current metrics
kubectl top pods -n coding-platform -l app=backend

# Load test with Apache Bench
ab -n 1000 -c 50 https://your-domain.com/api/health/
```

### Cost Optimization

Adjust HPA settings based on your needs:

```yaml
# For budget-constrained deployments
minReplicas: 1  # Accept some downtime during pod failures
maxReplicas: 5  # Limit maximum scaling

# For high-traffic production
minReplicas: 3  # Extra redundancy
maxReplicas: 15 # Handle larger spikes
```

## Secret Management

### Best Practices

1. **Never commit secrets to Git** - Use `.gitignore`
2. **Use external secret managers** in production
3. **Rotate secrets regularly** - Update credentials periodically
4. **Limit secret access** - Use RBAC to control who can read secrets
5. **Audit secret access** - Enable Kubernetes audit logging

### Verifying Secrets

```bash
# List secrets (values are hidden)
kubectl get secrets -n coding-platform

# Describe secret (shows keys, not values)
kubectl describe secret backend-secret -n coding-platform

# View secret value (base64 encoded)
kubectl get secret backend-secret -n coding-platform -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

### Updating Secrets

When you need to update environment variables like DATABASE_URL:

```bash
# Method 1: Create/update secret directly (recommended)
kubectl create secret generic backend-secret \
  --from-literal=DATABASE_URL='postgresql://user:password@host:port/database' \
  --namespace=coding-platform \
  --dry-run=client -o yaml | kubectl apply -f -

# Method 2: Using a YAML file
cat > /tmp/backend-secret.yaml <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: backend-secret
  namespace: coding-platform
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@host:port/database"
EOF

kubectl apply -f /tmp/backend-secret.yaml
rm /tmp/backend-secret.yaml

# After updating the secret, restart pods to pick up changes
kubectl rollout restart deployment/backend -n coding-platform

# Wait for rollout to complete
kubectl rollout status deployment/backend -n coding-platform --timeout=120s

# Verify pods are running
kubectl get pods -n coding-platform -l app=backend

# Check logs to verify database connection
kubectl logs -l app=backend -n coding-platform --tail=30
```

**Note**: Pods don't automatically detect secret changes - you must restart them using `kubectl rollout restart`.

## Monitoring

### Health Checks

```bash
# Check all pods
kubectl get pods -n coding-platform

# Check deployment status
kubectl get deployments -n coding-platform

# Check HPA status
kubectl get hpa -n coding-platform

# Check service endpoints
kubectl get svc backend -n coding-platform
```

### Logs

```bash
# View logs from all backend pods
kubectl logs -f deployment/backend -n coding-platform

# View logs from specific pod
kubectl logs <pod-name> -n coding-platform

# View logs from previous crashed pod
kubectl logs <pod-name> -n coding-platform --previous

# Stream logs from all pods
kubectl logs -f -l app=backend -n coding-platform
```

### Resource Usage

```bash
# Check pod resource usage
kubectl top pods -n coding-platform

# Check node resource usage
kubectl top nodes

# Detailed HPA metrics
kubectl describe hpa backend-hpa -n coding-platform
```

### Events

```bash
# View recent cluster events
kubectl get events -n coding-platform --sort-by='.lastTimestamp'

# Watch events in real-time
kubectl get events -n coding-platform -w
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status and events
kubectl describe pod <pod-name> -n coding-platform

# Common issues:
# - ImagePullBackOff: Check image name/tag
# - CrashLoopBackOff: Check logs for errors
# - Pending: Insufficient resources or scheduling issues
```

### Secret Not Found

```bash
# Verify secret exists
kubectl get secret backend-secret -n coding-platform

# If missing, create it
kubectl create secret generic backend-secret \
  --from-literal=DATABASE_URL='your-connection-string' \
  --namespace=coding-platform
```

### HPA Not Scaling

```bash
# Check metrics server is running
kubectl get deployment metrics-server -n kube-system

# Verify metrics API works
kubectl top nodes
kubectl top pods -n coding-platform

# Check HPA status and conditions
kubectl describe hpa backend-hpa -n coding-platform

# If HPA shows <unknown>:
# - Metrics server might not be installed
# - Resource requests must be set (already configured in 04-backend.yaml)
```

### Service Not Accessible

```bash
# Check service endpoints
kubectl get endpoints backend -n coding-platform

# If no endpoints, pods aren't ready - check pod status
kubectl get pods -n coding-platform -l app=backend

# Test service from inside cluster
kubectl run -it --rm debug --image=busybox --restart=Never -- \
  wget -O- http://backend.coding-platform.svc.cluster.local
```

### Database Connection Issues

```bash
# Verify secret is correctly set
kubectl get secret backend-secret -n coding-platform -o yaml

# Check pod logs for connection errors
kubectl logs deployment/backend -n coding-platform | grep -i "database\|connection"

# Test from pod
kubectl exec -it <pod-name> -n coding-platform -- env | grep DATABASE_URL
```

## Security

### Security Best Practices

1. **RBAC**: Limit service account permissions to only what's needed
2. **Network Policies**: Restrict pod-to-pod communication
3. **Pod Security Standards**: Enable admission controllers
4. **Secret Management**: Use external secret managers in production
5. **TLS**: Enable TLS for all external communication
6. **Audit Logging**: Track all API server access
7. **Regular Updates**: Keep Kubernetes and images updated
8. **Resource Limits**: Prevent resource exhaustion attacks

### Network Policies (Example)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-netpol
  namespace: coding-platform
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 8002
  egress:
  - to:
    - namespaceSelector: {}
  - to:  # Allow external database access
    ports:
    - protocol: TCP
      port: 5432
```

## Cleanup

### Delete Everything

```bash
# Delete entire namespace (removes all resources)
kubectl delete namespace coding-platform
```

### Delete Individual Resources

```bash
# Delete in reverse order
kubectl delete -f 07-ingress.yaml
kubectl delete -f 06-letsencrypt.yaml
kubectl delete -f 05-hpa.yaml
kubectl delete -f 04-backend.yaml
kubectl delete secret backend-secret -n coding-platform
kubectl delete -f 03-backend-config.yaml
kubectl delete -f 02-rbac.yaml
kubectl delete -f 01-namespace.yaml
```

## Updates and Rollbacks

### Updating Deployment

```bash
# Update image
kubectl set image deployment/backend backend=rraup12/coding-platform-backend:v2.0 -n coding-platform

# Or edit directly
kubectl edit deployment backend -n coding-platform

# Watch rollout
kubectl rollout status deployment/backend -n coding-platform
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/backend -n coding-platform

# Rollback to previous version
kubectl rollout undo deployment/backend -n coding-platform

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n coding-platform
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Horizontal Pod Autoscaler](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [External Secrets Operator](https://external-secrets.io/)
- [Let's Encrypt](https://letsencrypt.org/)
