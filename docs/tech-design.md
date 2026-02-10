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

1. **Session auth over JWT**: The UI is server-rendered HTML, so every request already includes cookies. Session-based auth (via Starlette `SessionMiddleware` with a signed cookie) is a natural fit — no need to manage token refresh, store JWTs in localStorage, or deal with XSS exposure of tokens. The session stores only the `user_id`; the server looks up the full user on each request.

2. **HTMX over SPA**: The only interactive behavior in the UI is the "Mark Reached Out" button, which swaps a single table row. HTMX handles this with HTML attributes (`hx-post`, `hx-target`, `hx-swap`) — no JavaScript framework, no build step, no client-side state management. The server returns an HTML partial (`lead_row.html`) and HTMX replaces the `<tr>` in place.

3. **Background email**: Email delivery (SMTP) can take seconds and is unreliable. If done inline, the prospect would stare at a spinner while the server talks to an SMTP server. FastAPI `BackgroundTasks` runs the email sends after the HTTP response is returned, so the user sees the thank-you page immediately. If email delivery fails, the lead is still saved — email is a side effect, not a prerequisite.

4. **Local filesystem for resume storage**: Resumes are stored on the local disk under `uploads/resumes/` rather than cloud storage (e.g. S3). This is a deliberate choice for a demo/low-traffic app — it avoids external service dependencies, IAM configuration, and SDK setup. Files are named `{uuid}_{original_filename}` to prevent collisions. The DB stores the relative path, and the download endpoint resolves it at serve time. The tradeoff: local storage doesn't survive container resets and doesn't scale horizontally — documented as a future migration to S3 if needed.

5. **String over PG ENUM for status**: PostgreSQL `ENUM` types are created via `CREATE TYPE`, which interacts poorly with async SQLAlchemy and Alembic — the `checkfirst` introspection doesn't work through the async adapter, leading to "type already exists" errors on migration. Using `VARCHAR(20)` in the DB avoids this entirely. The Python `LeadStatus` enum still validates values at the application layer (in schemas and service code), so invalid statuses can't be written through the app.

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
3. After a lead is submitted, emails are dispatched via FastAPI background tasks. Update the email content in `app/services/email_service.py` 

## Future Work

1. Create "lead"<->"user" mapping, so each admin user views only their leads. Communications will be sent to that admin user's email instead of the default ATTORNEY_EMAIL
2. Use Cloud storage like S3 instead of local resume storage
3. Email status tracking and template editing
4. Leads dashboard: pagination and advanced filtering