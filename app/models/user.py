from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin
from app.models.enums import Department, Gender, Role

if TYPE_CHECKING:
    from app.models.xray_image import XrayImage


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="gender"), nullable=False)
    department: Mapped[Department] = mapped_column(
        Enum(Department, name="department"), nullable=False
    )
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="role"), nullable=False, default=Role.PENDING,
        server_default=Role.PENDING.value
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("1")
    )

    uploaded_xray_images: Mapped[list[XrayImage]] = relationship(
        back_populates="uploader", passive_deletes=True
    )
