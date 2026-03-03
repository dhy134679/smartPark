"""停车记录模型。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, DECIMAL, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ParkingRecord(Base):
    """停车记录。"""

    __tablename__ = "parking_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    spot_id: Mapped[int | None] = mapped_column(ForeignKey("parking_spots.id"), nullable=True)
    plate_number: Mapped[str] = mapped_column(String(20), index=True)
    entry_time: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
    exit_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    owner_income: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    platform_income: Mapped[float] = mapped_column(DECIMAL(10, 2), default=0)
    is_resident: Mapped[bool] = mapped_column(Boolean, default=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    payment_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="parked")
    entry_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    exit_image: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    vehicle = relationship("Vehicle", back_populates="parking_records")
    spot = relationship("ParkingSpot", back_populates="parking_records")

