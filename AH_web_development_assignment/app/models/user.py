from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    gender: Mapped[str] = mapped_column(Enum("male", "female", name="gender"), nullable=False)
    department: Mapped[str] = mapped_column(
        Enum("developer", "medical team", "researcher", name="department"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        Enum("pending", "staff", "admin", name="role"),
        nullable=False,
        server_default="pending",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("1"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("current_timestamp(0)"),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=text("current_timestamp(0)"),
    )

    uploaded_xray_images = relationship("XrayImage", back_populates="uploader")
