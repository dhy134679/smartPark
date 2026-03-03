"""导航与路径规划。"""

from __future__ import annotations

from heapq import heappop, heappush
from math import inf

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ParkingSpot

GridPoint = tuple[int, int]


def _to_grid_point(x: float, y: float) -> GridPoint:
    return int(round(x)), int(round(y))


def _neighbors(node: GridPoint, width: int, height: int, blocked: set[GridPoint]) -> list[GridPoint]:
    x, y = node
    candidates = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    valid: list[GridPoint] = []
    for nx, ny in candidates:
        if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in blocked:
            valid.append((nx, ny))
    return valid


def _heuristic(a: GridPoint, b: GridPoint) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct_path(came_from: dict[GridPoint, GridPoint], current: GridPoint) -> list[GridPoint]:
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return list(reversed(path))


def _astar(start: GridPoint, goal: GridPoint, width: int, height: int, blocked: set[GridPoint]) -> list[GridPoint]:
    open_set: list[tuple[int, GridPoint]] = []
    heappush(open_set, (0, start))
    came_from: dict[GridPoint, GridPoint] = {}
    g_score: dict[GridPoint, int] = {start: 0}

    while open_set:
        _, current = heappop(open_set)
        if current == goal:
            return _reconstruct_path(came_from, current)
        for neighbor in _neighbors(current, width, height, blocked):
            tentative = g_score[current] + 1
            if tentative < g_score.get(neighbor, inf):
                came_from[neighbor] = current
                g_score[neighbor] = tentative
                f_score = tentative + _heuristic(neighbor, goal)
                heappush(open_set, (f_score, neighbor))
    return []


async def get_navigation_map(session: AsyncSession) -> dict:
    """返回地图信息。"""

    stmt = select(ParkingSpot).order_by(ParkingSpot.zone, ParkingSpot.spot_number)
    result = await session.execute(stmt)
    spots = list(result.scalars().all())
    return {
        "width": settings.navigation_grid_width,
        "height": settings.navigation_grid_height,
        "entry": settings.navigation_entry,
        "blocked": settings.navigation_blocked_cells,
        "spots": spots,
    }


async def plan_route_to_spot(
    session: AsyncSession, spot_id: int
) -> tuple[ParkingSpot | None, list[GridPoint]]:
    """计算 A* 路径。"""

    spot = await session.get(ParkingSpot, spot_id)
    if not spot:
        return None, []
    grid_map = await get_navigation_map(session)
    width = grid_map["width"]
    height = grid_map["height"]
    blocked = {tuple(cell) for cell in grid_map["blocked"]}
    start = tuple(grid_map["entry"])
    goal = _to_grid_point(spot.x_pos, spot.y_pos)
    path = _astar(start, goal, width, height, blocked)
    return spot, path

