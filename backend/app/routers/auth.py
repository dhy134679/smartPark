
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.schemas.auth import (
    AdminUserListItem,
    AdminUserUpdate,
    TokenResponse,
    ChangePasswordPayload,
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
    change_password,
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
    resident_only: bool = Query(True, description="仅查看住户"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    users = await list_users(
        session,
        keyword=keyword,
        role=role,
        resident_only=resident_only,
    )
    items = [AdminUserListItem.model_validate(user).model_dump() for user in users]
    return success_response({"items": items})


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限"
        )

    user = await session.get(User, user_id)
    if not user or user.role != "resident":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="住户不存在")

    return success_response({"user": UserProfile.model_validate(user).model_dump()})


@router.put("/users/{user_id}")
async def admin_edit_user(
    user_id: int,
    payload: AdminUserUpdate,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:

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
            password=payload.password,
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

    guest_phone = "guest_demo"
    await session.execute(
        delete(User).where(User.role == "guest", User.phone != guest_phone)
    )
    user = await get_user_by_phone(session, guest_phone)
    if not user:
        user = await create_user(
            session=session,
            phone=guest_phone,
            name="匿名游客",
            password="guest_demo_pwd",
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

    return success_response({"user": UserProfile.model_validate(user).model_dump()})


@router.put("/profile")
async def update_profile(
    payload: UserUpdate,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:

    try:
        updated = await update_user_profile(session, user, payload.name, payload.phone)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success_response({"user": UserProfile.model_validate(updated).model_dump()})


@router.put("/change-password")
async def update_password(
    payload: ChangePasswordPayload,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:

    try:
        await change_password(session, user, payload.old_password, payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return success_response({"updated": True})
