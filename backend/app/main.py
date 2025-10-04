"""Main FastAPI application for the Code Execution Platform."""

import asyncio
import os
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from typing import Any, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    health,
    sessions,
    users,
    workspace_files,
)
from app.core.postgres import init_db
from app.services.container_manager import container_manager
from app.websockets.handlers import handle_websocket_message
from app.websockets.manager import WebSocketManager

# Load environment variables
load_dotenv()

# Initialize WebSocket manager
websocket_manager = WebSocketManager()


def create_unique_session_id(
    base_session_id: str,
    user_id: Optional[str] = None,
) -> str:
    """Create a unique session ID that includes user ID and timestamp to prevent reuse."""
    timestamp = int(time.time() * 1000)  # milliseconds
    unique_id = str(uuid.uuid4())[:8]  # short UUID

    # Include user_id in session ID for better isolation
    if user_id:
        return f"user_{user_id}_ws_{base_session_id}_{timestamp}_{unique_id}"
    return f"{base_session_id}_{timestamp}_{unique_id}"


async def cleanup_websocket_session(websocket: WebSocket, reason: str = "") -> None:
    """Clean up WebSocket session and associated container if needed."""
    # Get session ID before disconnecting
    session_id = websocket_manager.get_session(websocket)
    websocket_manager.disconnect(websocket)

    # Clean up container if no other connections to this session
    if (
        session_id != "default"
        and not websocket_manager.has_other_connections_to_session(session_id)
    ):
        try:
            await container_manager.cleanup_session(session_id)
        except Exception:
            pass  # Cleanup errors are non-fatal


