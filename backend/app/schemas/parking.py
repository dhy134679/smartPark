"""停车相关数据模型。"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.spot import SpotSchema


class ParkingEntryPayload(BaseModel):
    """入场请求载荷。"""

    plate_number: str = Field(..., min_length=5, max_length=15)
    vehicle_brand: str | None = None
    vehicle_color: str | None = None
    entry_image: str | None = Field(
        None, description="模拟上传的图片路径，实际接口将接收文件"
    )


class ParkingExitPayload(BaseModel):
    """出场请求载荷。"""

    plate_number: str = Field(..., min_length=5, max_length=15)
    exit_image: str | None = None


class ParkingPayPayload(BaseModel):
    """支付请求载荷。"""

    record_id: int = Field(..., ge=1)


class ParkingRecordSchema(BaseModel):
    """停车记录返回结构。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    spot_id: int | None
    plate_number: str
    entry_time: datetime
    exit_time: datetime | None
    duration_minutes: int | None
    fee: float | None
    is_resident: bool
    is_paid: bool
    status: str
    entry_image: str | None = None
    exit_image: str | None = None
    spot: SpotSchema | None = None


class ParkingEntryResult(BaseModel):
    """入场结果。"""

    record_id: int
    plate_number: str
    is_resident: bool
    spot: SpotSchema | None = None


class ParkingExitResult(BaseModel):
    """出场结果。"""

    record_id: int
    plate_number: str
    duration_minutes: int
    fee: float
    is_resident: bool
    status: str


class ParkingPayResult(BaseModel):
    """支付结果。"""

    record_id: int
    is_paid: bool
    status: str


class ParkingRecordPage(BaseModel):
    """停车记录分页。"""

    items: list[ParkingRecordSchema]
    page: int
    size: int
    total: int


class ParkingStatistics(BaseModel):
    """停车统计。"""

    entries_today: int
    exits_today: int
    revenue_today: float
    occupied_spots: int

