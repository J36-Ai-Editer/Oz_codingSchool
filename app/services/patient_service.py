from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.repositories import patient_repository
from app.schemas.patient import PatientCreateRequest, PatientListQuery


async def create_patient(
    db: AsyncSession,
    request: PatientCreateRequest,
) -> Patient:
    patient = Patient(**request.model_dump())
    await patient_repository.create(db, patient)
    await db.commit()
    return patient


async def list_patients(
    db: AsyncSession,
    query: PatientListQuery,
) -> list[Patient]:
    if (
        query.min_age is not None
        and query.max_age is not None
        and query.min_age > query.max_age
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="나이 범위가 올바르지 않습니다.",
        )
    return await patient_repository.list_patients(
        db,
        name=query.name,
        gender=query.gender,
        min_age=query.min_age,
        max_age=query.max_age,
    )
