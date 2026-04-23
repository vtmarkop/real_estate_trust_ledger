import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel, utcnow
from trustledger_domain import NotificationChannel, NotificationDeliveryStatus

if TYPE_CHECKING:
    from app.models.automation_task import AutomationTask
    from app.models.consent import TrustReportConsent
    from app.models.organization import Organization
    from app.models.user import User


class NotificationDelivery(TimestampedModel, table=True):
    __tablename__ = "notification_deliveries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    channel: NotificationChannel = Field(
        default=NotificationChannel.EMAIL,
        nullable=False,
        max_length=32,
        index=True,
    )
    status: NotificationDeliveryStatus = Field(
        default=NotificationDeliveryStatus.PENDING,
        nullable=False,
        max_length=32,
        index=True,
    )
    template_key: str = Field(nullable=False, max_length=100, index=True)
    recipient_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
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
    automation_task_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="automation_tasks.id",
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
    recipient_address: str = Field(nullable=False, max_length=320)
    subject_line: str = Field(nullable=False, max_length=255)
    body_text: str = Field(nullable=False, max_length=4000)
    dedupe_key: str | None = Field(default=None, nullable=True, unique=True, max_length=255)
    scheduled_for: datetime = Field(default_factory=utcnow, nullable=False, index=True)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    sent_at: datetime | None = Field(default=None, nullable=True)
    attempt_count: int = Field(default=0, nullable=False, ge=0)
    last_error: str | None = Field(default=None, nullable=True, max_length=500)

    recipient_user: "User" = Relationship(
        back_populates="notification_deliveries_as_recipient",
        sa_relationship_kwargs={"foreign_keys": "NotificationDelivery.recipient_user_id"},
    )
    organization: "Organization" = Relationship(back_populates="notification_deliveries")
    consent: "TrustReportConsent" = Relationship(back_populates="notification_deliveries")
    automation_task: "AutomationTask" = Relationship(back_populates="notification_deliveries")
    requested_by_user: "User" = Relationship(
        back_populates="requested_notification_deliveries",
        sa_relationship_kwargs={"foreign_keys": "NotificationDelivery.requested_by_user_id"},
    )
    processed_by_user: "User" = Relationship(
        back_populates="processed_notification_deliveries",
        sa_relationship_kwargs={"foreign_keys": "NotificationDelivery.processed_by_user_id"},
    )
