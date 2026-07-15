from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from app.apis import practice_apis
from app.main import app


INITIAL_USERS = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!",
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!",
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@",
    },
]

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_user_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(practice_apis, "user_list", deepcopy(INITIAL_USERS))
    monkeypatch.setattr(practice_apis, "_next_user_id", 4)


def test_get_users_excludes_passwords() -> None:
    response = client.get("/practice_api/users")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert all("password" not in user for user in response.json())


def test_get_user_by_id() -> None:
    response = client.get("/practice_api/users/2")

    assert response.status_code == 200
    assert response.json() == {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
    }


def test_get_unknown_user_returns_404() -> None:
    response = client.get("/practice_api/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "회원을 찾을 수 없습니다."


def test_create_user_assigns_incrementing_id() -> None:
    response = client.post(
        "/practice_api/users",
        json={
            "name": "김코딩",
            "age": 20,
            "email": "coding@example.com",
            "password": "SecurePass!",
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": 4,
        "name": "김코딩",
        "age": 20,
        "email": "coding@example.com",
    }
    assert practice_apis.user_list[-1]["password"] == "SecurePass!"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("name", "김"),
        ("name", "가나다라마바사아자차카"),
        ("age", 13),
        ("email", "not-an-email"),
        ("email", "a" * 19 + "@example.com"),
        ("password", "short!A"),
        ("password", "lowercase!"),
        ("password", "UPPERCASE!"),
        ("password", "NoSpecial123"),
    ],
)
def test_create_user_rejects_invalid_fields(field: str, value: object) -> None:
    payload = {
        "name": "김코딩",
        "age": 20,
        "email": "coding@example.com",
        "password": "SecurePass!",
    }
    payload[field] = value

    response = client.post("/practice_api/users", json=payload)

    assert response.status_code == 422


def test_create_user_rejects_duplicate_email_case_insensitively() -> None:
    response = client.post(
        "/practice_api/users",
        json={
            "name": "김코딩",
            "age": 20,
            "email": "GILDONG24@EXAMPLE.COM",
            "password": "SecurePass!",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "이미 사용 중인 이메일입니다."


def test_update_user_changes_only_provided_fields() -> None:
    response = client.patch(
        "/practice_api/users/1",
        json={"age": 25, "email": "new-gildong@example.com"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "name": "홍길동",
        "age": 25,
        "email": "new-gildong@example.com",
    }
    assert practice_apis.user_list[0]["password"] == "Password1234!!"


def test_update_user_accepts_a_valid_password_without_exposing_it() -> None:
    response = client.patch(
        "/practice_api/users/1",
        json={"password": "ChangedPass!"},
    )

    assert response.status_code == 200
    assert "password" not in response.json()
    assert practice_apis.user_list[0]["password"] == "ChangedPass!"


def test_update_user_rejects_empty_body() -> None:
    response = client.patch("/practice_api/users/1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "수정할 항목을 하나 이상 입력해야 합니다."


def test_update_user_rejects_explicit_null() -> None:
    response = client.patch("/practice_api/users/1", json={"age": None})

    assert response.status_code == 422


def test_update_user_rejects_another_users_email() -> None:
    response = client.patch(
        "/practice_api/users/1",
        json={"email": "moonluck12@example.com"},
    )

    assert response.status_code == 409


def test_update_unknown_user_returns_404() -> None:
    response = client.patch("/practice_api/users/999", json={"age": 30})

    assert response.status_code == 404


def test_delete_user() -> None:
    response = client.delete("/practice_api/users/2")

    assert response.status_code == 204
    assert client.get("/practice_api/users/2").status_code == 404


def test_delete_unknown_user_returns_404() -> None:
    response = client.delete("/practice_api/users/999")

    assert response.status_code == 404
