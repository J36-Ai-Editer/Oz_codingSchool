import re
from datetime import datetime
from typing import Annotated

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from app.models.enums import Department, Gender, Role


def validate_password(value: str) -> str:
    if not re.search(r"[A-Z]", value):
        raise ValueError("비밀번호에 영문 대문자가 1개 이상 필요합니다.")
    if not re.search(r"[a-z]", value):
        raise ValueError("비밀번호에 영문 소문자가 1개 이상 필요합니다.")
    if not re.search(r"\d", value):
        raise ValueError("비밀번호에 숫자가 1개 이상 필요합니다.")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("비밀번호에 특수문자가 1개 이상 필요합니다.")
    return value


Password = Annotated[
    str,
    StringConstraints(min_length=8, max_length=20),
    AfterValidator(validate_password),
]


def normalize_phone_number(value: object) -> object:
    if not isinstance(value, str):
        return value
    normalized = re.sub(r"[^0-9]", "", value)
    if not re.fullmatch(r"01\d{8,9}", normalized):
        raise ValueError("전화번호는 01로 시작하는 10~11자리 숫자여야 합니다.")
    return normalized


def normalize_department(value: object) -> object:
    if not isinstance(value, str):
        return value
    aliases = {
        "developer": Department.DEV.value,
        "medical team": Department.MEDICAL.value,
        "researcher": Department.RESEARCH.value,
    }
    return aliases.get(value.strip().lower(), value.strip().upper())


def normalize_gender(value: object) -> object:
    if not isinstance(value, str):
        return value
    aliases = {"male": Gender.M.value, "female": Gender.F.value}
    return aliases.get(value.strip().lower(), value.strip().upper())


def normalize_role(value: object) -> object:
    if not isinstance(value, str):
        return value
    return value.strip().upper()


class UserSignupRequest(BaseModel):
    email: EmailStr = Field(max_length=255)
    password: Password
    name: str = Field(min_length=2, max_length=20)
    department: Department
    gender: Gender
    phone_number: str

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("name", mode="after")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("department", mode="before")
    @classmethod
    def accept_frontend_department(cls, value: object) -> object:
        return normalize_department(value)

    @field_validator("gender", mode="before")
    @classmethod
    def accept_frontend_gender(cls, value: object) -> object:
        return normalize_gender(value)

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone(cls, value: object) -> object:
        return normalize_phone_number(value)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    department: Department
    gender: Gender
    phone_number: str
    role: Role
    is_active: bool
    created_at: datetime

class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: EmailStr
    department: Department
    gender: Gender
    phone_number: str
    role: Role

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserListQuery(BaseModel):
    query: str | None = Field(default=None, max_length=255)
    department: Department | None = None

    @field_validator("query", mode="after")
    @classmethod
    def normalize_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("department", mode="before")
    @classmethod
    def accept_frontend_department(cls, value: object) -> object:
        if value in (None, ""):
            return None
        return normalize_department(value)


class UserUpdateRequest(BaseModel):
    # 마이페이지 수정은 요구사항에 따라 부서와 휴대폰 번호만 허용합니다.
    department: Department | None = None
    phone_number: str | None = None

    @field_validator("department", mode="before")
    @classmethod
    def accept_frontend_department(cls, value: object) -> object:
        return normalize_department(value)

    @field_validator("phone_number", mode="before")
    @classmethod
    def validate_phone(cls, value: object) -> object:
        if value is None:
            return value
        return normalize_phone_number(value)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "UserUpdateRequest":
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("수정 항목에 null을 입력할 수 없습니다.")
        return self


class PasswordUpdateRequest(BaseModel):
    # 비밀번호 변경 시 기존 비밀번호와 새 비밀번호를 함께 입력받습니다.
    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password


class UserRoleUpdateRequest(BaseModel):
    user_id: int = Field(ge=1)
    new_role: Role

    @field_validator("new_role", mode="before")
    @classmethod
    def accept_lowercase_role(cls, value: object) -> object:
        return normalize_role(value)


class MessageResponse(BaseModel):
    message: str
