from __future__ import annotations

from enum import Enum


class SystemRole(str, Enum):
    USER = "user"
    REVIEWER = "reviewer"
    ADMIN = "admin"

    @property
    def can_access_admin_surfaces(self) -> bool:
        return self in {SystemRole.REVIEWER, SystemRole.ADMIN}

    @property
    def can_manage_platform(self) -> bool:
        return self is SystemRole.ADMIN


class OrganizationType(str, Enum):
    AGENCY = "agency"
    INTERNAL = "internal"


class OrganizationMembershipRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    AGENT = "agent"
    REVIEWER = "reviewer"
    MEMBER = "member"

    @property
    def can_manage_members(self) -> bool:
        return self in {OrganizationMembershipRole.OWNER, OrganizationMembershipRole.ADMIN}

    @property
    def can_manage_organization(self) -> bool:
        return self in {OrganizationMembershipRole.OWNER, OrganizationMembershipRole.ADMIN}

    @property
    def can_run_trust_checks(self) -> bool:
        return self in {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.AGENT,
        }

    @property
    def can_review_verifications(self) -> bool:
        return self in {
            OrganizationMembershipRole.OWNER,
            OrganizationMembershipRole.ADMIN,
            OrganizationMembershipRole.REVIEWER,
        }


class ConsentScope(str, Enum):
    TRUST_REPORT_READ = "trust_report:read"
    TRUST_CHECK_RUN = "trust_check:run"
