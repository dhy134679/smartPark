"""停车流程接口。"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.parking import (
    ParkingEntryPayload,
    ParkingEntryResult,
    ParkingExitPayload,
    ParkingExitResult,
    ParkingPayPayload,
    ParkingPayResult,
    ParkingRecordPage,
    ParkingRecordSchema,
    ParkingStatistics,
)
from app.schemas.response import success_response
from app.schemas.spot import SpotSchema
from app.services import parking_service


router = APIRouter(prefix="/parking", tags=["出入管理"])


@router.post("/entry")
async def parking_entry(
    payload: ParkingEntryPayload, session: AsyncSession = Depends(get_db)
) -> dict:
    """车辆入场。"""

    try:
        record, spot = await parking_service.create_entry_record(
            session,
            plate_number=payload.plate_number,
            entry_image=payload.entry_image,
            vehicle_brand=payload.vehicle_brand,
            vehicle_color=payload.vehicle_color,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = ParkingEntryResult(
        record_id=record.id,
        plate_number=record.plate_number,
        is_resident=record.is_resident,
        spot=SpotSchema.model_validate(spot),
    )
    return success_response(result.model_dump())


@router.post("/exit")
async def parking_exit(
    payload: ParkingExitPayload, session: AsyncSession = Depends(get_db)
) -> dict:
    """车辆出场。"""

    record = await parking_service.complete_parking_exit(
        session, payload.plate_number, payload.exit_image
    )
    if not record:
        raise HTTPException(status_code=404, detail="未找到在场车辆")

    result = ParkingExitResult(
        record_id=record.id,
        plate_number=record.plate_number,
        duration_minutes=record.duration_minutes or 0,
        fee=float(record.fee or 0),
        is_resident=record.is_resident,
        status=record.status,
    )
    return success_response(result.model_dump())


@router.post("/pay")
async def parking_pay(
    payload: ParkingPayPayload, session: AsyncSession = Depends(get_db)
) -> dict:
    """模拟支付并更新记录状态。"""

    try:
        record = await parking_service.pay_parking_record(session, payload.record_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not record:
        raise HTTPException(status_code=404, detail="停车记录不存在")
    result = ParkingPayResult(
        record_id=record.id,
        is_paid=record.is_paid,
        status=record.status,
    )
    return success_response(result.model_dump())


@router.get("/records")
async def parking_records(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """停车记录分页。"""

    items, total = await parking_service.list_parking_records(session, page, size)
    records = [ParkingRecordSchema.model_validate(item) for item in items]
    page_model = ParkingRecordPage(items=records, page=page, size=size, total=total)
    return success_response(page_model.model_dump())


@router.get("/statistics")
async def parking_statistics(session: AsyncSession = Depends(get_db)) -> dict:
    """今日统计。"""

    stats = await parking_service.get_parking_statistics(session)
    payload = ParkingStatistics(**stats)
    return success_response(payload.model_dump())

