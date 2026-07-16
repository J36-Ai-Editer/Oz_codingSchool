from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Department
from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    return await db.scalar(select(User).where(User.id == user_id))


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    return await db.scalar(
        select(User).where(func.lower(User.email) == email.strip().lower())
    )


async def get_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
    return await db.scalar(
        select(User).where(User.phone_number == phone_number)
    )


async def create(db: AsyncSession, user: User) -> User:
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def save(db: AsyncSession, user: User) -> User:
    await db.flush()
    await db.refresh(user)
    return user


async def list_users(
    db: AsyncSession,
    *,
    query: str | None = None,
    department: Department | None = None,
) -> list[User]:
    statement: Select[tuple[User]] = select(User).order_by(User.id)
    if query and (normalized_query := query.strip()):
        pattern = f"%{normalized_query}%"
        statement = statement.where(
            or_(User.name.ilike(pattern), User.email.ilike(pattern))
        )
    if department is not None:
        statement = statement.where(User.department == department)
    result = await db.scalars(statement)
    return list(result.all())
