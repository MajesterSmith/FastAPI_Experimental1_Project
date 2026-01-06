from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    # Allows dept.employees in templates
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
    
    # Allows emp.department.name in templates
    department = relationship("Department", back_populates="employees")
    attendance = relationship("Attendance", back_populates="employee")

    my_leaves = relationship("Leave", foreign_keys="Leave.emp_id", back_populates="requester")
    managed_leaves = relationship("Leave", foreign_keys="Leave.admin_id", back_populates="approver")

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, default=func.now())
    is_present = Column(Boolean, default=True)
    emp_id = Column(Integer, ForeignKey("employees.id"))
    employee = relationship("Employee", back_populates="attendance")

class Leave(Base):
    __tablename__ = "leave"
    id = Column(Integer, primary_key = True, index = True)
    approve = Column(Boolean, nullable = True)
    emp_id = Column(Integer, ForeignKey("employees.id"))
    admin_id = Column(Integer, ForeignKey("employees.id"), nullable = True)
    date = Column(Date,default = func.now())

    requester = relationship("Employee", foreign_keys=[emp_id], back_populates="my_leaves")
    approver = relationship("Employee", foreign_keys=[admin_id], back_populates="managed_leaves")