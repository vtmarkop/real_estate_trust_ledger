import uuid
from typing import TYPE_CHECKING

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import OrganizationMembershipRole

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class OrganizationMembership(TimestampedModel, table=True):
    __tablename__ = "organization_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "organization_id", name="uq_organization_memberships_user_org"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    organization_id: uuid.UUID = Field(foreign_key="organizations.id", nullable=False)
    role: OrganizationMembershipRole = Field(
        default=OrganizationMembershipRole.MEMBER,
        nullable=False,
        max_length=50,
    )
    is_active: bool = Field(default=True, nullable=False)

    user: "User" = Relationship(back_populates="memberships")
    organization: "Organization" = Relationship(back_populates="memberships")

    @property
    def can_manage_members(self) -> bool:
        return self.role.can_manage_members and self.is_active

    @property
    def can_run_trust_checks(self) -> bool:
        return self.role.can_run_trust_checks and self.is_active
