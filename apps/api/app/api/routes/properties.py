from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from fastapi import APIRouter
from sqlalchemy import or_
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import Organization, OrganizationMembership, Property, Tenancy, User
from app.models.common import utcnow
from app.schemas.property import PropertyCreateRequest, PropertyResponse, PropertyUpdateRequest
from app.services.properties import (
    build_property_response,
    serialize_property_tags,
)
from trustledger_domain import OrganizationType, PropertyManagementMode


router = APIRouter(prefix="/properties", tags=["properties"])


def resolve_target_user(
    *,
    session: SessionDep,
    user_id: UUID | None,
    email: str | None,
    detail_prefix: str,
) -> User:
    user = session.get(User, user_id) if user_id is not None else None
    if email is not None:
        email_match = session.exec(
            select(User).where(User.email == email.lower().strip())
        ).first()
        if user is not None and email_match is not None and email_match.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{detail_prefix} email and user id refer to different users.",
            )
        user = user or email_match
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{detail_prefix} user not found.",
        )
    return user


def resolve_agency_assignment(
    *,
    session: SessionDep,
    property_record: Property,
    payload: PropertyUpdateRequest,
) -> tuple[UUID | None, UUID | None]:
    if getattr(payload, "clear_agency_assignment", False):
        return None, None

    wants_to_update_agency = (
        payload.assigned_agency_organization_id is not None
        or payload.assigned_agency_user_id is not None
        or payload.assigned_agency_user_email is not None
    )
    if not wants_to_update_agency:
        return property_record.assigned_agency_organization_id, property_record.assigned_agency_user_id

    organization_id = payload.assigned_agency_organization_id or property_record.assigned_agency_organization_id
    if organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose an agency before assigning an agency user.",
        )

    organization = session.get(Organization, organization_id)
    if (
        not organization
        or not organization.is_active
        or organization.organization_type != OrganizationType.AGENCY
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agency organization not found.",
        )

    if payload.assigned_agency_user_id is None and payload.assigned_agency_user_email is None:
        next_user_id = (
            property_record.assigned_agency_user_id
            if payload.assigned_agency_organization_id is None
            else None
        )
        return organization.id, next_user_id

    agency_user = resolve_target_user(
        session=session,
        user_id=payload.assigned_agency_user_id,
        email=payload.assigned_agency_user_email,
        detail_prefix="Agency",
    )
    membership = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization.id,
            OrganizationMembership.user_id == agency_user.id,
            OrganizationMembership.is_active == True,  # noqa: E712
        )
    ).first()
    if not membership or not membership.role.can_run_trust_checks:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The selected user is not an active operating member of that agency.",
        )
    return organization.id, agency_user.id


def determine_management_mode(
    *,
    property_record: Property | None,
    payload: PropertyCreateRequest | PropertyUpdateRequest,
) -> PropertyManagementMode:
    if payload.management_mode is not None:
        return payload.management_mode

    if isinstance(payload, PropertyCreateRequest):
        wants_agency_assignment = (
            payload.assigned_agency_organization_id is not None
            or payload.assigned_agency_user_id is not None
            or payload.assigned_agency_user_email is not None
        )
        return (
            PropertyManagementMode.AGENCY_MANAGED
            if wants_agency_assignment
            else PropertyManagementMode.OWNER_MANAGED
        )

    if payload.clear_agency_assignment:
        return PropertyManagementMode.OWNER_MANAGED

    wants_agency_assignment = (
        payload.assigned_agency_organization_id is not None
        or payload.assigned_agency_user_id is not None
        or payload.assigned_agency_user_email is not None
    )
    if wants_agency_assignment:
        return PropertyManagementMode.AGENCY_MANAGED

    if property_record is not None:
        return PropertyManagementMode(property_record.management_mode)

    return PropertyManagementMode.OWNER_MANAGED


def resolve_tenant_assignment(
    *,
    session: SessionDep,
    property_record: Property,
    payload: PropertyUpdateRequest,
) -> UUID | None:
    if getattr(payload, "clear_tenant_assignment", False):
        return None

    if payload.assigned_tenant_user_id is None and payload.assigned_tenant_email is None:
        return property_record.assigned_tenant_user_id

    tenant_user = resolve_target_user(
        session=session,
        user_id=payload.assigned_tenant_user_id,
        email=payload.assigned_tenant_email,
        detail_prefix="Tenant",
    )
    return tenant_user.id


def resolve_property_assignments(
    *,
    session: SessionDep,
    property_record: Property,
    payload: PropertyCreateRequest | PropertyUpdateRequest,
) -> tuple[PropertyManagementMode, UUID | None, UUID | None, UUID | None]:
    management_mode = determine_management_mode(
        property_record=property_record,
        payload=payload,
    )
    if management_mode == PropertyManagementMode.OWNER_MANAGED:
        tenant_user_id = resolve_tenant_assignment(
            session=session,
            property_record=property_record,
            payload=payload,
        )
        return management_mode, None, None, tenant_user_id

    next_agency_organization_id, next_agency_user_id = resolve_agency_assignment(
        session=session,
        property_record=property_record,
        payload=payload,
    )
    if next_agency_organization_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Choose an agency when the property is agency-managed.",
        )
    tenant_user_id = resolve_tenant_assignment(
        session=session,
        property_record=property_record,
        payload=payload,
    )
    return management_mode, next_agency_organization_id, next_agency_user_id, tenant_user_id


