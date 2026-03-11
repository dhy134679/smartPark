
from pydantic import BaseModel, Field


class TrendPoint(BaseModel):

    timestamp: str
    hour: int
    occupancy_rate: float


class AvailabilityPoint(BaseModel):

    timestamp: str
    available: int


class AvailabilityResponse(BaseModel):

    capacity: int
    trend: list[TrendPoint]
    availability: list[AvailabilityPoint]
    recommended_time: str = Field(..., description="建议到场时间戳")


class TrendResponse(BaseModel):

    trend: list[TrendPoint]

