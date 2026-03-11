
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.response import success_response
from app.schemas.vehicle import VehicleCreate, VehicleSchema
from app.services import vehicle_service


router = APIRouter(prefix="/vehicles", tags=["车辆"])


@router.get("")
async def list_vehicles(
    session: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:

    vehicles = await vehicle_service.list_user_vehicles(session, user)
    data = [VehicleSchema.model_validate(item).model_dump() for item in vehicles]
    return success_response({"items": data})


@router.get("/admin")
async def admin_list_vehicles(
    owner_id: int | None = Query(None, description="按用户ID筛选"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    vehicles = await vehicle_service.list_vehicles(session, owner_id)
    data = [VehicleSchema.model_validate(item).model_dump() for item in vehicles]
    return success_response({"items": data})


@router.post("")
async def bind_vehicle(
    payload: VehicleCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:

    try:
        vehicle = await vehicle_service.create_vehicle(
            session,
            user,
            payload.plate_number,
            payload.brand,
            payload.color,
            payload.is_resident,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    data = VehicleSchema.model_validate(vehicle).model_dump()
    return success_response({"vehicle": data})


@router.post("/admin/users/{user_id}")
async def admin_bind_vehicle_for_user(
    user_id: int,
    payload: VehicleCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    owner = await session.get(User, user_id)
    if not owner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    try:
        vehicle = await vehicle_service.create_vehicle(
            session,
            owner,
            payload.plate_number,
            payload.brand,
            payload.color,
            payload.is_resident,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    return success_response({"vehicle": VehicleSchema.model_validate(vehicle).model_dump()})


@router.delete("/{vehicle_id}")
async def remove_vehicle(
    vehicle_id: int,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:

    success = await vehicle_service.delete_vehicle(session, user, vehicle_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车辆不存在")
    return success_response({"deleted": True})


@router.delete("/admin/{vehicle_id}")
async def admin_remove_vehicle(
    vehicle_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    success = await vehicle_service.admin_delete_vehicle(session, vehicle_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车辆不存在")
    return success_response({"deleted": True})