@router.post("", response_model=PropertyResponse, status_code=201)
def create_property(
    payload: PropertyCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> PropertyResponse:
    property_record = Property(
        property_label=payload.property_label.strip(),
        address_line1=payload.address_line1.strip(),
        city=payload.city.strip(),
        country_code=payload.country_code.strip().upper(),
        custom_tags_json=serialize_property_tags(payload.custom_tags),
        created_by_user_id=current_user.id,
    )
    (
        management_mode,
        property_record.assigned_agency_organization_id,
        property_record.assigned_agency_user_id,
        property_record.assigned_tenant_user_id,
    ) = resolve_property_assignments(
        session=session,
        property_record=property_record,
        payload=payload,
    )
    property_record.management_mode = management_mode.value
    session.add(property_record)
    session.commit()
    session.refresh(property_record)
    return build_property_response(session=session, property_record=property_record)


@router.patch("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: UUID,
    payload: PropertyUpdateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> PropertyResponse:
    property_record = session.get(Property, property_id)
    if not property_record or not property_record.is_active and payload.is_active is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )

    is_tag_only_update = (
        payload.property_label is None
        and payload.address_line1 is None
        and payload.city is None
        and payload.country_code is None
        and payload.custom_tags is not None
        and payload.assigned_agency_organization_id is None
        and payload.assigned_agency_user_id is None
        and payload.assigned_agency_user_email is None
        and payload.assigned_tenant_user_id is None
        and payload.assigned_tenant_email is None
        and not payload.clear_agency_assignment
        and not payload.clear_tenant_assignment
        and payload.is_active is None
    )
    agency_membership = None
    if property_record.assigned_agency_organization_id is not None:
        agency_membership = session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.organization_id == property_record.assigned_agency_organization_id,
                OrganizationMembership.user_id == current_user.id,
                OrganizationMembership.is_active == True,  # noqa: E712
            )
        ).first()
    can_manage_assigned_agency_property_tags = (
        property_record.assigned_agency_user_id == current_user.id
        or (agency_membership is not None and agency_membership.role.can_run_trust_checks)
    )

    if current_user.system_role.can_manage_platform:
        pass
    elif property_record.created_by_user_id == current_user.id:
        pass
    elif is_tag_only_update and can_manage_assigned_agency_property_tags:
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to update this property record.",
        )

    if (
        payload.property_label is None
        and payload.address_line1 is None
        and payload.city is None
        and payload.country_code is None
        and payload.custom_tags is None
        and payload.management_mode is None
        and payload.assigned_agency_organization_id is None
        and payload.assigned_agency_user_id is None
        and payload.assigned_agency_user_email is None
        and payload.assigned_tenant_user_id is None
        and payload.assigned_tenant_email is None
        and not payload.clear_agency_assignment
        and not payload.clear_tenant_assignment
        and payload.is_active is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one property field must be updated.",
        )

    if payload.property_label is not None:
        property_record.property_label = payload.property_label.strip()
    if payload.address_line1 is not None:
        property_record.address_line1 = payload.address_line1.strip()
    if payload.city is not None:
        property_record.city = payload.city.strip()
    if payload.country_code is not None:
        property_record.country_code = payload.country_code.strip().upper()
    if payload.custom_tags is not None:
        property_record.custom_tags_json = serialize_property_tags(payload.custom_tags)
    (
        next_management_mode,
        next_agency_organization_id,
        next_agency_user_id,
        next_tenant_user_id,
    ) = resolve_property_assignments(
        session=session,
        property_record=property_record,
        payload=payload,
    )
    property_record.management_mode = next_management_mode.value
    property_record.assigned_agency_organization_id = next_agency_organization_id
    property_record.assigned_agency_user_id = next_agency_user_id
    property_record.assigned_tenant_user_id = next_tenant_user_id
    if payload.is_active is not None:
        property_record.is_active = payload.is_active
    property_record.updated_at = utcnow()
    session.add(property_record)
    session.commit()
    session.refresh(property_record)
    return build_property_response(session=session, property_record=property_record)


@router.get("/mine", response_model=list[PropertyResponse])
def list_my_properties(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[PropertyResponse]:
    direct_properties = session.exec(
        select(Property)
        .where(Property.created_by_user_id == current_user.id)
        .order_by(Property.created_at.desc())
    ).all()
    participant_tenancies = session.exec(
        select(Tenancy).where(
            or_(
                Tenancy.tenant_user_id == current_user.id,
                Tenancy.landlord_user_id == current_user.id,
            )
        )
    ).all()
    agency_membership_organization_ids = {
        membership.organization_id
        for membership in session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.user_id == current_user.id,
                OrganizationMembership.is_active == True,  # noqa: E712
            )
        ).all()
    }
    assignment_properties = session.exec(
        select(Property).where(
            or_(
                Property.assigned_tenant_user_id == current_user.id,
                Property.assigned_agency_user_id == current_user.id,
                Property.assigned_agency_organization_id.in_(agency_membership_organization_ids)
                if agency_membership_organization_ids
                else False,
            )
        )
    ).all()

    property_ids = {property_record.id for property_record in direct_properties}
    related_property_ids = {
        tenancy.property_id for tenancy in participant_tenancies if tenancy.property_id is not None
    }
    property_ids.update(related_property_ids)
    property_ids.update(property_record.id for property_record in assignment_properties)

    properties: list[PropertyResponse] = []
    for property_id in property_ids:
        property_record = session.get(Property, property_id)
        if not property_record:
            continue
        properties.append(build_property_response(session=session, property_record=property_record))
    properties.sort(key=lambda item: item.created_at, reverse=True)
    return properties
