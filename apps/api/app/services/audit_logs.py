from __future__ import annotations

from sqlmodel import Session

from app.models import AuditLog, Organization, User
from app.schemas.audit_log import AuditLogResponse
from trustledger_domain import AuditActionType, AuditOutcomeStatus


def build_audit_log_response(
    *,
    session: Session,
    audit_log: AuditLog,
) -> AuditLogResponse:
    actor_user = session.get(User, audit_log.actor_user_id) if audit_log.actor_user_id else None
    organization = (
        session.get(Organization, audit_log.organization_id)
        if audit_log.organization_id
        else None
    )
    subject_user = (
        session.get(User, audit_log.subject_user_id)
        if audit_log.subject_user_id
        else None
    )
    return AuditLogResponse(
        id=audit_log.id,
        actor_user_id=audit_log.actor_user_id,
        actor_user_email=actor_user.email if actor_user else None,
        organization_id=audit_log.organization_id,
        organization_name=organization.name if organization else None,
        subject_user_id=audit_log.subject_user_id,
        subject_user_email=subject_user.email if subject_user else None,
        action_type=audit_log.action_type,
        outcome_status=audit_log.outcome_status,
        target_type=audit_log.target_type,
        target_id=audit_log.target_id,
        details=audit_log.details,
        created_at=audit_log.created_at,
    )


def append_audit_log(
    *,
    session: Session,
    action_type: AuditActionType,
    outcome_status: AuditOutcomeStatus,
    actor_user_id: object | None = None,
    organization_id: object | None = None,
    subject_user_id: object | None = None,
    target_type: str | None = None,
    target_id: object | None = None,
    details: str | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_user_id=actor_user_id,
        organization_id=organization_id,
        subject_user_id=subject_user_id,
        action_type=action_type,
        outcome_status=outcome_status,
        target_type=target_type,
        target_id=str(target_id) if target_id is not None else None,
        details=details,
    )
    session.add(audit_log)
    session.flush()
    return audit_log
