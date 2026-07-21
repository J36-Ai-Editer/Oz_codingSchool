from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.models.enums import Department, Role
from app.models.user import User
from app.schemas.patient import (
    PatientCreateRequest,
    PatientListQuery,
    PatientResponse,
)
from app.services import patient_service


router = APIRouter(prefix="/api/v1/patients", tags=["Patient"])


async def require_approved_staff(current_user: CurrentUser) -> User:
    if current_user.role not in {Role.STAFF, Role.ADMIN}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다.",
        )
    return current_user


async def require_medical_staff(
    current_user: Annotated[User, Depends(require_approved_staff)],
) -> User:
    if current_user.role != Role.ADMIN and current_user.department != Department.MEDICAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="의료진 권한이 필요합니다.",
        )
    return current_user


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="환자 등록",
)
async def create_patient(
    request: PatientCreateRequest,
    db: DbSession,
    current_user: Annotated[User, Depends(require_medical_staff)],
) -> PatientResponse:
    del current_user
    return await patient_service.create_patient(db, request)


@router.get(
    "",
    response_model=list[PatientResponse],
    summary="환자 목록 조회",
)
async def list_patients(
    db: DbSession,
    current_user: Annotated[User, Depends(require_approved_staff)],
    query: Annotated[PatientListQuery, Query()],
) -> list[PatientResponse]:
    del current_user
    return await patient_service.list_patients(db, query)
