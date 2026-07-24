from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.dependencies import (
    CurrentApprovedUser,
    CurrentMedicalStaff,
    DbSession,
)
from app.models.enums import Gender
from app.schemas.medical_record import MedicalRecordListItem
from app.schemas.patient import PatientCreateRequest, PatientResponse, PatientUpdateRequest
from app.services import medical_record_service, patient_service


router = APIRouter(prefix="/api/v1/patients", tags=["Patient"])


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="환자 등록",
)
async def create_patient(
    request: PatientCreateRequest, medical_staff: CurrentMedicalStaff, db: DbSession
) -> PatientResponse:
    del medical_staff
    return await patient_service.create(db, request)


@router.get("", response_model=list[PatientResponse], summary="환자 목록 조회")
async def list_patients(
    approved_user: CurrentApprovedUser,
    db: DbSession,
    name: Annotated[str | None, Query(max_length=30)] = None,
    gender: Gender | None = None,
    min_age: Annotated[int | None, Query(ge=0, le=150)] = None,
    max_age: Annotated[int | None, Query(ge=0, le=150)] = None,
) -> list[PatientResponse]:
    del approved_user
    return await patient_service.list_patients(
        db, name=name, gender=gender, min_age=min_age, max_age=max_age
    )


@router.get("/{patient_id}", response_model=PatientResponse, summary="환자 상세 조회")
async def get_patient(
    patient_id: int, approved_user: CurrentApprovedUser, db: DbSession
) -> PatientResponse:
    del approved_user
    return await patient_service.get(db, patient_id)


@router.patch("/{patient_id}", response_model=PatientResponse, summary="환자 정보 수정")
async def update_patient(
    patient_id: int,
    request: PatientUpdateRequest,
    medical_staff: CurrentMedicalStaff,
    db: DbSession,
) -> PatientResponse:
    del medical_staff
    return await patient_service.update(db, patient_id, request)


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
