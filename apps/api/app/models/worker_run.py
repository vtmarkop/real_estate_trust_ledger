import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel, utcnow
from trustledger_domain import WorkerRunStatus

if TYPE_CHECKING:
    from app.models.user import User


class WorkerRun(TimestampedModel, table=True):
    __tablename__ = "worker_runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    worker_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    status: WorkerRunStatus = Field(
        default=WorkerRunStatus.RUNNING,
        nullable=False,
        max_length=32,
        index=True,
    )
    run_started_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)
    run_completed_at: datetime | None = Field(default=None, nullable=True)
    due_before: datetime = Field(default_factory=utcnow, nullable=False)
    requested_limit: int = Field(default=100, nullable=False, ge=1)
    claimed_automation_task_count: int = Field(default=0, nullable=False, ge=0)
    completed_automation_task_count: int = Field(default=0, nullable=False, ge=0)
    failed_automation_task_count: int = Field(default=0, nullable=False, ge=0)
    claimed_notification_count: int = Field(default=0, nullable=False, ge=0)
    sent_notification_count: int = Field(default=0, nullable=False, ge=0)
    failed_notification_count: int = Field(default=0, nullable=False, ge=0)
    processed_score_request_count: int = Field(default=0, nullable=False, ge=0)
    failed_score_request_count: int = Field(default=0, nullable=False, ge=0)
    cleaned_consent_reminder_count: int = Field(default=0, nullable=False, ge=0)
    cleaned_stale_follow_up_count: int = Field(default=0, nullable=False, ge=0)
    last_error: str | None = Field(default=None, nullable=True, max_length=1000)

    worker_user: "User" = Relationship(back_populates="worker_runs")
