import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import Gender


def normalize_patient_phone(value: object) -> object:
    if not isinstance(value, str):
        return value
    normalized = re.sub(r"[^0-9]", "", value)
    if not re.fullmatch(r"01\d{8,9}", normalized):
        raise ValueError("전화번호는 01로 시작하는 10~11자리 숫자여야 합니다.")
    return normalized


class PatientCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    age: int = Field(ge=0, le=150)
    gender: Gender
    phone: str

    @field_validator("name", mode="after")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("이름을 입력해주세요.")
        return normalized

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: object) -> object:
        return normalize_patient_phone(value)


class PatientListQuery(BaseModel):
    name: str | None = Field(default=None, max_length=30)
    gender: Gender | None = None
    min_age: int | None = Field(default=None, ge=0, le=150)
    max_age: int | None = Field(default=None, ge=0, le=150)

    @field_validator("name", mode="after")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, value: object) -> object:
        if value in (None, ""):
            return None
        if isinstance(value, str):
            return value.strip().upper()
        return value


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: Gender
    phone: str
    created_at: datetime
    updated_at: datetime | None
