"""
WebSocket middleware for LMS Core API.

This module provides middleware for WebSocket connections,
including connection management and authentication.
"""

import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from ..config import settings

logger = logging.getLogger(__name__)


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time functionality."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "live_data": set(),
            "device_status": set(),
            "alerts": set()
        }
    
    async def connect(self, websocket: WebSocket, connection_type: str):
        """
        Connect a WebSocket to a specific connection type.
        
        Args:
            websocket: WebSocket connection
            connection_type: Type of connection (live_data, device_status, alerts)
        """
        await websocket.accept()
        
        if connection_type in self.active_connections:
            self.active_connections[connection_type].add(websocket)
            logger.info(f"WebSocket connected to {connection_type}")
        else:
            logger.warning(f"Unknown connection type: {connection_type}")
    
    def disconnect(self, websocket: WebSocket, connection_type: str):
        """
        Disconnect a WebSocket from a specific connection type.
        
        Args:
            websocket: WebSocket connection
            connection_type: Type of connection
        """
        if connection_type in self.active_connections:
            self.active_connections[connection_type].discard(websocket)
            logger.info(f"WebSocket disconnected from {connection_type}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection.
        
        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(message)
    
    async def broadcast(self, message: str, connection_type: str):
        """
        Broadcast a message to all connections of a specific type.
        
        Args:
            message: Message to broadcast
            connection_type: Type of connection to broadcast to
        """
        if connection_type in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[connection_type]:
                try:
                    if connection.client_state == WebSocketState.CONNECTED:
                        await connection.send_text(message)
                    else:
                        disconnected.add(connection)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")
                    disconnected.add(connection)
            
            # Remove disconnected connections
            self.active_connections[connection_type] -= disconnected
    
    def get_connection_count(self, connection_type: str) -> int:
        """
        Get the number of active connections for a specific type.
        
        Args:
            connection_type: Type of connection
            
        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(connection_type, set()))


# Global WebSocket manager instance
websocket_manager = WebSocketConnectionManager()


class WebSocketMiddleware:
    """Middleware for WebSocket connection management."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            # Add WebSocket manager to scope for access in routes
            scope["websocket_manager"] = websocket_manager
        
        await self.app(scope, receive, send)


def setup_websocket_middleware(app):
    """
    Setup WebSocket middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(WebSocketMiddleware) 