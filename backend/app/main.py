"""Main FastAPI application for the Code Execution Platform."""

import os
import uuid
import time
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
    sessions,
    users,
    workspace,
)
from app.core.postgres import init_db
from app.core.session_manager import session_manager
from app.services.container_manager import container_manager
from app.websockets.handlers import handle_websocket_message
from app.websockets.manager import WebSocketManager


# Load environment variables
load_dotenv()

# Initialize WebSocket manager
websocket_manager = WebSocketManager()


def create_unique_session_id(base_session_id: str, user_id: Optional[str] = None) -> str:
    """Create a unique session ID that includes user ID and timestamp to prevent reuse."""
    timestamp = int(time.time() * 1000)  # milliseconds
    unique_id = str(uuid.uuid4())[:8]  # short UUID
    
    # Include user_id in session ID for better isolation
    if user_id:
        return f"user_{user_id}_ws_{base_session_id}_{timestamp}_{unique_id}"
    else:
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
        "http://localhost:3001",
        "http://127.0.0.1:3001",
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
app.include_router(reviews.router, tags=["reviews"])


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: Optional[str] = None) -> None:
    # Store user_id as a custom attribute on the websocket connection
    if user_id:
        # Use setattr to store user_id since path_params is read-only
        setattr(websocket, 'user_id', user_id)
        print(f"🔐 WebSocket connected for user: {user_id}")
    else:
        setattr(websocket, 'user_id', None)
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
            if 'sessionId' in data and data['sessionId'] != 'default':
                # Get user_id from WebSocket connection
                user_id = getattr(websocket, 'user_id', None)
                
                # Check if we already have a unique session ID for this connection
                current_session = websocket_manager.get_session(websocket)
                
                # Look for an existing session for this workspace across all containers
                existing_session = container_manager.find_session_by_workspace_id(data['sessionId'])
                
                if existing_session:
                    # Use existing session for this workspace
                    websocket_manager.set_session(websocket, existing_session)
                    data['sessionId'] = existing_session
                    print(f"🔄 Reusing existing container session for user {user_id}: {data['sessionId']}")
                elif current_session and current_session != 'default':
                    # Use current WebSocket session if it exists and is not default
                    data['sessionId'] = current_session
                    print(f"🔄 Using current WebSocket session for user {user_id}: {data['sessionId']}")
                else:
                    # Create new unique session ID and associate it with this WebSocket
                    unique_session_id = create_unique_session_id(data['sessionId'], user_id)
                    websocket_manager.set_session(websocket, unique_session_id)
                    print(f"🔄 Created unique session ID for user {user_id}: {data['sessionId']} → {unique_session_id}")
                    
                    # Update the message data with the unique session ID
                    data['sessionId'] = unique_session_id

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
        if session_id != "default" and not websocket_manager.has_other_connections_to_session(session_id):
            print(f"🧹 No other connections to session {session_id}, cleaning up container...")
            try:
                await container_manager.cleanup_session(session_id)
                print(f"✅ Container cleanup completed for session {session_id}")
            except Exception as cleanup_error:
                print(f"❌ Error during container cleanup for session {session_id}: {cleanup_error}")
        
        print("WebSocket client disconnected")
        
    except Exception as e:
        print(f"WebSocket error: {e}")
        # Get session ID before disconnecting
        session_id = websocket_manager.get_session(websocket)
        websocket_manager.disconnect(websocket)
        
        # Clean up container if no other connections to this session
        if session_id != "default" and not websocket_manager.has_other_connections_to_session(session_id):
            print(f"🧹 WebSocket error cleanup - removing container for session {session_id}")
            try:
                await container_manager.cleanup_session(session_id)
                print(f"✅ Container cleanup completed for session {session_id}")
            except Exception as cleanup_error:
                print(f"❌ Error during container cleanup for session {session_id}: {cleanup_error}")


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
