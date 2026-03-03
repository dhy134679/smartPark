"""收费规则模型。"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, DECIMAL, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FeeRule(Base):
    """收费规则。"""

    __tablename__ = "fee_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50))
    free_minutes: Mapped[int] = mapped_column(Integer, default=30)
    rate_per_hour: Mapped[float] = mapped_column(DECIMAL(10, 2), default=5)
    max_daily: Mapped[float] = mapped_column(DECIMAL(10, 2), default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP")
    )