async def check_and_notify_pod_ready(session_id: str, websocket: WebSocket) -> None:
    """Background task to check pod readiness and notify frontend."""
    max_wait = 60  # 60 seconds max wait
    check_interval = 2  # Check every 2 seconds
    elapsed = 0

    while elapsed < max_wait:
        await asyncio.sleep(check_interval)
        elapsed += check_interval

        # Clear previous progress line and send new progress update
        try:
            # First clear the previous line
            if elapsed > check_interval:
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "terminal_clear_progress",
                        "sessionId": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

            # Then send new progress
            await websocket_manager.send_personal_message(
                websocket,
                {
                    "type": "terminal_output",
                    "sessionId": session_id,
                    "output": f"⏳ Initializing environment... ({elapsed}s)",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception:
            break

        # Check if pod is ready
        session = await container_manager.get_or_create_session(session_id)
        if session and container_manager.is_pod_ready(session_id):
            try:
                # Clear all progress messages
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "terminal_clear_progress",
                        "sessionId": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )

                # Send pod ready notification
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "pod_ready",
                        "sessionId": session_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                )
            except Exception:
                break

            # Pod is ready, exit the loop
            break

    if elapsed >= max_wait:
        # Timeout - send error
        with suppress(Exception):
            await websocket_manager.send_personal_message(
                websocket,
                {
                    "type": "terminal_output",
                    "sessionId": session_id,
                    "output": "❌ Environment initialization timed out",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    from app.services.background_tasks import background_task_manager

    init_db()

    # Start background tasks for container management
    await background_task_manager.start_background_tasks()

    yield
    # Shutdown
    await background_task_manager.stop_background_tasks()


# Create FastAPI app
app = FastAPI(
    title="Code Execution Platform API",
    description="Backend API for the code execution platform with integrated terminal",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - get allowed origins from environment variable
cors_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])

# API routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(
    sessions.router,
    prefix="/api/sessions",
    tags=["sessions"],
)
app.include_router(
    workspace_files.router,
    prefix="/api/workspace",
    tags=["workspace_files"],
)


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: Optional[str] = None,
) -> None:
    # Store user_id as a custom attribute on the websocket connection
    if user_id:
        websocket.user_id = user_id  # type: ignore[attr-defined]
    else:
        websocket.user_id = None  # type: ignore[attr-defined]

    await websocket_manager.connect(websocket)

    # Send initial connection confirmation
    await websocket_manager.send_personal_message(
        websocket,
        {
            "type": "connection_established",
            "message": "WebSocket connected successfully",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Create unique session ID for each workspace connection to ensure isolation
            if "sessionId" in data and data["sessionId"] != "default":
                # Get user_id from WebSocket connection
                user_id = getattr(websocket, "user_id", None)

                # Check if we already have a unique session ID for this connection
                current_session = websocket_manager.get_session(websocket)
                workspace_uuid = data["sessionId"]

                # Check if current session matches the workspace - reuse if same workspace
                if current_session and current_session != "default":
                    current_workspace = container_manager._extract_workspace_id(
                        current_session,
                    )
                    if current_workspace == workspace_uuid:
                        # Same workspace, reuse existing session
                        data["sessionId"] = current_session
                    else:
                        # Different workspace, look for existing session for this workspace
                        existing_session = (
                            container_manager.find_session_by_workspace_id(
                                workspace_uuid,
                            )
                        )
                        if existing_session:
                            # Use existing session for this workspace
                            websocket_manager.set_session(websocket, existing_session)
                            data["sessionId"] = existing_session
                        else:
                            # Create new unique session ID for new workspace
                            unique_session_id = create_unique_session_id(
                                workspace_uuid,
                                user_id,
                            )
                            websocket_manager.set_session(websocket, unique_session_id)
                            data["sessionId"] = unique_session_id
                else:
                    # No current session, look for existing session for this workspace
                    existing_session = container_manager.find_session_by_workspace_id(
                        workspace_uuid,
                    )
                    if existing_session:
                        # Use existing session for this workspace
                        websocket_manager.set_session(websocket, existing_session)
                        data["sessionId"] = existing_session
                    else:
                        # Create new unique session ID and associate it with this WebSocket
                        unique_session_id = create_unique_session_id(
                            workspace_uuid,
                            user_id,
                        )
                        websocket_manager.set_session(websocket, unique_session_id)
                        data["sessionId"] = unique_session_id

                        # Start background task to check pod readiness
                        asyncio.create_task(
                            check_and_notify_pod_ready(unique_session_id, websocket),
                        )

            # Handle the message
            response = await handle_websocket_message(data, websocket)

            # Send response back to client
            if response:
                await websocket_manager.send_personal_message(websocket, response)

    except WebSocketDisconnect:
        await cleanup_websocket_session(websocket)

    except Exception:
        await cleanup_websocket_session(websocket, reason="WebSocket error cleanup")


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "message": "Code Execution Platform API",
        "status": "running",
        "docs": "/docs",
    }


@app.post("/workspace/{workspace_id}/shutdown")
async def shutdown_workspace(workspace_id: str) -> dict[str, Any]:
    """Gracefully shutdown a workspace and clean up its container."""
    try:
        # Find session by workspace ID
        session_id = container_manager.find_session_by_workspace_id(workspace_id)

        if not session_id:
            return {
                "success": True,
                "message": f"No active session found for workspace {workspace_id}",
                "workspace_id": workspace_id,
            }

        # Check if there are any active WebSocket connections to this session
        connection_count = websocket_manager.get_session_connection_count(session_id)

        # Clean up the session
        cleanup_success = await container_manager.cleanup_session(session_id)

        return {
            "success": cleanup_success,
            "message": f"Workspace {workspace_id} shutdown completed",
            "workspace_id": workspace_id,
            "session_id": session_id,
            "active_connections": connection_count,
            "container_cleaned": cleanup_success,
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Error shutting down workspace {workspace_id}: {e!s}",
            "workspace_id": workspace_id,
            "error": str(e),
        }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Disable reload for stable WebSocket connections
    # Use ENABLE_RELOAD=true env var to enable during development
    enable_reload = os.getenv("ENABLE_RELOAD", "false").lower() == "true"

    if enable_reload:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
            reload=True,
            reload_dirs=["app/"],
            reload_excludes=["venv/", "*.db", "__pycache__/", ".git/", "*.pyc"],
        )
    else:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
        )
