from __future__ import annotations

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
from app.models import ReferenceRequest, TrustEvent, User  # noqa: E402
from trustledger_domain import SystemRole  # noqa: E402


class ReferenceRequestApiTests(unittest.TestCase):
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

    def test_subject_can_request_counterparty_reference_and_profile_reflects_it(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
        )
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
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

        create_request = tenant_client.post(
            f"/api/v1/reference-requests/tenancies/{tenancy_id}",
            json={
                "subject_user_id": str(tenant.id),
                "requested_from_user_id": str(landlord.id),
                "message": "Please confirm I paid on time and treated the flat well.",
            },
        )
        self.assertEqual(create_request.status_code, 201, create_request.text)
        reference_request = create_request.json()
        self.assertEqual(reference_request["status"], "pending")

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        my_requests = landlord_client.get("/api/v1/reference-requests/mine")
        self.assertEqual(my_requests.status_code, 200, my_requests.text)
        self.assertEqual(len(my_requests.json()), 1)
        self.assertEqual(my_requests.json()[0]["requested_from_user_full_name"], "Landlord User")

        fulfill = landlord_client.post(
            f"/api/v1/reference-requests/{reference_request['id']}/fulfill",
            json={
                "artifact_name": "tenant-reference.pdf",
                "summary": "Tenant paid on time and returned the property in good condition.",
                "issuer_name": "Landlord User",
                "external_reference": "REF-2026-001",
            },
        )
        self.assertEqual(fulfill.status_code, 200, fulfill.text)
        self.assertEqual(fulfill.json()["status"], "fulfilled")
        self.assertIsNotNone(fulfill.json()["fulfilled_evidence_document_id"])

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        evidence_queue = reviewer_client.get("/api/v1/internal/review-queue/evidence")
        self.assertEqual(evidence_queue.status_code, 200, evidence_queue.text)
        self.assertEqual(len(evidence_queue.json()), 1)
        self.assertEqual(evidence_queue.json()[0]["reference_request_id"], reference_request["id"])
        self.assertEqual(
            evidence_queue.json()[0]["reference_requested_from_user_full_name"],
            "Landlord User",
        )

        review_evidence = reviewer_client.post(
            f"/api/v1/internal/review-queue/evidence/{fulfill.json()['fulfilled_evidence_document_id']}/decision",
            json={
                "review_status": "accepted",
                "review_notes": "Counterparty reference is coherent and attributable.",
            },
        )
        self.assertEqual(review_evidence.status_code, 200, review_evidence.text)
        self.assertEqual(review_evidence.json()["review_status"], "accepted")

        tenant_events = tenant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(tenant_events.status_code, 200, tenant_events.text)
        event_types = [event["event_type"] for event in tenant_events.json()]
        self.assertIn("reference_request:created", event_types)
        self.assertIn("reference_request:fulfilled", event_types)
        self.assertIn("evidence:accepted", event_types)

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)
        consent = tenant_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 14,
            },
        )
        self.assertEqual(consent.status_code, 201, consent.text)

        profile_preview = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/profile",
            json={
                "share_token": consent.json()["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(profile_preview.status_code, 200, profile_preview.text)
        profile = profile_preview.json()
        self.assertEqual(profile["profile_stage"], "reference_flow_foundation")
        self.assertEqual(profile["counterparty_reference_documents"], 1)
        self.assertEqual(profile["accepted_counterparty_reference_documents"], 1)

        with Session(self.engine) as session:
            requests = session.exec(select(ReferenceRequest)).all()
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0].status.value, "fulfilled")

    def test_reference_request_requires_subject_control_and_counterparty_fulfillment(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
        )
        outsider = self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
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

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        outsider_create = outsider_client.post(
            f"/api/v1/reference-requests/tenancies/{tenancy_id}",
            json={
                "subject_user_id": str(tenant.id),
                "requested_from_user_id": str(landlord.id),
            },
        )
        self.assertEqual(outsider_create.status_code, 403)

        create_request = tenant_client.post(
            f"/api/v1/reference-requests/tenancies/{tenancy_id}",
            json={
                "subject_user_id": str(tenant.id),
                "requested_from_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_request.status_code, 201, create_request.text)

        duplicate_request = tenant_client.post(
            f"/api/v1/reference-requests/tenancies/{tenancy_id}",
            json={
                "subject_user_id": str(tenant.id),
                "requested_from_user_id": str(landlord.id),
            },
        )
        self.assertEqual(duplicate_request.status_code, 409)

        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        outsider_fulfill = outsider_client.post(
            f"/api/v1/reference-requests/{create_request.json()['id']}/fulfill",
            json={
                "artifact_name": "tenant-reference.pdf",
                "summary": "Unauthorized reference.",
            },
        )
        self.assertEqual(outsider_fulfill.status_code, 403)

        self_fulfill = tenant_client.post(
            f"/api/v1/reference-requests/{create_request.json()['id']}/fulfill",
            json={
                "artifact_name": "tenant-reference.pdf",
                "summary": "Self-fulfillment should not be allowed.",
            },
        )
        self.assertEqual(self_fulfill.status_code, 403)


if __name__ == "__main__":
    unittest.main()
