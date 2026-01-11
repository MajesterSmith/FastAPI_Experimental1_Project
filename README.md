# FastAPI Employee Management System

A FastAPI application for managing employees, departments, attendance, and messaging.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --reload
```

## Database Migrations

This project uses Alembic for database migrations.

### Commands

- **Check current migration status:**
```bash
alembic current
```

- **Generate a new migration after model changes:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

- **Apply migrations:**
```bash
alembic upgrade head
```

- **Rollback migration:**
```bash
alembic downgrade -1
```

### Initial Setup

The database has been initialized with the following tables:
- departments
- employees
- attendance
- leaves
- messages

Default admin account:
- Email: admin@test.com
- Password: admin123

## Features

- User authentication and authorization
- Employee management
- Department management
- Attendance tracking
- Leave management
- Internal messaging
- Admin dashboard
- Employee dashboard