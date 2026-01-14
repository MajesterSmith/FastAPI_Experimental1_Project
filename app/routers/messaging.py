from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Form, Request
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..auth import get_current_user, pwd_context
from typing import Dict
from .. import models

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Store as list of websockets to allow multiple tabs per user
        self.active_connections: Dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)

    async def send_personal_message(self, message: str, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    # Potential improvement: Verify JWT token here!
    await manager.connect(websocket, user_id)
    try:
        while True:
            # Wait for data or disconnect
            await websocket.receive_text() 
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

@router.post("/send-message")
async def send_message(request: Request, receiver_id: int = Form(...), message: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return {"error": "Not authenticated"}
    
    # Save to DB
    msg = models.Message(sender_id=user.id, receiver_id=receiver_id, message=message)
    db.add(msg)
    db.commit()
    
    # Send to receiver if connected
    await manager.send_personal_message(f"{user.name}: {message}", receiver_id)
    
    return {"status": "sent"}

@router.get("/messages")
async def get_messages(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return {"error": "Not authenticated"}
    
    # Get messages for the user
    messages = db.query(models.Message)\
        .options(joinedload(models.Message.sender))\
        .filter(
            (models.Message.sender_id == user.id) | (models.Message.receiver_id == user.id)
        ).order_by(models.Message.timestamp).all()
    
    return {
        "messages": [
            {
                "sender_name": msg.sender.name,
                "message": msg.message,
                "timestamp": msg.timestamp
            } for msg in messages
        ]
    }