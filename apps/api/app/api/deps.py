from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlmodel import select

from app.core.config import Settings, get_settings
from app.core.db import SessionDep
from app.core.security import hash_token
from app.models import AuthSession, Organization, OrganizationMembership, Tenancy, User
from app.models.common import utcnow
from trustledger_domain import AccountWorkspaceRole, OrganizationType, SystemRole


def get_runtime_settings() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_runtime_settings)]


def get_current_session(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> AuthSession:
    session_token = request.cookies.get(settings.cookie_name)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )

    session_token_hash = hash_token(session_token)
    auth_session = session.exec(
        select(AuthSession).where(AuthSession.token_hash == session_token_hash)
    ).first()
    if not auth_session or not auth_session.is_active():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is invalid or expired.",
        )

    auth_session.last_seen_at = utcnow()
    auth_session.updated_at = utcnow()
    session.add(auth_session)
    session.commit()
    session.refresh(auth_session)
    return auth_session


CurrentSessionDep = Annotated[AuthSession, Depends(get_current_session)]


def get_current_user(
    auth_session: CurrentSessionDep,
    session: SessionDep,
) -> User:
    user = session.get(User, auth_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is inactive or unavailable.",
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def has_workspace_role(user: User, role: AccountWorkspaceRole) -> bool:
    return role in user.workspace_roles


def require_workspace_role_for_user(
    *,
    user: User,
    role: AccountWorkspaceRole,
    detail: str,
    allow_platform_admin: bool = False,
) -> None:
    if allow_platform_admin and user.system_role.can_manage_platform:
        return
    if has_workspace_role(user, role):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def require_tenancy_workspace_access(
    *,
    tenancy: Tenancy,
    current_user: User,
    detail: str,
    allow_internal_review: bool = False,
) -> None:
    if current_user.system_role.can_manage_platform:
        return
    if allow_internal_review and current_user.system_role.can_access_admin_surfaces:
        return
    if current_user.id == tenancy.tenant_user_id:
        require_workspace_role_for_user(
            user=current_user,
            role=AccountWorkspaceRole.TENANT,
            detail=detail,
        )
        return
    if current_user.id == tenancy.landlord_user_id:
        require_workspace_role_for_user(
            user=current_user,
            role=AccountWorkspaceRole.LANDLORD,
            detail=detail,
        )
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def require_system_roles(*allowed_roles: SystemRole):
    allowed = set(allowed_roles)

    def dependency(current_user: CurrentUserDep) -> User:
        if current_user.system_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resource.",
            )
        return current_user

    return dependency


@dataclass
class OrganizationAccessContext:
    organization: Organization
    current_user: User
    membership: OrganizationMembership | None
    is_platform_admin: bool


def get_organization_access_context(
    organization_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> OrganizationAccessContext:
    organization = session.get(Organization, organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )

    membership = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.is_active == True,  # noqa: E712
        )
    ).first()

    is_platform_admin = current_user.system_role.can_manage_platform
    if not is_platform_admin and membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization.",
        )

    return OrganizationAccessContext(
        organization=organization,
        current_user=current_user,
        membership=membership,
        is_platform_admin=is_platform_admin,
    )


OrganizationAccessDep = Annotated[OrganizationAccessContext, Depends(get_organization_access_context)]


def require_membership_manager(
    context: OrganizationAccessDep,
) -> OrganizationAccessContext:
    if context.is_platform_admin:
        return context
    if context.membership and context.membership.can_manage_members:
        return context
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to manage organization members.",
    )


OrganizationManagerDep = Annotated[OrganizationAccessContext, Depends(require_membership_manager)]


def require_agency_operator_access(
    context: OrganizationAccessDep,
) -> OrganizationAccessContext:
    if not context.organization.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is inactive.",
        )
    if context.organization.organization_type != OrganizationType.AGENCY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This resource is only available within agency organizations.",
        )
    require_workspace_role_for_user(
        user=context.current_user,
        role=AccountWorkspaceRole.AGENCY,
        detail="Your account does not have the agent role.",
    )
    if context.membership and context.membership.can_run_trust_checks:
        return context
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to operate agency resources for this organization.",
    )


OrganizationAgencyOperatorDep = Annotated[
    OrganizationAccessContext,
    Depends(require_agency_operator_access),
]


OrganizationTrustCheckDep = OrganizationAgencyOperatorDep
