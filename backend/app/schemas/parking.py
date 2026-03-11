
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.spot import SpotSchema


class ParkingEntryPayload(BaseModel):

    plate_number: str = Field(..., min_length=5, max_length=15)
    vehicle_brand: str | None = None
    vehicle_color: str | None = None
    entry_image: str | None = Field(
        None, description="模拟上传的图片路径，实际接口将接收文件"
    )
    target_spot_id: int | None = Field(
        None, description="指定进入的车位ID，不传则系统自动分配"
    )


class ParkingExitPayload(BaseModel):

    plate_number: str = Field(..., min_length=5, max_length=15)
    exit_image: str | None = None


class ParkingPayPayload(BaseModel):

    record_id: int = Field(..., ge=1)


class ParkingRecordSchema(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    vehicle_id: int
    spot_id: int | None
    plate_number: str
    entry_time: datetime
    exit_time: datetime | None
    duration_minutes: int | None
    fee: float | None
    owner_income: float | None = None
    platform_income: float | None = None
    is_resident: bool
    is_paid: bool
    status: str
    entry_image: str | None = None
    exit_image: str | None = None
    spot: SpotSchema | None = None


class ParkingEntryResult(BaseModel):

    record_id: int
    plate_number: str
    is_resident: bool
    spot: SpotSchema | None = None


class ParkingExitResult(BaseModel):

    record_id: int
    plate_number: str
    duration_minutes: int
    fee: float
    is_resident: bool
    status: str


class ParkingPayResult(BaseModel):

    record_id: int
    is_paid: bool
    status: str


class ParkingRecordPage(BaseModel):

    items: list[ParkingRecordSchema]
    page: int
    size: int
    total: int


class ParkingStatistics(BaseModel):

    entries_today: int
    exits_today: int
    revenue_today: float
    occupied_spots: int
