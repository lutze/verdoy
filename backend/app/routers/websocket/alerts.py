"""
WebSocket router for real-time alerts.
"""

from fastapi import APIRouter, WebSocket

router = APIRouter()

@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts."""
    await websocket.accept()
    await websocket.send_text("Alerts WebSocket not implemented.")
    await websocket.close() 