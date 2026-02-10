# Leads Management - Technical Design

## Overview

This document describes the technical design for a **FastAPI-based lead management application**. The system supports:

- A **public form** for prospects to submit leads (name, email, resume)
- **Email notifications** to both the prospect and the attorney
- An **internal admin UI** for viewing and updating leads (auth-protected)
- **Persistent storage** for lead and user data

The application is intentionally scoped as a **demo project** with low traffic expectations and local file storage.

## Goals & Non-Goals

### Goals
- Simple, maintainable server-rendered web application
- Clear separation between public and admin functionality
- Minimal frontend complexity (no JS framework)

### Non-Goals
- High-scale performance optimization
- Asynchronous job queues
- Fine-grained role-based permissions


## Architecture

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL via SQLAlchemy async ORM
- **Migrations**: Alembic (async)
- **Auth**: Session-based (signed cookie via Starlette SessionMiddleware)
- **Frontend**: Server-rendered HTML with Jinja2 + HTMX for partial updates
- **Styling**: Pico CSS (classless/minimal CSS framework)
- **Email**: SMTP via aiosmtplib (with dev mode console logging)
- **File uploads**: Local filesystem storage

## Application Structure

```
leads/
├── docker-compose.yml          # Postgres service
├── pyproject.toml              # Dependencies and build config
├── alembic.ini                 # Alembic settings
├── .env.example                # Template for environment variables
├── alembic/
│   ├── env.py                  # Async migration runner
│   └── versions/               # Migration files
├── uploads/resumes/            # Resume file storage (gitignored)
├── docs/
│   ├── tech-design.md
│   └── how-to-run.md
└── app/
    ├── main.py                 # App factory, lifespan (admin seed), middleware
    ├── config.py               # pydantic-settings configuration
    ├── database.py             # Async engine, session factory, Base
    ├── dependencies.py         # FastAPI deps (db session, current user)
    ├── models/
    │   ├── lead.py             # Lead model + LeadStatus enum
    │   └── user.py             # AdminUser model
    ├── schemas/
    │   ├── lead.py             # Lead request/response schemas
    │   └── user.py             # Login form schema
    ├── services/
    │   ├── auth_service.py     # Password hashing, authentication
    │   ├── lead_service.py     # Lead CRUD + state transitions
    │   ├── email_service.py    # SMTP / console email
    │   └── file_service.py     # Resume upload + download handling
    ├── routers/
    │   ├── api.py              # JSON REST API (/api/leads)
    │   ├── public.py           # Public interest form (/, /submit)
    │   ├── dashboard.py        # Attorney dashboard (/dashboard)
    │   └── auth.py             # Login/logout (/auth)
    ├── templates/
    │   ├── base.html           # Layout with Pico CSS + HTMX
    │   ├── login.html
    │   ├── dashboard/
    │   │   ├── lead_list.html  # Full leads table
    │   │   └── lead_row.html   # HTMX partial for row swap
    │   └── public/
    │       ├── interest_form.html
    │       └── thank_you.html
    └── static/css/styles.css
```


## Database Schema

### `leads`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK, auto-generated |
| first_name | VARCHAR(100) | NOT NULL |
| last_name | VARCHAR(100) | NOT NULL |
| email | VARCHAR(255) | NOT NULL, indexed |
| resume_path | TEXT | nullable |
| status | VARCHAR(20) | default 'PENDING', validated at app layer via Python enum |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### `admin_users`
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| username | VARCHAR(100) | UNIQUE, indexed |
| hashed_password | VARCHAR(255) | bcrypt |
| created_at | TIMESTAMPTZ | auto |

## Key Design Decisions

1. **Session auth over JWT**: Simpler for server-rendered HTML; no token refresh complexity.
2. **HTMX over SPA**: Minimal JavaScript; server renders HTML partials for interactive updates.
3. **Background email**: Emails dispatched via FastAPI `BackgroundTasks` to avoid blocking form responses.
4. **File validation**: Extension + content-type checks with 10 MB size limit. UUIDs in filenames prevent collisions.
5. **Path traversal protection**: Resume download endpoint validates paths stay within the upload directory.
6. **String over PG ENUM for status**: Avoids PostgreSQL `CREATE TYPE` migration headaches with async drivers. The Python `LeadStatus` enum validates values at the application layer.

### FastAPI vs Django
Django provides many features that align closely with this use case:

- Built-in admin interface (instant internal UI)
- Built-in authentication system
- ORM tightly integrated with forms and templates
- Batteries-included approach for CRUD apps

For a form-heavy, admin-centric application, Django would fit naturally.

## Routes

### JSON API (`/api/leads`)
- `POST /api/leads` — Create lead (public, multipart)
- `GET /api/leads` — List leads (auth required)
- `GET /api/leads/{id}` — Get lead (auth required)
- `PUT /api/leads/{id}` — Update lead (auth required)

### HTML
- `GET /` — Public interest form
- `POST /submit` — Process form submission
- `GET /thank-you` — Confirmation page
- `GET /auth/login` — Login page
- `POST /auth/login` — Process login
- `POST /auth/logout` — Destroy session
- `GET /dashboard` — Leads table
- `POST /dashboard/leads/{id}/reach-out` — Mark lead reached out (HTMX)
- `GET /dashboard/leads/{id}/resume` — Download resume

## Developer Notes

1. For configurations, `pydantic_settings` resolves each field in the order env vars -> .env file (defined in `model_config`) -> class defaults
2. Don't manually edit files in `alembic`. See "Creating Migrations" in how-to-run.md
3. After a lead is submitted, emails are dispatched via FastAPI background tasks. 

## Future Work

1. Create lead<->admin user mapping, so the admin user only views their leads. The email will be sent to that admin user (attorney) instead of the default ATTORNEY_EMAIL
2. Use Cloud storage like S3 instead of local storage for saving resumes
3. Password reset flow
4. Email status tracking
5. Leads dashboard: pagination and advanced filtering