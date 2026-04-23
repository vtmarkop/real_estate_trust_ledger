from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.security import hash_token, verify_password
from app.models import Organization, TrustReportConsent, User
from app.models.common import utcnow


MAX_FAILED_TRUST_REPORT_ACCESS_ATTEMPTS = 5
TRUST_REPORT_ACCESS_LOCKOUT_DURATION = timedelta(minutes=15)


@dataclass
class ValidatedTrustConsent:
    consent: TrustReportConsent
    subject_user: User
    organization: Organization


def find_trust_report_consent_by_share_token(
    *,
    session: Session,
    organization: Organization,
    share_token: str,
) -> TrustReportConsent | None:
    share_token_hash = hash_token(share_token.strip())
    consent = session.exec(
        select(TrustReportConsent).where(
            TrustReportConsent.share_token_hash == share_token_hash
        )
    ).first()
    if consent and consent.grantee_organization_id == organization.id:
        return consent
    return None


def validate_trust_report_consent(
    *,
    session: Session,
    organization: Organization,
    share_token: str,
    access_code: str,
) -> ValidatedTrustConsent:
    consent = find_trust_report_consent_by_share_token(
        session=session,
        organization=organization,
        share_token=share_token,
    )

    if not consent or consent.grantee_organization_id != organization.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found for this organization.",
        )

    if not consent.is_active():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Consent is expired or revoked.",
        )

    current_time = utcnow()
    if consent.is_access_locked(now=current_time):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Consent access is temporarily locked after repeated failed attempts.",
        )

    if not verify_password(access_code, consent.access_code_hash):
        consent.failed_access_attempt_count += 1
        consent.last_access_attempt_at = current_time
        consent.updated_at = current_time
        if consent.failed_access_attempt_count >= MAX_FAILED_TRUST_REPORT_ACCESS_ATTEMPTS:
            consent.access_locked_until = current_time + TRUST_REPORT_ACCESS_LOCKOUT_DURATION
            session.add(consent)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Consent access is temporarily locked after repeated failed attempts.",
            )
        session.add(consent)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access code is invalid.",
        )

    if (
        consent.failed_access_attempt_count > 0
        or consent.access_locked_until is not None
        or consent.last_validated_at is None
    ):
        consent.failed_access_attempt_count = 0
        consent.access_locked_until = None
        consent.last_validated_at = current_time
        consent.updated_at = current_time
        session.add(consent)
    else:
        consent.last_validated_at = current_time
        consent.updated_at = current_time
        session.add(consent)

    subject_user = session.get(User, consent.subject_user_id)
    if not subject_user or not subject_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent subject is unavailable.",
        )

    return ValidatedTrustConsent(
        consent=consent,
        subject_user=subject_user,
        organization=organization,
    )
