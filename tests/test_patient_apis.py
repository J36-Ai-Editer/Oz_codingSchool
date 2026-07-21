from httpx import AsyncClient

from app.core.security import create_access_token, hash_password
from app.models.enums import Department, Gender, Role
from app.models.patient import Patient
from app.models.user import User
from tests.conftest import TestSessionLocal


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_user(
    *,
    email: str,
    phone_number: str,
    department: Department,
    role: Role,
) -> tuple[User, str]:
    async with TestSessionLocal() as db:
        user = User(
            email=email,
            hashed_password=hash_password("Password1!"),
            name="테스트사용자",
            phone_number=phone_number,
            gender=Gender.F,
            department=department,
            role=role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        token = create_access_token(user.id)
        return user, token


async def create_patient(
    *,
    patient_id: int,
    name: str,
    age: int,
    gender: Gender,
    phone: str,
) -> Patient:
    async with TestSessionLocal() as db:
        patient = Patient(
            id=patient_id,
            name=name,
            age=age,
            gender=gender,
            phone=phone,
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
        return patient


async def test_openapi_contains_patient_operations(
    client: AsyncClient,
) -> None:
    response = await client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "get" in paths["/api/v1/patients"]
    assert "patch" in paths["/api/v1/patients/{patient_id}"]


async def test_patient_list_search_and_filters(
    client: AsyncClient,
) -> None:
    _, pending_token = await create_user(
        email="pending@example.com",
        phone_number="01011111111",
        department=Department.MEDICAL,
        role=Role.PENDING,
    )
    _, staff_token = await create_user(
        email="staff@example.com",
        phone_number="01022222222",
        department=Department.DEV,
        role=Role.STAFF,
    )

    await create_patient(
        patient_id=1,
        name="김철수",
        age=42,
        gender=Gender.M,
        phone="01033333333",
    )
    await create_patient(
        patient_id=2,
        name="김영희",
        age=35,
        gender=Gender.F,
        phone="01044444444",
    )
    await create_patient(
        patient_id=3,
        name="이연구",
        age=29,
        gender=Gender.F,
        phone="01055555555",
    )

    response = await client.get("/api/v1/patients")
    assert response.status_code == 401

    response = await client.get(
        "/api/v1/patients",
        headers=authorization(pending_token),
    )
    assert response.status_code == 403

    response = await client.get(
        "/api/v1/patients",
        headers=authorization(staff_token),
    )
    assert response.status_code == 200
    assert [patient["id"] for patient in response.json()] == [1, 2, 3]

    response = await client.get(
        "/api/v1/patients",
        headers=authorization(staff_token),
        params={
            "name": "김",
            "gender": "F",
            "min_age": 30,
            "max_age": 40,
        },
    )
    assert response.status_code == 200, response.text
    assert [patient["id"] for patient in response.json()] == [2]

    response = await client.get(
        "/api/v1/patients",
        headers=authorization(staff_token),
        params={"name": "존재하지않음"},
    )
    assert response.status_code == 200
    assert response.json() == []

    response = await client.get(
        "/api/v1/patients",
        headers=authorization(staff_token),
        params={"min_age": 60, "max_age": 20},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "나이 범위가 올바르지 않습니다."

    response = await client.get(
        "/api/v1/patients",
        headers=authorization(staff_token),
        params={"gender": "UNKNOWN"},
    )
    assert response.status_code == 422


async def test_patient_update_permissions_and_validation(
    client: AsyncClient,
) -> None:
    _, dev_staff_token = await create_user(
        email="dev@example.com",
        phone_number="01011112222",
        department=Department.DEV,
        role=Role.STAFF,
    )
    _, medical_staff_token = await create_user(
        email="medical@example.com",
        phone_number="01022223333",
        department=Department.MEDICAL,
        role=Role.STAFF,
    )
    _, admin_token = await create_user(
        email="admin-patient@example.com",
        phone_number="01033334444",
        department=Department.DEV,
        role=Role.ADMIN,
    )

    await create_patient(
        patient_id=10,
        name="수정전환자",
        age=50,
        gender=Gender.M,
        phone="01055556666",
    )

    response = await client.patch(
        "/api/v1/patients/10",
        headers=authorization(dev_staff_token),
        json={"name": "권한없는수정"},
    )
    assert response.status_code == 403

    response = await client.patch(
        "/api/v1/patients/10",
        headers=authorization(medical_staff_token),
        json={
            "name": "수정된환자",
            "phone": "010-7777-8888",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["name"] == "수정된환자"
    assert response.json()["phone"] == "01077778888"
    assert response.json()["age"] == 50
    assert response.json()["gender"] == "M"

    response = await client.patch(
        "/api/v1/patients/10",
        headers=authorization(medical_staff_token),
        json={},
    )
    assert response.status_code == 400

    response = await client.patch(
        "/api/v1/patients/10",
        headers=authorization(medical_staff_token),
        json={"age": 20},
    )
    assert response.status_code == 422

    response = await client.patch(
        "/api/v1/patients/10",
        headers=authorization(medical_staff_token),
        json={"phone": "1234"},
    )
    assert response.status_code == 422

    response = await client.patch(
        "/api/v1/patients/999999",
        headers=authorization(medical_staff_token),
        json={"name": "없는환자"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "환자를 찾을 수 없습니다."

    response = await client.patch(
        "/api/v1/patients/10",
        headers=authorization(admin_token),
        json={"name": "관리자수정"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "관리자수정"
