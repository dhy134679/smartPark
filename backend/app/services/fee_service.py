"""计费业务逻辑。"""

from __future__ import annotations

import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FeeRule

DEFAULT_FREE_MINUTES = 30
DEFAULT_RATE_PER_HOUR = 5.0
DEFAULT_MAX_DAILY = 50.0


async def get_active_fee_rule(session: AsyncSession) -> FeeRule | None:
    """获取生效的收费规则。"""

    stmt = (
        select(FeeRule)
        .where(FeeRule.is_active.is_(True))
        .order_by(FeeRule.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def calculate_fee(
    duration_minutes: int, is_resident: bool, fee_rule: FeeRule | None
) -> float:
    """根据时长计算费用。"""

    if duration_minutes <= 0 or is_resident:
        return 0.0

    free_minutes = fee_rule.free_minutes if fee_rule else DEFAULT_FREE_MINUTES
    rate_per_hour = (
        float(fee_rule.rate_per_hour) if fee_rule else DEFAULT_RATE_PER_HOUR
    )
    max_daily = float(fee_rule.max_daily) if fee_rule else DEFAULT_MAX_DAILY

    if duration_minutes <= free_minutes:
        return 0.0

    hours = math.ceil(duration_minutes / 60)
    fee = hours * rate_per_hour
    return float(min(fee, max_daily))

