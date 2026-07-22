from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    record_id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str
    ai_model: str
    created_at: datetime
    updated_at: datetime | None = None
