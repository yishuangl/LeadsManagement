import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import async_session
from app.services.auth_service import hash_password
from app.models.user import AdminUser

from sqlalchemy import select

logger = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Seed default admin user
    async with async_session() as session:
        result = await session.execute(
            select(AdminUser).where(
                AdminUser.username == settings.DEFAULT_ADMIN_USERNAME
            )
        )
        if result.scalar_one_or_none() is None:
            admin = AdminUser(
                username=settings.DEFAULT_ADMIN_USERNAME,
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            )
            session.add(admin)
            await session.commit()
            logger.info("Default admin user created")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Leads Management", lifespan=lifespan)

    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

    app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

    from app.routers import api, public, dashboard, auth

    app.include_router(auth.router)
    app.include_router(public.router)
    app.include_router(dashboard.router)
    app.include_router(api.router)

    @app.exception_handler(401)
    async def unauthorized_redirect(request: Request, exc):
        if not request.url.path.startswith("/api/"):
            return RedirectResponse(url="/auth/login", status_code=303)
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    return app


app = create_app()
