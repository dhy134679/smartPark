
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SpotChangeRequest(Base):

    __tablename__ = "spot_change_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    current_spot_id: Mapped[int | None] = mapped_column(
        ForeignKey("parking_spots.id"), nullable=True
    )
    target_spot_id: Mapped[int | None] = mapped_column(
        ForeignKey("parking_spots.id"), nullable=True
    )
    target_zone: Mapped[str | None] = mapped_column(String(1), nullable=True)
    action: Mapped[str] = mapped_column(String(20), default="change")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    review_comment: Mapped[str | None] = mapped_column(String(200), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

    requester = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    current_spot = relationship("ParkingSpot", foreign_keys=[current_spot_id])
    target_spot = relationship("ParkingSpot", foreign_keys=[target_spot_id])
