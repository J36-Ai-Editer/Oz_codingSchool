from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import patient_repository


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
