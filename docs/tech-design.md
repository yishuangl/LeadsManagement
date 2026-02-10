# Leads Management - Technical Design

## Overview

Internal application for managing leads from prospects interested in legal services. Attorneys use a dashboard to view and act on leads; prospects submit interest via a public form.

## Architecture

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL via SQLAlchemy async ORM
- **Migrations**: Alembic (async)
- **Auth**: Session-based (signed cookie via Starlette SessionMiddleware)
- **Frontend**: Server-rendered HTML with Jinja2 + HTMX for partial updates
- **Styling**: Pico CSS (classless/minimal CSS framework)
- **Email**: SMTP via aiosmtplib (with dev mode console logging)
- **File uploads**: Local filesystem storage

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
