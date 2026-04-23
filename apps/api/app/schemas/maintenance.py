from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import (
    DisputeVerdictOutcome,
    MaintenanceTicketPriority,
    MaintenanceTicketStatus,
)


class MaintenanceTicketCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    description: str = Field(min_length=2, max_length=1000)
    priority: MaintenanceTicketPriority = MaintenanceTicketPriority.NORMAL
    reported_stored_artifact_id: UUID | None = None
    reported_artifact_name: str | None = Field(default=None, min_length=2, max_length=255)


class MaintenanceTicketAcknowledgeRequest(BaseModel):
    landlord_response_notes: str | None = Field(default=None, max_length=1000)


class MaintenanceTicketResolveRequest(BaseModel):
    resolution_summary: str = Field(min_length=2, max_length=1000)
    resolution_stored_artifact_id: UUID | None = None
    resolution_artifact_name: str | None = Field(default=None, min_length=2, max_length=255)
    landlord_response_notes: str | None = Field(default=None, max_length=1000)


class MaintenanceTicketDisputeRequest(BaseModel):
    dispute_notes: str = Field(min_length=2, max_length=1000)


class MaintenanceTicketAppealRequest(BaseModel):
    appeal_notes: str = Field(min_length=2, max_length=1000)


class MaintenanceTicketVerdictRequest(BaseModel):
    verdict_outcome: DisputeVerdictOutcome
    verdict_summary: str = Field(min_length=2, max_length=1000)
    tenant_score_delta: int = Field(default=0, ge=-200, le=200)
    landlord_score_delta: int = Field(default=0, ge=-200, le=200)


class MaintenanceTicketResponse(BaseModel):
    id: UUID
    tenancy_id: UUID
    created_by_user_id: UUID
    created_by_user_full_name: str
    acknowledged_by_user_id: UUID | None = None
    acknowledged_by_user_full_name: str | None = None
    resolved_by_user_id: UUID | None = None
    resolved_by_user_full_name: str | None = None
    disputed_by_user_id: UUID | None = None
    disputed_by_user_full_name: str | None = None
    review_requested_by_user_id: UUID | None = None
    review_requested_by_user_full_name: str | None = None
    reviewed_by_user_id: UUID | None = None
    reviewed_by_user_full_name: str | None = None
    appeal_requested_by_user_id: UUID | None = None
    appeal_requested_by_user_full_name: str | None = None
    title: str
    description: str
    priority: MaintenanceTicketPriority
    ticket_status: MaintenanceTicketStatus
    reported_stored_artifact_id: UUID | None = None
    reported_artifact_name: str | None = None
    reported_artifact_content_type: str | None = None
    reported_artifact_size_bytes: int | None = None
    landlord_response_notes: str | None = None
    acknowledged_at: datetime | None = None
    resolution_summary: str | None = None
    resolution_stored_artifact_id: UUID | None = None
    resolution_artifact_name: str | None = None
    resolution_artifact_content_type: str | None = None
    resolution_artifact_size_bytes: int | None = None
    resolved_at: datetime | None = None
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
