
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Vehicle(Base):

    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(20), default="car")
    is_resident: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    owner = relationship("User", back_populates="vehicles")
    parking_records = relationship("ParkingRecord", back_populates="vehicle")

