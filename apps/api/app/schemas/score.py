from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, model_validator


class TrustScoreInputsResponse(BaseModel):
    tenant_counterparty_confirmed_tenancies: int
    tenant_verified_tenancies: int
    landlord_counterparty_confirmed_tenancies: int
    landlord_verified_tenancies: int
    accepted_tenant_evidence_documents: int
    accepted_landlord_evidence_documents: int
    accepted_tenant_counterparty_references: int
    accepted_landlord_counterparty_references: int
    accepted_history_imports: int
    tenant_adjudication_adjustment: int
    landlord_adjudication_adjustment: int


class TrustScoreSummaryResponse(BaseModel):
    user_id: UUID
    tenant_score: int
    landlord_score: int
    verification_strength: int
    scoring_version: str
    calculated_at: datetime
    inputs: TrustScoreInputsResponse


class TrustScoreHistoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    tenant_score: int
    landlord_score: int
    verification_strength: int
    scoring_version: str
    calculation_reason: str
    calculated_at: datetime


class TrustScoreRecalculationRequestResponse(BaseModel):
    id: UUID
    user_id: UUID
    batch_id: UUID | None
    requested_by_user_id: UUID | None
    processed_by_user_id: UUID | None
    calculation_reason: str
    status: str
    attempt_count: int
    scheduled_for: datetime
    started_at: datetime | None
    completed_at: datetime | None
    last_error: str | None
    result_tenant_score: int | None
    result_landlord_score: int | None
    result_verification_strength: int | None
    result_scoring_version: str | None
    result_calculated_at: datetime | None
    created_at: datetime


class TrustScoreRecalculationBatchCreateRequest(BaseModel):
    scope_type: str
    organization_id: UUID | None = None
    scheduled_for: datetime | None = None


class TrustScoreRecalculationDirectCreateRequest(BaseModel):
    user_id: UUID | None = None
    user_email: EmailStr | None = None
    scheduled_for: datetime | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "TrustScoreRecalculationDirectCreateRequest":
        if self.user_id is None and self.user_email is None:
            raise ValueError("Either user_id or user_email must be provided.")
        return self


class TrustScoreRecalculationBatchResponse(BaseModel):
    id: UUID
    scope_type: str
    organization_id: UUID | None
    requested_by_user_id: UUID | None
    calculation_reason: str
    status: str
    scheduled_for: datetime
    requested_user_count: int
    pending_request_count: int
    processing_request_count: int
    completed_request_count: int
    failed_request_count: int
    request_ids: list[UUID]
    started_at: datetime | None
    completed_at: datetime | None
    last_error: str | None
    created_at: datetime
