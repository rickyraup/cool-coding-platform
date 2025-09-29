#!/bin/sh

# Start Docker daemon in background
dockerd &

# Wait for Docker daemon to be ready
until docker info >/dev/null 2>&1; do
    echo "Waiting for Docker daemon to start..."
    sleep 1
done

echo "Docker daemon started successfully"

# Build the Python execution environment image
echo "Building code-platform-python Docker image..."
docker build -t code-platform-python -f /app/Dockerfile.python /app
if [ $? -eq 0 ]; then
    echo "✅ Docker image 'code-platform-python' built successfully"
else
    echo "❌ Failed to build Docker image 'code-platform-python'"
fi

# Start the FastAPI application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}