from __future__ import annotations

from sqlmodel import Session, select
from sqlalchemy import or_

from app.models import (
    AgencyTrustCheck,
    EvidenceDocument,
    HistoryImport,
    Organization,
    Tenancy,
    TrustEvent,
    TrustReportConsent,
    User,
)
from app.schemas.score import TrustScoreInputsResponse
from app.services.scoring import TrustScoreComputation
from app.schemas.trust_check import TrustProfileSummaryResponse
from trustledger_domain import (
    EvidenceDocumentType,
    EvidenceReviewStatus,
    HistoryImportStatus,
    VerificationStatus,
)


PROFILE_STAGE = "reference_flow_foundation"


def build_trust_profile_summary(
    *,
    session: Session,
    subject_user: User,
    organization: Organization,
    consent: TrustReportConsent,
    score_computation: TrustScoreComputation,
) -> TrustProfileSummaryResponse:
    consents = session.exec(
        select(TrustReportConsent).where(
            TrustReportConsent.subject_user_id == subject_user.id
        )
    ).all()
    trust_checks = session.exec(
        select(AgencyTrustCheck)
        .where(AgencyTrustCheck.subject_user_id == subject_user.id)
        .order_by(AgencyTrustCheck.created_at.desc())
    ).all()
    tenancies = session.exec(
        select(Tenancy).where(
            or_(
                Tenancy.tenant_user_id == subject_user.id,
                Tenancy.landlord_user_id == subject_user.id,
            )
        )
    ).all()
    history_imports = session.exec(
        select(HistoryImport).where(HistoryImport.subject_user_id == subject_user.id)
    ).all()
    evidence_documents = session.exec(
        select(EvidenceDocument).where(EvidenceDocument.subject_user_id == subject_user.id)
    ).all()
    trust_events = session.exec(
        select(TrustEvent)
        .where(TrustEvent.subject_user_id == subject_user.id)
        .order_by(TrustEvent.created_at.desc())
    ).all()

    active_share_consents = sum(1 for current in consents if current.is_active())
    organization_trust_checks = sum(
        1 for trust_check in trust_checks if trust_check.organization_id == organization.id
    )
    linked_properties = len({tenancy.property_id for tenancy in tenancies if tenancy.property_id is not None})
    counterparty_confirmed_tenancies = sum(
        1
        for tenancy in tenancies
        if tenancy.verification_status == VerificationStatus.COUNTERPARTY_CONFIRMED
    )
    reviewed_tenancies = sum(
        1
        for tenancy in tenancies
        if tenancy.verification_status in {VerificationStatus.REVIEWED, VerificationStatus.VERIFIED}
    )
    verified_tenancies = sum(
        1 for tenancy in tenancies if tenancy.verification_status == VerificationStatus.VERIFIED
    )
    accepted_evidence_documents = sum(
        1
        for evidence_document in evidence_documents
        if evidence_document.review_status == EvidenceReviewStatus.ACCEPTED
    )
    rejected_evidence_documents = sum(
        1
        for evidence_document in evidence_documents
        if evidence_document.review_status == EvidenceReviewStatus.REJECTED
    )
    submitted_history_imports = sum(
        1 for history_import in history_imports if history_import.status == HistoryImportStatus.SUBMITTED
    )
    accepted_history_imports = sum(
        1 for history_import in history_imports if history_import.status == HistoryImportStatus.ACCEPTED
    )
    rejected_history_imports = sum(
        1 for history_import in history_imports if history_import.status == HistoryImportStatus.REJECTED
    )
    counterparty_reference_documents = sum(
        1
        for evidence_document in evidence_documents
        if evidence_document.document_type == EvidenceDocumentType.LANDLORD_REFERENCE
        and evidence_document.reference_request_id is not None
    )
    accepted_counterparty_reference_documents = sum(
        1
        for evidence_document in evidence_documents
        if evidence_document.document_type == EvidenceDocumentType.LANDLORD_REFERENCE
        and evidence_document.reference_request_id is not None
        and evidence_document.review_status == EvidenceReviewStatus.ACCEPTED
    )
    last_trust_event_at = trust_events[0].created_at if trust_events else None
    last_agency_trust_check_at = trust_checks[0].created_at if trust_checks else None

    return TrustProfileSummaryResponse(
        profile_stage=PROFILE_STAGE,
        subject_user_id=subject_user.id,
        subject_full_name=subject_user.full_name,
        email_verified=subject_user.email_verified,
        account_active=subject_user.is_active,
        linked_properties=linked_properties,
        reported_tenancies=len(tenancies),
        counterparty_confirmed_tenancies=counterparty_confirmed_tenancies,
        reviewed_tenancies=reviewed_tenancies,
        verified_tenancies=verified_tenancies,
        submitted_evidence_documents=len(evidence_documents),
        accepted_evidence_documents=accepted_evidence_documents,
        rejected_evidence_documents=rejected_evidence_documents,
        submitted_history_imports=submitted_history_imports,
        accepted_history_imports=accepted_history_imports,
        rejected_history_imports=rejected_history_imports,
        counterparty_reference_documents=counterparty_reference_documents,
        accepted_counterparty_reference_documents=accepted_counterparty_reference_documents,
        tenant_score=score_computation.tenant_score,
        landlord_score=score_computation.landlord_score,
        verification_strength=score_computation.verification_strength,
        scoring_version=score_computation.scoring_version,
        score_calculated_at=score_computation.calculated_at,
        score_inputs=TrustScoreInputsResponse(
            tenant_counterparty_confirmed_tenancies=score_computation.inputs.tenant_counterparty_confirmed_tenancies,
            tenant_verified_tenancies=score_computation.inputs.tenant_verified_tenancies,
            landlord_counterparty_confirmed_tenancies=score_computation.inputs.landlord_counterparty_confirmed_tenancies,
            landlord_verified_tenancies=score_computation.inputs.landlord_verified_tenancies,
            accepted_tenant_evidence_documents=score_computation.inputs.accepted_tenant_evidence_documents,
            accepted_landlord_evidence_documents=score_computation.inputs.accepted_landlord_evidence_documents,
            accepted_tenant_counterparty_references=score_computation.inputs.accepted_tenant_counterparty_references,
            accepted_landlord_counterparty_references=score_computation.inputs.accepted_landlord_counterparty_references,
            accepted_history_imports=score_computation.inputs.accepted_history_imports,
            tenant_adjudication_adjustment=score_computation.inputs.tenant_adjudication_adjustment,
            landlord_adjudication_adjustment=score_computation.inputs.landlord_adjudication_adjustment,
        ),
        active_share_consents=active_share_consents,
        trust_event_count=len(trust_events),
        total_agency_trust_checks=len(trust_checks),
        organization_trust_checks=organization_trust_checks,
        last_trust_event_at=last_trust_event_at,
        last_agency_trust_check_at=last_agency_trust_check_at,
        consent_id=consent.id,
        consent_scope=consent.scope,
        consent_created_at=consent.created_at,
        consent_expires_at=consent.expires_at,
        shared_with_organization_id=organization.id,
        shared_with_organization_name=organization.name,
    )
