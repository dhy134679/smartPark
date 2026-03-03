"""车位预测推理服务。"""

from __future__ import annotations

from datetime import datetime, timedelta
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ParkingSpot, SpotStatusLog

DEFAULT_CAPACITY = 50


async def _fetch_recent_logs(session: AsyncSession, limit: int = 120) -> list[SpotStatusLog]:
    stmt = (
        select(SpotStatusLog)
        .order_by(SpotStatusLog.timestamp.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _hourly_pattern(logs: list[SpotStatusLog]) -> dict[int, float]:
    buckets: dict[int, list[float]] = {}
    for log in logs:
        buckets.setdefault(log.hour, []).append(log.occupancy_rate)
    return {hour: round(mean(values), 2) for hour, values in buckets.items()}


def _generate_trend(pattern: dict[int, float], start: datetime, horizon: int, last_rate: float) -> list[dict]:
    items: list[dict] = []
    rate = last_rate
    for step in range(1, horizon + 1):
        ts = start + timedelta(hours=step)
        hour_avg = pattern.get(ts.hour)
        if hour_avg is not None:
            rate = (rate * 0.4) + (hour_avg * 0.6)
        else:
            delta = -0.03 if rate > 0.75 else 0.03
            rate = max(0.1, min(0.95, rate + delta))
        items.append({"timestamp": ts.isoformat(), "hour": ts.hour, "occupancy_rate": round(rate, 2)})
    return items


async def predict_trend(session: AsyncSession, horizon: int = 12) -> list[dict]:
    """预测未来若干小时的占用率。"""

    logs = await _fetch_recent_logs(session)
    pattern = _hourly_pattern(logs)
    last_rate = logs[0].occupancy_rate if logs else 0.6
    now = datetime.utcnow()
    return _generate_trend(pattern, now, horizon, last_rate)


async def predict_availability(session: AsyncSession) -> dict:
    """计算未来趋势与推荐到场时间。"""

    trend = await predict_trend(session, horizon=12)
    capacity = await session.scalar(select(func.count(ParkingSpot.id))) or DEFAULT_CAPACITY
    best_slot = next((item for item in trend if item["occupancy_rate"] < 0.6), None)
    available_counts = [
        {
            "timestamp": item["timestamp"],
            "available": int(capacity * (1 - item["occupancy_rate"]))
        }
        for item in trend
    ]
    recommendation = best_slot["timestamp"] if best_slot else trend[-1]["timestamp"]
    return {
        "capacity": int(capacity),
        "trend": trend,
        "availability": available_counts,
        "recommended_time": recommendation,
    }

