from collections.abc import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.apis.patients import router
from app.core.db.databases import async_get_db
from app.core.dependencies import get_current_user
from app.models.enums import Department, Gender, Role
from app.models.patient import Patient
from app.models.user import User


@compiles(BigInteger, "sqlite")
def compile_big_integer_as_integer(type_, compiler, **kwargs):  # type: ignore[no-untyped-def]
    del type_, compiler, kwargs
    return "INTEGER"


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


def build_user(*, role: Role, department: Department) -> User:
    return User(
        id=1,
        email="staff@example.com",
        hashed_password="unused",
        name="테스트직원",
        phone_number="01099998888",
        gender=Gender.F,
        department=department,
        role=role,
        is_active=True,
    )


app = FastAPI()
app.include_router(router)
app.dependency_overrides[async_get_db] = override_get_db
current_user = build_user(role=Role.STAFF, department=Department.MEDICAL)
app.dependency_overrides[get_current_user] = lambda: current_user


@pytest_asyncio.fixture(autouse=True)
async def reset_patient_table() -> AsyncGenerator[None, None]:
    global current_user
    current_user = build_user(role=Role.STAFF, department=Department.MEDICAL)
    async with test_engine.begin() as connection:
        await connection.run_sync(Patient.__table__.create, checkfirst=True)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Patient.__table__.drop, checkfirst=True)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


async def test_create_patient_normalizes_input(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/patients",
        json={
            "name": "  김환자  ",
            "age": 42,
            "gender": "m",
            "phone": "010-1234-5678",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["id"] == 1
    assert body["name"] == "김환자"
    assert body["gender"] == "M"
    assert body["phone"] == "01012345678"
    assert "created_at" in body


async def test_list_patients_combines_filters(client: AsyncClient) -> None:
    patients = [
        {"name": "김환자", "age": 42, "gender": "M", "phone": "01011112222"},
        {"name": "김영희", "age": 26, "gender": "F", "phone": "01033334444"},
        {"name": "박환자", "age": 50, "gender": "M", "phone": "01055556666"},
    ]
    for patient in patients:
        response = await client.post("/api/v1/patients", json=patient)
        assert response.status_code == 201, response.text

    response = await client.get(
        "/api/v1/patients",
        params={"name": "김", "gender": "M", "min_age": 30, "max_age": 45},
    )

    assert response.status_code == 200, response.text
    assert [patient["name"] for patient in response.json()] == ["김환자"]


async def test_list_rejects_invalid_age_range(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/patients",
        params={"min_age": 50, "max_age": 20},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "나이 범위가 올바르지 않습니다."


async def test_permissions(client: AsyncClient) -> None:
    global current_user

    current_user = build_user(role=Role.PENDING, department=Department.MEDICAL)
    response = await client.get("/api/v1/patients")
    assert response.status_code == 403

    current_user = build_user(role=Role.STAFF, department=Department.DEV)
    response = await client.post(
        "/api/v1/patients",
        json={"name": "권한없음", "age": 30, "gender": "F", "phone": "01077778888"},
    )
    assert response.status_code == 403

    response = await client.get("/api/v1/patients")
    assert response.status_code == 200

    current_user = build_user(role=Role.ADMIN, department=Department.DEV)
    response = await client.post(
        "/api/v1/patients",
        json={"name": "관리자등록", "age": 35, "gender": "M", "phone": "01088889999"},
    )
    assert response.status_code == 201
