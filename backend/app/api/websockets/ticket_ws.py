"""ArgusCX — WebSocket for real-time ticket updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

active_connections: list[WebSocket] = []

@router.websocket("/ws/tickets")
async def ticket_websocket(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    logger.info("WebSocket client connected", total=len(active_connections))
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "ping", "message": "pong"})
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info("WebSocket client disconnected")


async def broadcast(message: dict):
    """Broadcast a message to all connected WebSocket clients."""
    for conn in active_connections:
        try:
            await conn.send_json(message)
        except Exception:
            pass
