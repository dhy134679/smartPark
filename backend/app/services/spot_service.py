"""车位业务逻辑。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ParkingRecord, ParkingSpot, SpotChangeRequest, User


async def list_spots(session: AsyncSession, zone: str | None = None) -> list[ParkingSpot]:
    """查询车位列表。"""

    stmt = select(ParkingSpot).order_by(ParkingSpot.zone, ParkingSpot.spot_number)
    if zone:
        stmt = stmt.where(ParkingSpot.zone == zone)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_spot_by_id(session: AsyncSession, spot_id: int) -> ParkingSpot | None:
    """按 ID 查询车位。"""

    return await session.get(ParkingSpot, spot_id)


async def list_my_spots(session: AsyncSession, user_id: int) -> list[ParkingSpot]:
    """查询当前用户名下车位。"""

    stmt = (
        select(ParkingSpot)
        .where(ParkingSpot.owner_id == user_id)
        .order_by(ParkingSpot.zone, ParkingSpot.spot_number)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_my_income(session: AsyncSession, user_id: int) -> dict:
    """查询用户共享收益总额与最近记录。"""

    stmt = select(func.sum(ParkingRecord.owner_income)).join(
        ParkingSpot, ParkingRecord.spot_id == ParkingSpot.id
    ).where(
        ParkingSpot.owner_id == user_id,
        ParkingRecord.status == "paid"
    )
    result = await session.execute(stmt)
    total = result.scalar() or 0.0

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
    if not owner_id:
        spot.is_shared = False
        spot.shared_start = None
        spot.shared_end = None

    await session.commit()
    await session.refresh(spot)
    return spot


async def create_spot_change_request(
    session: AsyncSession,
    user: User,
    action: str,
    target_spot_id: int | None,
    target_zone: str | None,
    reason: str | None,
) -> SpotChangeRequest:
    """创建车位变更申请。"""

    my_spots = await list_my_spots(session, user.id)
    current_spot_id = my_spots[0].id if my_spots else None

    if action in {"assign", "change"} and not target_spot_id:
        raise ValueError("请选择目标车位")

    if action == "release" and not current_spot_id:
        raise ValueError("当前没有已分配车位，无需释放")

    if target_spot_id:
        target_spot = await session.get(ParkingSpot, target_spot_id)
        if not target_spot:
            raise ValueError("目标车位不存在")
        if target_spot.owner_id and target_spot.owner_id != user.id:
            raise ValueError("目标车位已分配给其他用户")
        if target_zone and target_spot.zone != target_zone:
            raise ValueError("目标车位不在所选区域")

    request = SpotChangeRequest(
        user_id=user.id,
        current_spot_id=current_spot_id,
        target_spot_id=target_spot_id,
        target_zone=target_zone,
        action=action,
        reason=reason,
        status="pending",
    )
    session.add(request)
    await session.commit()
    await session.refresh(request)
    return request


async def list_spot_change_requests(
    session: AsyncSession,
    user_id: int | None = None,
    status: str | None = None,
) -> list[SpotChangeRequest]:
    """查询车位变更申请列表。"""

    stmt = select(SpotChangeRequest).order_by(SpotChangeRequest.created_at.desc())
    if user_id is not None:
        stmt = stmt.where(SpotChangeRequest.user_id == user_id)
    if status:
        stmt = stmt.where(SpotChangeRequest.status == status)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def review_spot_change_request(
    session: AsyncSession,
    request_id: int,
    reviewer: User,
    status: str,
    comment: str | None,
) -> SpotChangeRequest | None:
    """管理员审批车位变更申请。"""

    request = await session.get(SpotChangeRequest, request_id)
    if not request:
        return None
    if request.status != "pending":
        raise ValueError("该申请已处理")

    request.status = status
    request.review_comment = comment
    request.reviewer_id = reviewer.id
    request.reviewed_at = datetime.now()

    if status == "approved":
        if request.action in {"change", "release"} and request.current_spot_id:
            current_spot = await session.get(ParkingSpot, request.current_spot_id)
            if current_spot and current_spot.owner_id == request.user_id:
                current_spot.owner_id = None
                current_spot.is_shared = False
                current_spot.shared_start = None
                current_spot.shared_end = None
        if request.action in {"change", "assign"} and request.target_spot_id:
            target_spot = await session.get(ParkingSpot, request.target_spot_id)
            if not target_spot:
                raise ValueError("目标车位不存在")
            if target_spot.owner_id and target_spot.owner_id != request.user_id:
                raise ValueError("目标车位已被占用")
            target_spot.owner_id = request.user_id

    await session.commit()
    await session.refresh(request)
    return request
