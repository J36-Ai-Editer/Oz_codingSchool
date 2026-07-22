from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ai_analysis_result import AIAnalysisResult
from app.models.medical_record import MedicalRecord


async def get_record_with_xrays(
    db: AsyncSession,
    record_id: int,
) -> MedicalRecord | None:
    statement = (
        select(MedicalRecord)
        .options(selectinload(MedicalRecord.xray_images))
        .where(MedicalRecord.id == record_id)
    )
    return await db.scalar(statement)


async def create(
    db: AsyncSession,
    analysis: AIAnalysisResult,
) -> AIAnalysisResult:
    if db.get_bind().dialect.name == "sqlite":
        max_id = await db.scalar(select(func.max(AIAnalysisResult.id)))
        analysis.id = (max_id or 0) + 1

    db.add(analysis)
    await db.flush()
    await db.refresh(analysis)
    return analysis


async def list_by_record(
    db: AsyncSession,
    record_id: int,
) -> list[AIAnalysisResult]:
    result = await db.scalars(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(AIAnalysisResult.created_at.desc(), AIAnalysisResult.id.desc())
    )
    return list(result.all())
