from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.apis import ai_predictions
from app.core.security import create_access_token, hash_password
from app.models.enums import Department, Gender, Role
from app.models.user import User
from tests.conftest import TestSessionLocal


async def create_test_user(role: Role) -> User:
    async with TestSessionLocal() as db:
        user = User(
            email=f"{role.value.lower()}@example.com",
            hashed_password=hash_password("Password1234!"),
            name="테스트사용자",
            department=Department.MEDICAL,
            gender=Gender.M,
            phone_number="01011112222",
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


def make_analysis(record_id: int = 10) -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        record_id=record_id,
        is_pneumonia=True,
        confidence=91.25,
        heatmap_url="",
        ai_model="SimpleCNN-v1",
        created_at=datetime(2026, 7, 22, 15, 0, 0),
        updated_at=None,
    )


@pytest.mark.asyncio
async def test_predict_pneumonia_success(client, monkeypatch) -> None:
    user = await create_test_user(Role.STAFF)
    token = create_access_token(user.id)

    async def fake_predict_record(db, record_id):
        assert record_id == 10
        return make_analysis(record_id)

    monkeypatch.setattr(
        ai_predictions.ai_analysis_service, "predict_record", fake_predict_record
    )
    response = await client.post(
        "/api/v1/medical-records/10/predict",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["record_id"] == 10
    assert response.json()["is_pneumonia"] is True
    assert response.json()["confidence"] == 91.25


@pytest.mark.asyncio
async def test_list_analyses_success(client, monkeypatch) -> None:
    user = await create_test_user(Role.STAFF)
    token = create_access_token(user.id)

    async def fake_list_record_analyses(db, record_id):
        return [make_analysis(record_id)]

    monkeypatch.setattr(
        ai_predictions.ai_analysis_service,
        "list_record_analyses",
        fake_list_record_analyses,
    )
    response = await client.get(
        "/api/v1/medical-records/10/analyses",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["ai_model"] == "SimpleCNN-v1"


@pytest.mark.asyncio
async def test_predict_requires_login(client) -> None:
    response = await client.post("/api/v1/medical-records/10/predict")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pending_user_cannot_predict(client) -> None:
    user = await create_test_user(Role.PENDING)
    token = create_access_token(user.id)
    response = await client.post(
        "/api/v1/medical-records/10/predict",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_predict_record_not_found(client, monkeypatch) -> None:
    user = await create_test_user(Role.STAFF)
    token = create_access_token(user.id)

    async def fake_predict_record(db, record_id):
        raise HTTPException(status_code=404, detail="진료기록을 찾을 수 없습니다.")

    monkeypatch.setattr(
        ai_predictions.ai_analysis_service, "predict_record", fake_predict_record
    )
    response = await client.post(
        "/api/v1/medical-records/999/predict",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "진료기록을 찾을 수 없습니다."
