from datetime import UTC, datetime

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import (
    MAX_XRAY_IMAGE_SIZE,
    get_allowed_xray_extension,
    save_xray_image,
)
from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.models.xray_image import XrayImage
from app.repositories import medical_record_repository, patient_repository


async def _commit(db: AsyncSession) -> None:
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 차트번호입니다.",
        ) from exc


async def create_medical_record(
    db: AsyncSession,
    *,
    patient_id: int,
    chart_number: str,
    symptoms: str,
    xray_image: UploadFile,
    current_user: User,
    shooting_datetime: datetime | None = None,
) -> MedicalRecord:
    patient = await patient_repository.get_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )

    if await medical_record_repository.get_by_chart_number(db, chart_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 차트번호입니다.",
        )

    extension = get_allowed_xray_extension(xray_image.filename)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="지원하지 않는 이미지 형식입니다.",
        )

    content = await xray_image.read()
    if len(content) > MAX_XRAY_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="허용된 파일 크기를 초과했습니다.",
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    image_url = save_xray_image(content, extension, now)
    medical_record = MedicalRecord(
        patient_id=patient_id,
        chart_number=chart_number,
        symptoms=symptoms,
    )
    xray = XrayImage(
        record_id=0,
        uploader_id=current_user.id,
        image_url=image_url,
        shooting_datetime=shooting_datetime or now,
    )

    created = await medical_record_repository.create_with_xray_image(
        db,
        medical_record,
        xray,
    )
    await _commit(db)

    record = await medical_record_repository.get_by_id(db, created.id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )
    return record


async def get_medical_record(
    db: AsyncSession,
    record_id: int,
) -> MedicalRecord:
    record = await medical_record_repository.get_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )
    return record
