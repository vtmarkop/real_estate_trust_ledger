from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import (
    DisputeVerdictOutcome,
    PaymentProofStatus,
    PaymentRecordStatus,
    PaymentRecordType,
)


class PaymentCreateRequest(BaseModel):
    payer_user_id: UUID
    payee_user_id: UUID
    payment_type: PaymentRecordType
    amount_minor: int = Field(ge=0)
    currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    due_date: date
    period_start_date: date | None = None
    period_end_date: date | None = None
    paid_at: datetime | None = None
    proof_stored_artifact_id: UUID | None = None
    proof_artifact_name: str | None = Field(default=None, min_length=2, max_length=255)
    proof_summary: str | None = Field(default=None, min_length=2, max_length=1000)
    external_reference: str | None = Field(default=None, min_length=2, max_length=255)


class PaymentProofSubmitRequest(BaseModel):
    proof_stored_artifact_id: UUID | None = None
    proof_artifact_name: str = Field(min_length=2, max_length=255)
    proof_summary: str = Field(min_length=2, max_length=1000)
    paid_at: datetime | None = None
    external_reference: str | None = Field(default=None, min_length=2, max_length=255)


class PaymentDecisionRequest(BaseModel):
    payment_status: PaymentRecordStatus
    counterparty_notes: str | None = Field(default=None, max_length=1000)
    counterparty_stored_artifact_id: UUID | None = None
    counterparty_artifact_name: str | None = Field(default=None, min_length=2, max_length=255)


class PaymentDisputeRequest(BaseModel):
    dispute_notes: str = Field(min_length=2, max_length=1000)


class PaymentAppealRequest(BaseModel):
    appeal_notes: str = Field(min_length=2, max_length=1000)


class PaymentVerdictRequest(BaseModel):
    verdict_outcome: DisputeVerdictOutcome
    verdict_summary: str = Field(min_length=2, max_length=1000)
    tenant_score_delta: int = Field(default=0, ge=-200, le=200)
    landlord_score_delta: int = Field(default=0, ge=-200, le=200)


class PaymentResponse(BaseModel):
    id: UUID
    tenancy_id: UUID
    payer_user_id: UUID
    payer_user_full_name: str
    payee_user_id: UUID
    payee_user_full_name: str
    created_by_user_id: UUID
    created_by_user_full_name: str
    counterparty_action_by_user_id: UUID | None = None
    counterparty_action_by_user_full_name: str | None = None
    disputed_by_user_id: UUID | None = None
    disputed_by_user_full_name: str | None = None
    review_requested_by_user_id: UUID | None = None
    review_requested_by_user_full_name: str | None = None
    reviewed_by_user_id: UUID | None = None
    reviewed_by_user_full_name: str | None = None
    appeal_requested_by_user_id: UUID | None = None
    appeal_requested_by_user_full_name: str | None = None
    payment_type: PaymentRecordType
    payment_status: PaymentRecordStatus
    proof_status: PaymentProofStatus
    amount_minor: int
    currency_code: str
    due_date: date
    period_start_date: date | None = None
    period_end_date: date | None = None
    paid_at: datetime | None = None
    proof_stored_artifact_id: UUID | None = None
    counterparty_stored_artifact_id: UUID | None = None
    proof_artifact_name: str | None = None
    counterparty_artifact_name: str | None = None
    proof_artifact_content_type: str | None = None
    proof_artifact_size_bytes: int | None = None
    counterparty_artifact_content_type: str | None = None
    counterparty_artifact_size_bytes: int | None = None
    proof_summary: str | None = None
    external_reference: str | None = None
    counterparty_notes: str | None = None
    counterparty_action_at: datetime | None = None
    dispute_notes: str | None = None
    disputed_at: datetime | None = None
    review_requested_at: datetime | None = None
    verdict_outcome: DisputeVerdictOutcome | None = None
    verdict_summary: str | None = None
    verdict_tenant_score_delta: int = 0
    verdict_landlord_score_delta: int = 0
    reviewed_at: datetime | None = None
    appeal_notes: str | None = None
    appeal_requested_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
