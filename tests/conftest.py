from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.db.databases import async_get_db
from app.main import app
from app.models.patient import Patient
from app.models.user import User


test_engine = create_async_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[async_get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def reset_user_table() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as connection:
        await connection.run_sync(User.__table__.create, checkfirst=True)
        await connection.run_sync(Patient.__table__.create, checkfirst=True)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Patient.__table__.drop, checkfirst=True)
        await connection.run_sync(User.__table__.drop, checkfirst=True)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client
