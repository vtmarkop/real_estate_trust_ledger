from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import unittest

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
from app.models import TrustEvent, User  # noqa: E402
from trustledger_domain import AccountWorkspaceRole, SystemRole  # noqa: E402


class TenancyReviewApiTests(unittest.TestCase):
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

    def test_property_records_can_be_created_reused_and_listed(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        create_property = landlord_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Flat 4B",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        property_body = create_property.json()

        landlord_properties = landlord_client.get("/api/v1/properties/mine")
        self.assertEqual(landlord_properties.status_code, 200, landlord_properties.text)
        self.assertEqual(len(landlord_properties.json()), 1)
        self.assertEqual(landlord_properties.json()[0]["id"], property_body["id"])

        create_tenancy = landlord_client.post(
            "/api/v1/tenancies",
            json={
                "property_id": property_body["id"],
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": landlord_properties.json()[0]["created_by_user_id"],
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        self.assertEqual(create_tenancy.json()["property_id"], property_body["id"])
        self.assertEqual(create_tenancy.json()["property_label"], "Flat 4B")

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        tenant_properties = tenant_client.get("/api/v1/properties/mine")
        self.assertEqual(tenant_properties.status_code, 200, tenant_properties.text)
        self.assertEqual(len(tenant_properties.json()), 1)
        self.assertEqual(tenant_properties.json()[0]["id"], property_body["id"])

    def test_property_tags_can_be_created_updated_and_exposed(self) -> None:
        self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        create_property = landlord_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Portfolio Flat",
                "address_line1": "18 Ledger Avenue",
                "city": "Athens",
                "country_code": "GR",
                "custom_tags": ["Priority", "City Center", "priority"],
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        self.assertEqual(create_property.json()["custom_tags"], ["Priority", "City Center"])

        update_property = landlord_client.patch(
            f"/api/v1/properties/{create_property.json()['id']}",
            json={"custom_tags": ["Renovation", "Waterfront"]},
        )
        self.assertEqual(update_property.status_code, 200, update_property.text)
        self.assertEqual(update_property.json()["custom_tags"], ["Renovation", "Waterfront"])

        my_properties = landlord_client.get("/api/v1/properties/mine")
        self.assertEqual(my_properties.status_code, 200, my_properties.text)
        self.assertEqual(my_properties.json()[0]["custom_tags"], ["Renovation", "Waterfront"])

    def test_participant_can_create_tenancy_list_it_and_request_review(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Flat 4B",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        tenancy_body = create_tenancy.json()
        self.assertEqual(tenancy_body["verification_status"], "self_reported")
        self.assertEqual(tenancy_body["tenant_full_name"], "Tenant User")

        tenant_list = tenant_client.get("/api/v1/tenancies/mine")
        self.assertEqual(tenant_list.status_code, 200, tenant_list.text)
        self.assertEqual(len(tenant_list.json()), 1)

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        landlord_list = landlord_client.get("/api/v1/tenancies/mine")
        self.assertEqual(landlord_list.status_code, 200, landlord_list.text)
        self.assertEqual(len(landlord_list.json()), 1)

        review_request = tenant_client.post(
            f"/api/v1/tenancies/{tenancy_body['id']}/request-review"
        )
        self.assertEqual(review_request.status_code, 200, review_request.text)
        self.assertIsNotNone(review_request.json()["review_requested_at"])

        with Session(self.engine) as session:
            events = session.exec(select(TrustEvent)).all()
            self.assertEqual(len(events), 4)
            event_counts = Counter(event.event_type for event in events)
            self.assertEqual(event_counts["tenancy:created"], 2)
            self.assertEqual(event_counts["tenancy:review_requested"], 2)

    def test_participant_can_create_tenancy_with_counterparty_email(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Email Linked Flat",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_email": "landlord@example.com",
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        self.assertEqual(create_tenancy.json()["landlord_full_name"], "Landlord User")

    def test_third_party_cannot_create_tenancy_for_other_users(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        response = outsider_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Flat 4B",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_counterparty_confirmation_clears_review_queue_and_updates_history(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord2@example.com",
            full_name="Landlord Two",
            password="landlord-password-456",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Flat 4B",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        tenancy_id = create_tenancy.json()["id"]

        request_review = tenant_client.post(f"/api/v1/tenancies/{tenancy_id}/request-review")
        self.assertEqual(request_review.status_code, 200, request_review.text)
        self.assertIsNotNone(request_review.json()["review_requested_at"])

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord2@example.com", password="landlord-password-456")
        confirm_tenancy = landlord_client.post(f"/api/v1/tenancies/{tenancy_id}/confirm")
        self.assertEqual(confirm_tenancy.status_code, 200, confirm_tenancy.text)
        self.assertEqual(confirm_tenancy.json()["verification_status"], "counterparty_confirmed")
        self.assertIsNone(confirm_tenancy.json()["review_requested_at"])
        self.assertEqual(confirm_tenancy.json()["counterparty_confirmed_by_user_full_name"], "Landlord Two")

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        queue_response = reviewer_client.get("/api/v1/internal/review-queue/tenancies")
        self.assertEqual(queue_response.status_code, 200, queue_response.text)
        self.assertEqual(queue_response.json(), [])

        tenant_events = tenant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(tenant_events.status_code, 200, tenant_events.text)
        self.assertEqual(tenant_events.json()[0]["event_type"], "tenancy:counterparty_confirmed")

    def test_trust_event_surfaces_include_property_context(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
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

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        create_property = landlord_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Flat 4B",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)

        create_tenancy = landlord_client.post(
            "/api/v1/tenancies",
            json={
                "property_id": create_property.json()["id"],
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        tenancy_id = create_tenancy.json()["id"]

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        confirm_response = tenant_client.post(f"/api/v1/tenancies/{tenancy_id}/confirm")
        self.assertEqual(confirm_response.status_code, 200, confirm_response.text)

        tenant_events = tenant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(tenant_events.status_code, 200, tenant_events.text)
        self.assertEqual(len(tenant_events.json()), 2)
        self.assertEqual(tenant_events.json()[0]["property_label"], "Flat 4B")

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        tenancy_events = reviewer_client.get(f"/api/v1/trust-events/tenancies/{tenancy_id}")
        self.assertEqual(tenancy_events.status_code, 200, tenancy_events.text)
        self.assertEqual(len(tenancy_events.json()), 4)
        self.assertEqual(tenancy_events.json()[0]["property_id"], create_property.json()["id"])

    def test_reviewer_queue_and_profile_reflect_verified_tenancy_history(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
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

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Flat 4B",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        tenancy_id = create_tenancy.json()["id"]

        request_review = tenant_client.post(f"/api/v1/tenancies/{tenancy_id}/request-review")
        self.assertEqual(request_review.status_code, 200, request_review.text)

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        queue_response = reviewer_client.get("/api/v1/internal/review-queue/tenancies")
        self.assertEqual(queue_response.status_code, 200, queue_response.text)
        self.assertEqual(len(queue_response.json()), 1)
        self.assertEqual(queue_response.json()[0]["id"], tenancy_id)

        review_decision = reviewer_client.post(
            f"/api/v1/internal/review-queue/tenancies/{tenancy_id}/decision",
            json={
                "verification_status": "verified",
                "review_notes": "Lease details checked against submitted evidence.",
            },
        )
        self.assertEqual(review_decision.status_code, 200, review_decision.text)
        self.assertEqual(review_decision.json()["verification_status"], "verified")
        self.assertEqual(review_decision.json()["reviewed_by_user_full_name"], "Reviewer User")

        queue_after = reviewer_client.get("/api/v1/internal/review-queue/tenancies")
        self.assertEqual(queue_after.status_code, 200, queue_after.text)
        self.assertEqual(queue_after.json(), [])

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        create_consent = tenant_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 14,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_body = create_consent.json()

        profile_preview = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/profile",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(profile_preview.status_code, 200, profile_preview.text)
        profile = profile_preview.json()
        self.assertEqual(profile["profile_stage"], "reference_flow_foundation")
        self.assertEqual(profile["linked_properties"], 1)
        self.assertEqual(profile["reported_tenancies"], 1)
        self.assertEqual(profile["counterparty_confirmed_tenancies"], 0)
        self.assertEqual(profile["reviewed_tenancies"], 1)
        self.assertEqual(profile["verified_tenancies"], 1)
        self.assertEqual(profile["submitted_evidence_documents"], 0)
        self.assertEqual(profile["accepted_evidence_documents"], 0)
        self.assertEqual(profile["rejected_evidence_documents"], 0)
        self.assertEqual(profile["submitted_history_imports"], 0)
        self.assertEqual(profile["accepted_history_imports"], 0)
        self.assertEqual(profile["rejected_history_imports"], 0)
        self.assertEqual(profile["counterparty_reference_documents"], 0)
        self.assertEqual(profile["accepted_counterparty_reference_documents"], 0)
        self.assertEqual(profile["trust_event_count"], 3)
        self.assertIsNotNone(profile["last_trust_event_at"])

        with Session(self.engine) as session:
            tenant_events = session.exec(
                select(TrustEvent).where(TrustEvent.subject_user_id == tenant.id)
            ).all()
            landlord_events = session.exec(
                select(TrustEvent).where(TrustEvent.subject_user_id == landlord.id)
            ).all()
            self.assertEqual(len(tenant_events), 3)
            self.assertEqual(len(landlord_events), 3)


if __name__ == "__main__":
    unittest.main()
