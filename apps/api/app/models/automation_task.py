import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel, utcnow
from trustledger_domain import AutomationTaskStatus, AutomationTaskType

if TYPE_CHECKING:
    from app.models.notification_delivery import NotificationDelivery
    from app.models.consent import TrustReportConsent
    from app.models.organization import Organization
    from app.models.trust_score_recalculation import (
        TrustScoreRecalculationBatch,
        TrustScoreRecalculationRequest,
    )
    from app.models.user import User


class AutomationTask(TimestampedModel, table=True):
    __tablename__ = "automation_tasks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    task_type: AutomationTaskType = Field(nullable=False, max_length=64, index=True)
    status: AutomationTaskStatus = Field(
        default=AutomationTaskStatus.PENDING,
        nullable=False,
        max_length=32,
        index=True,
    )
    title: str = Field(nullable=False, max_length=255)
    details: str | None = Field(default=None, nullable=True, max_length=1000)
    result_notes: str | None = Field(default=None, nullable=True, max_length=1000)
    subject_user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True, index=True)
    organization_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="organizations.id",
        nullable=True,
        index=True,
    )
    consent_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="trust_report_consents.id",
        nullable=True,
        index=True,
    )
    requested_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    processed_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    score_recalculation_request_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="trust_score_recalculation_requests.id",
        nullable=True,
        index=True,
    )
    score_recalculation_batch_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="trust_score_recalculation_batches.id",
        nullable=True,
        index=True,
    )
    dedupe_key: str | None = Field(default=None, nullable=True, unique=True, max_length=255)
    scheduled_for: datetime = Field(default_factory=utcnow, nullable=False, index=True)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    attempt_count: int = Field(default=0, nullable=False, ge=0)
    last_error: str | None = Field(default=None, nullable=True, max_length=500)

    subject_user: "User" = Relationship(
        back_populates="automation_tasks_as_subject",
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.subject_user_id"},
    )
    organization: "Organization" = Relationship(back_populates="automation_tasks")
    consent: "TrustReportConsent" = Relationship(back_populates="automation_tasks")
    requested_by_user: "User" = Relationship(
        back_populates="requested_automation_tasks",
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.requested_by_user_id"},
    )
    processed_by_user: "User" = Relationship(
        back_populates="processed_automation_tasks",
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.processed_by_user_id"},
    )
    score_recalculation_request: "TrustScoreRecalculationRequest" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.score_recalculation_request_id"}
    )
    score_recalculation_batch: "TrustScoreRecalculationBatch" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.score_recalculation_batch_id"}
    )
    notification_deliveries: list["NotificationDelivery"] = Relationship(
        back_populates="automation_task"
    )
