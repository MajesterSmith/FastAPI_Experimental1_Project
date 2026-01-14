from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date
from ..database import get_db
from ..auth import get_current_user
from .. import models

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/")
    
    if user.role == "admin":
        return templates.TemplateResponse("admin_dash.html", {
            "request": request, "user": user,
            "employees": db.query(models.Employee).all(),
            "departments": db.query(models.Department).all(),
            "logs": db.query(models.Attendance).all(),
            "pending_leaves": db.query(models.Leave).filter(models.Leave.approve == None).all(),
            "admin_id": user.id
        })
    
    marked = db.query(models.Attendance).filter(models.Attendance.emp_id == user.id, models.Attendance.date == date.today()).first()
    admin = db.query(models.Employee).filter(models.Employee.role == "admin").first()
    return templates.TemplateResponse("employee_dash.html", {
        "request": request, "user": user, "marked": marked, "today": date.today(),
        "my_leaves": db.query(models.Leave).filter(models.Leave.emp_id == user.id).all(),
        "admin_id": admin.id if admin else 1
    })