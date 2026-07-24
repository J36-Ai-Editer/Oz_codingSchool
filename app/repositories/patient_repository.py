from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient


async def get_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    return await db.scalar(select(Patient).where(Patient.id == patient_id))


async def get_active_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    # 소프트 삭제된 환자는 없는 것으로 취급한다.
    return await db.scalar(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.is_deleted.is_(False),
        )
    )


async def save(db: AsyncSession, patient: Patient) -> Patient:
    await db.flush()
    await db.refresh(patient)
    return patient


async def list_active(
    db: AsyncSession,
    *,
    name: str | None = None,
    gender: str | None = None,
    min_age: int | None = None,
    max_age: int | None = None,
) -> list[Patient]:
    query = select(Patient).where(Patient.is_deleted.is_(False))
    if name:
        query = query.where(Patient.name.contains(name))
    if gender:
        query = query.where(Patient.gender == gender)
    if min_age is not None:
        query = query.where(Patient.age >= min_age)
    if max_age is not None:
        query = query.where(Patient.age <= max_age)
    result = await db.scalars(query.order_by(Patient.id))
    return list(result.all())
