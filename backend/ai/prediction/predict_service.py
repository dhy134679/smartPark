
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import exp
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ParkingRecord, ParkingSpot, SpotStatusLog, Vehicle

DEFAULT_CAPACITY = 50
DEFAULT_OCCUPANCY_RATE = 0.6
DEFAULT_RESIDENT_STAY_MINUTES = 10 * 60
DEFAULT_VISITOR_STAY_MINUTES = 3 * 60
HISTORY_DAYS = 30
LOG_HISTORY_LIMIT = 240
RECORD_HISTORY_LIMIT = 2000


@dataclass
class ActiveParkingFeature:

    is_resident: bool
    elapsed_minutes: float
    remaining_weight: float = 1.0


async def _fetch_recent_logs(
    session: AsyncSession,
    limit: int = LOG_HISTORY_LIMIT,
) -> list[SpotStatusLog]:
    stmt = select(SpotStatusLog).order_by(SpotStatusLog.timestamp.desc()).limit(limit)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _fetch_active_records(session: AsyncSession) -> list[ParkingRecord]:
    stmt = (
        select(ParkingRecord)
        .where(ParkingRecord.status == "parked")
        .order_by(ParkingRecord.entry_time.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def _fetch_recent_records(
    session: AsyncSession,
    days: int = HISTORY_DAYS,
    limit: int = RECORD_HISTORY_LIMIT,
) -> list[ParkingRecord]:
    since = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(ParkingRecord)
        .where(ParkingRecord.entry_time >= since)
        .order_by(ParkingRecord.entry_time.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


def _build_log_pattern(logs: list[SpotStatusLog]) -> dict[tuple[bool | None, int], float]:

    precise_buckets: dict[tuple[bool, int], list[float]] = {}
    hourly_buckets: dict[int, list[float]] = {}

    for log in logs:
        precise_buckets.setdefault((log.is_weekend, log.hour), []).append(log.occupancy_rate)
        hourly_buckets.setdefault(log.hour, []).append(log.occupancy_rate)

    pattern: dict[tuple[bool | None, int], float] = {}
    for key, values in precise_buckets.items():
        pattern[key] = round(mean(values), 2)
    for hour, values in hourly_buckets.items():
        pattern[(None, hour)] = round(mean(values), 2)
    return pattern


def _build_arrival_profile(
    records: list[ParkingRecord],
) -> dict[tuple[bool | None, int, bool], float]:

    day_buckets: dict[tuple[bool, int, bool], int] = {}
    day_sets: dict[bool, set] = {False: set(), True: set()}
    hourly_counts: dict[tuple[int, bool], int] = {}
    all_days: set = set()

    for record in records:
        entry_time = record.entry_time
        is_weekend = entry_time.weekday() >= 5
        record_date = entry_time.date()
        day_sets[is_weekend].add(record_date)
        all_days.add(record_date)
        day_buckets[(is_weekend, entry_time.hour, record.is_resident)] = (
            day_buckets.get((is_weekend, entry_time.hour, record.is_resident), 0) + 1
        )
        hourly_counts[(entry_time.hour, record.is_resident)] = (
            hourly_counts.get((entry_time.hour, record.is_resident), 0) + 1
        )

    profile: dict[tuple[bool | None, int, bool], float] = {}
    for key, total in day_buckets.items():
        is_weekend, hour, is_resident = key
        days = max(len(day_sets[is_weekend]), 1)
        profile[(is_weekend, hour, is_resident)] = round(total / days, 2)

    total_days = max(len(all_days), 1)
    for (hour, is_resident), total in hourly_counts.items():
        profile[(None, hour, is_resident)] = round(total / total_days, 2)

    return profile


def _build_average_stay_minutes(records: list[ParkingRecord]) -> dict[bool, float]:

    samples: dict[bool, list[int]] = {True: [], False: []}
    for record in records:
        if record.duration_minutes and record.duration_minutes > 0:
            samples[record.is_resident].append(record.duration_minutes)

    return {
        True: round(mean(samples[True]), 2) if samples[True] else DEFAULT_RESIDENT_STAY_MINUTES,
        False: round(mean(samples[False]), 2) if samples[False] else DEFAULT_VISITOR_STAY_MINUTES,
    }


def _lookup_rate(
    pattern: dict[tuple[bool | None, int], float],
    ts: datetime,
    fallback_rate: float,
) -> float:
    is_weekend = ts.weekday() >= 5
    return pattern.get((is_weekend, ts.hour), pattern.get((None, ts.hour), fallback_rate))


def _lookup_arrivals(
    profile: dict[tuple[bool | None, int, bool], float],
    ts: datetime,
    is_resident: bool,
) -> float:
    is_weekend = ts.weekday() >= 5
    return profile.get((is_weekend, ts.hour, is_resident), profile.get((None, ts.hour, is_resident), 0.0))


def _departure_cdf(elapsed_minutes: float, avg_stay_minutes: float) -> float:

    safe_avg = max(avg_stay_minutes, 60.0)
    scale = max(45.0, safe_avg * 0.3)
    exponent = -((elapsed_minutes - safe_avg) / scale)
    return 1.0 / (1.0 + exp(exponent))


def _estimate_step_departures(
    features: list[ActiveParkingFeature],
    avg_stay_minutes: dict[bool, float],
) -> tuple[float, float]:

    resident_exits = 0.0
    visitor_exits = 0.0

    for feature in features:
        if feature.remaining_weight <= 0.01:
            continue

        avg_minutes = avg_stay_minutes[feature.is_resident]
        previous_cdf = _departure_cdf(feature.elapsed_minutes, avg_minutes)
        next_elapsed = feature.elapsed_minutes + 60
        next_cdf = _departure_cdf(next_elapsed, avg_minutes)
        survival = max(1.0 - previous_cdf, 1e-6)
        conditional_leave = min(max((next_cdf - previous_cdf) / survival, 0.0), 1.0)
        exit_weight = feature.remaining_weight * conditional_leave
        feature.remaining_weight -= exit_weight
        feature.elapsed_minutes = next_elapsed

        if feature.is_resident:
            resident_exits += exit_weight
        else:
            visitor_exits += exit_weight

    features[:] = [item for item in features if item.remaining_weight > 0.01]
    return resident_exits, visitor_exits


def _estimate_step_arrivals(
    ts: datetime,
    profile: dict[tuple[bool | None, int, bool], float],
    resident_presence_ratio: float,
    occupancy_rate: float,
) -> tuple[float, float]:

    resident_base = _lookup_arrivals(profile, ts, True)
    visitor_base = _lookup_arrivals(profile, ts, False)

    resident_gap = max(0.0, 1.0 - resident_presence_ratio)
    resident_factor = 0.35 + resident_gap * 0.85
    if 17 <= ts.hour <= 22:
        resident_factor += resident_gap * 0.35
    elif 0 <= ts.hour <= 6:
        resident_factor *= 0.6

    visitor_factor = max(0.25, 1.0 - occupancy_rate * 0.45)
    if 8 <= ts.hour <= 19:
        visitor_factor += 0.15

    resident_arrivals = resident_base * resident_factor
    visitor_arrivals = visitor_base * visitor_factor
    return resident_arrivals, visitor_arrivals


def _build_active_features(active_records: list[ParkingRecord], now: datetime) -> list[ActiveParkingFeature]:

    features: list[ActiveParkingFeature] = []
    for record in active_records:
        elapsed = max((now - record.entry_time).total_seconds() / 60, 1)
        features.append(
            ActiveParkingFeature(
                is_resident=record.is_resident,
                elapsed_minutes=elapsed,
            )
        )
    return features


def _rebalance_feature_weights(
    features: list[ActiveParkingFeature],
    resident_target: float,
    visitor_target: float,
) -> None:

    resident_weight = sum(item.remaining_weight for item in features if item.is_resident)
    visitor_weight = sum(item.remaining_weight for item in features if not item.is_resident)

    resident_scale = resident_target / resident_weight if resident_weight > 0 else 0.0
    visitor_scale = visitor_target / visitor_weight if visitor_weight > 0 else 0.0

    for feature in features:
        if feature.is_resident and resident_weight > 0:
            feature.remaining_weight *= resident_scale
        if (not feature.is_resident) and visitor_weight > 0:
            feature.remaining_weight *= visitor_scale

    if resident_target > 0 and resident_weight == 0:
        features.append(
            ActiveParkingFeature(
                is_resident=True,
                elapsed_minutes=0,
                remaining_weight=resident_target,
            )
        )
    if visitor_target > 0 and visitor_weight == 0:
        features.append(
            ActiveParkingFeature(
                is_resident=False,
                elapsed_minutes=0,
                remaining_weight=visitor_target,
            )
        )

    features[:] = [item for item in features if item.remaining_weight > 0.01]


def _generate_trend(
    start: datetime,
    horizon: int,
    capacity: int,
    active_records: list[ParkingRecord],
    recent_records: list[ParkingRecord],
    logs: list[SpotStatusLog],
    resident_vehicle_total: int,
) -> list[dict]:

    if capacity <= 0:
        capacity = DEFAULT_CAPACITY

    active_features = _build_active_features(active_records, start)
    avg_stay_minutes = _build_average_stay_minutes(recent_records)
    arrival_profile = _build_arrival_profile(recent_records)
    log_pattern = _build_log_pattern(logs)

    resident_active = sum(1.0 for item in active_records if item.is_resident)
    visitor_active = float(len(active_records) - resident_active)
    last_rate = logs[0].occupancy_rate if logs else (len(active_records) / capacity if capacity else DEFAULT_OCCUPANCY_RATE)

    items: list[dict] = []
    for step in range(1, horizon + 1):
        ts = start + timedelta(hours=step)
        resident_exits, visitor_exits = _estimate_step_departures(active_features, avg_stay_minutes)

        resident_active = max(resident_active - resident_exits, 0.0)
        visitor_active = max(visitor_active - visitor_exits, 0.0)

        occupancy_rate = (resident_active + visitor_active) / capacity
        resident_presence_ratio = (
            resident_active / resident_vehicle_total if resident_vehicle_total > 0 else 0.0
        )
        resident_arrivals, visitor_arrivals = _estimate_step_arrivals(
            ts,
            arrival_profile,
            resident_presence_ratio,
            occupancy_rate,
        )

        resident_active += resident_arrivals
        visitor_active += visitor_arrivals

        if resident_arrivals > 0:
            active_features.append(
                ActiveParkingFeature(
                    is_resident=True,
                    elapsed_minutes=0,
                    remaining_weight=resident_arrivals,
                )
            )
        if visitor_arrivals > 0:
            active_features.append(
                ActiveParkingFeature(
                    is_resident=False,
                    elapsed_minutes=0,
                    remaining_weight=visitor_arrivals,
                )
            )

        projected_occupied = min(max(resident_active + visitor_active, 0.0), float(capacity))
        baseline_rate = _lookup_rate(log_pattern, ts, fallback_rate=last_rate)
        blended_rate = ((projected_occupied / capacity) * 0.7) + (baseline_rate * 0.3)
        blended_rate = max(0.05, min(0.98, blended_rate))

        resident_share = resident_active / max(resident_active + visitor_active, 1e-6)
        projected_occupied = blended_rate * capacity
        resident_active = projected_occupied * resident_share
        visitor_active = projected_occupied - resident_active
        _rebalance_feature_weights(active_features, resident_active, visitor_active)
        last_rate = blended_rate

        items.append(
            {
                "timestamp": ts.isoformat(),
                "hour": ts.hour,
                "occupancy_rate": round(blended_rate, 2),
            }
        )

    return items


async def predict_trend(session: AsyncSession, horizon: int = 12) -> list[dict]:

    capacity = await session.scalar(select(func.count(ParkingSpot.id))) or DEFAULT_CAPACITY
    resident_vehicle_total = await session.scalar(
        select(func.count(Vehicle.id)).where(Vehicle.is_resident.is_(True))
    ) or 0
    active_records = await _fetch_active_records(session)
    recent_records = await _fetch_recent_records(session)
    logs = await _fetch_recent_logs(session)
    now = datetime.utcnow()
    return _generate_trend(
        start=now,
        horizon=horizon,
        capacity=int(capacity),
        active_records=active_records,
        recent_records=recent_records,
        logs=logs,
        resident_vehicle_total=int(resident_vehicle_total),
    )


async def predict_availability(session: AsyncSession) -> dict:

    trend = await predict_trend(session, horizon=12)
    capacity = await session.scalar(select(func.count(ParkingSpot.id))) or DEFAULT_CAPACITY

    available_counts = []
    for item in trend:
        available = max(int(round(capacity * (1 - item["occupancy_rate"]))), 0)
        available_counts.append({"timestamp": item["timestamp"], "available": available})

    recommendation = max(available_counts, key=lambda item: (item["available"], item["timestamp"]))["timestamp"]
    return {
        "capacity": int(capacity),
        "trend": trend,
        "availability": available_counts,
        "recommended_time": recommendation,
    }
