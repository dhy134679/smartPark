"""认证相关接口。"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.auth import (
    AdminUserListItem,
    AdminUserUpdate,
    TokenResponse,

    UserLogin,
    UserProfile,
    UserRegister,
    UserUpdate,
)
from app.schemas.response import success_response
from app.services.auth_service import (
    admin_delete_user,
    admin_update_user,
    authenticate_user,
    create_access_token,
    create_user,
    get_user_by_phone,
    list_users,
    update_user_profile,
)


router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register")
async def register_user(
    payload: UserRegister, session: AsyncSession = Depends(get_db)
) -> dict:
    """用户注册。"""

    exists = await get_user_by_phone(session, payload.phone)
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="手机号已注册"
        )
    user = await create_user(session, payload.phone, payload.name, payload.password)
    user_profile = UserProfile.model_validate(user)
    return success_response({"user": user_profile.model_dump()})


@router.post("/login")
async def login_user(
    payload: UserLogin, session: AsyncSession = Depends(get_db)
) -> dict:
    """用户登录。"""

    user = await authenticate_user(session, payload.phone, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="手机号或密码错误"
        )
    token = create_access_token(user)
    response = TokenResponse(access_token=token, user=UserProfile.model_validate(user))
    return success_response(response.model_dump())


@router.post("/users")
async def admin_create_user(
    payload: UserRegister,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """管理员手动创建住户账户。"""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    exists = await get_user_by_phone(session, payload.phone)
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="手机号已存在"
        )

    user = await create_user(session, payload.phone, payload.name, payload.password)
    user.is_resident = True
    await session.commit()
    await session.refresh(user)

    return success_response({"user": UserProfile.model_validate(user).model_dump()})


@router.get("/users")
async def admin_list_users(
    keyword: str | None = Query(None, description="姓名/手机号模糊搜索"),
    role: str | None = Query(None, description="按角色筛选"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """管理员查询用户列表。"""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    users = await list_users(session, keyword=keyword, role=role)
    items = [AdminUserListItem.model_validate(user).model_dump() for user in users]
    return success_response({"items": items})


@router.put("/users/{user_id}")
async def admin_edit_user(
    user_id: int,
    payload: AdminUserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """管理员更新用户信息。"""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    try:
        user = await admin_update_user(
            session=session,
            current_user=current_user,
            target_user_id=user_id,
            name=payload.name,
            phone=payload.phone,
            role=payload.role,
            is_resident=payload.is_resident,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return success_response({"user": UserProfile.model_validate(user).model_dump()})


@router.delete("/users/{user_id}")
async def admin_remove_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """管理员删除用户。"""

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    try:
        deleted = await admin_delete_user(
            session=session, current_user=current_user, target_user_id=user_id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    return success_response({"deleted": True})


@router.post("/guest_login")
async def guest_login(session: AsyncSession = Depends(get_db)) -> dict:
    """游客登录。临时使用不需要注册手机号。"""

    # users.phone 字段限制最大 20 字符：gst_ + 10位时间戳 + 4位随机码 = 18 字符。
    import time
    import uuid

    guest_phone = f"gst_{int(time.time())}_{str(uuid.uuid4())[:4]}"

    user = await create_user(
        session=session,
        phone=guest_phone,
        name="匿名游客",
        password=guest_phone,
    )
    user.role = "guest"
    user.is_resident = False
    await session.commit()
    await session.refresh(user)

    token = create_access_token(user)
    response = TokenResponse(access_token=token, user=UserProfile.model_validate(user))
    return success_response(response.model_dump())


@router.get("/profile")
async def get_profile(user: User = Depends(get_current_user)) -> dict:
    """获取个人信息。"""

    return success_response({"user": UserProfile.model_validate(user).model_dump()})


@router.put("/profile")
async def update_profile(
    payload: UserUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """修改个人信息。"""

    try:
        updated = await update_user_profile(session, user, payload.name, payload.phone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response({"user": UserProfile.model_validate(updated).model_dump()})
