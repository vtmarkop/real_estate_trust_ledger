from __future__ import annotations

from uuid import UUID

from datetime import datetime

from pydantic import BaseModel, Field

from trustledger_domain import AccountWorkspaceRole, SystemRole


class InternalAccessResponse(BaseModel):
    user_id: UUID
    email: str
    system_role: SystemRole
    can_manage_platform: bool


class InternalUserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    system_role: SystemRole
    workspace_roles: list[AccountWorkspaceRole]
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime


class WorkspaceRolesUpdateRequest(BaseModel):
    workspace_roles: list[AccountWorkspaceRole] = Field(min_length=1)
