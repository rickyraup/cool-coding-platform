"""Main FastAPI application for the Code Execution Platform."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    health,
    postgres_sessions,
    session_workspace,
    sessions,
    users,
    workspace,
)
from app.core.postgres import init_db
from app.core.session_manager import session_manager
from app.websockets.handlers import handle_websocket_message
from app.websockets.manager import WebSocketManager


# Load environment variables
load_dotenv()

# Initialize WebSocket manager
websocket_manager = WebSocketManager()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    from app.services.background_tasks import background_task_manager

    init_db()
    print("🗄️ Database initialized")
    print("🚀 Session manager ready")

    # Start background tasks for container management
    print("🐳 Starting container lifecycle background tasks...")
    await background_task_manager.start_background_tasks()

    yield
    # Shutdown
    print("🔄 Shutting down...")
    print("🧹 Cleaning up active sessions and stopping background tasks...")
    await background_task_manager.stop_background_tasks()
    await session_manager.cleanup_all_sessions()
    print("✅ Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="Code Execution Platform API",
    description="Backend API for the code execution platform with integrated terminal",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])

# PostgreSQL-based routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(
    postgres_sessions.router,
    prefix="/api/postgres_sessions",
    tags=["postgres_sessions"],
)
app.include_router(workspace.router, prefix="/api/workspace", tags=["workspace"])
app.include_router(
    session_workspace.router,
    prefix="/api/session_workspace",
    tags=["session_workspace"],
)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket_manager.connect(websocket)

    # Send initial connection confirmation
    await websocket_manager.send_personal_message(
        websocket,
        {
            "type": "connection_established",
            "message": "WebSocket connected successfully",
            "timestamp": "2024-01-01T00:00:00Z",
        },
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            print(f"🔍 WebSocket received data: {data}")

            # Handle the message
            response = await handle_websocket_message(data, websocket)
            print(f"🔍 WebSocket handler response: {response}")

            # Send response back to client
            if response:
                await websocket_manager.send_personal_message(websocket, response)

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        print("WebSocket client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "message": "Code Execution Platform API",
        "status": "running",
        "docs": "/docs",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Disable reload for stable WebSocket connections
    # Use ENABLE_RELOAD=true env var to enable during development
    enable_reload = os.getenv("ENABLE_RELOAD", "false").lower() == "true"

    uvicorn_config = {
        "host": "0.0.0.0",
        "port": port,
        "log_level": "info",
    }

    if enable_reload:
        uvicorn_config.update(
            {
                "reload": True,
                "reload_dirs": ["app/"],
                "reload_excludes": ["venv/", "*.db", "__pycache__/", ".git/", "*.pyc"],
            },
        )
        print("🔄 Running in development mode with auto-reload")
    else:
        print("🚀 Running in production mode (stable WebSocket connections)")

    uvicorn.run("app.main:app", **uvicorn_config)
