from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import Gender
from app.schemas.user import normalize_gender, normalize_phone_number


class PatientListQuery(BaseModel):
    """환자 목록 조회 시 이름·성별·나이 범위를 검증하는 Query Schema."""

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
    def accept_frontend_gender(cls, value: object) -> object:
        if value is None:
            return value
        return normalize_gender(value)


class PatientUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    """환자 이름과 연락처의 부분 수정을 검증하는 Request Schema."""

    name: str | None = Field(default=None, min_length=1, max_length=30)
    phone: str | None = Field(default=None, max_length=11)

    @field_validator("name", mode="after")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            raise ValueError("이름은 공백으로만 입력할 수 없습니다.")
        return normalized

    @field_validator("phone", mode="before")
    @classmethod
    def validate_phone(cls, value: object) -> object:
        if value is None:
            return value
        return normalize_phone_number(value)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "PatientUpdateRequest":
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("수정 항목에 null을 입력할 수 없습니다.")
        return self


class PatientResponse(BaseModel):
    """환자 목록 조회 및 수정 성공 시 반환하는 Response Schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: Gender | None
    phone: str
    created_at: datetime
    updated_at: datetime | None
