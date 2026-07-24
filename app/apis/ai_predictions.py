from typing import Annotated

from fastapi import APIRouter, Path, status

from app.core.dependencies import CurrentApprovedUser, CurrentMedicalStaff, DbSession
from app.schemas.ai_analysis import AIAnalysisResponse
from app.services import ai_analysis_service


router = APIRouter(prefix="/api/v1/medical-records", tags=["AI Prediction"])


@router.post(
    "/{record_id}/predict",
    response_model=AIAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="AI 폐렴 예측 수행",
)
async def predict_pneumonia(
    record_id: Annotated[int, Path(ge=1)],
    current_user: CurrentMedicalStaff,
    db: DbSession,
) -> AIAnalysisResponse:
    del current_user
    return await ai_analysis_service.predict_record(db, record_id)


@router.get(
    "/{record_id}/analyses",
    response_model=list[AIAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="AI 폐렴 예측 결과 목록 조회",
)
async def list_pneumonia_analyses(
    record_id: Annotated[int, Path(ge=1)],
    current_user: CurrentApprovedUser,
    db: DbSession,
) -> list[AIAnalysisResponse]:
    del current_user
    return await ai_analysis_service.list_record_analyses(db, record_id)
