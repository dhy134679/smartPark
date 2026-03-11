
from datetime import datetime, timedelta

import bcrypt
import jwt
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ParkingSpot, User


def hash_password(password: str) -> str:

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except (ValueError, AttributeError):
        return False


async def get_user_by_phone(session: AsyncSession, phone: str) -> User | None:

    result = await session.execute(select(User).where(User.phone == phone))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession, phone: str, name: str, password: str
) -> User:

    user = User(
        phone=phone,
        name=name,
        password_hash=hash_password(password),
        role="resident",
        is_resident=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession, phone: str, password: str
) -> User | None:

    user = await get_user_by_phone(session, phone)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_access_token(user: User) -> str:

    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user.id), "phone": user.phone, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:

    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


async def update_user_profile(
    session: AsyncSession, user: User, name: str | None, phone: str | None
) -> User:

    if phone and phone != user.phone:
        exists = await get_user_by_phone(session, phone)
        if exists and exists.id != user.id:
            raise ValueError("手机号已被使用")
        user.phone = phone
    if name:
        user.name = name
    await session.commit()
    await session.refresh(user)
    return user


async def list_users(
    session: AsyncSession,
    keyword: str | None = None,
    role: str | None = None,
    resident_only: bool = True,
) -> list[User]:

    stmt = select(User)
    if keyword:
        keyword_like = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(User.name.like(keyword_like), User.phone.like(keyword_like))
        )
    if role:
        stmt = stmt.where(User.role == role)
    elif resident_only:
        stmt = stmt.where(User.role == "resident")
    stmt = stmt.order_by(User.id.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def admin_update_user(
    session: AsyncSession,
    current_user: User,
    target_user_id: int,
    name: str | None = None,
    phone: str | None = None,
    password: str | None = None,
    role: str | None = None,
    is_resident: bool | None = None,
) -> User | None:

    target_user = await session.get(User, target_user_id)
    if not target_user:
        return None

    if phone and phone != target_user.phone:
        exists = await get_user_by_phone(session, phone)
        if exists and exists.id != target_user.id:
            raise ValueError("手机号已被使用")
        target_user.phone = phone

    if name:
        target_user.name = name

    if password:
        target_user.password_hash = hash_password(password)

    if role:
        if (
            target_user.id == current_user.id
            and target_user.role == "admin"
            and role != "admin"
        ):
            raise ValueError("不能取消当前登录管理员的管理员角色")
        target_user.role = role

    if is_resident is not None:
        target_user.is_resident = is_resident

    await session.commit()
    await session.refresh(target_user)
    return target_user


async def admin_delete_user(
    session: AsyncSession, current_user: User, target_user_id: int
) -> bool:

    target_user = await session.get(User, target_user_id)
    if not target_user:
        return False
    if target_user.id == current_user.id:
        raise ValueError("不能删除当前登录管理员")


    await session.execute(
        update(ParkingSpot)
        .where(ParkingSpot.owner_id == target_user.id)
        .values(owner_id=None, is_shared=False, shared_start=None, shared_end=None)
    )
    await session.delete(target_user)
    await session.commit()
    return True



async def change_password(
    session: AsyncSession, user: User, old_password: str, new_password: str
) -> User:

    if not verify_password(old_password, user.password_hash):
        raise ValueError("原密码不正确")
    if old_password == new_password:
        raise ValueError("新密码不能与原密码一致")

    user.password_hash = hash_password(new_password)
    await session.commit()
    await session.refresh(user)
    return user
