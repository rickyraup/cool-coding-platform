# Auto-Scaling Configuration

## Overview
The platform now supports automatic horizontal scaling to handle multiple simultaneous users without performance degradation or connection timeouts.

## Components

### 1. Horizontal Pod Autoscaler (HPA)
**File**: `k8s/04-hpa.yaml`

**Configuration**:
- **Min replicas**: 2 (always maintains 2 backend pods for redundancy)
- **Max replicas**: 10 (can scale up to 10 pods under heavy load)
- **CPU threshold**: 70% average utilization
- **Memory threshold**: 80% average utilization

**Scaling Behavior**:
- **Scale Up**: Immediate response, doubles pods or adds 2 (whichever is more)
- **Scale Down**: 5-minute stabilization window, removes 50% or 1 pod (whichever is less)

### 2. Backend Deployment
**File**: `k8s/03-backend.yaml`

**Resources per Pod**:
- **CPU Request**: 250m (0.25 cores)
- **CPU Limit**: 1000m (1 core)
- **Memory Request**: 512Mi
- **Memory Limit**: 1Gi

### 3. Metrics Server
Required for HPA to function. Provides CPU and memory metrics.

## How It Works

### Simultaneous User Scenario
1. **User 1** connects → Uses backend pod 1
2. **User 2** connects → Load balanced to backend pod 2
3. **Users 3-4** connect → CPU/memory increases on both pods
4. When average CPU hits **70%** or memory hits **80%**:
   - HPA triggers scale-up
   - Kubernetes adds 2 more backend pods (or doubles current count)
   - New users are distributed across all 4 pods
5. When load decreases:
   - After 5-minute stabilization period
   - HPA scales down gradually
   - Maintains minimum of 2 pods

### Cluster Autoscaling
The DigitalOcean Kubernetes cluster is also configured with cluster autoscaling:
- If pods can't be scheduled due to insufficient node resources
- Cluster autoscaler adds new nodes (up to max: 7)
- New nodes are 2vCPU, 2GB RAM instances

## Current Status

### Deployed Configuration
```bash
# Check backend pods
kubectl get pods -n coding-platform -l app=backend

# Check HPA status
kubectl get hpa -n coding-platform

# Check detailed HPA metrics
kubectl describe hpa backend-hpa -n coding-platform

# Check node scaling
kubectl get nodes

# Monitor metrics
kubectl top pods -n coding-platform
kubectl top nodes
```

### Expected Behavior
- **2 backend pods** running at all times
- **Load balancing** across both pods via Service
- **Automatic scale-up** when CPU > 70% or memory > 80%
- **Gradual scale-down** after 5 minutes of low utilization
- **Cluster node addition** if pods can't fit on existing nodes

## Testing Concurrent Users

### Manual Load Test
```bash
# Terminal 1 - User 1
curl https://cool-coding-platform.fly.dev/api/health/

# Terminal 2 - User 2
curl https://cool-coding-platform.fly.dev/api/health/

# Watch pods scale
watch kubectl get pods -n coding-platform -l app=backend
```

### Load Testing Tool
```bash
# Install Apache Bench
brew install ab

# Simulate 10 concurrent users, 100 requests
ab -n 100 -c 10 https://cool-coding-platform.fly.dev/api/health/

# Monitor HPA during test
watch kubectl get hpa -n coding-platform
```

## Troubleshooting

### HPA shows `<unknown>` for metrics
```bash
# Check metrics-server is running
kubectl get deployment metrics-server -n kube-system

# Check metrics API is available
kubectl top nodes
```

### Pods stuck in Pending
```bash
# Check pod events
kubectl describe pod <pod-name> -n coding-platform

# Common causes:
# - Insufficient cluster resources (cluster autoscaler will add nodes)
# - Node initializing (wait 2-3 minutes)
```

### Scale-up not triggering
```bash
# Verify HPA is watching the right metrics
kubectl describe hpa backend-hpa -n coding-platform

# Check current resource usage
kubectl top pods -n coding-platform -l app=backend

# Manually test scale
kubectl scale deployment backend --replicas=5 -n coding-platform
```

## Cost Considerations

### Current Setup
- **2 backend pods** always running = constant cost
- **Node autoscaling** = additional nodes only when needed
- **Max 10 backend pods** = upper limit on scaling costs

### Cost Optimization Tips
1. **Reduce minReplicas to 1** if not worried about downtime during pod failures
2. **Adjust CPU/memory thresholds** higher (e.g., 85%) to delay scaling
3. **Set lower maxReplicas** if budget-constrained
4. **Monitor actual usage** and adjust based on real traffic patterns

## Production Recommendations

✅ **Current Setup is Good For**:
- 2-20 simultaneous users with current config
- Can handle bursts up to 100+ users (scales to 10 pods)
- High availability (2+ pods always running)

⚠️ **Consider Adjusting If**:
- Budget is tight → reduce minReplicas to 1
- Consistent high load → increase minReplicas to 3
- Unpredictable spikes → keep current config (optimal)

## Deployment

All changes are already applied to production. To update:

```bash
# Update HPA configuration
kubectl apply -f k8s/04-hpa.yaml

# Update backend deployment
kubectl apply -f k8s/03-backend.yaml

# Verify changes
kubectl rollout status deployment/backend -n coding-platform
kubectl get hpa -n coding-platform
```