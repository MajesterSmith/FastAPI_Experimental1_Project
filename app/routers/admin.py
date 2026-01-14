from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..auth import get_current_user, pwd_context
from .. import models

router = APIRouter()

@router.post("/admin/add-dept")
async def add_dept(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    if not db.query(models.Department).filter(models.Department.name == name).first():
        db.add(models.Department(name=name))
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Department Added", status_code=302)

@router.post("/admin/add-emp")
async def add_emp(request: Request, name: str = Form(...), email: str = Form(...), salary: float = Form(...), dept_id: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    new_emp = models.Employee(name=name, email=email, salary=salary, dept_id=dept_id, hashed_password=pwd_context.hash("password123"))
    db.add(new_emp)
    db.commit()
    return RedirectResponse(url="/dashboard?msg=Employee Registered", status_code=302)

@router.post("/admin/move-emp")
async def move_emp(request: Request, emp_id: int = Form(...), new_dept_id: int = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    emp = db.query(models.Employee).filter(models.Employee.id == emp_id).first()
    if emp:
        emp.dept_id = new_dept_id
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Employee Moved", status_code=302)

@router.get("/admin/del-dept/{id}")
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

@router.post("/admin/edit-dept")
async def edit_dept(request: Request, dept_id: int = Form(...), name: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    dept = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if dept:
        dept.name = name
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Department Renamed", status_code=302)

@router.post("/admin/edit-emp")
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

@router.get("/admin/del-emp/{id}")
async def delete_employee(request: Request, id: int, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    emp = db.query(models.Employee).filter(models.Employee.id == id).first()
    if emp:
        db.delete(emp)
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Employee Deleted", status_code=302)

@router.post("/admin/approve-leave")
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