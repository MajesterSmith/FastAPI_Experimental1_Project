import logging
from datetime import date
from fastapi import FastAPI, Depends, Form, Request, status, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

logging.getLogger('passlib').setLevel(logging.ERROR)

import models
from database import engine, get_db, SessionLocal
from auth import create_access_token, get_current_user, pwd_context

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        admin_dept = db.query(models.Department).filter(models.Department.name == "Management").first()
        if not admin_dept:
            admin_dept = models.Department(name="Management")
            db.add(admin_dept)
            db.commit()
            db.refresh(admin_dept)
            
        admin_exists = db.query(models.Employee).filter(models.Employee.email == "admin@test.com").first()
        if not admin_exists:
            admin = models.Employee(
                name="Admin User", 
                email="admin@test.com", 
                hashed_password=pwd_context.hash("admin123"), 
                role="admin", 
                salary=0.0,
                dept_id=admin_dept.id
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

# --- AUTHENTICATION ---
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "user": None})

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.Employee).filter(models.Employee.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return RedirectResponse(url="/?error=Invalid Credentials", status_code=302)
    
    token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax")
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("access_token")
    return response

# --- DASHBOARDS ---
@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/")
    
    if user.role == "admin":
        return templates.TemplateResponse("admin_dash.html", {
            "request": request, "user": user,
            "employees": db.query(models.Employee).all(),
            "departments": db.query(models.Department).all(),
            "logs": db.query(models.Attendance).all(),
            "pending_leaves": db.query(models.Leave).filter(models.Leave.approve == None).all()
        })
    
    marked = db.query(models.Attendance).filter(models.Attendance.emp_id == user.id, models.Attendance.date == date.today()).first()
    return templates.TemplateResponse("employee_dash.html", {
        "request": request, "user": user, "marked": marked, "today": date.today(),
        "my_leaves": db.query(models.Leave).filter(models.Leave.emp_id == user.id).all()
    })

# --- ADMIN ACTIONS ---
@app.post("/admin/add-dept")
async def add_dept(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if not db.query(models.Department).filter(models.Department.name == name).first():
        db.add(models.Department(name=name))
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Department Added", status_code=302)

@app.post("/admin/add-emp")
async def add_emp(request: Request, name: str = Form(...), email: str = Form(...), salary: float = Form(...), dept_id: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    new_emp = models.Employee(name=name, email=email, salary=salary, dept_id=dept_id, hashed_password=pwd_context.hash("password123"))
    db.add(new_emp)
    db.commit()
    return RedirectResponse(url="/dashboard?msg=Employee Registered", status_code=302)

@app.post("/admin/move-emp")
async def move_emp(request: Request, emp_id: int = Form(...), new_dept_id: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if emp:
        emp.dept_id = new_dept_id
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Employee Moved", status_code=302)

@app.get("/admin/del-dept/{id}")
async def delete_department(request: Request, id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    # Check if any employees are linked to this department
    has_employees = db.query(models.Employee).filter(models.Employee.dept_id == id).first()
    
    if has_employees:
        return RedirectResponse(url="/dashboard?error=Cannot delete department with assigned employees", status_code=302)
    
    dept = db.query(models.Department).filter(models.Department.id == id).first()
    if dept:
        db.delete(dept)
        db.commit()
    
    return RedirectResponse(url="/dashboard?msg=Department Deleted", status_code=302)

@app.post("/admin/edit-dept")
async def edit_dept(request: Request, dept_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if dept:
        dept.name = name
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Department Renamed", status_code=302)

@app.post("/admin/edit-emp")
async def edit_employee(
    request: Request,
    emp_id: int = Form(...), 
    new_name: str = Form(...), 
    new_email: str = Form(...), 
    new_salary: float = Form(...), 
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if emp:
        emp.name = new_name
        emp.email = new_email
        emp.salary = new_salary
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Employee Updated", status_code=302)

@app.get("/admin/del-emp/{id}")
async def delete_employee(request: Request, id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    emp = db.query(models.Employee).filter(models.Employee.id == id).first()
    if emp:
        db.delete(emp)
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Employee Deleted", status_code=302)

@app.post("/admin/approve-leave")
async def approve_leave(request: Request, leave_id: int = Form(...), decision: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    leave = db.query(models.Leave).filter(models.Leave.id == leave_id).first()
    if leave:
        if decision == "approve":
            leave.approve = True
        elif decision == "reject":
            leave.approve = False
        leave.admin_id = user.id
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Leave Request Processed", status_code=302)

# --- USER ACTIONS ---
@app.post("/mark-attendance")
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

@app.post("/request-leave")
async def request_leave(request: Request, leave_date: date = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/")
    db.add(models.Leave(emp_id=user.id, date=leave_date, approve=None))
    db.commit()
    return RedirectResponse(url="/dashboard?msg=Leave Requested", status_code=302)

@app.post("/change-password")
async def change_password(request: Request, new_pwd: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/")
    user.hashed_password = pwd_context.hash(new_pwd)
    db.commit()
    return RedirectResponse(url="/dashboard?msg=Password Changed", status_code=302)