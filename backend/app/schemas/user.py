from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


# =========================================================
# USER ROLES
# =========================================================


class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    CASHIER = "cashier"
    WAITER = "waiter"


class TenantUserRole(str, Enum):
    ADMIN = "admin"
    CASHIER = "cashier"
    WAITER = "waiter"


# =========================================================
# USER CREATE
# =========================================================


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

    business_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=120,
    )

    role: TenantUserRole = TenantUserRole.WAITER


# =========================================================
# BUSINESS OWNER SIGNUP
# =========================================================


class OwnerSignup(BaseModel):
    business_name: str = Field(
        min_length=2,
        max_length=120,
    )

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )

    pin: str = Field(
        pattern=r"^\d{4}$",
    )


# =========================================================
# LOGIN
# =========================================================


class UserLogin(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )


class UserPinLogin(BaseModel):
    business_id: str = Field(
        min_length=24,
        max_length=24,
        pattern=r"^[0-9a-fA-F]{24}$",
    )

    pin: str = Field(
        pattern=r"^\d{4}$",
    )


# =========================================================
# PIN UPDATE
# =========================================================


class UserPinUpdate(BaseModel):
    pin: str = Field(
        pattern=r"^\d{4}$",
    )


# =========================================================
# USER RESPONSE
# =========================================================


class UserResponse(BaseModel):
    id: str
    business_id: str | None = None
    name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


# =========================================================
# TOKEN RESPONSE
# =========================================================


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# =========================================================
# SUBSCRIPTION RESPONSE
# =========================================================


class SubscriptionResponse(BaseModel):
    business_id: str
    plan: str
    status: str
    started_at: datetime | None = None
    expires_at: datetime | None = None
    payment_provider: str | None = None


# =========================================================
# USER UPDATE
# =========================================================


class UserUpdate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
    )

    email: EmailStr

    role: TenantUserRole


# =========================================================
# USER STATUS
# =========================================================


class UserStatusUpdate(BaseModel):
    is_active: bool