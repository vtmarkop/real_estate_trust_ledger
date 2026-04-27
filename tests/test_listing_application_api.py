from __future__ import annotations

from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session


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
from app.models import User  # noqa: E402
from trustledger_domain import (  # noqa: E402
    AccountWorkspaceRole,
    OrganizationMembershipRole,
    SystemRole,
)


class ListingApplicationApiTests(unittest.TestCase):
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
        workspace_roles: tuple[AccountWorkspaceRole, ...] | None = None,
    ) -> User:
        with Session(self.engine) as session:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                system_role=system_role,
            )
            if workspace_roles is not None:
                user.set_workspace_roles(workspace_roles)
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

    def create_agency(self, client: TestClient, *, name: str = "Acme Realty") -> dict:
        response = client.post(
            "/api/v1/organizations",
            json={
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "organization_type": "agency",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def add_membership(
        self,
        client: TestClient,
        *,
        organization_id: str,
        user_id: str,
        role: OrganizationMembershipRole,
    ) -> None:
        response = client.post(
            f"/api/v1/organizations/{organization_id}/memberships",
            json={"user_id": user_id, "role": role.value},
        )
        self.assertEqual(response.status_code, 201, response.text)

    def build_verified_tenant_history(
        self,
        *,
        tenant_email: str,
        tenant_password: str,
        tenant_id: str,
        landlord_email: str,
        landlord_password: str,
        landlord_id: str,
        reviewer_email: str,
        reviewer_password: str,
    ) -> None:
        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant_email, password=tenant_password)
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "History Flat",
                "address_line1": "8 Archive Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2025-01-01",
                "lease_end_date": "2025-12-31",
                "monthly_rent_minor": 78000,
                "deposit_minor": 156000,
                "currency_code": "EUR",
                "tenant_user_id": tenant_id,
                "landlord_user_id": landlord_id,
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        tenancy_id = create_tenancy.json()["id"]

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord_email, password=landlord_password)
        confirm_tenancy = landlord_client.post(f"/api/v1/tenancies/{tenancy_id}/confirm")
        self.assertEqual(confirm_tenancy.status_code, 200, confirm_tenancy.text)

        tenant_review_request = tenant_client.post(f"/api/v1/tenancies/{tenancy_id}/request-review")
        self.assertEqual(tenant_review_request.status_code, 200, tenant_review_request.text)

        reviewer_client = self.new_client()
        self.login(reviewer_client, email=reviewer_email, password=reviewer_password)
        review_decision = reviewer_client.post(
            f"/api/v1/internal/review-queue/tenancies/{tenancy_id}/decision",
            json={
                "verification_status": "verified",
                "review_notes": "Tenant history checked for listing eligibility.",
            },
        )
        self.assertEqual(review_decision.status_code, 200, review_decision.text)

    def test_agency_can_publish_listing_and_manage_eligible_application(self) -> None:
        applicant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Applicant",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="History Landlord",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )

        self.build_verified_tenant_history(
            tenant_email="tenant@example.com",
            tenant_password="tenant-password-123",
            tenant_id=str(applicant.id),
            landlord_email="landlord@example.com",
            landlord_password="landlord-password-123",
            landlord_id=str(landlord.id),
            reviewer_email="reviewer@example.com",
            reviewer_password="reviewer-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        create_property = owner_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Agency Flat",
                "address_line1": "22 Market Lane",
                "city": "Athens",
                "country_code": "GR",
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)

        create_listing = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/listings",
            json={
                "property_id": create_property.json()["id"],
                "title": "Central Flat",
                "description": "Near the metro.",
                "monthly_rent_minor": 110000,
                "deposit_minor": 220000,
                "currency_code": "EUR",
                "minimum_tenant_score": 575,
                "minimum_verification_strength": 18,
            },
        )
        self.assertEqual(create_listing.status_code, 201, create_listing.text)
        listing = create_listing.json()
        self.assertEqual(listing["property_label"], "Agency Flat")

        applicant_client = self.new_client()
        self.login(applicant_client, email="tenant@example.com", password="tenant-password-123")
        open_listings = applicant_client.get("/api/v1/listings/open")
        self.assertEqual(open_listings.status_code, 200, open_listings.text)
        self.assertEqual(len(open_listings.json()), 1)

        submit_application = applicant_client.post(
            f"/api/v1/listings/{listing['id']}/applications",
            json={"applicant_note": "Stable employment and clean tenancy history."},
        )
        self.assertEqual(submit_application.status_code, 201, submit_application.text)
        application = submit_application.json()
        self.assertEqual(application["application_status"], "submitted")
        self.assertTrue(application["eligibility_met"])
        self.assertEqual(application["applicant_tenant_score"], 575)
        self.assertEqual(application["applicant_verification_strength"], 18)
        self.assertEqual(application["applicant_score_version"], "v1")
        self.assertIsNotNone(application["applicant_score_calculated_at"])

        my_applications = applicant_client.get("/api/v1/applications/mine")
        self.assertEqual(my_applications.status_code, 200, my_applications.text)
        self.assertEqual(len(my_applications.json()), 1)

        org_applications = owner_client.get(
            f"/api/v1/organizations/{agency['id']}/applications"
        )
        self.assertEqual(org_applications.status_code, 200, org_applications.text)
        self.assertEqual(len(org_applications.json()), 1)
        self.assertEqual(org_applications.json()[0]["applicant_tenant_score"], 575)
        self.assertEqual(org_applications.json()[0]["applicant_verification_strength"], 18)

        dashboard = owner_client.get(
            f"/api/v1/organizations/{agency['id']}/screening-dashboard"
        )
        self.assertEqual(dashboard.status_code, 200, dashboard.text)
        self.assertEqual(dashboard.json()["total_listings"], 1)
        self.assertEqual(dashboard.json()["open_listings"], 1)
        self.assertEqual(dashboard.json()["total_applications"], 1)
        self.assertEqual(dashboard.json()["submitted_applications"], 1)
        self.assertEqual(dashboard.json()["average_applicant_tenant_score"], 575.0)
        self.assertEqual(dashboard.json()["average_applicant_verification_strength"], 18.0)
        self.assertEqual(len(dashboard.json()["recent_applications"]), 1)

        accepted_application = owner_client.patch(
            f"/api/v1/organizations/{agency['id']}/applications/{application['id']}",
            json={
                "application_status": "accepted",
                "status_notes": "Eligibility and screening requirements satisfied.",
            },
        )
        self.assertEqual(accepted_application.status_code, 200, accepted_application.text)
        self.assertEqual(accepted_application.json()["application_status"], "accepted")
        self.assertEqual(
            accepted_application.json()["decided_by_user_full_name"],
            "Agency Owner",
        )

        applicant_trust_events = applicant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(applicant_trust_events.status_code, 200, applicant_trust_events.text)
        event_types = [event["event_type"] for event in applicant_trust_events.json()]
        self.assertIn("application:submitted", event_types)
        self.assertIn("application:status_updated", event_types)
        self.assertEqual(applicant_trust_events.json()[0]["listing_title"], "Central Flat")
        self.assertEqual(applicant_trust_events.json()[0]["property_label"], "Agency Flat")

        owner_trust_events = owner_client.get("/api/v1/trust-events/mine")
        self.assertEqual(owner_trust_events.status_code, 200, owner_trust_events.text)
        self.assertEqual(owner_trust_events.json()[0]["event_type"], "listing:published")

    def test_application_is_blocked_when_listing_requirements_are_not_met(self) -> None:
        self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Applicant",
            password="tenant-password-123",
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        create_property = owner_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Agency Flat",
                "address_line1": "22 Market Lane",
                "city": "Athens",
                "country_code": "GR",
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)

        create_listing = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/listings",
            json={
                "property_id": create_property.json()["id"],
                "title": "Central Flat",
                "description": "Near the metro.",
                "monthly_rent_minor": 110000,
                "deposit_minor": 220000,
                "currency_code": "EUR",
                "minimum_tenant_score": 600,
                "minimum_verification_strength": 20,
            },
        )
        self.assertEqual(create_listing.status_code, 201, create_listing.text)

        applicant_client = self.new_client()
        self.login(applicant_client, email="tenant@example.com", password="tenant-password-123")
        blocked_application = applicant_client.post(
            f"/api/v1/listings/{create_listing.json()['id']}/applications",
            json={"applicant_note": "Please consider me."},
        )
        self.assertEqual(blocked_application.status_code, 409)

    def test_non_operator_cannot_manage_agency_listings_or_applications(self) -> None:
        member = self.seed_user(
            email="member@agency.example",
            full_name="Agency Member",
            password="member-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )
        applicant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Applicant",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="History Landlord",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )

        self.build_verified_tenant_history(
            tenant_email="tenant@example.com",
            tenant_password="tenant-password-123",
            tenant_id=str(applicant.id),
            landlord_email="landlord@example.com",
            landlord_password="landlord-password-123",
            landlord_id=str(landlord.id),
            reviewer_email="reviewer@example.com",
            reviewer_password="reviewer-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)
        self.add_membership(
            owner_client,
            organization_id=agency["id"],
            user_id=str(member.id),
            role=OrganizationMembershipRole.MEMBER,
        )

        create_property = owner_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Agency Flat",
                "address_line1": "22 Market Lane",
                "city": "Athens",
                "country_code": "GR",
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)

        create_listing = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/listings",
            json={
                "property_id": create_property.json()["id"],
                "title": "Central Flat",
                "description": "Near the metro.",
                "monthly_rent_minor": 110000,
                "deposit_minor": 220000,
                "currency_code": "EUR",
                "minimum_tenant_score": 575,
                "minimum_verification_strength": 18,
            },
        )
        self.assertEqual(create_listing.status_code, 201, create_listing.text)

        applicant_client = self.new_client()
        self.login(applicant_client, email="tenant@example.com", password="tenant-password-123")
        submit_application = applicant_client.post(
            f"/api/v1/listings/{create_listing.json()['id']}/applications",
            json={"applicant_note": "Please consider me."},
        )
        self.assertEqual(submit_application.status_code, 201, submit_application.text)

        member_client = self.new_client()
        self.login(member_client, email="member@agency.example", password="member-password-123")
        denied_listing_create = member_client.post(
            f"/api/v1/organizations/{agency['id']}/listings",
            json={
                "property_id": create_property.json()["id"],
                "title": "Second Listing",
                "description": "Blocked for member role.",
                "monthly_rent_minor": 100000,
                "deposit_minor": 200000,
                "currency_code": "EUR",
            },
        )
        self.assertEqual(denied_listing_create.status_code, 403)

        denied_application_view = member_client.get(
            f"/api/v1/organizations/{agency['id']}/applications"
        )
        self.assertEqual(denied_application_view.status_code, 403)


if __name__ == "__main__":
    unittest.main()
