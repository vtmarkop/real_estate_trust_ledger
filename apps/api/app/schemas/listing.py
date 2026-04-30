from __future__ import annotations

from datetime import date
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import ApplicationStatus, ListingStatus, TenancyStatus


class ListingCreateRequest(BaseModel):
    property_id: UUID
    title: str = Field(min_length=2, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    monthly_rent_minor: int = Field(ge=0)
    deposit_minor: int = Field(default=0, ge=0)
    currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    minimum_tenant_score: int = Field(default=0, ge=0, le=1000)
    minimum_verification_strength: int = Field(default=0, ge=0, le=100)


class ListingUpdateRequest(BaseModel):
    listing_status: ListingStatus | None = None
    description: str | None = Field(default=None, max_length=1000)
    minimum_tenant_score: int | None = Field(default=None, ge=0, le=1000)
    minimum_verification_strength: int | None = Field(default=None, ge=0, le=100)


class ListingResponse(BaseModel):
    id: UUID
    organization_id: UUID | None = None
    organization_name: str | None = None
    owner_landlord_user_id: UUID | None = None
    owner_landlord_full_name: str | None = None
    listing_source: str
    manager_name: str
    property_id: UUID
    property_label: str
    address_line1: str
    city: str
    country_code: str
    created_by_user_id: UUID
    created_by_user_full_name: str
    listing_status: ListingStatus
    title: str
    description: str | None = None
    monthly_rent_minor: int
    deposit_minor: int
    currency_code: str
    minimum_tenant_score: int
    minimum_verification_strength: int
    created_at: datetime
    updated_at: datetime


class ApplicationCreateRequest(BaseModel):
    applicant_note: str | None = Field(default=None, max_length=1000)


class ApplicationUpdateRequest(BaseModel):
    application_status: ApplicationStatus
    status_notes: str | None = Field(default=None, max_length=1000)


class ApplicationTenancyCreateRequest(BaseModel):
    lease_start_date: date
    lease_end_date: date | None = None
    tenancy_status: TenancyStatus = TenancyStatus.ACTIVE


class ListingApplicationResponse(BaseModel):
    id: UUID
    listing_id: UUID
    listing_title: str
    listing_status: ListingStatus
    organization_id: UUID | None = None
    organization_name: str | None = None
    owner_landlord_user_id: UUID | None = None
    owner_landlord_full_name: str | None = None
    listing_source: str
    manager_name: str
    applicant_user_id: UUID
    applicant_full_name: str
    applicant_tenant_score: int | None = None
    applicant_verification_strength: int | None = None
    applicant_score_version: str | None = None
    applicant_score_calculated_at: datetime | None = None
    submitted_by_user_id: UUID
    submitted_by_user_full_name: str
    application_status: ApplicationStatus
    eligibility_met: bool
    eligibility_notes: str | None = None
    applicant_note: str | None = None
    status_notes: str | None = None
    decided_by_user_id: UUID | None = None
    decided_by_user_full_name: str | None = None
    decided_at: datetime | None = None
    tenancy_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class AgencyScreeningDashboardResponse(BaseModel):
    organization_id: UUID
    organization_name: str
    total_listings: int
    open_listings: int
    total_applications: int
    submitted_applications: int
    under_review_applications: int
    accepted_applications: int
    rejected_applications: int
    withdrawn_applications: int
    average_applicant_tenant_score: float | None = None
    average_applicant_verification_strength: float | None = None
    recent_applications: list[ListingApplicationResponse]
