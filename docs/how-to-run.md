# How to Run

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- pip

## Setup

1. **Clone and enter the project directory**

2. **Copy the environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start PostgreSQL**
   ```bash
   docker compose up -d
   ```

4. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```
   or
   ```bash
   python3 -m uvicorn app.main:app --reload
   ```

## Default Credentials

- **Username**: `admin`
- **Password**: `admin`

A default admin user is created automatically on first startup.

## Usage

| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Public interest form |
| http://localhost:8000/auth/login | Attorney login |
| http://localhost:8000/dashboard | Leads dashboard (requires login) |

## Email

By default, `EMAIL_ENABLED=false` — emails are logged to the console. To enable SMTP delivery, set `EMAIL_ENABLED=true` and configure the SMTP settings in `.env`.

## File Uploads

Resumes are stored in `uploads/resumes/`. Accepted formats: PDF, DOC, DOCX (max 10 MB).

## Creating Migrations

After modifying models:
```bash
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```
