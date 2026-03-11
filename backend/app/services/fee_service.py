
from __future__ import annotations

import math

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import FeeRule, ParkingRecord

DEFAULT_FREE_MINUTES = 30
DEFAULT_RATE_PER_HOUR = 5.0
DEFAULT_MAX_DAILY = 50.0


async def get_active_fee_rule(session: AsyncSession) -> FeeRule | None:

    stmt = (
        select(FeeRule)
        .where(FeeRule.is_active.is_(True))
        .order_by(FeeRule.id.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_or_create_active_fee_rule(session: AsyncSession) -> FeeRule:

    fee_rule = await get_active_fee_rule(session)
    if fee_rule:
        return fee_rule

    fee_rule = FeeRule(
        name="标准收费",
        free_minutes=DEFAULT_FREE_MINUTES,
        rate_per_hour=DEFAULT_RATE_PER_HOUR,
        max_daily=DEFAULT_MAX_DAILY,
        is_active=True,
    )
    session.add(fee_rule)
    await session.commit()
    await session.refresh(fee_rule)
    return fee_rule


async def update_active_fee_rule(
    session: AsyncSession,
    name: str,
    free_minutes: int,
    rate_per_hour: float,
    max_daily: float,
) -> FeeRule:

    fee_rule = await get_or_create_active_fee_rule(session)
    fee_rule.name = name
    fee_rule.free_minutes = free_minutes
    fee_rule.rate_per_hour = rate_per_hour
    fee_rule.max_daily = max_daily
    fee_rule.is_active = True
    await session.commit()
    await session.refresh(fee_rule)
    return fee_rule


async def get_income_summary(session: AsyncSession) -> dict:

    stmt = select(
        func.coalesce(func.sum(ParkingRecord.fee), 0).label("total_fee"),
        func.coalesce(func.sum(ParkingRecord.owner_income), 0).label("owner_income"),
        func.coalesce(func.sum(ParkingRecord.platform_income), 0).label(
            "platform_income"
        ),
        func.coalesce(
            func.sum(case((ParkingRecord.owner_income > 0, 1), else_=0)),
            0,
        ).label("owner_count"),
        func.coalesce(
            func.sum(case((ParkingRecord.platform_income > 0, 1), else_=0)),
            0,
        ).label("platform_count"),
    ).where(ParkingRecord.fee > 0, ParkingRecord.status.in_(["exited", "paid"]))

    result = await session.execute(stmt)
    row = result.one()
    return {
        "total_fee": float(row.total_fee or 0),
        "owner_income_total": float(row.owner_income or 0),
        "admin_income_total": float(row.platform_income or 0),
        "owner_income_count": int(row.owner_count or 0),
        "admin_income_count": int(row.platform_count or 0),
    }


def calculate_fee(
    duration_minutes: int, is_resident: bool, fee_rule: FeeRule | None
) -> float:

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

