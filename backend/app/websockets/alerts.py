"""WebSocket endpoint for alerts."""
import jwt
from fastapi import WebSocket, WebSocketDisconnect
from ..config import settings
from ..database import get_db
from ..websockets.managers import alert_manager


async def authenticate_websocket(websocket: WebSocket):
    """Authenticate WebSocket connection via query param token."""
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=4001)
        return None
    
    try:
        db = get_db()
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["uid"]}, {"_id": 0, "password": 0})
        
        if not user:
            await websocket.close(code=4001)
            return None
        
        return user
        
    except Exception:
        await websocket.close(code=4001)
        return None


async def alerts_websocket_handler(websocket: WebSocket):
    """Handle WebSocket connections for alerts."""
    user = await authenticate_websocket(websocket)
    
    if not user:
        return
    
    await alert_manager.connect(websocket, user["id"])
    
    try:
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket, user["id"])
