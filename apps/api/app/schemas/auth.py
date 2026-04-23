from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from trustledger_domain import SystemRole


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    system_role: SystemRole
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime


class AuthSessionResponse(BaseModel):
    id: UUID
    is_current: bool
    is_active: bool
    expires_at: datetime
    revoked_at: datetime | None
    last_seen_at: datetime
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class AuthSessionBulkRevokeResponse(BaseModel):
    current_session_id: UUID
    revoked_session_count: int
    revoked_session_ids: list[UUID]
