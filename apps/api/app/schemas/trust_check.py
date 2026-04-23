from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import ConsentScope


class TrustCheckAccessRequest(BaseModel):
    share_token: str = Field(min_length=20, max_length=255)
    access_code: str = Field(min_length=4, max_length=64)


class TrustCheckValidationResponse(BaseModel):
    consent_id: UUID
    organization_id: UUID
    subject_user_id: UUID
    subject_full_name: str
    scope: ConsentScope
    expires_at: datetime
    validated_at: datetime


class TrustProfileSummaryResponse(BaseModel):
    profile_stage: str
    subject_user_id: UUID
    subject_full_name: str
    email_verified: bool
    account_active: bool
    linked_properties: int
    reported_tenancies: int
    counterparty_confirmed_tenancies: int
    reviewed_tenancies: int
    verified_tenancies: int
    submitted_evidence_documents: int
    accepted_evidence_documents: int
    rejected_evidence_documents: int
    submitted_history_imports: int
    accepted_history_imports: int
    rejected_history_imports: int
    counterparty_reference_documents: int
    accepted_counterparty_reference_documents: int
    tenant_score: int
    landlord_score: int
    verification_strength: int
    scoring_version: str
    score_calculated_at: datetime
    active_share_consents: int
    trust_event_count: int
    total_agency_trust_checks: int
    organization_trust_checks: int
    last_trust_event_at: datetime | None = None
    last_agency_trust_check_at: datetime | None = None
    consent_id: UUID
    consent_scope: ConsentScope
    consent_created_at: datetime
    consent_expires_at: datetime
    shared_with_organization_id: UUID
    shared_with_organization_name: str


class AgencyTrustCheckResponse(BaseModel):
    id: UUID
    organization_id: UUID
    consent_id: UUID
    requested_by_user_id: UUID
    requested_by_user_full_name: str
    subject_user_id: UUID
    subject_full_name: str
    scope: ConsentScope
    created_at: datetime


class AgencyTrustCheckResultResponse(AgencyTrustCheckResponse):
    profile: TrustProfileSummaryResponse
