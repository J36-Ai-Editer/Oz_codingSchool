from httpx import AsyncClient

from app.core.security import hash_password
from app.models.enums import Department, Gender, Role
from app.models.user import User
from tests.conftest import TestSessionLocal


async def create_admin() -> User:
    async with TestSessionLocal() as db:
        admin = User(
            email="admin@example.com",
            hashed_password=hash_password("AdminPassword1!"),
            name="관리자",
            phone_number="01099998888",
            gender=Gender.F,
            department=Department.DEV,
            role=Role.ADMIN,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        return admin


async def login(
    client: AsyncClient,
    *,
    email: str,
    password: str,
) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/users/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200, response.text
    assert "HttpOnly" in response.headers["set-cookie"]
    body = response.json()
    return body["access_token"], response.cookies["refresh_token"]


def authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_openapi_contains_all_ten_user_operations(client: AsyncClient) -> None:
    docs_response = await client.get("/docs")
    assert docs_response.status_code == 200
    assert "Swagger UI" in docs_response.text

    response = await client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    user_paths = {
        path: operations
        for path, operations in paths.items()
        if path.startswith("/api/v1/users")
        or path.startswith("/api/v1/admin/users")
    }
    assert sum(len(operations) for operations in user_paths.values()) == 10


async def test_complete_user_and_admin_flow(client: AsyncClient) -> None:
    signup_payload = {
        "email": "user@example.com",
        "password": "Password1!",
        "name": "테스트사용자",
        "department": "developer",
        "gender": "male",
        "phone_number": "010-1234-5678",
    }
    response = await client.post("/api/v1/users/signup", json=signup_payload)
    assert response.status_code == 201, response.text
    user = response.json()
    user_id = user["id"]
    assert user["department"] == "DEV"
    assert user["gender"] == "M"
    assert user["phone_number"] == "01012345678"
    assert user["role"] == "PENDING"
    assert "password" not in user
    assert "hashed_password" not in user

    response = await client.post("/api/v1/users/signup", json=signup_payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "이미 사용 중인 이메일입니다."

    response = await client.post(
        "/api/v1/users/login",
        data={"username": "user@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401

    user_token, _ = await login(
        client,
        email="user@example.com",
        password="Password1!",
    )

    response = await client.post(
        "/api/v1/users/refresh",
    )
    assert response.status_code == 200, response.text
    assert response.json()["token_type"] == "bearer"

    response = await client.get(
        "/api/v1/users/me",
        headers=authorization(user_token),
    )
    assert response.status_code == 200
    assert response.json()["email"] == "user@example.com"

    response = await client.patch(
        "/api/v1/users/me",
        headers=authorization(user_token),
        json={},
    )
    assert response.status_code == 400

    response = await client.patch(
        "/api/v1/users/me",
        headers=authorization(user_token),
        json={"department": "researcher", "phone_number": "010-7777-8888"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["department"] == "RESEARCH"
    assert response.json()["phone_number"] == "01077778888"

    response = await client.patch(
        "/api/v1/users/me/password",
        headers=authorization(user_token),
        json={
            "current_password": "WrongPassword1!",
            "new_password": "NewPassword2@",
        },
    )
    assert response.status_code == 400

    response = await client.patch(
        "/api/v1/users/me/password",
        headers=authorization(user_token),
        json={
            "current_password": "Password1!",
            "new_password": "NewPassword2@",
        },
    )
    assert response.status_code == 200, response.text

    response = await client.post(
        "/api/v1/users/login",
        data={"username": "user@example.com", "password": "Password1!"},
    )
    assert response.status_code == 401
    user_token, _ = await login(
        client,
        email="user@example.com",
        password="NewPassword2@",
    )

    admin = await create_admin()
    admin_token, _ = await login(
        client,
        email="admin@example.com",
        password="AdminPassword1!",
    )

    response = await client.get(
        "/api/v1/admin/users",
        headers=authorization(user_token),
    )
    assert response.status_code == 403

    response = await client.get(
        "/api/v1/admin/users",
        headers=authorization(admin_token),
        params={"query": "user", "department": "researcher"},
    )
    assert response.status_code == 200, response.text
    assert [listed_user["id"] for listed_user in response.json()] == [user_id]

    response = await client.patch(
        "/api/v1/admin/users/role",
        headers=authorization(admin_token),
        json={"user_id": user_id, "new_role": "staff"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["role"] == "STAFF"

    response = await client.patch(
        "/api/v1/admin/users/role",
        headers=authorization(admin_token),
        json={"user_id": admin.id, "new_role": "STAFF"},
    )
    assert response.status_code == 400

    # 존재하지 않는 user_id로 권한 변경 시도 → 404
    response = await client.patch(
        "/api/v1/admin/users/role",
        headers=authorization(admin_token),
        json={"user_id": 999999, "new_role": "STAFF"},
    )
    assert response.status_code == 404

    response = await client.post(
        "/api/v1/users/logout",
        headers=authorization(user_token),
    )
    assert response.status_code == 204
    assert "refresh_token=\"\"" in response.headers["set-cookie"]

    response = await client.delete(
        "/api/v1/users/me",
        headers=authorization(user_token),
    )
    assert response.status_code == 204

    response = await client.get(
        "/api/v1/users/me",
        headers=authorization(user_token),
    )
    assert response.status_code == 401

    response = await client.post(
        "/api/v1/users/login",
        data={"username": "user@example.com", "password": "NewPassword2@"},
    )
    assert response.status_code == 401


async def test_signup_validation_and_missing_auth(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/users/signup",
        json={
            "email": "invalid-email",
            "password": "weak",
            "name": "한",
            "department": "unknown",
            "gender": "unknown",
            "phone_number": "1234",
        },
    )
    assert response.status_code == 422

    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401

    response = await client.post("/api/v1/users/refresh")
    assert response.status_code == 401
