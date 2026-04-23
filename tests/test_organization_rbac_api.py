from __future__ import annotations

from pathlib import Path
import sys
import unittest
import uuid

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"

for path in (API_ROOT, DOMAIN_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.core.db import create_engine_from_url, get_session  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import Organization, OrganizationMembership, User  # noqa: E402
from trustledger_domain import OrganizationMembershipRole, SystemRole  # noqa: E402


class OrganizationRbacApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)

        app = create_app()

        def override_get_session():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        self.app = app
        self.clients: list[TestClient] = []

    def tearDown(self) -> None:
        for client in self.clients:
            client.close()
        self.app.dependency_overrides.clear()

    def new_client(self) -> TestClient:
        client = TestClient(self.app)
        self.clients.append(client)
        return client

    def seed_user(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        system_role: SystemRole = SystemRole.USER,
    ) -> User:
        with Session(self.engine) as session:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                system_role=system_role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def login(self, client: TestClient, *, email: str, password: str) -> None:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_user_can_create_agency_and_owner_membership_is_created(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )
        client = self.new_client()
        self.login(client, email="owner@example.com", password="owner-password-123")

        response = client.post(
            "/api/v1/organizations",
            json={
                "name": "Acme Realty",
                "slug": "Acme Realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        body = response.json()
        self.assertEqual(body["slug"], "acme-realty")
        self.assertEqual(body["current_user_membership_role"], "owner")

        with Session(self.engine) as session:
            memberships = session.exec(select(OrganizationMembership)).all()
            self.assertEqual(len(memberships), 1)
            self.assertEqual(memberships[0].role, OrganizationMembershipRole.OWNER)

    def test_only_org_manager_can_add_members(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )
        agent = self.seed_user(
            email="agent@example.com",
            full_name="Org Agent",
            password="agent-password-123",
        )
        member = self.seed_user(
            email="member@example.com",
            full_name="Org Member",
            password="member-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@example.com", password="owner-password-123")
        create_org = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Acme Realty",
                "slug": "acme-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(create_org.status_code, 201, create_org.text)
        organization_id = create_org.json()["id"]

        add_agent = owner_client.post(
            f"/api/v1/organizations/{organization_id}/memberships",
            json={"user_id": str(agent.id), "role": "agent"},
        )
        self.assertEqual(add_agent.status_code, 201, add_agent.text)

        agent_client = self.new_client()
        self.login(agent_client, email="agent@example.com", password="agent-password-123")
        forbidden_add = agent_client.post(
            f"/api/v1/organizations/{organization_id}/memberships",
            json={"user_id": str(member.id), "role": "member"},
        )
        self.assertEqual(forbidden_add.status_code, 403)

        memberships_response = agent_client.get(f"/api/v1/organizations/{organization_id}/memberships")
        self.assertEqual(memberships_response.status_code, 200)
        self.assertEqual(len(memberships_response.json()), 2)

    def test_manager_can_update_membership_role_and_deactivate_member(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )
        agent = self.seed_user(
            email="agent@example.com",
            full_name="Org Agent",
            password="agent-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@example.com", password="owner-password-123")
        create_org = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Acme Realty",
                "slug": "acme-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(create_org.status_code, 201, create_org.text)
        organization_id = create_org.json()["id"]

        add_agent = owner_client.post(
            f"/api/v1/organizations/{organization_id}/memberships",
            json={"user_id": str(agent.id), "role": "member"},
        )
        self.assertEqual(add_agent.status_code, 201, add_agent.text)
        membership_id = add_agent.json()["id"]

        promote_member = owner_client.patch(
            f"/api/v1/organizations/{organization_id}/memberships/{membership_id}",
            json={"role": "agent"},
        )
        self.assertEqual(promote_member.status_code, 200, promote_member.text)
        self.assertEqual(promote_member.json()["role"], "agent")
        self.assertTrue(promote_member.json()["is_active"])

        deactivate_member = owner_client.patch(
            f"/api/v1/organizations/{organization_id}/memberships/{membership_id}",
            json={"is_active": False},
        )
        self.assertEqual(deactivate_member.status_code, 200, deactivate_member.text)
        self.assertFalse(deactivate_member.json()["is_active"])

        agent_client = self.new_client()
        self.login(agent_client, email="agent@example.com", password="agent-password-123")
        denied_org_access = agent_client.get(f"/api/v1/organizations/{organization_id}")
        self.assertEqual(denied_org_access.status_code, 403)

    def test_owner_can_add_member_by_email(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )
        invitee = self.seed_user(
            email="invitee@example.com",
            full_name="Invited User",
            password="invitee-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@example.com", password="owner-password-123")
        create_org = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Email Invite Realty",
                "slug": "email-invite-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(create_org.status_code, 201, create_org.text)
        organization_id = create_org.json()["id"]

        add_member = owner_client.post(
            f"/api/v1/organizations/{organization_id}/memberships",
            json={"user_email": "invitee@example.com", "role": "member"},
        )
        self.assertEqual(add_member.status_code, 201, add_member.text)
        self.assertEqual(add_member.json()["user_id"], str(invitee.id))
        self.assertEqual(add_member.json()["user_email"], "invitee@example.com")

    def test_last_active_owner_cannot_be_demoted_or_deactivated(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@example.com", password="owner-password-123")
        create_org = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Acme Realty",
                "slug": "acme-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(create_org.status_code, 201, create_org.text)
        organization_id = create_org.json()["id"]

        memberships = owner_client.get(f"/api/v1/organizations/{organization_id}/memberships")
        self.assertEqual(memberships.status_code, 200, memberships.text)
        owner_membership_id = memberships.json()[0]["id"]

        demote_owner = owner_client.patch(
            f"/api/v1/organizations/{organization_id}/memberships/{owner_membership_id}",
            json={"role": "admin"},
        )
        self.assertEqual(demote_owner.status_code, 409)

        deactivate_owner = owner_client.patch(
            f"/api/v1/organizations/{organization_id}/memberships/{owner_membership_id}",
            json={"is_active": False},
        )
        self.assertEqual(deactivate_owner.status_code, 409)

    def test_non_member_cannot_access_organization(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )
        self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@example.com", password="owner-password-123")
        create_org = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Acme Realty",
                "slug": "acme-realty",
                "organization_type": "agency",
            },
        )
        organization_id = create_org.json()["id"]

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        response = outsider_client.get(f"/api/v1/organizations/{organization_id}")
        self.assertEqual(response.status_code, 403)

    def test_user_can_list_only_active_memberships_in_my_organizations(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )
        second_member = self.seed_user(
            email="member@example.com",
            full_name="Second Member",
            password="member-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@example.com", password="owner-password-123")

        first_org = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Acme Realty",
                "slug": "acme-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(first_org.status_code, 201, first_org.text)
        first_org_id = first_org.json()["id"]

        second_org = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Signal Rentals",
                "slug": "signal-rentals",
                "organization_type": "agency",
            },
        )
        self.assertEqual(second_org.status_code, 201, second_org.text)
        second_org_id = second_org.json()["id"]

        added_membership = owner_client.post(
            f"/api/v1/organizations/{second_org_id}/memberships",
            json={"user_id": str(second_member.id), "role": "member"},
        )
        self.assertEqual(added_membership.status_code, 201, added_membership.text)
        second_membership_id = added_membership.json()["id"]

        deactivate_membership = owner_client.patch(
            f"/api/v1/organizations/{second_org_id}/memberships/{second_membership_id}",
            json={"is_active": False},
        )
        self.assertEqual(deactivate_membership.status_code, 200, deactivate_membership.text)

        list_mine = owner_client.get("/api/v1/organizations/mine")
        self.assertEqual(list_mine.status_code, 200, list_mine.text)
        bodies = list_mine.json()

        self.assertEqual(len(bodies), 2)
        self.assertEqual({body["id"] for body in bodies}, {first_org_id, second_org_id})
        self.assertEqual(
            {body["current_user_membership_role"] for body in bodies},
            {"owner"},
        )

        member_client = self.new_client()
        self.login(member_client, email="member@example.com", password="member-password-123")
        member_list_mine = member_client.get("/api/v1/organizations/mine")
        self.assertEqual(member_list_mine.status_code, 200, member_list_mine.text)
        self.assertEqual(member_list_mine.json(), [])

    def test_authenticated_user_can_read_active_agency_directory(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Org Owner",
            password="owner-password-123",
        )
        self.seed_user(
            email="viewer@example.com",
            full_name="Directory Viewer",
            password="viewer-password-123",
        )
        self.seed_user(
            email="admin@example.com",
            full_name="Platform Admin",
            password="admin-password-123",
            system_role=SystemRole.ADMIN,
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@example.com", password="owner-password-123")

        active_agency = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Acme Realty",
                "slug": "acme-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(active_agency.status_code, 201, active_agency.text)

        hidden_agency = owner_client.post(
            "/api/v1/organizations",
            json={
                "name": "Hidden Realty",
                "slug": "hidden-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(hidden_agency.status_code, 201, hidden_agency.text)

        admin_client = self.new_client()
        self.login(admin_client, email="admin@example.com", password="admin-password-123")
        internal_org = admin_client.post(
            "/api/v1/organizations",
            json={
                "name": "Internal Ops",
                "slug": "internal-ops",
                "organization_type": "internal",
            },
        )
        self.assertEqual(internal_org.status_code, 201, internal_org.text)

        with Session(self.engine) as session:
            hidden = session.get(Organization, uuid.UUID(hidden_agency.json()["id"]))
            self.assertIsNotNone(hidden)
            hidden.is_active = False
            session.add(hidden)
            session.commit()

        viewer_client = self.new_client()
        self.login(viewer_client, email="viewer@example.com", password="viewer-password-123")
        directory_response = viewer_client.get("/api/v1/organizations/directory/agencies")
        self.assertEqual(directory_response.status_code, 200, directory_response.text)
        directory = directory_response.json()

        self.assertEqual(len(directory), 1)
        self.assertEqual(directory[0]["name"], "Acme Realty")
        self.assertEqual(directory[0]["organization_type"], "agency")
        self.assertIsNone(directory[0]["current_user_membership_role"])

    def test_internal_surface_requires_reviewer_or_admin_and_only_admin_can_create_internal_org(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        self.seed_user(
            email="admin@example.com",
            full_name="Admin User",
            password="admin-password-123",
            system_role=SystemRole.ADMIN,
        )
        self.seed_user(
            email="user@example.com",
            full_name="Regular User",
            password="user-password-123",
        )

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        reviewer_internal = reviewer_client.get("/api/v1/internal/access")
        self.assertEqual(reviewer_internal.status_code, 200)
        self.assertEqual(reviewer_internal.json()["system_role"], "reviewer")

        regular_client = self.new_client()
        self.login(regular_client, email="user@example.com", password="user-password-123")
        denied_internal = regular_client.get("/api/v1/internal/access")
        self.assertEqual(denied_internal.status_code, 403)

        denied_internal_org = regular_client.post(
            "/api/v1/organizations",
            json={
                "name": "Internal Ops",
                "slug": "internal-ops",
                "organization_type": "internal",
            },
        )
        self.assertEqual(denied_internal_org.status_code, 403)

        admin_client = self.new_client()
        self.login(admin_client, email="admin@example.com", password="admin-password-123")
        internal_org = admin_client.post(
            "/api/v1/organizations",
            json={
                "name": "Internal Ops",
                "slug": "internal-ops",
                "organization_type": "internal",
            },
        )
        self.assertEqual(internal_org.status_code, 201, internal_org.text)
        self.assertEqual(internal_org.json()["organization_type"], "internal")


if __name__ == "__main__":
    unittest.main()
