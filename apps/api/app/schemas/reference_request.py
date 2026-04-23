from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import ReferenceRequestStatus


class ReferenceRequestCreateRequest(BaseModel):
    subject_user_id: UUID
    requested_from_user_id: UUID
    message: str | None = Field(default=None, max_length=1000)


class ReferenceRequestFulfillmentRequest(BaseModel):
    artifact_name: str = Field(min_length=2, max_length=255)
    summary: str = Field(min_length=2, max_length=1000)
    stored_artifact_id: UUID | None = None
    issuer_name: str | None = Field(default=None, max_length=255)
    external_reference: str | None = Field(default=None, max_length=255)


class ReferenceRequestResponse(BaseModel):
    id: UUID
    tenancy_id: UUID
    subject_user_id: UUID
    subject_user_full_name: str
    requested_by_user_id: UUID
    requested_by_user_full_name: str
    requested_from_user_id: UUID
    requested_from_user_full_name: str
    status: ReferenceRequestStatus
    message: str | None = None
    fulfilled_at: datetime | None = None
    fulfilled_evidence_document_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
