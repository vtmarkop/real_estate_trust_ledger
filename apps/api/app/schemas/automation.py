from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from trustledger_domain import AutomationTaskStatus, AutomationTaskType


class AutomationTaskResponse(BaseModel):
    id: UUID
    task_type: AutomationTaskType
    status: AutomationTaskStatus
    title: str
    details: str | None
    result_notes: str | None
    subject_user_id: UUID | None
    subject_user_email: str | None
    organization_id: UUID | None
    organization_name: str | None
    consent_id: UUID | None
    consent_expires_at: datetime | None
    score_recalculation_request_id: UUID | None
    score_recalculation_batch_id: UUID | None
    requested_by_user_id: UUID | None
    processed_by_user_id: UUID | None
    dedupe_key: str | None
    scheduled_for: datetime
    started_at: datetime | None
    completed_at: datetime | None
    attempt_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime


class AutomationFollowUpCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    details: str | None = Field(default=None, max_length=1000)
    subject_user_id: UUID | None = None
    subject_user_email: EmailStr | None = None
    organization_id: UUID | None = None
    scheduled_for: datetime | None = None


class AutomationTaskProcessRequest(BaseModel):
    status: AutomationTaskStatus
    result_notes: str | None = Field(default=None, max_length=1000)


class ScheduledScoreRefreshTaskCreateRequest(BaseModel):
    scheduled_for: datetime | None = None


class AutomationTaskClaimRequest(BaseModel):
    task_type: AutomationTaskType | None = None
    limit: int = Field(default=1, ge=1, le=100)
    due_before: datetime | None = None


class AutomationCleanupRequest(BaseModel):
    due_before: datetime | None = None
    stale_after_days: int = Field(default=30, ge=1, le=365)


class AutomationCleanupResponse(BaseModel):
    task_type: AutomationTaskType | None
    processed_task_count: int
    task_ids: list[UUID]
    processed_at: datetime
