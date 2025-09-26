import asyncio
from typing import Any, Optional

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self.connection_sessions: dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        print(
            f"WebSocket connection established. Total connections: {len(self.active_connections)}",
        )

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_sessions:
            del self.connection_sessions[websocket]
        print(
            f"WebSocket connection closed. Total connections: {len(self.active_connections)}",
        )

    async def send_personal_message(
        self, websocket: WebSocket, message: dict[str, Any],
    ) -> None:
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)

    async def send_to_session(self, session_id: str, message: dict[str, Any]) -> None:
        """Send message to all WebSockets connected to a specific session."""
        for websocket, ws_session_id in self.connection_sessions.items():
            if ws_session_id == session_id:
                await self.send_personal_message(websocket, message)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Send message to all connected WebSockets."""
        if self.active_connections:
            tasks = []
            for connection in self.active_connections.copy():
                tasks.append(self.send_personal_message(connection, message))
            await asyncio.gather(*tasks, return_exceptions=True)

    def set_session(self, websocket: WebSocket, session_id: str) -> None:
        """Associate a WebSocket connection with a session ID."""
        self.connection_sessions[websocket] = session_id

    def get_session(self, websocket: WebSocket) -> str:
        """Get the session ID for a WebSocket connection."""
        return self.connection_sessions.get(websocket, "default")

    def get_active_connections_count(self) -> int:
        return len(self.active_connections)
    
    def has_other_connections_to_session(self, session_id: str, exclude_websocket: Optional[WebSocket] = None) -> bool:
        """Check if there are other WebSocket connections to the same session."""
        for websocket, ws_session_id in self.connection_sessions.items():
            if ws_session_id == session_id and websocket != exclude_websocket:
                return True
        return False
    
    def get_session_connection_count(self, session_id: str) -> int:
        """Get the number of active connections for a specific session."""
        count = 0
        for ws_session_id in self.connection_sessions.values():
            if ws_session_id == session_id:
                count += 1
        return count
