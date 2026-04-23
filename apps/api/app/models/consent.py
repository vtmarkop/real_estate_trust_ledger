import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel, ensure_utc, utcnow
from trustledger_domain import ConsentScope

if TYPE_CHECKING:
    from app.models.agency_trust_check import AgencyTrustCheck
    from app.models.automation_task import AutomationTask
    from app.models.notification_delivery import NotificationDelivery
    from app.models.organization import Organization
    from app.models.user import User


class TrustReportConsent(TimestampedModel, table=True):
    __tablename__ = "trust_report_consents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subject_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    granted_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    grantee_organization_id: uuid.UUID = Field(foreign_key="organizations.id", nullable=False)
    scope: ConsentScope = Field(default=ConsentScope.TRUST_REPORT_READ, nullable=False, max_length=50)
    share_token_hash: str = Field(index=True, unique=True, nullable=False, max_length=64)
    access_code_hash: str = Field(nullable=False, max_length=255)
    failed_access_attempt_count: int = Field(default=0, nullable=False, ge=0)
    last_access_attempt_at: Optional[datetime] = Field(default=None, nullable=True)
    access_locked_until: Optional[datetime] = Field(default=None, nullable=True)
    last_validated_at: Optional[datetime] = Field(default=None, nullable=True)
    expires_at: datetime = Field(nullable=False)
    revoked_at: Optional[datetime] = Field(default=None, nullable=True)

    subject_user: "User" = Relationship(
        back_populates="consents_as_subject",
        sa_relationship_kwargs={"foreign_keys": "TrustReportConsent.subject_user_id"},
    )
    granted_by_user: "User" = Relationship(
        back_populates="consents_granted",
        sa_relationship_kwargs={"foreign_keys": "TrustReportConsent.granted_by_user_id"},
    )
    grantee_organization: "Organization" = Relationship(back_populates="report_consents")
    trust_checks: List["AgencyTrustCheck"] = Relationship(back_populates="consent")
    automation_tasks: List["AutomationTask"] = Relationship(back_populates="consent")
    notification_deliveries: List["NotificationDelivery"] = Relationship(back_populates="consent")

    def is_active(self, *, now: Optional[datetime] = None) -> bool:
        current = ensure_utc(now or utcnow())
        expires_at = ensure_utc(self.expires_at)
        return self.revoked_at is None and current < expires_at

    def is_access_locked(self, *, now: Optional[datetime] = None) -> bool:
        if self.access_locked_until is None:
            return False
        current = ensure_utc(now or utcnow())
        return current < ensure_utc(self.access_locked_until)
