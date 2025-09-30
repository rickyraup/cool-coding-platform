#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Docker Image Build and Push Script${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Prompt for Docker Hub username
read -p "Enter your Docker Hub username: " DOCKER_USERNAME

if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${RED}Error: Docker Hub username is required${NC}"
    exit 1
fi

# Docker login
echo -e "\n${YELLOW}Logging into Docker Hub...${NC}"
docker login

# Build backend image
echo -e "\n${GREEN}Building backend image...${NC}"
docker build -f Dockerfile.backend -t $DOCKER_USERNAME/coding-platform-backend:latest .

# Build executor image
echo -e "\n${GREEN}Building executor image...${NC}"
docker build -f Dockerfile.executor -t $DOCKER_USERNAME/coding-platform-executor:latest .

# Push backend image
echo -e "\n${GREEN}Pushing backend image...${NC}"
docker push $DOCKER_USERNAME/coding-platform-backend:latest

# Push executor image
echo -e "\n${GREEN}Pushing executor image...${NC}"
docker push $DOCKER_USERNAME/coding-platform-executor:latest

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Images built and pushed successfully!${NC}"
echo -e "${GREEN}========================================${NC}\n"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update k8s/04-backend.yaml with image: $DOCKER_USERNAME/coding-platform-backend:latest"
echo "2. Update k8s/03-backend-config.yaml with EXECUTION_IMAGE: $DOCKER_USERNAME/coding-platform-executor:latest"
echo "3. Run: ./k8s/deploy.sh"

echo -e "\n${YELLOW}Or update automatically:${NC}"
echo "sed -i '' 's|your-dockerhub-username|$DOCKER_USERNAME|g' k8s/04-backend.yaml"
echo "sed -i '' 's|your-dockerhub-username|$DOCKER_USERNAME|g' k8s/03-backend-config.yaml"