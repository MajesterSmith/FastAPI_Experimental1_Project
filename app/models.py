from .database import Base
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, DateTime
from datetime import date, datetime
from sqlalchemy.orm import relationship

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    employees = relationship("Employee", back_populates="department")

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True) 
    hashed_password = Column(String)
    role = Column(String, default="employee")
    salary = Column(Float, default=0.0)
    dept_id = Column(Integer, ForeignKey("departments.id"))

    department = relationship("Department", back_populates="employees")
    attendance_logs = relationship("Attendance", back_populates="employee")
    leaves = relationship("Leave", back_populates="employee", foreign_keys="[Leave.emp_id]")
    notifications = relationship("Notification", back_populates="user")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(Date, default=date.today)
    employee = relationship("Employee", back_populates="attendance_logs")

class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(Integer, ForeignKey("employees.id"))
    date = Column(Date)
    approve = Column(Boolean, nullable=True)
    admin_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    employee = relationship("Employee", back_populates="leaves", foreign_keys=[emp_id])

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("employees.id"))
    receiver_id = Column(Integer, ForeignKey("employees.id"))
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("employees.id"))
    title = Column(String)
    message = Column(String)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("Employee", back_populates="notifications")