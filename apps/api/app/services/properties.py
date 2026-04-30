from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import Organization, Property, User
from app.schemas.property import PropertyResponse
from trustledger_domain import AccountWorkspaceRole, PropertyManagementMode


def normalize_property_tags(tags: list[str] | None) -> list[str]:
    if not tags:
        return []

    normalized: list[str] = []
    seen: set[str] = set()
    for raw_tag in tags:
        tag = " ".join((raw_tag or "").strip().split())
        if not tag:
            continue
        key = tag.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag[:64])
    return normalized[:20]


def serialize_property_tags(tags: list[str] | None) -> str:
    return json.dumps(normalize_property_tags(tags), ensure_ascii=True)


def parse_property_tags(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return normalize_property_tags([str(item) for item in parsed])


def build_property_response(
    *,
    session: Session,
    property_record: Property,
) -> PropertyResponse:
    created_by_user = session.get(User, property_record.created_by_user_id)
    if not created_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Property creator is unavailable.",
        )
    owner_landlord_user = (
        session.get(User, property_record.owner_landlord_user_id)
        if property_record.owner_landlord_user_id
        else None
    )
    effective_owner_landlord_user = owner_landlord_user
    if (
        effective_owner_landlord_user is None
        and AccountWorkspaceRole.LANDLORD in created_by_user.workspace_roles
    ):
        effective_owner_landlord_user = created_by_user
    assigned_agency_organization = (
        session.get(Organization, property_record.assigned_agency_organization_id)
        if property_record.assigned_agency_organization_id
        else None
    )
    assigned_agency_user = (
        session.get(User, property_record.assigned_agency_user_id)
        if property_record.assigned_agency_user_id
        else None
    )
    assigned_tenant_user = (
        session.get(User, property_record.assigned_tenant_user_id)
        if property_record.assigned_tenant_user_id
        else None
    )
    return PropertyResponse(
        id=property_record.id,
        property_label=property_record.property_label,
        address_line1=property_record.address_line1,
        city=property_record.city,
        country_code=property_record.country_code,
        custom_tags=parse_property_tags(property_record.custom_tags_json),
        management_mode=PropertyManagementMode(property_record.management_mode),
        created_by_user_id=property_record.created_by_user_id,
        created_by_user_full_name=created_by_user.full_name,
        owner_landlord_user_id=(
            effective_owner_landlord_user.id if effective_owner_landlord_user else None
        ),
        owner_landlord_user_full_name=(
            effective_owner_landlord_user.full_name if effective_owner_landlord_user else None
        ),
        owner_landlord_user_email=(
            effective_owner_landlord_user.email if effective_owner_landlord_user else None
        ),
        assigned_agency_organization_id=property_record.assigned_agency_organization_id,
        assigned_agency_organization_name=(
            assigned_agency_organization.name if assigned_agency_organization else None
        ),
        assigned_agency_user_id=property_record.assigned_agency_user_id,
        assigned_agency_user_full_name=(
            assigned_agency_user.full_name if assigned_agency_user else None
        ),
        assigned_agency_user_email=assigned_agency_user.email if assigned_agency_user else None,
        assigned_tenant_user_id=property_record.assigned_tenant_user_id,
        assigned_tenant_user_full_name=(
            assigned_tenant_user.full_name if assigned_tenant_user else None
        ),
        assigned_tenant_user_email=assigned_tenant_user.email if assigned_tenant_user else None,
        is_active=property_record.is_active,
        created_at=property_record.created_at,
        updated_at=property_record.updated_at,
    )
