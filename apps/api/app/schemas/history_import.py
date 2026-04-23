from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import HistoryImportStatus


class HistoryImportCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    summary: str | None = Field(default=None, max_length=1000)


class HistoryImportReviewDecisionRequest(BaseModel):
    status: HistoryImportStatus
    review_notes: str | None = Field(default=None, max_length=1000)


class HistoryImportResponse(BaseModel):
    id: UUID
    subject_user_id: UUID
    subject_user_full_name: str
    created_by_user_id: UUID
    created_by_user_full_name: str
    title: str
    summary: str | None = None
    status: HistoryImportStatus
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by_user_id: UUID | None = None
    reviewed_by_user_full_name: str | None = None
    review_notes: str | None = None
    tenancy_count: int
    evidence_document_count: int
    created_at: datetime
    updated_at: datetime
