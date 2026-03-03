"""车位预测接口。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ai.prediction import predict_service
from app.database import get_db
from app.schemas.predict import AvailabilityResponse, TrendResponse
from app.schemas.response import success_response


router = APIRouter(prefix="/predict", tags=["预测"])


@router.get("/availability")
async def predict_availability(session: AsyncSession = Depends(get_db)) -> dict:
    """未来空闲预估。"""

    data = await predict_service.predict_availability(session)
    payload = AvailabilityResponse(**data)
    return success_response(payload.model_dump())


@router.get("/trend")
async def predict_trend(
    horizon: int = Query(12, ge=1, le=24),
    session: AsyncSession = Depends(get_db),
) -> dict:
    """未来占用率趋势。"""

    trend = await predict_service.predict_trend(session, horizon=horizon)
    payload = TrendResponse(trend=trend)
    return success_response(payload.model_dump())

