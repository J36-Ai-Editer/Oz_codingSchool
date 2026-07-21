from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient


async def get_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    return await db.scalar(select(Patient).where(Patient.id == patient_id))
