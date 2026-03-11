
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.fee import FeeIncomeSummary, FeeRuleSchema, FeeRuleUpdatePayload
from app.schemas.response import success_response
from app.services import fee_service


router = APIRouter(prefix="/fees", tags=["收费管理"])


@router.get("/rule")
async def get_fee_rule(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    rule = await fee_service.get_or_create_active_fee_rule(session)
    return success_response({"rule": FeeRuleSchema.model_validate(rule).model_dump()})


@router.put("/rule")
async def update_fee_rule(
    payload: FeeRuleUpdatePayload,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    rule = await fee_service.update_active_fee_rule(
        session=session,
        name=payload.name,
        free_minutes=payload.free_minutes,
        rate_per_hour=payload.rate_per_hour,
        max_daily=payload.max_daily,
    )
    return success_response({"rule": FeeRuleSchema.model_validate(rule).model_dump()})


@router.get("/income-summary")
async def get_income_summary(
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    summary = await fee_service.get_income_summary(session)
    data = FeeIncomeSummary(**summary)
    return success_response(data.model_dump())
