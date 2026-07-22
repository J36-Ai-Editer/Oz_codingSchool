from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from app.core.security import create_access_token, hash_password
from app.models.enums import Department, Gender, Role
from app.models.patient import Patient
from app.models.user import User
from tests.conftest import TestSessionLocal, test_engine


@pytest_asyncio.fixture(autouse=True)
async def reset_patient_table() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as connection:
        await connection.run_sync(Patient.__table__.create, checkfirst=True)
    yield
    async with test_engine.begin() as connection:
        await connection.run_sync(Patient.__table__.drop, checkfirst=True)


@pytest_asyncio.fixture
async def medical_token() -> str:
    async with TestSessionLocal() as db:
        user = User(
            email="day7-test@example.com",
            hashed_password=hash_password("Password1234!"),
            name="테스트의료진",
            department=Department.MEDICAL,
            gender=Gender.M,
            phone_number="01055556666",
            role=Role.STAFF,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return create_access_token(user.id)


@pytest.mark.asyncio
async def test_patient_crud_flow(client, medical_token: str) -> None:
    headers = {"Authorization": f"Bearer {medical_token}"}

    created = await client.post(
        "/api/v1/patients",
        headers=headers,
        json={"name": "김환자", "age": 42, "gender": "M", "phone": "01012345678"},
    )
    assert created.status_code == 201
    patient_id = created.json()["id"]

    listed = await client.get("/api/v1/patients?gender=M", headers=headers)
    assert listed.status_code == 200
    assert [patient["id"] for patient in listed.json()] == [patient_id]

    detail = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["phone"] == "01012345678"

    updated = await client.patch(
        f"/api/v1/patients/{patient_id}",
        headers=headers,
        json={"name": "김환자수정", "phone": "01099998888"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "김환자수정"

    deleted = await client.delete(f"/api/v1/patients/{patient_id}", headers=headers)
    assert deleted.status_code == 204

    missing = await client.get(f"/api/v1/patients/{patient_id}", headers=headers)
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_patient_age_range_validation(client, medical_token: str) -> None:
    response = await client.get(
        "/api/v1/patients?min_age=50&max_age=20",
        headers={"Authorization": f"Bearer {medical_token}"},
    )
    assert response.status_code == 400
