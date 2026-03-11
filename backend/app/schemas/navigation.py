
from pydantic import BaseModel, Field

from app.schemas.spot import SpotSchema


class NavigationMap(BaseModel):

    width: int
    height: int
    entry: tuple[int, int]
    blocked: list[tuple[int, int]]
    spots: list[SpotSchema]


class RouteRequest(BaseModel):

    spot_id: int = Field(..., description="目标车位 ID")


class RouteNode(BaseModel):

    x: int
    y: int


class RouteResponse(BaseModel):

    spot: SpotSchema
    route: list[RouteNode]
    steps: int

