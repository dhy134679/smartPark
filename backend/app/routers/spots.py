"""车位管理接口。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.response import success_response
from app.schemas.spot import (
    SpotChangeRequestCreate,
    SpotChangeRequestReview,
    SpotChangeRequestSchema,
    SpotOwnerUpdate,
    SpotSchema,
    SpotSharePayload,
    SpotStatusUpdate,
)
from app.services import spot_service


router = APIRouter(prefix="/spots", tags=["车位"])


@router.get("")
async def get_spots(
    zone: str | None = Query(None, description="区域筛选"),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """车位列表。"""

    spots = await spot_service.list_spots(session, zone)
    items = [SpotSchema.model_validate(spot).model_dump() for spot in spots]
    return success_response({"items": items})


@router.get("/summary")
async def get_spot_summary(session: AsyncSession = Depends(get_db)) -> dict:
    """车位统计。"""

    summary = await spot_service.get_spot_summary(session)
    return success_response(summary)


@router.get("/my")
async def get_my_spots(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """获取我名下的车位列表。"""

    spots = await spot_service.list_my_spots(session, user.id)
    items = [SpotSchema.model_validate(spot).model_dump() for spot in spots]
    return success_response({"items": items})


@router.get("/my/income")
async def get_my_income_stats(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """获取我的车位共享收益明细。"""

    income_data = await spot_service.get_my_income(session, user.id)
    return success_response(income_data)


@router.post("/change-requests")
async def create_change_request(
    payload: SpotChangeRequestCreate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """住户提交车位变更申请。"""

    if user.role in {"guest", "admin"}:
        raise HTTPException(status_code=403, detail="当前角色不支持提交申请")

    try:
        req = await spot_service.create_spot_change_request(
            session,
            user,
            payload.action,
            payload.target_spot_id,
            payload.target_zone,
            payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return success_response({"request": SpotChangeRequestSchema.model_validate(req).model_dump()})


@router.get("/change-requests/my")
async def list_my_change_requests(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """住户查看自己的申请记录。"""

    rows = await spot_service.list_spot_change_requests(session, user_id=user.id)
    data = [SpotChangeRequestSchema.model_validate(item).model_dump() for item in rows]
    return success_response({"items": data})


@router.get("/change-requests")
async def admin_list_change_requests(
    status_filter: str | None = Query(None, alias="status", description="按状态筛选"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """管理员查询车位变更申请。"""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无管理员权限")

    rows = await spot_service.list_spot_change_requests(session, status=status_filter)
    data = [SpotChangeRequestSchema.model_validate(item).model_dump() for item in rows]
    return success_response({"items": data})


@router.put("/change-requests/{request_id}/review")
async def admin_review_change_request(
    request_id: int,
    payload: SpotChangeRequestReview,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """管理员审批车位变更申请。"""

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无管理员权限")

    try:
        req = await spot_service.review_spot_change_request(
            session, request_id, current_user, payload.status, payload.comment
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not req:
        raise HTTPException(status_code=404, detail="申请不存在")

    return success_response({"request": SpotChangeRequestSchema.model_validate(req).model_dump()})


@router.put("/{spot_id}/share")
async def share_spot(
    spot_id: int,
    payload: SpotSharePayload,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """设置共享车位。"""

    spot = await spot_service.get_spot_by_id(session, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车位不存在")
    if user.role != "admin" and spot.owner_id != user.id:
        raise HTTPException(status_code=403, detail="仅车位所有人可设置共享")

    spot = await spot_service.update_spot_share(
        session,
        spot_id,
        payload.is_shared,
        payload.shared_start,
        payload.shared_end,
    )
    data = SpotSchema.model_validate(spot).model_dump()
    return success_response({"spot": data})


@router.put("/{spot_id}/status")
async def update_spot_status(
    spot_id: int,
    payload: SpotStatusUpdate,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """更新车位状态。"""

    spot = await spot_service.update_spot_status(session, spot_id, payload.status)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车位不存在")
    data = SpotSchema.model_validate(spot).model_dump()
    return success_response({"spot": data})


@router.put("/{spot_id}/owner")
async def assign_spot_owner(
    spot_id: int,
    payload: SpotOwnerUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """给车位指派业主绑定（仅限管理员）。"""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    try:
        spot = await spot_service.update_spot_owner(session, spot_id, payload.owner_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="车位不存在")

    return success_response({"spot": SpotSchema.model_validate(spot).model_dump()})
