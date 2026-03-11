
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SpotStatusLog(Base):

    __tablename__ = "spot_status_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    spot_id: Mapped[int] = mapped_column(ForeignKey("parking_spots.id"))
    status: Mapped[str] = mapped_column(String(20), default="free")
    occupancy_rate: Mapped[float] = mapped_column(Float, default=0)
    total_occupied: Mapped[int] = mapped_column(Integer, default=0)
    total_free: Mapped[int] = mapped_column(Integer, default=0)
    hour: Mapped[int] = mapped_column(Integer)
    day_of_week: Mapped[int] = mapped_column(Integer)
    is_weekend: Mapped[bool] = mapped_column(Boolean, default=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )
