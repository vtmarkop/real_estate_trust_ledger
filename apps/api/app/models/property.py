import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.organization import Organization
    from app.models.tenancy import Tenancy
    from app.models.user import User


class Property(TimestampedModel, table=True):
    __tablename__ = "properties"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    property_label: str = Field(nullable=False, max_length=255)
    address_line1: str = Field(nullable=False, max_length=255)
    city: str = Field(nullable=False, max_length=120)
    country_code: str = Field(nullable=False, max_length=2)
    custom_tags_json: str = Field(default="[]", nullable=False, max_length=2000)
    management_mode: str = Field(
        default="owner_managed",
        nullable=False,
        max_length=32,
    )
    created_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    assigned_agency_organization_id: Optional[uuid.UUID] = Field(
        foreign_key="organizations.id",
        default=None,
        nullable=True,
        index=True,
    )
    assigned_agency_user_id: Optional[uuid.UUID] = Field(
        foreign_key="users.id",
        default=None,
        nullable=True,
        index=True,
    )
    assigned_tenant_user_id: Optional[uuid.UUID] = Field(
        foreign_key="users.id",
        default=None,
        nullable=True,
        index=True,
    )
    is_active: bool = Field(default=True, nullable=False)

    created_by_user: "User" = Relationship(
        back_populates="properties_created",
        sa_relationship_kwargs={"foreign_keys": "Property.created_by_user_id"},
    )
    assigned_agency_organization: Optional["Organization"] = Relationship(
        back_populates="properties_assigned"
    )
    assigned_agency_user: Optional["User"] = Relationship(
        back_populates="properties_as_assigned_agent",
        sa_relationship_kwargs={"foreign_keys": "Property.assigned_agency_user_id"},
    )
    assigned_tenant_user: Optional["User"] = Relationship(
        back_populates="properties_as_assigned_tenant",
        sa_relationship_kwargs={"foreign_keys": "Property.assigned_tenant_user_id"},
    )
    listings: List["Listing"] = Relationship(back_populates="property_record")
    tenancies: List["Tenancy"] = Relationship(back_populates="property_record")
