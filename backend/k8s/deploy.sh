#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Code Execution Platform - K8s Deployment${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}Error: kubectl is not installed${NC}"
    echo "Please install kubectl: https://kubernetes.io/docs/tasks/tools/"
    exit 1
fi

# Check if connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: Not connected to a Kubernetes cluster${NC}"
    echo "Please configure kubectl to connect to your cluster"
    exit 1
fi

echo -e "${YELLOW}Current Kubernetes context:${NC}"
kubectl config current-context
echo ""

read -p "Continue with deployment? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

# Deploy namespace
echo -e "\n${GREEN}Creating namespace...${NC}"
kubectl apply -f 00-namespace.yaml

# Deploy RBAC
echo -e "\n${GREEN}Creating RBAC resources...${NC}"
kubectl apply -f 01-rbac.yaml

# Deploy PostgreSQL
echo -e "\n${GREEN}Deploying PostgreSQL...${NC}"
kubectl apply -f 02-postgres.yaml

# Wait for PostgreSQL to be ready
echo -e "\n${YELLOW}Waiting for PostgreSQL to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=postgres -n coding-platform --timeout=120s

# Deploy backend config
echo -e "\n${GREEN}Creating backend configuration...${NC}"
kubectl apply -f 03-backend-config.yaml

# Deploy backend
echo -e "\n${GREEN}Deploying backend...${NC}"
kubectl apply -f 04-backend.yaml

# Wait for backend to be ready
echo -e "\n${YELLOW}Waiting for backend to be ready...${NC}"
kubectl wait --for=condition=ready pod -l app=backend -n coding-platform --timeout=120s

# Show status
echo -e "\n${GREEN}Deployment complete!${NC}\n"
echo -e "${YELLOW}Status:${NC}"
kubectl get pods -n coding-platform
echo ""
kubectl get svc -n coding-platform

echo -e "\n${YELLOW}Getting backend URL...${NC}"
EXTERNAL_IP=$(kubectl get svc backend -n coding-platform -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")
if [ "$EXTERNAL_IP" != "pending" ] && [ -n "$EXTERNAL_IP" ]; then
    echo -e "${GREEN}Backend URL: http://$EXTERNAL_IP${NC}"
    echo -e "\n${YELLOW}Test the API:${NC}"
    echo "curl http://$EXTERNAL_IP/api/health/"
else
    echo -e "${YELLOW}LoadBalancer external IP is pending. Run this command to check:${NC}"
    echo "kubectl get svc backend -n coding-platform"
fi

echo -e "\n${YELLOW}To view logs:${NC}"
echo "kubectl logs -f -l app=backend -n coding-platform"

echo -e "\n${YELLOW}To watch pods:${NC}"
echo "kubectl get pods -n coding-platform --watch"

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment finished successfully!${NC}"
echo -e "${GREEN}========================================${NC}"