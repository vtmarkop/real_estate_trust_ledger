from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from trustledger_domain import NotificationChannel, NotificationDeliveryStatus


class NotificationDeliveryResponse(BaseModel):
    id: UUID
    channel: NotificationChannel
    status: NotificationDeliveryStatus
    template_key: str
    recipient_user_id: UUID | None
    recipient_user_email: str | None
    organization_id: UUID | None
    organization_name: str | None
    consent_id: UUID | None
    automation_task_id: UUID | None
    requested_by_user_id: UUID | None
    requested_by_user_email: str | None
    processed_by_user_id: UUID | None
    processed_by_user_email: str | None
    recipient_address: str
    subject_line: str
    body_text: str
    dedupe_key: str | None
    scheduled_for: datetime
    started_at: datetime | None
    completed_at: datetime | None
    sent_at: datetime | None
    attempt_count: int
    last_error: str | None
    created_at: datetime
    updated_at: datetime
