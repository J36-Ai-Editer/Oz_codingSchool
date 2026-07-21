from datetime import datetime

from pydantic import BaseModel, ConfigDict


class XrayImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: str
    shooting_datetime: datetime
    created_at: datetime


class MedicalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    xray_images: list[XrayImageResponse]
    created_at: datetime
    updated_at: datetime | None = None
