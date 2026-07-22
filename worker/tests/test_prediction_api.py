from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import BigInteger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.apis.ai_predictions import router
from app.core.db.databases import Base, async_get_db
from app.core.dependencies import get_current_user
from app.models.enums import Department, Gender, Role
from app.models.medical_record import MedicalRecord
from app.models.patient import Patient
from app.models.user import User
from app.models.xray_image import XrayImage


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


def make_user(role: Role = Role.STAFF) -> User:
    return User(
        id=1,
        email="doctor@example.com",
        hashed_password="unused",
        name="의료진",
        phone_number="01012345678",
        gender=Gender.F,
        department=Department.MEDICAL,
        role=role,
        is_active=True,
    )


app = FastAPI()
app.include_router(router)
app.dependency_overrides[async_get_db] = override_get_db
current_user = make_user()
app.dependency_overrides[get_current_user] = lambda: current_user


@pytest_asyncio.fixture(autouse=True)
async def reset_database(tmp_path, monkeypatch) -> AsyncGenerator[None, None]:
    global current_user
    current_user = make_user()
    monkeypatch.chdir(tmp_path)
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        yield test_client


async def seed_record(*, with_xray: bool = True) -> int:
    async with TestSessionLocal() as db:
        patient = Patient(
            id=1,
            name="김환자",
            age=45,
            gender=Gender.M,
            phone="01011112222",
        )
        record = MedicalRecord(
            id=1,
            patient_id=1,
            chart_number="CHART-001",
            symptoms="기침과 발열",
        )
        db.add_all([patient, record])
        if with_xray:
            image_path = Path("media/xray/test.png")
            image_path.parent.mkdir(parents=True, exist_ok=True)
            Image.new("L", (128, 128), color=128).save(image_path)
            db.add(
                XrayImage(
                    id=1,
                    record_id=1,
                    uploader_id=None,
                    image_url="/media/xray/test.png",
                    shooting_datetime=datetime.now(UTC).replace(tzinfo=None),
                )
            )
        await db.commit()
        return record.id


async def test_predict_and_list_analyses(client: AsyncClient) -> None:
    record_id = await seed_record()

    response = await client.post(f"/api/v1/medical-records/{record_id}/predict")
    assert response.status_code == 201, response.text
    prediction = response.json()
    assert prediction["record_id"] == record_id
    assert isinstance(prediction["is_pneumonia"], bool)
    assert 0 <= prediction["confidence"] <= 100
    assert prediction["ai_model"] == "SimpleCNN-v1"
    assert prediction["heatmap_url"] == ""

    response = await client.get(f"/api/v1/medical-records/{record_id}/analyses")
    assert response.status_code == 200, response.text
    analyses = response.json()
    assert len(analyses) == 1
    assert analyses[0]["id"] == prediction["id"]


async def test_missing_record_returns_404(client: AsyncClient) -> None:
    response = await client.post("/api/v1/medical-records/999/predict")
    assert response.status_code == 404
    assert response.json()["detail"] == "진료기록을 찾을 수 없습니다."


async def test_record_without_xray_returns_404(client: AsyncClient) -> None:
    record_id = await seed_record(with_xray=False)
    response = await client.post(f"/api/v1/medical-records/{record_id}/predict")
    assert response.status_code == 404
    assert response.json()["detail"] == "진료기록에 등록된 X-ray 이미지가 없습니다."


async def test_pending_user_is_forbidden(client: AsyncClient) -> None:
    global current_user
    current_user = make_user(role=Role.PENDING)

    response = await client.get("/api/v1/medical-records/1/analyses")
    assert response.status_code == 403
