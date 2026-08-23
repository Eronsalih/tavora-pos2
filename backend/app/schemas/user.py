from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    CASHIER = "cashier"
    WAITER = "waiter"


class UserCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )

    pin: str | None = Field(
        default=None,
        pattern=r"^\d{4}$",
    )

    role: UserRole = UserRole.WAITER


class UserLogin(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )


class UserPinLogin(BaseModel):
    pin: str = Field(
        pattern=r"^\d{4}$",
    )


class UserPinUpdate(BaseModel):
    pin: str = Field(
        pattern=r"^\d{4}$",
    )


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    role: UserRole


class UserStatusUpdate(BaseModel):
    is_active: bool