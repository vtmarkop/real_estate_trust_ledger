from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from trustledger_domain import PropertyManagementMode


class PropertyCreateRequest(BaseModel):
    property_label: str = Field(min_length=2, max_length=255)
    address_line1: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=120)
    country_code: str = Field(min_length=2, max_length=2)
    custom_tags: list[str] = Field(default_factory=list)
    management_mode: PropertyManagementMode | None = None
    owner_landlord_user_id: UUID | None = None
    owner_landlord_email: EmailStr | None = None
    assigned_agency_organization_id: UUID | None = None
    assigned_agency_user_id: UUID | None = None
    assigned_agency_user_email: EmailStr | None = None
    assigned_tenant_user_id: UUID | None = None
    assigned_tenant_email: EmailStr | None = None


class PropertyUpdateRequest(BaseModel):
    property_label: str | None = Field(default=None, min_length=2, max_length=255)
    address_line1: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=120)
    country_code: str | None = Field(default=None, min_length=2, max_length=2)
    custom_tags: list[str] | None = None
    management_mode: PropertyManagementMode | None = None
    owner_landlord_user_id: UUID | None = None
    owner_landlord_email: EmailStr | None = None
    assigned_agency_organization_id: UUID | None = None
    assigned_agency_user_id: UUID | None = None
    assigned_agency_user_email: EmailStr | None = None
    assigned_tenant_user_id: UUID | None = None
    assigned_tenant_email: EmailStr | None = None
    clear_agency_assignment: bool = False
    clear_owner_landlord_assignment: bool = False
    clear_tenant_assignment: bool = False
    is_active: bool | None = None


class PropertyResponse(BaseModel):
    id: UUID
    property_label: str
    address_line1: str
    city: str
    country_code: str
    custom_tags: list[str]
    management_mode: PropertyManagementMode
    created_by_user_id: UUID
    created_by_user_full_name: str
    owner_landlord_user_id: UUID | None = None
    owner_landlord_user_full_name: str | None = None
    owner_landlord_user_email: str | None = None
    assigned_agency_organization_id: UUID | None = None
    assigned_agency_organization_name: str | None = None
    assigned_agency_user_id: UUID | None = None
    assigned_agency_user_full_name: str | None = None
    assigned_agency_user_email: str | None = None
    assigned_tenant_user_id: UUID | None = None
    assigned_tenant_user_full_name: str | None = None
    assigned_tenant_user_email: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
