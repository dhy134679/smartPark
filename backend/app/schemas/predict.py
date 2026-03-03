"""车位预测数据模型。"""

from pydantic import BaseModel, Field


class TrendPoint(BaseModel):
    """趋势点。"""

    timestamp: str
    hour: int
    occupancy_rate: float


class AvailabilityPoint(BaseModel):
    """空闲数量点。"""

    timestamp: str
    available: int


class AvailabilityResponse(BaseModel):
    """空闲预测返回。"""

    capacity: int
    trend: list[TrendPoint]
    availability: list[AvailabilityPoint]
    recommended_time: str = Field(..., description="建议到场时间戳")


class TrendResponse(BaseModel):
    """趋势返回。"""

    trend: list[TrendPoint]

