import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.enums import Gender


def normalize_phone(value: str) -> str:
    normalized = re.sub(r"[^0-9]", "", value)
    if not re.fullmatch(r"01\d{8,9}", normalized):
        raise ValueError("전화번호는 01로 시작하는 10~11자리 숫자여야 합니다.")
    return normalized


class PatientCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    age: int = Field(ge=0, le=150)
    gender: Gender
    phone: str

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("이름을 입력해주세요.")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)


class PatientUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=30)
    phone: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("이름을 입력해주세요.")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return normalize_phone(value) if value is not None else None

    @model_validator(mode="after")
    def reject_nulls(self) -> "PatientUpdateRequest":
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("수정 항목에 null을 입력할 수 없습니다.")
        return self


class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: Gender
    phone: str
