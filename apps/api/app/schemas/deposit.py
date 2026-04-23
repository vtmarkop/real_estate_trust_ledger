from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import DepositStatus, DisputeVerdictOutcome


class DepositCreateRequest(BaseModel):
    move_out_date: date | None = None
    return_due_date: date | None = None
    settlement_notes: str | None = Field(default=None, max_length=1000)


class DepositSettlementRequest(BaseModel):
    proposed_return_minor: int = Field(ge=0)
    withheld_amount_minor: int = Field(default=0, ge=0)
    move_out_date: date | None = None
    return_due_date: date | None = None
    returned_at: datetime | None = None
    settlement_stored_artifact_id: UUID | None = None
    settlement_artifact_name: str | None = Field(default=None, min_length=2, max_length=255)
    settlement_summary: str | None = Field(default=None, min_length=2, max_length=1000)
    settlement_notes: str | None = Field(default=None, max_length=1000)


class DepositDisputeRequest(BaseModel):
    dispute_notes: str = Field(min_length=2, max_length=1000)


class DepositAppealRequest(BaseModel):
    appeal_notes: str = Field(min_length=2, max_length=1000)


class DepositVerdictRequest(BaseModel):
    verdict_outcome: DisputeVerdictOutcome
    verdict_summary: str = Field(min_length=2, max_length=1000)
    tenant_score_delta: int = Field(default=0, ge=-200, le=200)
    landlord_score_delta: int = Field(default=0, ge=-200, le=200)


class DepositResponse(BaseModel):
    id: UUID
    tenancy_id: UUID
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
    held_amount_minor: int
    proposed_return_minor: int
    withheld_amount_minor: int
    currency_code: str
    deposit_status: DepositStatus
    move_out_date: date | None = None
    return_due_date: date | None = None
    returned_at: datetime | None = None
    settlement_stored_artifact_id: UUID | None = None
    settlement_artifact_name: str | None = None
    settlement_artifact_content_type: str | None = None
    settlement_artifact_size_bytes: int | None = None
    settlement_summary: str | None = None
    settlement_notes: str | None = None
    dispute_notes: str | None = None
    counterparty_action_at: datetime | None = None
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
