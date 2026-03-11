
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ParkingSpot(Base):

    __tablename__ = "parking_spots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    spot_number: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    zone: Mapped[str] = mapped_column(String(1))
    status: Mapped[str] = mapped_column(String(20), default="free")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    shared_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    shared_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    x_pos: Mapped[float] = mapped_column(Float, default=0)
    y_pos: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    owner = relationship("User", back_populates="parking_spots")
    parking_records = relationship("ParkingRecord", back_populates="spot")

