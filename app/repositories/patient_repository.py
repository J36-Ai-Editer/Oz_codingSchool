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
