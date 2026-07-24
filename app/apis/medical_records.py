from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, File, Form, Path, UploadFile, status

from app.core.dependencies import CurrentApprovedUser, CurrentMedicalStaff, DbSession
from app.schemas.medical_record import MedicalRecordResponse
from app.services import medical_record_service


router = APIRouter(tags=["Medical Records"])


@router.post(
    "/api/v1/patients/{patient_id}/medical-records",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="진료기록 등록",
)
async def create_medical_record(
    patient_id: Annotated[int, Path(...)],
    current_user: CurrentMedicalStaff,
    db: DbSession,
    chart_number: Annotated[str, Form(min_length=1, max_length=50)],
    symptoms: Annotated[str, Form(min_length=1)],
    xray_image: Annotated[UploadFile, File()],
    shooting_datetime: Annotated[datetime | None, Form()] = None,
) -> MedicalRecordResponse:
    return await medical_record_service.create_medical_record(
        db,
        patient_id=patient_id,
        chart_number=chart_number,
        symptoms=symptoms,
        xray_image=xray_image,
        current_user=current_user,
        shooting_datetime=shooting_datetime,
    )


@router.get(
    "/api/v1/medical-records/{record_id}",
    response_model=MedicalRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="진료기록 상세 조회",
)
async def get_medical_record_detail(
    record_id: Annotated[int, Path(...)],
    current_user: CurrentApprovedUser,
    db: DbSession,
) -> MedicalRecordResponse:
    del current_user
    return await medical_record_service.get_medical_record(db, record_id)
