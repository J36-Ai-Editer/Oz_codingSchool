from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin

if TYPE_CHECKING:
    from app.models.medical_record import MedicalRecord


class AIAnalysisResult(TimestampMixin, Base):
    __tablename__ = "ai_analysis_results"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    record_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_pneumonia: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    heatmap_url: Mapped[str] = mapped_column(String(255), nullable=False)
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False)

    medical_record: Mapped[MedicalRecord] = relationship(
        back_populates="ai_analysis_results"
    )
