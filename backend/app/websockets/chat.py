"""WebSocket endpoint for community chat."""
import json
import uuid
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from ..database import get_db
from ..websockets.managers import chat_manager
from ..websockets.alerts import authenticate_websocket


last_message_times = {}


async def chat_websocket_handler(websocket: WebSocket):
    """Handle WebSocket connections for community chat."""
    user = await authenticate_websocket(websocket)
    
    if not user:
        return
    
    await chat_manager.connect(websocket)
    
    try:
        db = get_db()
        
        # Send recent message history
        recent_messages = await db.community_chat.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(50).to_list(50)
        
        await websocket.send_json({
            "type": "history",
            "data": list(reversed(recent_messages))
        })
        
        # Handle incoming messages
        while True:
            raw_data = await websocket.receive_text()
            data = json.loads(raw_data)
            
            message_text = data.get("message", "").strip()
            
            # Validate message
            if not message_text or len(message_text) > 500:
                continue
            
            # Rate limiting: 2 seconds between messages
            now = datetime.now(timezone.utc)
            user_id = user["id"]
            
            if user_id in last_message_times:
                time_diff = (now - last_message_times[user_id]).total_seconds()
                if time_diff < 2:
                    await websocket.send_json({
                        "type": "error",
                        "data": "Rate limited. Wait 2 seconds."
                    })
                    continue
            
            last_message_times[user_id] = now
            
            # Save message to database
            record = {
                "id": str(uuid.uuid4()),
                "userId": user_id,
                "username": user["name"],
                "message": message_text,
                "timestamp": now.isoformat()
            }
            
            await db.community_chat.insert_one(record.copy())
            
            # Broadcast to all connected clients
            await chat_manager.broadcast({
                "type": "message",
                "data": record
            })
            
    except WebSocketDisconnect:
        chat_manager.disconnect(websocket)
