import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AdminUser


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


async def create_user(
    session: AsyncSession, username: str, password: str
) -> AdminUser | None:
    user = AdminUser(username=username, hashed_password=hash_password(password))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return None
    return user


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> AdminUser | None:
    result = await session.execute(
        select(AdminUser).where(AdminUser.username == username)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user
