"""生成模拟占用率数据，便于训练或演示。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from random import Random


@dataclass
class OccupancySample:
    """结构化的数据条目。"""

    hour: int
    day_of_week: int
    is_weekend: bool
    occupancy_rate: float
    created_at: datetime


def generate_samples(days: int = 7, seed: int = 2024) -> list[OccupancySample]:
    """生成一定天数的模拟占用率样本。"""

    rand = Random(seed)
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    samples: list[OccupancySample] = []
    for offset in range(days * 24):
        ts = now - timedelta(hours=offset)
        base = 0.6 + 0.2 * rand.random()
        if 7 <= ts.hour <= 10:
            base += 0.2
        if 18 <= ts.hour <= 21:
            base += 0.15
        if ts.weekday() >= 5:
            base -= 0.15
        base = max(0.1, min(0.95, base))
        samples.append(
            OccupancySample(
                hour=ts.hour,
                day_of_week=ts.weekday(),
                is_weekend=ts.weekday() >= 5,
                occupancy_rate=round(base, 2),
                created_at=ts,
            )
        )
    return list(reversed(samples))

