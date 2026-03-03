"""认证相关数据模型。"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):
    """注册请求。"""

    phone: str = Field(..., min_length=6, max_length=20)
    name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=64)


class UserLogin(BaseModel):
    """登录请求。"""

    phone: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6, max_length=64)


class UserUpdate(BaseModel):
    """更新资料。"""

    name: str | None = Field(None, min_length=1, max_length=50)
    phone: str | None = Field(None, min_length=6, max_length=20)


class UserProfile(BaseModel):
    """用户返回信息。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    name: str
    role: str
    is_resident: bool


class TokenResponse(BaseModel):
    """登录返回。"""

    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class AdminUserListItem(BaseModel):
    """管理员用户列表项。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    name: str
    role: str
    is_resident: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):
    """管理员更新用户。"""

    name: str | None = Field(None, min_length=1, max_length=50)
    phone: str | None = Field(None, min_length=6, max_length=20)
    role: Literal["resident", "admin", "guest"] | None = None
    is_resident: bool | None = None

