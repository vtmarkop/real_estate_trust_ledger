from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from trustledger_domain import OrganizationMembershipRole, OrganizationType


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=120)
    organization_type: OrganizationType = OrganizationType.AGENCY


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    organization_type: OrganizationType
    is_active: bool
    created_at: datetime
    current_user_membership_role: OrganizationMembershipRole | None = None


class AgencyOperatorDirectoryResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    role: OrganizationMembershipRole


class CommercialOverviewResponse(BaseModel):
    organization_id: UUID
    organization_name: str
    active_member_count: int
    tracked_property_count: int
    total_listings: int
    open_listing_count: int
    listings_without_applicants_count: int
    total_applications: int
    applications_last_30_days: int
    total_trust_checks: int
    trust_checks_last_30_days: int
    acceptance_rate_percent: float | None = None
    average_time_to_decision_hours: float | None = None
    generated_at: datetime


class MembershipCreateRequest(BaseModel):
    user_id: UUID | None = None
    user_email: EmailStr | None = None
    role: OrganizationMembershipRole = OrganizationMembershipRole.MEMBER

    @model_validator(mode="after")
    def validate_target_user(self) -> "MembershipCreateRequest":
        if self.user_id is None and self.user_email is None:
            raise ValueError("Either user_id or user_email must be provided.")
        return self


class MembershipUpdateRequest(BaseModel):
    role: OrganizationMembershipRole | None = None
    is_active: bool | None = None


class MembershipResponse(BaseModel):
    id: UUID
    user_id: UUID
    organization_id: UUID
    role: OrganizationMembershipRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    user_email: str
    user_full_name: str
