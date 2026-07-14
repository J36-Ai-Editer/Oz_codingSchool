import re
from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator


router = APIRouter(prefix="/practice_api", tags=["practice_api"])

user_list = [
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

_next_user_id = max(user["id"] for user in user_list) + 1
EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


def validate_email(value: str) -> str:
    if EMAIL_PATTERN.fullmatch(value) is None:
        raise ValueError("올바른 이메일 형식이 아닙니다.")
    return value


def validate_password(value: str) -> str:
    if not any(character.isupper() for character in value):
        raise ValueError("비밀번호에는 대문자가 1개 이상 필요합니다.")
    if not any(character.islower() for character in value):
        raise ValueError("비밀번호에는 소문자가 1개 이상 필요합니다.")
    if not any(
        not character.isalnum() and not character.isspace() for character in value
    ):
        raise ValueError("비밀번호에는 특수문자가 1개 이상 필요합니다.")
    return value


Name = Annotated[str, Field(min_length=2, max_length=10)]
Age = Annotated[int, Field(ge=14)]
Email = Annotated[
    str,
    Field(max_length=30),
    AfterValidator(validate_email),
]
Password = Annotated[
    str,
    Field(min_length=8, max_length=20),
    AfterValidator(validate_password),
]


class UserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Name
    age: Age
    email: Email
    password: Password


class UserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    age: Age | None = None
    email: Email | None = None
    password: Password | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "UserUpdate":
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name}에는 null을 입력할 수 없습니다.")
        return self


class UserPublic(BaseModel):
    id: int
    name: str
    age: int
    email: str


def find_user(user_id: int) -> dict:
    for user in user_list:
        if user["id"] == user_id:
            return user
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="회원을 찾을 수 없습니다.",
    )


def ensure_email_is_unique(email: str, *, excluding_user_id: int | None = None) -> None:
    normalized_email = email.casefold()
    if any(
        user["email"].casefold() == normalized_email
        and user["id"] != excluding_user_id
        for user in user_list
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다.",
        )


@router.get("/users", response_model=list[UserPublic])
def get_users() -> list[dict]:
    """비밀번호를 제외한 모든 회원 정보를 조회합니다."""
    return user_list


@router.get("/users/{user_id}", response_model=UserPublic)
def get_user(user_id: int) -> dict:
    """ID로 특정 회원을 조회합니다."""
    return find_user(user_id)


@router.post(
    "/users",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def create_user(user_data: UserCreate) -> dict:
    """검증된 회원 정보를 추가하고 ID를 자동으로 부여합니다."""
    global _next_user_id

    ensure_email_is_unique(user_data.email)
    user = {"id": _next_user_id, **user_data.model_dump()}
    _next_user_id += 1
    user_list.append(user)
    return user


@router.patch("/users/{user_id}", response_model=UserPublic)
def update_user(user_id: int, user_data: UserUpdate) -> dict:
    """입력된 나이, 이메일, 비밀번호만 수정합니다."""
    user = find_user(user_id)
    updates = user_data.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목을 하나 이상 입력해야 합니다.",
        )

    if "email" in updates:
        ensure_email_is_unique(updates["email"], excluding_user_id=user_id)

    user.update(updates)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int) -> Response:
    """ID로 특정 회원을 삭제합니다."""
    user = find_user(user_id)
    user_list.remove(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
