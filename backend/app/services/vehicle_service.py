"""车辆业务逻辑。"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Vehicle


async def list_user_vehicles(session: AsyncSession, user: User) -> list[Vehicle]:
    """查询用户绑定车辆。"""

    stmt = select(Vehicle).where(Vehicle.owner_id == user.id).order_by(Vehicle.id.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_vehicles(
    session: AsyncSession, owner_id: int | None = None
) -> list[Vehicle]:
    """查询车辆列表，可按用户筛选。"""

    stmt = select(Vehicle)
    if owner_id is not None:
        stmt = stmt.where(Vehicle.owner_id == owner_id)
    stmt = stmt.order_by(Vehicle.id.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_vehicle(
    session: AsyncSession,
    user: User,
    plate_number: str,
    brand: str | None,
    color: str | None,
    is_resident: bool,
) -> Vehicle:
    """绑定新车辆。"""

    plate = plate_number.upper()
    stmt = select(Vehicle).where(Vehicle.plate_number == plate)
    existing = await session.execute(stmt)
    vehicle = existing.scalar_one_or_none()
    if vehicle and vehicle.owner_id and vehicle.owner_id != user.id:
        raise ValueError("车牌已由其他账户绑定")
    if not vehicle:
        vehicle = Vehicle(
            plate_number=plate,
            brand=brand,
            color=color,
            is_resident=is_resident,
            owner_id=user.id,
        )
        session.add(vehicle)
    else:
        vehicle.owner_id = user.id
        vehicle.brand = brand or vehicle.brand
        vehicle.color = color or vehicle.color
        vehicle.is_resident = is_resident
    await session.commit()
    await session.refresh(vehicle)
    return vehicle


async def delete_vehicle(session: AsyncSession, user: User, vehicle_id: int) -> bool:
    """解绑车辆。"""

    vehicle = await session.get(Vehicle, vehicle_id)
    if not vehicle or vehicle.owner_id != user.id:
        return False
    await session.delete(vehicle)
    await session.commit()
    return True


async def admin_delete_vehicle(session: AsyncSession, vehicle_id: int) -> bool:
    """管理员删除车辆。"""

    vehicle = await session.get(Vehicle, vehicle_id)
    if not vehicle:
        return False
    await session.delete(vehicle)
    await session.commit()
    return True

