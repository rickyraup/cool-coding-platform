"""Main FastAPI application for the Code Execution Platform."""

import os
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Optional

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    health,
    postgres_sessions,
    reviews,
    session_workspace,
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
    base_session_id: str, user_id: Optional[str] = None
) -> str:
    """Create a unique session ID that includes user ID and timestamp to prevent reuse."""
    timestamp = int(time.time() * 1000)  # milliseconds
    unique_id = str(uuid.uuid4())[:8]  # short UUID

    # Include user_id in session ID for better isolation
    if user_id:
        return f"user_{user_id}_ws_{base_session_id}_{timestamp}_{unique_id}"
    return f"{base_session_id}_{timestamp}_{unique_id}"


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
    print("🧹 Stopping background tasks...")
    await background_task_manager.stop_background_tasks()
    print("✅ Cleanup complete")


# Create FastAPI app
app = FastAPI(
    title="Code Execution Platform API",
    description="Backend API for the code execution platform with integrated terminal",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware - get allowed origins from environment variable
cors_origins = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
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

# PostgreSQL-based routers
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(
    postgres_sessions.router,
    prefix="/api/postgres_sessions",
    tags=["postgres_sessions"],
)
app.include_router(
    session_workspace.router,
    prefix="/api/session_workspace",
    tags=["session_workspace"],
)
app.include_router(
    workspace_files.router, prefix="/api/workspace", tags=["workspace_files"]
)
app.include_router(reviews.router, tags=["reviews"])


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, user_id: Optional[str] = None
) -> None:
    # Store user_id as a custom attribute on the websocket connection
    if user_id:
        # Use setattr to store user_id since path_params is read-only
        websocket.user_id = user_id
        print(f"🔐 WebSocket connected for user: {user_id}")
    else:
        websocket.user_id = None
        print("⚠️ WebSocket connected without user authentication")

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
                        current_session
                    )
                    if current_workspace == workspace_uuid:
                        # Same workspace, reuse existing session
                        data["sessionId"] = current_session
                        print(
                            f"🔄 Reusing existing container session for user {user_id}: {current_session}"
                        )
                    else:
                        # Different workspace, look for existing session for this workspace
                        existing_session = (
                            container_manager.find_session_by_workspace_id(
                                workspace_uuid
                            )
                        )
                        if existing_session:
                            # Use existing session for this workspace
                            websocket_manager.set_session(websocket, existing_session)
                            data["sessionId"] = existing_session
                            print(
                                f"🔄 Switching to existing container session for user {user_id}: {existing_session}"
                            )
                        else:
                            # Create new unique session ID for new workspace
                            unique_session_id = create_unique_session_id(
                                workspace_uuid, user_id
                            )
                            websocket_manager.set_session(websocket, unique_session_id)
                            print(
                                f"🔄 Created unique session ID for user {user_id}: {workspace_uuid} → {unique_session_id}"
                            )
                            data["sessionId"] = unique_session_id
                else:
                    # No current session, look for existing session for this workspace
                    existing_session = container_manager.find_session_by_workspace_id(
                        workspace_uuid
                    )
                    if existing_session:
                        # Use existing session for this workspace
                        websocket_manager.set_session(websocket, existing_session)
                        data["sessionId"] = existing_session
                        print(
                            f"🔄 Using existing container session for user {user_id}: {existing_session}"
                        )
                    else:
                        # Create new unique session ID and associate it with this WebSocket
                        unique_session_id = create_unique_session_id(
                            workspace_uuid, user_id
                        )
                        websocket_manager.set_session(websocket, unique_session_id)
                        print(
                            f"🔄 Created unique session ID for user {user_id}: {workspace_uuid} → {unique_session_id}"
                        )
                        data["sessionId"] = unique_session_id

            # Handle the message
            response = await handle_websocket_message(data, websocket)
            print(f"🔍 WebSocket handler response: {response}")

            # Send response back to client
            if response:
                await websocket_manager.send_personal_message(websocket, response)

    except WebSocketDisconnect:
        # Get session ID before disconnecting
        session_id = websocket_manager.get_session(websocket)
        websocket_manager.disconnect(websocket)

        # Clean up container if no other connections to this session
        if (
            session_id != "default"
            and not websocket_manager.has_other_connections_to_session(session_id)
        ):
            print(
                f"🧹 No other connections to session {session_id}, cleaning up container..."
            )
            try:
                await container_manager.cleanup_session(session_id)
                print(f"✅ Container cleanup completed for session {session_id}")
            except Exception as cleanup_error:
                print(
                    f"❌ Error during container cleanup for session {session_id}: {cleanup_error}"
                )

        print("WebSocket client disconnected")

    except Exception as e:
        print(f"WebSocket error: {e}")
        # Get session ID before disconnecting
        session_id = websocket_manager.get_session(websocket)
        websocket_manager.disconnect(websocket)

        # Clean up container if no other connections to this session
        if (
            session_id != "default"
            and not websocket_manager.has_other_connections_to_session(session_id)
        ):
            print(
                f"🧹 WebSocket error cleanup - removing container for session {session_id}"
            )
            try:
                await container_manager.cleanup_session(session_id)
                print(f"✅ Container cleanup completed for session {session_id}")
            except Exception as cleanup_error:
                print(
                    f"❌ Error during container cleanup for session {session_id}: {cleanup_error}"
                )


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
            "message": f"Error shutting down workspace {workspace_id}: {str(e)}",
            "workspace_id": workspace_id,
            "error": str(e),
        }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # Disable reload for stable WebSocket connections
    # Use ENABLE_RELOAD=true env var to enable during development
    enable_reload = os.getenv("ENABLE_RELOAD", "false").lower() == "true"

    if enable_reload:
        print("🔄 Running in development mode with auto-reload")
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
        print("🚀 Running in production mode (stable WebSocket connections)")
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            log_level="info",
        )
