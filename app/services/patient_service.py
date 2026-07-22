from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import patient_repository
from app.models.patient import Patient
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest


async def create(db: AsyncSession, request: PatientCreateRequest) -> Patient:
    patient = Patient(**request.model_dump())
    db.add(patient)
    await patient_repository.save(db, patient)
    await db.commit()
    return patient


async def list_patients(
    db: AsyncSession,
    *,
    name: str | None,
    gender: str | None,
    min_age: int | None,
    max_age: int | None,
) -> list[Patient]:
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(status_code=400, detail="나이 범위가 올바르지 않습니다.")
    return await patient_repository.list_active(
        db, name=name, gender=gender, min_age=min_age, max_age=max_age
    )


async def get(db: AsyncSession, patient_id: int) -> Patient:
    patient = await patient_repository.get_active_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="환자를 찾을 수 없습니다.")
    return patient


async def update(
    db: AsyncSession, patient_id: int, request: PatientUpdateRequest
) -> Patient:
    if not request.model_fields_set:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="수정할 항목을 하나 이상 입력해주세요.",
        )
    patient = await get(db, patient_id)
    for field, value in request.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    await patient_repository.save(db, patient)
    await db.commit()
    return patient


async def soft_delete(db: AsyncSession, patient_id: int) -> None:
    # 이미 삭제된 환자도 조회되지 않으므로 404가 된다.
    patient = await patient_repository.get_active_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )
    # 하드 삭제와 달리 진료기록·X-Ray는 보존하고 삭제 플래그만 세운다.
    patient.is_deleted = True
    patient.deleted_at = datetime.now(UTC).replace(tzinfo=None)
    await patient_repository.save(db, patient)
    await db.commit()
