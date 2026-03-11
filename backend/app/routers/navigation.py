
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.navigation import NavigationMap, RouteNode, RouteRequest, RouteResponse
from app.schemas.response import success_response
from app.schemas.spot import SpotSchema
from app.services import navigation_service


router = APIRouter(prefix="/navigation", tags=["导航"])


@router.get("/map")
async def navigation_map(session: AsyncSession = Depends(get_db)) -> dict:

    nav_map = await navigation_service.get_navigation_map(session)
    spots = [SpotSchema.model_validate(spot) for spot in nav_map["spots"]]
    payload = NavigationMap(
        width=nav_map["width"],
        height=nav_map["height"],
        entry=tuple(nav_map["entry"]),
        blocked=[tuple(cell) for cell in nav_map["blocked"]],
        spots=spots,
    )
    return success_response(payload.model_dump())


@router.post("/route")
async def plan_route(
    payload: RouteRequest,
    session: AsyncSession = Depends(get_db),
) -> dict:

    spot, route = await navigation_service.plan_route_to_spot(session, payload.spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="车位不存在")
    if not route:
        raise HTTPException(status_code=400, detail="无法规划路径")
    route_nodes = [RouteNode(x=point[0], y=point[1]) for point in route]
    payload_resp = RouteResponse(
        spot=SpotSchema.model_validate(spot),
        route=route_nodes,
        steps=len(route_nodes),
    )
    return success_response(payload_resp.model_dump())

