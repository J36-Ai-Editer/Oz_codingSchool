from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.medical_record import MedicalRecord
from app.models.xray_image import XrayImage


async def _next_id_for_sqlite(db: AsyncSession, model: type) -> int | None:
    bind = db.get_bind()
    if bind.dialect.name != "sqlite":
        return None
    max_id = await db.scalar(select(func.max(model.id)))
    return (max_id or 0) + 1


async def get_by_id(db: AsyncSession, record_id: int) -> MedicalRecord | None:
    statement = (
        select(MedicalRecord)
        .options(selectinload(MedicalRecord.xray_images))
        .where(MedicalRecord.id == record_id)
    )
    return await db.scalar(statement)


async def list_by_patient(
    db: AsyncSession,
    patient_id: int,
) -> list[MedicalRecord]:
    result = await db.scalars(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient_id)
        .order_by(MedicalRecord.id)
    )
    return list(result.all())


async def get_by_chart_number(
    db: AsyncSession,
    chart_number: str,
) -> MedicalRecord | None:
    return await db.scalar(
        select(MedicalRecord).where(MedicalRecord.chart_number == chart_number)
    )


async def create_with_xray_image(
    db: AsyncSession,
    medical_record: MedicalRecord,
    xray_image: XrayImage,
) -> MedicalRecord:
    medical_record.id = await _next_id_for_sqlite(db, MedicalRecord)
    db.add(medical_record)
    await db.flush()

    xray_image.record_id = medical_record.id
    xray_image.id = await _next_id_for_sqlite(db, XrayImage)
    db.add(xray_image)
    await db.flush()

    await db.refresh(medical_record)
    await db.refresh(xray_image)
    return medical_record
