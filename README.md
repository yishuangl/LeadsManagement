# Leads Management

Internal application for managing leads from prospects interested in legal services. Prospects submit interest through a public form; attorneys view and act on leads via an authenticated dashboard.

**Stack**: FastAPI, PostgreSQL, SQLAlchemy (async), HTMX, Jinja2, Pico CSS

## Quick Start

```bash
cp .env.example .env
docker compose up -d
python -m venv .venv
source .venv/bin/activate
pip install -e .
alembic upgrade head
uvicorn app.main:app --reload
```

Open http://localhost:8000 for the public form, or http://localhost:8000/auth/login to access the dashboard (default credentials: `admin` / `admin`).

## Documentation

- [How to Run](docs/how-to-run.md) — detailed setup, configuration, and usage instructions
- [Technical Design](docs/tech-design.md) — architecture, schema, design decisions, and future work
