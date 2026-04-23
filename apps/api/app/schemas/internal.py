from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from trustledger_domain import SystemRole


class InternalAccessResponse(BaseModel):
    user_id: UUID
    email: str
    system_role: SystemRole
    can_manage_platform: bool
