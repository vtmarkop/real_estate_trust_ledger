from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import EvidenceDocumentType, EvidenceReviewStatus


class EvidenceCreateRequest(BaseModel):
    subject_user_id: UUID
    document_type: EvidenceDocumentType
    artifact_name: str = Field(min_length=2, max_length=255)
    summary: str = Field(min_length=2, max_length=1000)
    stored_artifact_id: UUID | None = None
    issuer_name: str | None = Field(default=None, max_length=255)
    document_date: date | None = None
    amount_minor: int | None = Field(default=None, ge=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    external_reference: str | None = Field(default=None, max_length=255)


class EvidenceReviewDecisionRequest(BaseModel):
    review_status: EvidenceReviewStatus
    review_notes: str | None = Field(default=None, max_length=1000)


class EvidenceResponse(BaseModel):
    id: UUID
    tenancy_id: UUID
    subject_user_id: UUID
    subject_user_full_name: str
    uploaded_by_user_id: UUID
    uploaded_by_user_full_name: str
    reference_request_id: UUID | None = None
    reference_requested_from_user_id: UUID | None = None
    reference_requested_from_user_full_name: str | None = None
    document_type: EvidenceDocumentType
    review_status: EvidenceReviewStatus
    artifact_name: str
    stored_artifact_id: UUID | None = None
    has_uploaded_artifact: bool
    artifact_content_type: str | None = None
    artifact_size_bytes: int | None = None
    summary: str
    issuer_name: str | None = None
    document_date: date | None = None
    amount_minor: int | None = None
    currency_code: str | None = None
    external_reference: str | None = None
    review_requested_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by_user_id: UUID | None = None
    reviewed_by_user_full_name: str | None = None
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime
