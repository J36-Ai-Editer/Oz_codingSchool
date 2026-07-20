import re

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator


# =========================================================
# 1. Router 생성
# =========================================================

router = APIRouter(
    prefix="/practice_api",
    tags=["Practice API"],
)


# =========================================================
# 2. 기본 회원 데이터
# =========================================================

user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Passw0rd1234!!",
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!!",
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPassword12@",
    },
]


# =========================================================
# 3. 검증에 사용할 정규표현식
# =========================================================

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

UPPERCASE_PATTERN = re.compile(r"[A-Z]")

# 영문자와 숫자가 아닌 문자를 특수문자로 판단
SPECIAL_CHARACTER_PATTERN = re.compile(r"[^A-Za-z0-9]")


# =========================================================
# 4. 공통 검증 함수
# =========================================================

def validate_email_format(email: str) -> str:
    """이메일 형식이 올바른지 검사합니다."""

    email = email.lower()

    if not EMAIL_PATTERN.fullmatch(email):
        raise ValueError("올바른 이메일 형식이 아닙니다.")

    return email


def validate_password_format(password: str) -> str:
    """비밀번호에 대문자와 특수문자가 포함되었는지 검사합니다."""

    if not UPPERCASE_PATTERN.search(password):
        raise ValueError("비밀번호에는 대문자가 1개 이상 포함되어야 합니다.")

    if not SPECIAL_CHARACTER_PATTERN.search(password):
        raise ValueError("비밀번호에는 특수문자가 1개 이상 포함되어야 합니다.")

    return password


# =========================================================
# 5. Request / Response 모델
# =========================================================

class UserResponse(BaseModel):
    """API 응답으로 보여줄 회원 정보입니다."""

    id: int
    name: str
    age: int
    email: str


class UserCreate(BaseModel):
    """회원 추가 시 Request Body로 받을 값입니다."""

    name: str = Field(
        min_length=2,
        max_length=10,
        description="이름은 2자 이상 10자 이하입니다.",
    )

    age: int = Field(
        ge=14,
        description="나이는 14세 이상이어야 합니다.",
    )

    email: str = Field(
        max_length=30,
        description="이메일은 최대 30자까지 입력할 수 있습니다.",
    )

    password: str = Field(
        min_length=8,
        max_length=20,
        description="비밀번호는 8자 이상 20자 이하입니다.",
    )

    @field_validator("email")
    @classmethod
    def check_email(cls, email: str) -> str:
        return validate_email_format(email)

    @field_validator("password")
    @classmethod
    def check_password(cls, password: str) -> str:
        return validate_password_format(password)


class UserUpdate(BaseModel):
    """회원 수정 시 Request Body로 받을 값입니다."""

    age: int | None = Field(
        default=None,
        ge=14,
        description="나이는 14세 이상이어야 합니다.",
    )

    email: str | None = Field(
        default=None,
        max_length=30,
        description="이메일은 최대 30자까지 입력할 수 있습니다.",
    )

    password: str | None = Field(
        default=None,
        min_length=8,
        max_length=20,
        description="비밀번호는 8자 이상 20자 이하입니다.",
    )

    @field_validator("email")
    @classmethod
    def check_email(cls, email: str | None) -> str | None:
        if email is None:
            return None

        return validate_email_format(email)

    @field_validator("password")
    @classmethod
    def check_password(cls, password: str | None) -> str | None:
        if password is None:
            return None

        return validate_password_format(password)


# =========================================================
# 6. 회원 검색 공통 함수
# =========================================================

def find_user(user_id: int) -> dict:
    """ID가 일치하는 회원을 반환합니다."""

    for user in user_list:
        if user["id"] == user_id:
            return user

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="해당 ID의 회원을 찾을 수 없습니다.",
    )


# =========================================================
# API 1. 전체 회원 조회
# GET /practice_api/users
# =========================================================

@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="전체 회원 조회",
)
def get_users():
    return user_list


# =========================================================
# API 2. 특정 회원 조회
# GET /practice_api/users/{user_id}
# =========================================================

@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="특정 회원 조회",
)
def get_user(user_id: int):
    return find_user(user_id)


# =========================================================
# API 3. 회원 추가
# POST /practice_api/users
# =========================================================

@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원 추가",
)
def create_user(new_user: UserCreate):
    # 이메일 중복 여부 확인
    for user in user_list:
        if user["email"] == new_user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 사용 중인 이메일입니다.",
            )

    # 현재 가장 큰 ID에 1을 더해서 새 ID 생성
    new_id = max(
        (user["id"] for user in user_list),
        default=0,
    ) + 1

    new_user_data = {
        "id": new_id,
        **new_user.model_dump(),
    }

    user_list.append(new_user_data)

    return new_user_data


# =========================================================
# API 4. 회원 정보 수정
# PATCH /practice_api/users/{user_id}
# =========================================================

@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    summary="회원 정보 수정",
)
def update_user(user_id: int, update_request: UserUpdate):
    user = find_user(user_id)

    # 실제로 전달된 값만 딕셔너리로 변환
    update_data = update_request.model_dump(
        exclude_unset=True,
        exclude_none=True,
    )

    # 아무 값도 입력하지 않은 경우
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목을 한 개 이상 입력해야 합니다.",
        )

    # 이메일을 수정하는 경우 중복 검사
    if "email" in update_data:
        for saved_user in user_list:
            if (
                saved_user["id"] != user_id
                and saved_user["email"] == update_data["email"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 사용 중인 이메일입니다.",
                )

    # 입력받은 값만 기존 회원 정보에 반영
    user.update(update_data)

    return user


# =========================================================
# API 5. 회원 삭제
# DELETE /practice_api/users/{user_id}
# =========================================================

@router.delete(
    "/users/{user_id}",
    summary="회원 삭제",
)
def delete_user(user_id: int):
    user = find_user(user_id)

    user_list.remove(user)

    return {
        "message": f"{user_id}번 회원이 삭제되었습니다.",
    }