"""车辆相关数据模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class VehicleCreate(BaseModel):
    """绑定车辆请求。"""

    plate_number: str = Field(..., min_length=5, max_length=12)
    brand: str | None = None
    color: str | None = None
    is_resident: bool = False


class VehicleSchema(BaseModel):
    """车辆返回信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    plate_number: str
    owner_id: int | None = None
    brand: str | None = None
    color: str | None = None
    vehicle_type: str
    is_resident: bool
    is_active: bool
    created_at: datetime

