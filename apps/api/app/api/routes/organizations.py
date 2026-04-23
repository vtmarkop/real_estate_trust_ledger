from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import (
    CurrentUserDep,
    OrganizationAccessDep,
    OrganizationAgencyOperatorDep,
    OrganizationManagerDep,
    SessionDep,
)
from app.models import Organization, OrganizationMembership, User
from app.models.common import utcnow
from app.schemas.organization import (
    CommercialOverviewResponse,
    MembershipCreateRequest,
    MembershipResponse,
    MembershipUpdateRequest,
    OrganizationCreateRequest,
    OrganizationResponse,
)
from app.services.commercial_overview import build_commercial_overview
from trustledger_domain import OrganizationMembershipRole, OrganizationType


router = APIRouter(prefix="/organizations", tags=["organizations"])


def normalize_slug(raw_slug: str) -> str:
    return raw_slug.strip().lower().replace(" ", "-")


def build_organization_response(
    organization: Organization,
    current_user_membership_role: OrganizationMembershipRole | None = None,
) -> OrganizationResponse:
    return OrganizationResponse(
        id=organization.id,
        name=organization.name,
        slug=organization.slug,
        organization_type=organization.organization_type,
        is_active=organization.is_active,
        created_at=organization.created_at,
        current_user_membership_role=current_user_membership_role,
    )


def build_membership_response(
    membership: OrganizationMembership,
    user: User,
) -> MembershipResponse:
    return MembershipResponse(
        id=membership.id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        role=membership.role,
        is_active=membership.is_active,
        created_at=membership.created_at,
        updated_at=membership.updated_at,
        user_email=user.email,
        user_full_name=user.full_name,
    )


def assert_owner_safety(
    *,
    membership: OrganizationMembership,
    next_role: OrganizationMembershipRole,
    next_is_active: bool,
    session: SessionDep,
    ) -> None:
    if membership.role != OrganizationMembershipRole.OWNER or not membership.is_active:
        return
    if next_role == OrganizationMembershipRole.OWNER and next_is_active:
        return

    other_active_owners = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == membership.organization_id,
            OrganizationMembership.role == OrganizationMembershipRole.OWNER,
            OrganizationMembership.is_active == True,  # noqa: E712
            OrganizationMembership.id != membership.id,
        )
    ).all()
    if not other_active_owners:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization must retain at least one active owner.",
        )


def resolve_membership_target_user(
    *,
    session: SessionDep,
    payload: MembershipCreateRequest,
) -> User:
    target_user = session.get(User, payload.user_id) if payload.user_id is not None else None
    if payload.user_email is not None:
        email_match = session.exec(
            select(User).where(User.email == payload.user_email.lower().strip())
        ).first()
        if payload.user_id is not None and email_match and email_match.id != payload.user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="user_id and user_email refer to different users.",
            )
        target_user = target_user or email_match

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )
    return target_user


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_organization(
    payload: OrganizationCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> OrganizationResponse:
    if (
        payload.organization_type == OrganizationType.INTERNAL
        and not current_user.system_role.can_manage_platform
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only platform admins can create internal organizations.",
        )

    slug = normalize_slug(payload.slug)
    existing = session.exec(select(Organization).where(Organization.slug == slug)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Organization slug already exists.",
        )

    organization = Organization(
        name=payload.name.strip(),
        slug=slug,
        organization_type=payload.organization_type,
    )
    session.add(organization)
    session.commit()
    session.refresh(organization)

    membership = OrganizationMembership(
        user_id=current_user.id,
        organization_id=organization.id,
        role=OrganizationMembershipRole.OWNER,
    )
    session.add(membership)
    session.commit()

    return build_organization_response(
        organization,
        current_user_membership_role=membership.role,
    )


@router.get("/mine", response_model=list[OrganizationResponse])
def list_my_organizations(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[OrganizationResponse]:
    memberships = session.exec(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.is_active == True,  # noqa: E712
        )
        .order_by(OrganizationMembership.created_at.desc())
    ).all()

    responses: list[OrganizationResponse] = []
    seen_organization_ids: set[UUID] = set()
    for membership in memberships:
        if membership.organization_id in seen_organization_ids:
            continue
        organization = session.get(Organization, membership.organization_id)
        if not organization:
            continue
        responses.append(
            build_organization_response(
                organization,
                current_user_membership_role=membership.role,
            )
        )
        seen_organization_ids.add(membership.organization_id)

    return responses


@router.get("/directory/agencies", response_model=list[OrganizationResponse])
def list_agency_directory(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[OrganizationResponse]:
    organizations = session.exec(
        select(Organization)
        .where(
            Organization.organization_type == OrganizationType.AGENCY,
            Organization.is_active == True,  # noqa: E712
        )
        .order_by(Organization.created_at.desc())
    ).all()

    membership_roles = {
        membership.organization_id: membership.role
        for membership in session.exec(
            select(OrganizationMembership).where(
                OrganizationMembership.user_id == current_user.id,
                OrganizationMembership.is_active == True,  # noqa: E712
            )
        ).all()
    }

    return [
        build_organization_response(
            organization,
            current_user_membership_role=membership_roles.get(organization.id),
        )
        for organization in organizations
    ]


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    access: OrganizationAccessDep,
) -> OrganizationResponse:
    membership_role = access.membership.role if access.membership else None
    return build_organization_response(access.organization, membership_role)


@router.get(
    "/{organization_id}/commercial-overview",
    response_model=CommercialOverviewResponse,
)
def get_organization_commercial_overview(
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> CommercialOverviewResponse:
    return build_commercial_overview(
        session=session,
        organization=access.organization,
    )


@router.get("/{organization_id}/memberships", response_model=list[MembershipResponse])
def list_organization_memberships(
    access: OrganizationAccessDep,
    session: SessionDep,
) -> list[MembershipResponse]:
    memberships = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == access.organization.id
        )
    ).all()

    responses: list[MembershipResponse] = []
    for membership in memberships:
        user = session.get(User, membership.user_id)
        if not user:
            continue
        responses.append(
            build_membership_response(membership, user)
        )
    return responses


@router.post(
    "/{organization_id}/memberships",
    response_model=MembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_membership(
    organization_id: UUID,
    payload: MembershipCreateRequest,
    access: OrganizationManagerDep,
    session: SessionDep,
) -> MembershipResponse:
    target_user = resolve_membership_target_user(session=session, payload=payload)

    existing = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == target_user.id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization.",
        )

    membership = OrganizationMembership(
        user_id=target_user.id,
        organization_id=organization_id,
        role=payload.role,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)

    return build_membership_response(membership, target_user)


@router.patch(
    "/{organization_id}/memberships/{membership_id}",
    response_model=MembershipResponse,
)
def update_organization_membership(
    organization_id: UUID,
    membership_id: UUID,
    payload: MembershipUpdateRequest,
    access: OrganizationManagerDep,
    session: SessionDep,
) -> MembershipResponse:
    if payload.role is None and payload.is_active is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one membership field must be updated.",
        )

    membership = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.id == membership_id,
            OrganizationMembership.organization_id == organization_id,
        )
    ).first()
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization membership not found.",
        )

    next_role = payload.role or membership.role
    next_is_active = membership.is_active if payload.is_active is None else payload.is_active
    assert_owner_safety(
        membership=membership,
        next_role=next_role,
        next_is_active=next_is_active,
        session=session,
    )

    membership.role = next_role
    membership.is_active = next_is_active
    membership.updated_at = utcnow()
    session.add(membership)
    session.commit()
    session.refresh(membership)

    target_user = session.get(User, membership.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target user not found.",
        )
    return build_membership_response(membership, target_user)
