from fastapi import APIRouter, status

from app.core.dependencies import (
    CurrentApprovedUser,
    CurrentMedicalStaff,
    DbSession,
)
from app.schemas.medical_record import MedicalRecordListItem
from app.services import medical_record_service, patient_service


router = APIRouter(prefix="/api/v1/patients", tags=["Patient"])


@router.get(
    "/{patient_id}/medical-records",
    response_model=list[MedicalRecordListItem],
    summary="환자별 진료기록 목록 조회",
)
async def get_patient_records(
    patient_id: int,
    approved_user: CurrentApprovedUser,
    db: DbSession,
) -> list[MedicalRecordListItem]:
    del approved_user
    return await medical_record_service.list_records(db, patient_id)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="환자 삭제",
)
async def delete_patient(
    patient_id: int,
    medical_staff: CurrentMedicalStaff,
    db: DbSession,
) -> None:
    del medical_staff
    await patient_service.soft_delete(db, patient_id)
