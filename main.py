import datetime
from fastapi import FastAPI, Depends, HTTPException, Form, Request, status, Response
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship, declarative_base
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# Settings for JWT
SECRET_KEY = os.getenv("SECRET_KEY", "optional-fallback-for-local-dev")
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./default.db")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# --- DATABASE ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./employee_app.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELS ---
class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    salary = Column(Float, default=0.0)
    role = Column(String, default="employee")
    dept_id = Column(Integer, ForeignKey("departments.id"))
    department = relationship("Department", back_populates="employees")
    attendance = relationship("Attendance", back_populates="employee")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=func.now())
    is_present = Column(Boolean, default=True)
    emp_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee", back_populates="attendance")

Base.metadata.create_all(bind=engine)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        return db.query(Employee).filter(Employee.email == email).first()
    except JWTError:
        return None

# --- APP SETUP ---
app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_current_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    if not user_id: return None
    return db.query(Employee).filter(Employee.id == int(user_id)).first()

# --- ROUTES ---

@app.on_event("startup")
def startup():
    db = SessionLocal()
    admin_exists = db.query(Employee).filter(Employee.email == "admin@test.com").first()
    if not admin_exists:
        admin_dept = Department(name="Admin Dept")
        db.add(admin_dept)
        db.commit()
        db.refresh(admin_dept)

        admin = Employee(
            name="Admin User", 
            email="admin@test.com", 
            hashed_password=pwd_context.hash("admin123"), 
            role="admin", 
            dept_id=admin_dept.id
        )
        db.add(admin)
        db.commit()
    db.close()

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return RedirectResponse(url="/?error=1", status_code=302)
    
    access_token = create_access_token(data={"sub": user.email})
    
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    res = RedirectResponse(url="/")
    res.delete_cookie("access_token")
    return res

@app.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user: return RedirectResponse(url="/")
    
    if user.role == "admin":
        return templates.TemplateResponse("admin_dash.html", {
            "request": request, "user": user,
            "employees": db.query(Employee).all(),
            "departments": db.query(Department).all(),
            "logs": db.query(Attendance).all()
        })
    
    marked = db.query(Attendance).filter(Attendance.emp_id == user.id, Attendance.date == datetime.date.today()).first()
    return templates.TemplateResponse("employee_dash.html", {"request": request, "user": user, "marked": marked, "today": datetime.date.today()})

# --- CRUD OPERATIONS ---

@app.post("/admin/edit-emp")
async def edit_employee(
    emp_id: int = Form(...), 
    name: str = Form(...), 
    email: str = Form(...), 
    salary: float = Form(...), 
    db: Session = Depends(get_db)
):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if emp:
        emp.name = name
        emp.email = email
        emp.salary = salary
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/edit-dept")
async def edit_department(
    dept_id: int = Form(...), 
    name: str = Form(...), 
    db: Session = Depends(get_db)
):
    dept = db.query(Department).filter(Department.id == dept_id).first()
    if dept:
        dept.name = name
        db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/add-dept")
async def add_dept(request: Request, name: str = Form(...), db: Session = Depends(get_db)):
    db.add(Department(name=name))
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/add-emp")
async def add_emp(name: str = Form(...), email: str = Form(...), salary: float = Form(...), dept_id: int = Form(...), db: Session = Depends(get_db)):
    new_emp = Employee(name=name, email=email, salary=salary, dept_id=dept_id, hashed_password=pwd_context.hash("password123"))
    db.add(new_emp)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/admin/move-emp")
async def move_emp(emp_id: int = Form(...), dept_id: int = Form(...), db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    emp.dept_id = dept_id
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.get("/admin/del-emp/{id}")
async def del_emp(id: int, db: Session = Depends(get_db)):
    db.query(Employee).filter(Employee.id == id).delete()
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/mark-attendance")
async def mark_attendance(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    db.add(Attendance(emp_id=user.id))
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/change-password")
async def change_pwd(request: Request, new_pwd: str = Form(...), db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    user.hashed_password = pwd_context.hash(new_pwd)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=302)