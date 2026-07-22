from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models.ai_analysis_result import AIAnalysisResult
from app.repositories import ai_analysis_repository
from worker.model import InvalidImageError, predict_pneumonia


AI_MODEL_NAME = "SimpleCNN-v1"
MEDIA_URL_PREFIX = "/media/"


def _resolve_media_path(image_url: str) -> Path:
    if not image_url.startswith(MEDIA_URL_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="저장된 X-ray 이미지 경로가 올바르지 않습니다.",
        )

    media_root = (Path.cwd() / "media").resolve()
    image_path = (Path.cwd() / image_url.lstrip("/")).resolve()
    try:
        image_path.relative_to(media_root)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="저장된 X-ray 이미지 경로가 올바르지 않습니다.",
        ) from exc

    if not image_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 X-ray 이미지 파일을 찾을 수 없습니다.",
        )
    return image_path


async def predict_record(
    db: AsyncSession,
    record_id: int,
) -> AIAnalysisResult:
    record = await ai_analysis_repository.get_record_with_xrays(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )
    if not record.xray_images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록에 등록된 X-ray 이미지가 없습니다.",
        )

    latest_xray = max(record.xray_images, key=lambda image: image.id)
    image_path = _resolve_media_path(latest_xray.image_url)
    try:
        prediction = await run_in_threadpool(predict_pneumonia, image_path)
    except InvalidImageError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    analysis = AIAnalysisResult(
        record_id=record.id,
        is_pneumonia=prediction.is_pneumonia,
        confidence=Decimal(f"{prediction.confidence * 100:.2f}"),
        heatmap_url="",
        ai_model=AI_MODEL_NAME,
    )
    created = await ai_analysis_repository.create(db, analysis)
    await db.commit()
    return created


async def list_record_analyses(
    db: AsyncSession,
    record_id: int,
) -> list[AIAnalysisResult]:
    record = await ai_analysis_repository.get_record_with_xrays(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )
    return await ai_analysis_repository.list_by_record(db, record_id)
