import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import ListingStatus

if TYPE_CHECKING:
    from app.models.application import ListingApplication
    from app.models.organization import Organization
    from app.models.property import Property
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class Listing(TimestampedModel, table=True):
    __tablename__ = "listings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    organization_id: uuid.UUID = Field(foreign_key="organizations.id", nullable=False, index=True)
    property_id: uuid.UUID = Field(foreign_key="properties.id", nullable=False, index=True)
    created_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    listing_status: ListingStatus = Field(default=ListingStatus.OPEN, nullable=False, max_length=32)
    title: str = Field(nullable=False, max_length=255)
    description: Optional[str] = Field(default=None, nullable=True, max_length=1000)
    monthly_rent_minor: int = Field(nullable=False, ge=0)
    deposit_minor: int = Field(default=0, nullable=False, ge=0)
    currency_code: str = Field(default="EUR", nullable=False, max_length=3)
    minimum_counterparty_confirmed_tenancies: int = Field(default=0, nullable=False, ge=0)
    minimum_verified_tenancies: int = Field(default=0, nullable=False, ge=0)
    minimum_tenant_score: int = Field(default=0, nullable=False, ge=0, le=1000)
    minimum_verification_strength: int = Field(default=0, nullable=False, ge=0, le=100)

    organization: "Organization" = Relationship(back_populates="listings")
    property_record: "Property" = Relationship(back_populates="listings")
    created_by_user: "User" = Relationship(back_populates="listings_created")
    applications: List["ListingApplication"] = Relationship(back_populates="listing")
    trust_events: List["TrustEvent"] = Relationship(back_populates="listing")
