from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..auth import get_current_user, pwd_context
from .. import models

router = APIRouter()

@router.post("/mark-attendance")
async def mark_attendance(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/")
    already = db.query(models.Attendance).filter(models.Attendance.emp_id == user.id, models.Attendance.date == date.today()).first()
    if not already:
        db.add(models.Attendance(emp_id=user.id))
        db.commit()
        return RedirectResponse(url="/dashboard?msg=Attendance Marked", status_code=302)
    return RedirectResponse(url="/dashboard?error=Already Marked", status_code=302)

@router.post("/request-leave")
async def request_leave(request: Request, leave_date: date = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/")
    db.add(models.Leave(emp_id=user.id, date=leave_date, approve=None))
    db.commit()
    return RedirectResponse(url="/dashboard?msg=Leave Requested", status_code=302)

@router.post("/change-password")
async def change_password(request: Request, new_pwd: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/")
    user.hashed_password = pwd_context.hash(new_pwd)
    db.commit()
    return RedirectResponse(url="/dashboard?msg=Password Changed", status_code=302)