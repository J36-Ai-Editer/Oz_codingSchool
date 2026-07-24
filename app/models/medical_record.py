from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin

if TYPE_CHECKING:
    from app.models.ai_analysis_result import AIAnalysisResult
    from app.models.patient import Patient
    from app.models.xray_image import XrayImage


class MedicalRecord(TimestampMixin, Base):
    __tablename__ = "medical_records"

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    patient_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
    )
    chart_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    symptoms: Mapped[str] = mapped_column(Text, nullable=False)

    patient: Mapped[Patient] = relationship(back_populates="medical_records")
    xray_images: Mapped[list[XrayImage]] = relationship(
        back_populates="medical_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ai_analysis_results: Mapped[list[AIAnalysisResult]] = relationship(
        back_populates="medical_record",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
