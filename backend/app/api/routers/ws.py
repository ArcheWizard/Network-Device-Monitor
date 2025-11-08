"""WebSocket endpoint for real-time device updates and metrics streaming."""

from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from ...config import settings
from ...utils.auth import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages to all clients."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            "WebSocket client connected. Total connections: %d",
            len(self.active_connections),
        )

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection from active list."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(
                "WebSocket client disconnected. Total connections: %d",
                len(self.active_connections),
            )

    async def broadcast(self, message: Dict):
        """Broadcast message to all connected clients.

        Args:
            message: Dictionary to send as JSON to all clients
        """
        if not self.active_connections:
            return

        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning("Failed to send message to client: %s", e)
                disconnected.append(connection)

        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to_client(self, websocket: WebSocket, message: Dict):
        """Send message to a specific client.

        Args:
            websocket: Target WebSocket connection
            message: Dictionary to send as JSON
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.warning("Failed to send message to client: %s", e)
            self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()


def get_manager() -> ConnectionManager:
    """Get the global WebSocket connection manager."""
    return manager


@router.websocket("/ws/stream")
async def stream(ws: WebSocket, token: Optional[str] = Query(None)):
    """WebSocket endpoint for streaming device updates and metrics.

    Authentication via query parameter: /ws/stream?token=<jwt_token>
    If REQUIRE_AUTH=True, valid token must be provided.

    Event types:
    - hello: Initial connection confirmation
    - device_discovered: New device found during discovery
    - device_up: Device came online
    - device_down: Device went offline
    - latency: Latency metrics update
    """
    # Authenticate if auth is required
    if settings.REQUIRE_AUTH:
        if not token:
            logger.warning("WebSocket connection rejected: No token provided")
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication required")
            return

        # Decode and validate token
        payload = decode_access_token(token)
        if not payload:
            logger.warning("WebSocket connection rejected: Invalid token")
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
            return

        # Verify user exists and is active
        username = payload.get("sub")
        if not username:
            logger.warning("WebSocket connection rejected: Invalid token payload")
            await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token payload")
            return

        # Check user in database (optional but recommended)
        user_repo = getattr(ws.app.state, "user_repo", None)
        if user_repo:
            try:
                user_data = await user_repo.get_user_by_username(username)
                if not user_data or not user_data.get("is_active", True):
                    logger.warning("WebSocket connection rejected: User inactive or not found")
                    await ws.close(code=status.WS_1008_POLICY_VIOLATION, reason="User inactive")
                    return
            except Exception as e:
                logger.error("Failed to verify user for WebSocket: %s", e)
                await ws.close(code=status.WS_1011_INTERNAL_ERROR, reason="Authentication error")
                return

        logger.info("WebSocket authenticated for user: %s", username)

    await manager.connect(ws)
    try:
        # Send welcome message
        await ws.send_json(
            {
                "type": "hello",
                "message": "Connected to Network Device Monitor",
                "ts": int(time.time()),
            }
        )

        # Keep connection alive and handle client messages
        while True:
            data = await ws.receive_text()
            # Echo back or handle client commands if needed
            logger.debug("Received from client: %s", data)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
        manager.disconnect(ws)
    except Exception as e:
        logger.error("WebSocket error: %s", e)
        manager.disconnect(ws)
