"""
WebSocket router for device status events.
"""

from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/ws/device-status")
async def websocket_device_status(websocket: WebSocket):
    """WebSocket endpoint for device status events."""
    await websocket.accept()
    await websocket.send_text("Device status WebSocket not implemented.")
    await websocket.close() 