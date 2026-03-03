"""停车流程业务逻辑。"""

from __future__ import annotations

from datetime import datetime
from math import ceil

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ParkingRecord, ParkingSpot, Vehicle
from app.services.fee_service import calculate_fee, get_active_fee_rule


async def get_vehicle_by_plate(
    session: AsyncSession, plate_number: str
) -> Vehicle | None:
    """根据车牌号码查询车辆。"""

    stmt = select(Vehicle).where(Vehicle.plate_number == plate_number.upper())
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def ensure_vehicle(
    session: AsyncSession,
    plate_number: str,
    brand: str | None = None,
    color: str | None = None,
) -> Vehicle:
    """若车辆不存在则自动创建。"""

    plate = plate_number.upper()
    vehicle = await get_vehicle_by_plate(session, plate)
    if vehicle:
        return vehicle
    vehicle = Vehicle(
        plate_number=plate,
        brand=brand,
        color=color,
        is_resident=False,
    )
    session.add(vehicle)
    await session.commit()
    await session.refresh(vehicle)
    return vehicle


async def allocate_free_spot(session: AsyncSession) -> ParkingSpot | None:
    """选择一个可用车位。"""

    stmt = (
        select(ParkingSpot)
        .where(ParkingSpot.status == "free")
        .order_by(ParkingSpot.zone, ParkingSpot.spot_number)
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_entry_record(
    session: AsyncSession,
    plate_number: str,
    entry_image: str | None = None,
    vehicle_brand: str | None = None,
    vehicle_color: str | None = None,
) -> tuple[ParkingRecord, ParkingSpot]:
    """创建入场记录并占用车位。"""

    active_record = await get_active_record(session, plate_number)
    if active_record:
        return active_record, active_record.spot  # type: ignore[attr-defined]

    vehicle = await ensure_vehicle(session, plate_number, vehicle_brand, vehicle_color)
    spot = await allocate_free_spot(session)
    if not spot:
        raise ValueError("当前无空闲车位")

    record = ParkingRecord(
        vehicle_id=vehicle.id,
        spot_id=spot.id,
        plate_number=vehicle.plate_number,
        entry_time=datetime.utcnow(),
        status="parked",
        is_resident=vehicle.is_resident,
        entry_image=entry_image,
    )
    record.spot = spot
    session.add(record)
    spot.status = "occupied"
    await session.commit()
    await session.refresh(record)
    if record.spot_id:
        await session.refresh(record, attribute_names=["spot"])
    await session.refresh(spot)
    return record, spot


async def get_active_record(
    session: AsyncSession, plate_number: str
) -> ParkingRecord | None:
    """查找未出场的停车记录。"""

    stmt = (
        select(ParkingRecord)
        .options(selectinload(ParkingRecord.spot))
        .where(ParkingRecord.plate_number == plate_number.upper())
        .where(ParkingRecord.status == "parked")
        .order_by(ParkingRecord.entry_time.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def complete_parking_exit(
    session: AsyncSession, plate_number: str, exit_image: str | None = None
) -> ParkingRecord | None:
    """办理出场流程。"""

    record = await get_active_record(session, plate_number)
    if not record:
        return None

    record.exit_time = datetime.utcnow()
    duration = record.exit_time - record.entry_time
    record.duration_minutes = max(1, ceil(duration.total_seconds() / 60))

    fee_rule = await get_active_fee_rule(session)
    record.fee = calculate_fee(record.duration_minutes, record.is_resident, fee_rule)
    record.status = "paid" if record.fee == 0 else "exited"
    record.is_paid = record.fee == 0
    if record.is_paid:
        record.payment_time = record.exit_time
    record.exit_image = exit_image

    if record.spot_id:
        spot = await session.get(ParkingSpot, record.spot_id)
        if spot:
            spot.status = "free"
            # 车位收益计算逻辑：只有当该车位被所有者设置为 'is_shared' (共享车位) 且产生费用时，收益 100% 归车位所有者。
            if spot.owner_id and spot.is_shared and record.fee > 0:
                record.owner_income = record.fee
                record.platform_income = 0.0
            else:
                record.owner_income = 0.0
                record.platform_income = record.fee


    await session.commit()
    await session.refresh(record)
    if record.spot_id:
        await session.refresh(record, attribute_names=["spot"])
    return record


async def pay_parking_record(
    session: AsyncSession, record_id: int
) -> ParkingRecord | None:
    """将停车记录标记为已支付。"""

    record = await session.get(ParkingRecord, record_id)
    if not record:
        return None
    if record.is_paid:
        return record
    if record.status != "exited":
        raise ValueError("当前记录状态不可支付")
    record.is_paid = True
    record.status = "paid"
    record.payment_time = datetime.utcnow()
    await session.commit()
    await session.refresh(record)
    return record


async def list_parking_records(
    session: AsyncSession, page: int = 1, size: int = 10
) -> tuple[list[ParkingRecord], int]:
    """分页查询停车记录。"""

    page = max(page, 1)
    size = max(min(size, 100), 1)
    offset = (page - 1) * size

    stmt = (
        select(ParkingRecord)
        .options(selectinload(ParkingRecord.spot))
        .order_by(ParkingRecord.entry_time.desc())
        .offset(offset)
        .limit(size)
    )
    result = await session.execute(stmt)
    items = list(result.scalars().all())

    total = await session.scalar(select(func.count(ParkingRecord.id)))
    return items, int(total or 0)


async def get_parking_statistics(session: AsyncSession) -> dict:
    """计算当日统计数据。"""

    now = datetime.utcnow()
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    entries_stmt = select(func.count(ParkingRecord.id)).where(
        ParkingRecord.entry_time >= day_start
    )
    exits_stmt = select(func.count(ParkingRecord.id)).where(
        ParkingRecord.exit_time.is_not(None), ParkingRecord.exit_time >= day_start
    )
    revenue_stmt = select(func.coalesce(func.sum(ParkingRecord.fee), 0)).where(
        ParkingRecord.exit_time.is_not(None), ParkingRecord.exit_time >= day_start
    )
    occupied_stmt = select(func.count(ParkingSpot.id)).where(
        ParkingSpot.status == "occupied"
    )

    entries = await session.scalar(entries_stmt) or 0
    exits = await session.scalar(exits_stmt) or 0
    revenue = await session.scalar(revenue_stmt) or 0
    occupied = await session.scalar(occupied_stmt) or 0

    return {
        "entries_today": int(entries),
        "exits_today": int(exits),
        "revenue_today": float(revenue),
        "occupied_spots": int(occupied),
    }

