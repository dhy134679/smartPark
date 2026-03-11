
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserRegister(BaseModel):

    phone: str = Field(..., min_length=6, max_length=20)
    name: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=64)


class UserLogin(BaseModel):

    phone: str = Field(..., min_length=6, max_length=20)
    password: str = Field(..., min_length=6, max_length=64)


class UserUpdate(BaseModel):

    name: str | None = Field(None, min_length=1, max_length=50)
    phone: str | None = Field(None, min_length=6, max_length=20)


class UserProfile(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    name: str
    role: str
    is_resident: bool


class TokenResponse(BaseModel):

    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class AdminUserListItem(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int
    phone: str
    name: str
    role: str
    is_resident: bool
    created_at: datetime


class AdminUserUpdate(BaseModel):

    name: str | None = Field(None, min_length=1, max_length=50)
    phone: str | None = Field(None, min_length=6, max_length=20)
    password: str | None = Field(None, min_length=6, max_length=64)
    role: Literal["resident", "admin"] | None = None
    is_resident: bool | None = None



class ChangePasswordPayload(BaseModel):

    old_password: str = Field(..., min_length=6, max_length=64)
    new_password: str = Field(..., min_length=6, max_length=64)
