from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from trustledger_domain import WorkerRunStatus


class WorkerRunResponse(BaseModel):
    id: UUID
    worker_user_id: UUID
    worker_user_email: str | None
    status: WorkerRunStatus
    run_started_at: datetime
    run_completed_at: datetime | None
    due_before: datetime
    requested_limit: int
    claimed_automation_task_count: int
    completed_automation_task_count: int
    failed_automation_task_count: int
    claimed_notification_count: int
    sent_notification_count: int
    failed_notification_count: int
    processed_score_request_count: int
    failed_score_request_count: int
    cleaned_consent_reminder_count: int
    cleaned_stale_follow_up_count: int
    last_error: str | None
    created_at: datetime
