"""车位相关数据模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SpotSchema(BaseModel):
    """对外返回的车位信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    spot_number: str
    zone: str
    status: Literal["free", "occupied", "reserved"]
    owner_id: int | None = None
    is_shared: bool
    shared_start: datetime | None = None
    shared_end: datetime | None = None
    x_pos: float
    y_pos: float


class SpotSharePayload(BaseModel):
    """更新共享时间段。"""

    shared_start: datetime | None = Field(None, description="共享开始时间")
    shared_end: datetime | None = Field(None, description="共享结束时间")
    is_shared: bool = Field(True, description="是否开启共享")


class SpotOwnerUpdate(BaseModel):
    """管理员指派车位给业主。"""

    owner_id: int | None = Field(None, description="对应的业主ID，传空则解除绑定")


class SpotStatusUpdate(BaseModel):
    """更新车位状态。"""

    status: Literal["free", "occupied", "reserved"]


class SpotSummary(BaseModel):
    """车位概览。"""

    total: int
    free: int
    occupied: int
    reserved: int
    shared: int
