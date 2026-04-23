import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import ApplicationStatus

if TYPE_CHECKING:
    from app.models.listing import Listing
    from app.models.user import User


class ListingApplication(TimestampedModel, table=True):
    __tablename__ = "listing_applications"
    __table_args__ = (
        UniqueConstraint("listing_id", "applicant_user_id", name="uq_listing_applications_listing_applicant"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    listing_id: uuid.UUID = Field(foreign_key="listings.id", nullable=False, index=True)
    applicant_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    submitted_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    application_status: ApplicationStatus = Field(
        default=ApplicationStatus.SUBMITTED,
        nullable=False,
        max_length=32,
    )
    applicant_tenant_score: int | None = Field(default=None, nullable=True, ge=0, le=1000)
    applicant_verification_strength: int | None = Field(default=None, nullable=True, ge=0, le=100)
    applicant_score_version: str | None = Field(default=None, nullable=True, max_length=32)
    applicant_score_calculated_at: Optional[datetime] = Field(default=None, nullable=True)
    eligibility_met: bool = Field(default=True, nullable=False)
    eligibility_notes: Optional[str] = Field(default=None, nullable=True, max_length=500)
    applicant_note: Optional[str] = Field(default=None, nullable=True, max_length=1000)
    status_notes: Optional[str] = Field(default=None, nullable=True, max_length=1000)
    decided_by_user_id: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None, nullable=True)
    decided_at: Optional[datetime] = Field(default=None, nullable=True)

    listing: "Listing" = Relationship(back_populates="applications")
    applicant_user: "User" = Relationship(
        back_populates="applications_as_applicant",
        sa_relationship_kwargs={"foreign_keys": "ListingApplication.applicant_user_id"},
    )
    submitted_by_user: "User" = Relationship(
        back_populates="applications_submitted",
        sa_relationship_kwargs={"foreign_keys": "ListingApplication.submitted_by_user_id"},
    )
    decided_by_user: "User" = Relationship(
        back_populates="applications_decided",
        sa_relationship_kwargs={"foreign_keys": "ListingApplication.decided_by_user_id"},
    )
