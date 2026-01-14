from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user
from ..models import Notification, Employee
from datetime import datetime

router = APIRouter()

@router.get("/notifications")
async def get_notifications(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return {"error": "Not authenticated"}

    notifications = db.query(Notification).filter(
        Notification.user_id == user.id,
        Notification.is_read == False
    ).order_by(Notification.created_at.desc()).all()

    return {"notifications": notifications}

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return {"error": "Not authenticated"}

    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user.id
    ).first()

    if notification:
        notification.is_read = True
        db.commit()

    return {"success": True}