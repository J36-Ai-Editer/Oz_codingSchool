from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.core.dependencies import (
    CurrentApprovedUser,
    CurrentMedicalStaff,
    DbSession,
)
from app.schemas.patient import (
    PatientListQuery,
    PatientResponse,
    PatientUpdateRequest,
)
from app.services import patient_service


router = APIRouter(prefix="/api/v1/patients", tags=["Patient"])


@router.get(
    "",
    response_model=list[PatientResponse],
    summary="환자 목록 조회",
)
async def get_patients(
    query: Annotated[PatientListQuery, Depends()],
    current_user: CurrentApprovedUser,
    db: DbSession,
) -> list[PatientResponse]:
    del current_user

    return await patient_service.list_patients(
        db,
        name=query.name,
        gender=query.gender,
        min_age=query.min_age,
        max_age=query.max_age,
    )


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="환자 정보 수정",
)
async def update_patient(
    patient_id: Annotated[int, Path(ge=1)],
    request: PatientUpdateRequest,
    current_user: CurrentMedicalStaff,
    db: DbSession,
) -> PatientResponse:
    del current_user

    return await patient_service.update_patient(
        db,
        patient_id,
        request,
    )
