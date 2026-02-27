"""WebSocket connection managers."""
from typing import Dict, List
from fastapi import WebSocket


class AlertConnectionManager:
    """Manages WebSocket connections for alerts."""
    
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store new WebSocket connection."""
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove WebSocket connection."""
        if user_id in self.connections:
            self.connections[user_id] = [
                ws for ws in self.connections[user_id] if ws != websocket
            ]
    
    async def send_to_user(self, user_id: str, data: dict):
        """Send data to all connections for a specific user."""
        for websocket in self.connections.get(user_id, []):
            try:
                await websocket.send_json(data)
            except:
                pass  # Connection already closed
    
    async def broadcast_all(self, data: dict):
        """Broadcast data to all connected users."""
        for user_id in self.connections:
            await self.send_to_user(user_id, data)


class ChatConnectionManager:
    """Manages WebSocket connections for community chat."""
    
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store new WebSocket connection."""
        await websocket.accept()
        self.connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection."""
        self.connections = [ws for ws in self.connections if ws != websocket]
    
    async def broadcast(self, data: dict):
        """Broadcast data to all connected clients."""
        for websocket in self.connections:
            try:
                await websocket.send_json(data)
            except:
                pass  # Connection already closed


# Global instances
alert_manager = AlertConnectionManager()
chat_manager = ChatConnectionManager()
