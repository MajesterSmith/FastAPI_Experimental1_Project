# FastAPI Employee Management System

A FastAPI application for managing employees, departments, attendance, and messaging.

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
uvicorn main:app --reload
```

### Docker Setup

1. **Build and run with Docker Compose:**
```bash
docker-compose up --build
```

2. **Run database migrations in Docker:**
```bash
# Access the running app container
docker-compose exec app alembic upgrade head
```

3. **Stop the containers:**
```bash
docker-compose down
```

4. **Stop and remove volumes (including database data):**
```bash
docker-compose down -v
```

**Access the application:**
- API: http://localhost:8000
- Database: localhost:5432 (PostgreSQL)

**Default admin account:**
- Email: admin@test.com
- Password: admin123

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

## Features

- User authentication and authorization
- Employee management
- Department management
- Attendance tracking
- Leave management
- Internal messaging
- Admin dashboard
- Employee dashboard