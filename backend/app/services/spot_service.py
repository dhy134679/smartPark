"""车位相关业务逻辑。"""

from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ParkingSpot, User


async def list_spots(session: AsyncSession, zone: str | None = None) -> list[ParkingSpot]:
    """按区域筛选车位列表。"""

    stmt = select(ParkingSpot)
    if zone:
        stmt = stmt.where(ParkingSpot.zone == zone.upper())
    stmt = stmt.order_by(ParkingSpot.zone, ParkingSpot.spot_number)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_spot_by_id(session: AsyncSession, spot_id: int) -> ParkingSpot | None:
    """根据主键获取车位。"""

    return await session.get(ParkingSpot, spot_id)


async def list_my_spots(session: AsyncSession, user_id: int) -> list[ParkingSpot]:
    """获取指定业主名下的所有车位。"""

    stmt = select(ParkingSpot).where(ParkingSpot.owner_id == user_id).order_by(ParkingSpot.spot_number)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_my_income(session: AsyncSession, user_id: int) -> dict:
    """统计业主名下所有车位共享产生的收益。"""
    from app.models import ParkingRecord

    stmt = select(
        func.coalesce(func.sum(ParkingRecord.owner_income), 0).label("total_income")
    ).join(ParkingSpot, ParkingRecord.spot_id == ParkingSpot.id).where(
        ParkingSpot.owner_id == user_id,
        ParkingRecord.status == "paid"
    )
    result = await session.execute(stmt)
    total = result.scalar() or 0.0

    # 简单明细(最近10条产生收益的记录)
    detail_stmt = select(ParkingRecord).join(
        ParkingSpot, ParkingRecord.spot_id == ParkingSpot.id
    ).where(
        ParkingSpot.owner_id == user_id,
        ParkingRecord.owner_income > 0,
        ParkingRecord.status == "paid"
    ).order_by(ParkingRecord.entry_time.desc()).limit(10)
    
    details_res = await session.execute(detail_stmt)
    details = details_res.scalars().all()

    return {
        "total_income": float(total),
        "recent_details": [
            {
                "plate_number": record.plate_number,
                "amount": float(record.owner_income),
                "time": record.exit_time.strftime("%Y-%m-%d %H:%M") if record.exit_time else "",
            }
            for record in details
        ]
    }



async def get_spot_summary(session: AsyncSession) -> dict:
    """统计车位数量。"""

    stmt = select(
        func.count(ParkingSpot.id).label("total"),
        func.sum(case((ParkingSpot.status == "free", 1), else_=0)).label("free"),
        func.sum(case((ParkingSpot.status == "occupied", 1), else_=0)).label(
            "occupied"
        ),
        func.sum(case((ParkingSpot.status == "reserved", 1), else_=0)).label(
            "reserved"
        ),
        func.sum(case((ParkingSpot.is_shared.is_(True), 1), else_=0)).label(
            "shared"
        ),
    )
    result = await session.execute(stmt)
    row = result.one()
    return {
        "total": row.total or 0,
        "free": row.free or 0,
        "occupied": row.occupied or 0,
        "reserved": row.reserved or 0,
        "shared": row.shared or 0,
    }


async def update_spot_share(
    session: AsyncSession,
    spot_id: int,
    is_shared: bool,
    shared_start: datetime | None,
    shared_end: datetime | None,
) -> ParkingSpot | None:
    """更新共享时间信息。"""

    spot = await get_spot_by_id(session, spot_id)
    if not spot:
        return None
    spot.is_shared = is_shared
    spot.shared_start = shared_start
    spot.shared_end = shared_end
    await session.commit()
    await session.refresh(spot)
    return spot


async def update_spot_status(
    session: AsyncSession, spot_id: int, status: str
) -> ParkingSpot | None:
    """修改车位状态。"""

    spot = await get_spot_by_id(session, spot_id)
    if not spot:
        return None
    spot.status = status
    await session.commit()
    await session.refresh(spot)
    return spot


async def update_spot_owner(
    session: AsyncSession, spot_id: int, owner_id: int | None
) -> ParkingSpot | None:
    """给指定车位派发或解除业主。"""

    spot = await get_spot_by_id(session, spot_id)
    if not spot:
        return None
    if owner_id is not None:
        owner = await session.get(User, owner_id)
        if not owner:
            raise ValueError("业主用户不存在")
    spot.owner_id = owner_id
    # 如果解除业主绑定，连带将分享状态重置
    if not owner_id:
        spot.is_shared = False
        spot.shared_start = None
        spot.shared_end = None
    
    await session.commit()
    await session.refresh(spot)
    return spot
