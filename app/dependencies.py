from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.user import AdminUser


async def get_db():
    async with async_session() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(request: Request, db: DbSession) -> AdminUser:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


CurrentUser = Annotated[AdminUser, Depends(get_current_user)]


async def get_current_user_or_none(request: Request, db: DbSession) -> AdminUser | None:
    """Returns the current user or None (no exception). For HTML routes that redirect."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    result = await db.execute(
        select(AdminUser).where(AdminUser.id == UUID(user_id))
    )
    return result.scalar_one_or_none()
