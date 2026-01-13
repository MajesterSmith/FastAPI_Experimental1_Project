import logging
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

logging.getLogger('passlib').setLevel(logging.ERROR)

import models
from database import engine
from routers import auth, dashboard, admin, employee, messaging, notifications

# models.Base.metadata.create_all(bind=engine)  # Removed - using Alembic migrations now

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from database import SessionLocal
    from auth import pwd_context
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
    
    yield
    
    # Shutdown (if needed)
    pass

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(employee.router)
app.include_router(messaging.router)
app.include_router(notifications.router)