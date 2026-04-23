from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import TenancyStatus, VerificationStatus


class TenancyCreateRequest(BaseModel):
    history_import_id: UUID | None = None
    property_id: UUID | None = None
    property_label: str | None = Field(default=None, min_length=2, max_length=255)
    address_line1: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    lease_start_date: date
    lease_end_date: date | None = None
    monthly_rent_minor: int = Field(ge=0)
    deposit_minor: int = Field(default=0, ge=0)
    currency_code: str = Field(default="EUR", min_length=3, max_length=3)
    tenant_user_id: UUID | None = None
    tenant_email: str | None = Field(default=None, min_length=3, max_length=320)
    landlord_user_id: UUID | None = None
    landlord_email: str | None = Field(default=None, min_length=3, max_length=320)
    tenancy_status: TenancyStatus = TenancyStatus.ACTIVE


class TenancyReviewDecisionRequest(BaseModel):
    verification_status: VerificationStatus
    review_notes: str | None = Field(default=None, max_length=1000)


class TenancyResponse(BaseModel):
    id: UUID
    history_import_id: UUID | None = None
    property_id: UUID | None = None
    property_label: str
    address_line1: str
    city: str
    country_code: str
    tenancy_status: TenancyStatus
    verification_status: VerificationStatus
    lease_start_date: date
    lease_end_date: date | None = None
    monthly_rent_minor: int
    deposit_minor: int
    currency_code: str
    tenant_user_id: UUID
    tenant_full_name: str
    landlord_user_id: UUID
    landlord_full_name: str
    created_by_user_id: UUID
    created_by_user_full_name: str
    counterparty_confirmed_at: datetime | None = None
    counterparty_confirmed_by_user_id: UUID | None = None
    counterparty_confirmed_by_user_full_name: str | None = None
    review_requested_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by_user_id: UUID | None = None
    reviewed_by_user_full_name: str | None = None
    review_notes: str | None = None
    created_at: datetime
    updated_at: datetime
