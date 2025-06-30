"""
WebSocket router for live sensor data.
"""

from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/ws/live-data")
async def websocket_live_data(websocket: WebSocket):
    """WebSocket endpoint for live sensor readings."""
    await websocket.accept()
    await websocket.send_text("Live data WebSocket not implemented.")
    await websocket.close() 