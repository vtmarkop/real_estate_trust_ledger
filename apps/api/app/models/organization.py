import uuid
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import OrganizationType

if TYPE_CHECKING:
    from app.models.agency_trust_check import AgencyTrustCheck
    from app.models.automation_task import AutomationTask
    from app.models.consent import TrustReportConsent
    from app.models.listing import Listing
    from app.models.membership import OrganizationMembership
    from app.models.notification_delivery import NotificationDelivery
    from app.models.property import Property
    from app.models.trust_score_recalculation import TrustScoreRecalculationBatch


class Organization(TimestampedModel, table=True):
    __tablename__ = "organizations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False, max_length=255)
    slug: str = Field(index=True, unique=True, nullable=False, max_length=120)
    organization_type: OrganizationType = Field(
        default=OrganizationType.AGENCY,
        nullable=False,
        max_length=50,
    )
    is_active: bool = Field(default=True, nullable=False)

    memberships: List["OrganizationMembership"] = Relationship(back_populates="organization")
    report_consents: List["TrustReportConsent"] = Relationship(back_populates="grantee_organization")
    listings: List["Listing"] = Relationship(back_populates="organization")
    properties_assigned: List["Property"] = Relationship(back_populates="assigned_agency_organization")
    trust_checks: List["AgencyTrustCheck"] = Relationship(back_populates="organization")
    automation_tasks: List["AutomationTask"] = Relationship(back_populates="organization")
    notification_deliveries: List["NotificationDelivery"] = Relationship(back_populates="organization")
    trust_score_recalculation_batches: List["TrustScoreRecalculationBatch"] = Relationship(
        back_populates="organization"
    )
