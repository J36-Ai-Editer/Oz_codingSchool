from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Gender
from app.models.patient import Patient
from app.repositories import patient_repository
from app.schemas.patient import PatientUpdateRequest


async def _commit(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="환자 정보를 저장하는 중 충돌이 발생했습니다.",
        ) from exc


async def list_patients(
    db: AsyncSession,
    *,
    name: str | None,
    gender: Gender | None,
    min_age: int | None,
    max_age: int | None,
) -> list[Patient]:
    if (
        min_age is not None
        and max_age is not None
        and min_age > max_age
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="나이 범위가 올바르지 않습니다.",
        )

    return await patient_repository.list_patients(
        db,
        name=name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
    )


async def update_patient(
    db: AsyncSession,
    patient_id: int,
    request: PatientUpdateRequest,
) -> Patient:
    patient = await patient_repository.get_by_id(db, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )

    updates = request.model_dump(exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목을 하나 이상 입력해주세요.",
        )

    for field, value in updates.items():
        setattr(patient, field, value)

    await patient_repository.save(db, patient)
    await _commit(db)

    return patient
