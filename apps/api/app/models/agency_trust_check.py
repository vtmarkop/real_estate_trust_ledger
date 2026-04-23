import uuid
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import ConsentScope

if TYPE_CHECKING:
    from app.models.consent import TrustReportConsent
    from app.models.organization import Organization
    from app.models.user import User


class AgencyTrustCheck(TimestampedModel, table=True):
    __tablename__ = "agency_trust_checks"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID = Field(foreign_key="organizations.id", nullable=False, index=True)
    consent_id: uuid.UUID = Field(foreign_key="trust_report_consents.id", nullable=False, index=True)
    requested_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    subject_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    scope: ConsentScope = Field(default=ConsentScope.TRUST_REPORT_READ, nullable=False, max_length=50)

    organization: "Organization" = Relationship(back_populates="trust_checks")
    consent: "TrustReportConsent" = Relationship(back_populates="trust_checks")
    requested_by_user: "User" = Relationship(
        back_populates="requested_trust_checks",
        sa_relationship_kwargs={"foreign_keys": "AgencyTrustCheck.requested_by_user_id"},
    )
    subject_user: "User" = Relationship(
        back_populates="subject_trust_checks",
        sa_relationship_kwargs={"foreign_keys": "AgencyTrustCheck.subject_user_id"},
    )
