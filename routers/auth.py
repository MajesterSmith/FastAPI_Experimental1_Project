from fastapi import APIRouter, Form, Depends, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from auth import create_access_token, pwd_context
import models

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": None})

@router.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.Employee).filter(models.Employee.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return RedirectResponse(url="/?error=Invalid Credentials", status_code=302)
    
    token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response