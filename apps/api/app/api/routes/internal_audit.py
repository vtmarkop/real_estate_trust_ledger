from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import select

from app.api.deps import SessionDep, require_system_roles
from app.models import AuditLog
from app.schemas.audit_log import AuditLogResponse
from app.services.audit_logs import build_audit_log_response
from trustledger_domain import AuditActionType, SystemRole


router = APIRouter(prefix="/internal/audit-logs", tags=["internal-audit"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    session: SessionDep,
    action_type: AuditActionType | None = Query(default=None),
    actor_user_id: UUID | None = Query(default=None),
    organization_id: UUID | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> list[AuditLogResponse]:
    query = select(AuditLog)
    if action_type is not None:
        query = query.where(AuditLog.action_type == action_type)
    if actor_user_id is not None:
        query = query.where(AuditLog.actor_user_id == actor_user_id)
    if organization_id is not None:
        query = query.where(AuditLog.organization_id == organization_id)

    audit_logs = session.exec(
        query.order_by(AuditLog.created_at.desc())
    ).all()[:limit]
    return [
        build_audit_log_response(session=session, audit_log=audit_log)
        for audit_log in audit_logs
    ]
