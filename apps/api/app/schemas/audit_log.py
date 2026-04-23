from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from trustledger_domain import AuditActionType, AuditOutcomeStatus


class AuditLogResponse(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    actor_user_email: str | None
    organization_id: UUID | None
    organization_name: str | None
    subject_user_id: UUID | None
    subject_user_email: str | None
    action_type: AuditActionType
    outcome_status: AuditOutcomeStatus
    target_type: str | None
    target_id: str | None
    details: str | None
    created_at: datetime
