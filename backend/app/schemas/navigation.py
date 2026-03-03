"""导航相关数据模型。"""

from pydantic import BaseModel, Field

from app.schemas.spot import SpotSchema


class NavigationMap(BaseModel):
    """停车场地图数据。"""

    width: int
    height: int
    entry: tuple[int, int]
    blocked: list[tuple[int, int]]
    spots: list[SpotSchema]


class RouteRequest(BaseModel):
    """寻路请求。"""

    spot_id: int = Field(..., description="目标车位 ID")


class RouteNode(BaseModel):
    """路径节点。"""

    x: int
    y: int


class RouteResponse(BaseModel):
    """寻路结果。"""

    spot: SpotSchema
    route: list[RouteNode]
    steps: int

