from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.core.security import generate_session_token, hash_password, hash_token
from app.models import Organization, TrustReportConsent
from app.models.common import utcnow
from app.schemas.audit_log import AuditLogResponse
from app.schemas.consent import (
    TrustReportConsentCreateRequest,
    TrustReportConsentCreateResponse,
    TrustReportConsentResponse,
)
from app.services.automation import cancel_consent_expiry_reminder, ensure_consent_expiry_reminder
from app.services.audit_logs import append_audit_log, build_audit_log_response
from trustledger_domain import AuditActionType, AuditOutcomeStatus, ConsentScope, OrganizationType
from app.models import AuditLog


router = APIRouter(prefix="/consents/trust-report", tags=["consents"])


def build_consent_response(
    consent: TrustReportConsent,
    organization: Organization,
) -> TrustReportConsentResponse:
    return TrustReportConsentResponse(
        id=consent.id,
        subject_user_id=consent.subject_user_id,
        granted_by_user_id=consent.granted_by_user_id,
        grantee_organization_id=consent.grantee_organization_id,
        grantee_organization_name=organization.name,
        grantee_organization_slug=organization.slug,
        scope=consent.scope,
        failed_access_attempt_count=consent.failed_access_attempt_count,
        last_access_attempt_at=consent.last_access_attempt_at,
        access_locked_until=consent.access_locked_until,
        last_validated_at=consent.last_validated_at,
        expires_at=consent.expires_at,
        revoked_at=consent.revoked_at,
        is_active=consent.is_active(),
        created_at=consent.created_at,
    )


@router.post("", response_model=TrustReportConsentCreateResponse, status_code=status.HTTP_201_CREATED)
def create_trust_report_consent(
    payload: TrustReportConsentCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> TrustReportConsentCreateResponse:
    organization = session.get(Organization, payload.grantee_organization_id)
    if not organization or not organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grantee organization not found.",
        )
    if organization.organization_type != OrganizationType.AGENCY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Trust report sharing is currently limited to agency organizations.",
        )

    share_token = generate_session_token()
    consent = TrustReportConsent(
        subject_user_id=current_user.id,
        granted_by_user_id=current_user.id,
        grantee_organization_id=organization.id,
        scope=ConsentScope.TRUST_REPORT_READ,
        share_token_hash=hash_token(share_token),
        access_code_hash=hash_password(payload.access_code.strip()),
        expires_at=utcnow() + timedelta(days=payload.expires_in_days),
    )
    session.add(consent)
    session.commit()
    session.refresh(consent)
    ensure_consent_expiry_reminder(session=session, consent=consent)
    append_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_REPORT_CONSENT_CREATED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=current_user.id,
        organization_id=organization.id,
        subject_user_id=current_user.id,
        target_type="trust_report_consent",
        target_id=consent.id,
        details=f"Trust report consent granted to organization {organization.slug}.",
    )
    session.commit()
    session.refresh(consent)

    response = build_consent_response(consent, organization)
    return TrustReportConsentCreateResponse(**response.model_dump(), share_token=share_token)


@router.get("", response_model=list[TrustReportConsentResponse])
def list_trust_report_consents(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[TrustReportConsentResponse]:
    consents = session.exec(
        select(TrustReportConsent)
        .where(TrustReportConsent.subject_user_id == current_user.id)
        .order_by(TrustReportConsent.created_at.desc())
    ).all()

    responses: list[TrustReportConsentResponse] = []
    for consent in consents:
        organization = session.get(Organization, consent.grantee_organization_id)
        if not organization:
            continue
        responses.append(build_consent_response(consent, organization))
    return responses


@router.get("/access-history", response_model=list[AuditLogResponse])
def list_trust_report_access_history(
    current_user: CurrentUserDep,
    session: SessionDep,
    organization_id: UUID | None = None,
    limit: int = 50,
) -> list[AuditLogResponse]:
    query = (
        select(AuditLog)
        .where(
            AuditLog.subject_user_id == current_user.id,
            AuditLog.action_type.in_(
                [
                    AuditActionType.TRUST_CHECK_VALIDATED,
                    AuditActionType.TRUST_PROFILE_PREVIEWED,
                    AuditActionType.TRUST_CHECK_CREATED,
                ]
            ),
        )
        .order_by(AuditLog.created_at.desc())
    )
    if organization_id is not None:
        query = query.where(AuditLog.organization_id == organization_id)

    audit_logs = session.exec(query).all()[: max(1, min(limit, 100))]
    return [
        build_audit_log_response(session=session, audit_log=audit_log)
        for audit_log in audit_logs
    ]


@router.post("/{consent_id}/revoke", response_model=TrustReportConsentResponse)
def revoke_trust_report_consent(
    consent_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> TrustReportConsentResponse:
    consent = session.exec(
        select(TrustReportConsent).where(
            TrustReportConsent.id == consent_id,
            TrustReportConsent.subject_user_id == current_user.id,
        )
    ).first()
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found.",
        )

    if consent.revoked_at is None:
        consent.revoked_at = utcnow()
        consent.updated_at = utcnow()
        session.add(consent)
        cancel_consent_expiry_reminder(
            session=session,
            consent=consent,
            result_notes="Consent revoked by subject user before expiry.",
        )
        append_audit_log(
            session=session,
            action_type=AuditActionType.TRUST_REPORT_CONSENT_REVOKED,
            outcome_status=AuditOutcomeStatus.CANCELED,
            actor_user_id=current_user.id,
            organization_id=consent.grantee_organization_id,
            subject_user_id=current_user.id,
            target_type="trust_report_consent",
            target_id=consent.id,
            details="Trust report consent revoked by subject user.",
        )
        session.commit()
        session.refresh(consent)

    organization = session.get(Organization, consent.grantee_organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grantee organization not found.",
        )
    return build_consent_response(consent, organization)
