from fastapi import FastAPI, Depends, Form, Request, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date

import models
from database import engine, get_db
from auth import create_access_token, get_current_user, pwd_context

# Create Database Tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- INITIALIZATION ---
@app.on_event("startup")
def startup():
    db = next(get_db())
    admin_exists = db.query(models.Employee).filter(models.Employee.email == "admin@test.com").first()
    if not admin_exists:
        admin_dept = models.Department(name="Management")
        db.add(admin_dept)
        db.commit()
        db.refresh(admin_dept)
        admin = models.Employee(
            name="Admin User", 
            email="admin@test.com", 
            hashed_password=pwd_context.hash("admin123"), 
            role="admin", 
            dept_id=admin_dept.id
        )
        db.add(admin)
        db.commit()

# --- AUTH ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": None})

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.Employee).filter(models.Employee.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return RedirectResponse(url="/?error=1", status_code=status.HTTP_302_FOUND)
    
    token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

# --- DASHBOARD ---
@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/")
    
    if user.role == "admin":
        return templates.TemplateResponse("admin_dash.html", {
            "request": request, 
            "user": user,
            "employees": db.query(models.Employee).all(),
            "departments": db.query(models.Department).all(),
            "logs": db.query(models.Attendance).all()
        })
    
    marked = db.query(models.Attendance).filter(
        models.Attendance.emp_id == user.id, 
        models.Attendance.date == date.today()
    ).first()
    return templates.TemplateResponse("employee_dash.html", {
        "request": request, "user": user, "marked": marked, "today": date.today()
    })

# --- ACTIONS ---
@app.post("/admin/add-dept")
async def add_dept(name: str = Form(...), db: Session = Depends(get_db)):
    db.add(models.Department(name=name))
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/edit-dept")
async def edit_dept(dept_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if dept:
        dept.name = name
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/add-emp")
async def add_emp(name: str = Form(...), email: str = Form(...), salary: float = Form(...), dept_id: int = Form(...), db: Session = Depends(get_db)):
    new_emp = models.Employee(
        name=name, email=email, salary=salary, dept_id=dept_id, 
        hashed_password=pwd_context.hash("password123")
    )
    db.add(new_emp)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/edit-emp")
async def edit_emp(emp_id: int = Form(...), name: str = Form(...), email: str = Form(...), salary: float = Form(...), db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if emp:
        emp.name, emp.email, emp.salary = name, email, salary
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/admin/del-emp/{id}")
async def del_emp(id: int, db: Session = Depends(get_db)):
    db.query(models.Employee).filter(models.Employee.id == id).delete()
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/move-emp")
async def move_emp(emp_id: int = Form(...), dept_id: int = Form(...), db: Session = Depends(get_db)):
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if emp:
        emp.dept_id = dept_id
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/mark-attendance")
async def mark_attendance(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        db.add(models.Attendance(emp_id=user.id))
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/change-password")
async def change_pwd(request: Request, new_pwd: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        user.hashed_password = pwd_context.hash(new_pwd)
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)