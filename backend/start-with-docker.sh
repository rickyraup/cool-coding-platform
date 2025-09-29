#!/bin/sh

# Start Docker daemon in background
dockerd &

# Wait for Docker daemon to be ready
until docker info >/dev/null 2>&1; do
    echo "Waiting for Docker daemon to start..."
    sleep 1
done

echo "Docker daemon started successfully"

# Start the FastAPI application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}