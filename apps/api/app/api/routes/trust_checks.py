from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUserDep, OrganizationTrustCheckDep, SessionDep
from app.models import AgencyTrustCheck, User
from app.models.common import utcnow
from app.schemas.trust_check import (
    AgencyTrustCheckResponse,
    AgencyTrustCheckResultResponse,
    TrustCheckAccessRequest,
    TrustProfileSummaryResponse,
    TrustCheckValidationResponse,
)
from app.services.audit_logs import append_audit_log
from app.services.consents import (
    find_trust_report_consent_by_share_token,
    validate_trust_report_consent,
)
from app.services.scoring import refresh_user_trust_score
from app.services.trust_profiles import build_trust_profile_summary
from trustledger_domain import AuditActionType, AuditOutcomeStatus, ScoreCalculationReason


router = APIRouter(prefix="/organizations/{organization_id}/trust-checks", tags=["trust-checks"])


def build_trust_check_response(
    trust_check: AgencyTrustCheck,
    *,
    requester: User,
    subject: User,
) -> AgencyTrustCheckResponse:
    return AgencyTrustCheckResponse(
        id=trust_check.id,
        organization_id=trust_check.organization_id,
        consent_id=trust_check.consent_id,
        requested_by_user_id=trust_check.requested_by_user_id,
        requested_by_user_full_name=requester.full_name,
        subject_user_id=trust_check.subject_user_id,
        subject_full_name=subject.full_name,
        scope=trust_check.scope,
        created_at=trust_check.created_at,
    )


def validate_trust_report_consent_with_audit(
    *,
    session: SessionDep,
    organization,
    actor_user_id,
    action_type: AuditActionType,
    share_token: str,
    access_code: str,
):
    try:
        return validate_trust_report_consent(
            session=session,
            organization=organization,
            share_token=share_token,
            access_code=access_code,
        )
    except HTTPException:
        consent = find_trust_report_consent_by_share_token(
            session=session,
            organization=organization,
            share_token=share_token,
        )
        append_audit_log(
            session=session,
            action_type=action_type,
            outcome_status=AuditOutcomeStatus.DENIED,
            actor_user_id=actor_user_id,
            organization_id=organization.id,
            subject_user_id=consent.subject_user_id if consent else None,
            target_type="trust_report_consent" if consent else "organization",
            target_id=consent.id if consent else organization.id,
            details="Protected trust-sharing access attempt was denied.",
        )
        session.commit()
        raise


@router.post("/validate", response_model=TrustCheckValidationResponse)
def validate_trust_check_access(
    organization_id: UUID,
    payload: TrustCheckAccessRequest,
    access: OrganizationTrustCheckDep,
    session: SessionDep,
) -> TrustCheckValidationResponse:
    validated = validate_trust_report_consent_with_audit(
        session=session,
        organization=access.organization,
        actor_user_id=access.current_user.id,
        action_type=AuditActionType.TRUST_CHECK_VALIDATED,
        share_token=payload.share_token,
        access_code=payload.access_code,
    )
    append_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_CHECK_VALIDATED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=access.current_user.id,
        organization_id=access.organization.id,
        subject_user_id=validated.subject_user.id,
        target_type="trust_report_consent",
        target_id=validated.consent.id,
        details="Agency trust-check access validated.",
    )
    session.commit()
    return TrustCheckValidationResponse(
        consent_id=validated.consent.id,
        organization_id=organization_id,
        subject_user_id=validated.subject_user.id,
        subject_full_name=validated.subject_user.full_name,
        scope=validated.consent.scope,
        expires_at=validated.consent.expires_at,
        validated_at=utcnow(),
    )


@router.post("/profile", response_model=TrustProfileSummaryResponse)
def get_trust_profile_preview(
    payload: TrustCheckAccessRequest,
    access: OrganizationTrustCheckDep,
    session: SessionDep,
) -> TrustProfileSummaryResponse:
    validated = validate_trust_report_consent_with_audit(
        session=session,
        organization=access.organization,
        actor_user_id=access.current_user.id,
        action_type=AuditActionType.TRUST_PROFILE_PREVIEWED,
        share_token=payload.share_token,
        access_code=payload.access_code,
    )
    score_computation = refresh_user_trust_score(
        session=session,
        user=validated.subject_user,
        calculation_reason=ScoreCalculationReason.TRUST_CHECK_PREVIEW,
    )
    append_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_PROFILE_PREVIEWED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=access.current_user.id,
        organization_id=access.organization.id,
        subject_user_id=validated.subject_user.id,
        target_type="trust_report_consent",
        target_id=validated.consent.id,
        details="Agency trust profile previewed.",
    )
    session.commit()
    return build_trust_profile_summary(
        session=session,
        subject_user=validated.subject_user,
        organization=access.organization,
        consent=validated.consent,
        score_computation=score_computation,
    )


@router.post("", response_model=AgencyTrustCheckResultResponse, status_code=201)
def create_trust_check(
    organization_id: UUID,
    payload: TrustCheckAccessRequest,
    current_user: CurrentUserDep,
    access: OrganizationTrustCheckDep,
    session: SessionDep,
) -> AgencyTrustCheckResponse:
    validated = validate_trust_report_consent_with_audit(
        session=session,
        organization=access.organization,
        actor_user_id=current_user.id,
        action_type=AuditActionType.TRUST_CHECK_CREATED,
        share_token=payload.share_token,
        access_code=payload.access_code,
    )
    trust_check = AgencyTrustCheck(
        organization_id=organization_id,
        consent_id=validated.consent.id,
        requested_by_user_id=current_user.id,
        subject_user_id=validated.subject_user.id,
        scope=validated.consent.scope,
    )
    session.add(trust_check)
    session.commit()
    session.refresh(trust_check)

    score_computation = refresh_user_trust_score(
        session=session,
        user=validated.subject_user,
        calculation_reason=ScoreCalculationReason.AGENCY_TRUST_CHECK,
    )
    session.commit()
    profile = build_trust_profile_summary(
        session=session,
        subject_user=validated.subject_user,
        organization=access.organization,
        consent=validated.consent,
        score_computation=score_computation,
    )
    append_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_CHECK_CREATED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=current_user.id,
        organization_id=access.organization.id,
        subject_user_id=validated.subject_user.id,
        target_type="agency_trust_check",
        target_id=trust_check.id,
        details="Agency trust check created from a validated consent.",
    )
    session.commit()
    result = build_trust_check_response(
        trust_check,
        requester=current_user,
        subject=validated.subject_user,
    )
    return AgencyTrustCheckResultResponse(**result.model_dump(), profile=profile)


@router.get("", response_model=list[AgencyTrustCheckResponse])
def list_trust_checks(
    access: OrganizationTrustCheckDep,
    session: SessionDep,
) -> list[AgencyTrustCheckResponse]:
    trust_checks = session.exec(
        select(AgencyTrustCheck)
        .where(AgencyTrustCheck.organization_id == access.organization.id)
        .order_by(AgencyTrustCheck.created_at.desc())
    ).all()

    responses: list[AgencyTrustCheckResponse] = []
    for trust_check in trust_checks:
        requester = session.get(User, trust_check.requested_by_user_id)
        subject = session.get(User, trust_check.subject_user_id)
        if not requester or not subject:
            continue
        responses.append(
            build_trust_check_response(
                trust_check,
                requester=requester,
                subject=subject,
            )
        )
    return responses
