from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys
import unittest
import uuid

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
from app.models import (  # noqa: E402
    AgencyTrustCheck,
    Listing,
    ListingApplication,
    Organization,
    OrganizationMembership,
    Property,
    TrustReportConsent,
    User,
)
from app.models.common import utcnow  # noqa: E402
from trustledger_domain import (  # noqa: E402
    ApplicationStatus,
    ConsentScope,
    ListingStatus,
    OrganizationMembershipRole,
)


class CommercialOverviewApiTests(unittest.TestCase):
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
    ) -> User:
        with Session(self.engine) as session:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
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

    def test_agency_operator_can_read_commercial_overview(self) -> None:
        owner = self.seed_user(
            email="owner@example.com",
            full_name="Agency Owner",
            password="owner-password-123",
        )
        agent = self.seed_user(
            email="agent@example.com",
            full_name="Agency Agent",
            password="agent-password-123",
        )
        applicant_one = self.seed_user(
            email="applicant1@example.com",
            full_name="Applicant One",
            password="applicant-password-123",
        )
        applicant_two = self.seed_user(
            email="applicant2@example.com",
            full_name="Applicant Two",
            password="applicant-password-123",
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

        with Session(self.engine) as session:
            organization = session.get(Organization, uuid.UUID(organization_id))
            self.assertIsNotNone(organization)

            session.add(
                OrganizationMembership(
                    user_id=agent.id,
                    organization_id=organization.id,
                    role=OrganizationMembershipRole.AGENT,
                )
            )

            property_one = Property(
                property_label="Marble Flat",
                address_line1="101 Marble Street",
                city="Athens",
                country_code="GR",
                created_by_user_id=owner.id,
            )
            property_two = Property(
                property_label="Harbor Loft",
                address_line1="22 Harbor Street",
                city="Athens",
                country_code="GR",
                created_by_user_id=owner.id,
            )
            session.add(property_one)
            session.add(property_two)
            session.flush()

            open_listing_without_applicants = Listing(
                organization_id=organization.id,
                property_id=property_one.id,
                created_by_user_id=owner.id,
                listing_status=ListingStatus.OPEN,
                title="Quiet marble flat",
                monthly_rent_minor=120000,
                deposit_minor=240000,
                currency_code="EUR",
            )
            open_listing_with_pipeline = Listing(
                organization_id=organization.id,
                property_id=property_two.id,
                created_by_user_id=owner.id,
                listing_status=ListingStatus.OPEN,
                title="Harbor loft",
                monthly_rent_minor=135000,
                deposit_minor=270000,
                currency_code="EUR",
            )
            session.add(open_listing_without_applicants)
            session.add(open_listing_with_pipeline)
            session.flush()

            created_at = utcnow() - timedelta(days=4)
            session.add(
                ListingApplication(
                    listing_id=open_listing_with_pipeline.id,
                    applicant_user_id=applicant_one.id,
                    submitted_by_user_id=applicant_one.id,
                    application_status=ApplicationStatus.ACCEPTED,
                    applicant_tenant_score=710,
                    applicant_verification_strength=78,
                    applicant_score_version="v1",
                    created_at=created_at,
                    updated_at=created_at,
                    decided_by_user_id=owner.id,
                    decided_at=created_at + timedelta(hours=24),
                )
            )
            session.add(
                ListingApplication(
                    listing_id=open_listing_with_pipeline.id,
                    applicant_user_id=applicant_two.id,
                    submitted_by_user_id=applicant_two.id,
                    application_status=ApplicationStatus.SUBMITTED,
                    applicant_tenant_score=650,
                    applicant_verification_strength=61,
                    applicant_score_version="v1",
                )
            )

            consent = TrustReportConsent(
                subject_user_id=applicant_one.id,
                granted_by_user_id=applicant_one.id,
                grantee_organization_id=organization.id,
                scope=ConsentScope.TRUST_REPORT_READ,
                share_token_hash="a" * 64,
                access_code_hash="b" * 64,
                expires_at=utcnow() + timedelta(days=30),
            )
            session.add(consent)
            session.flush()
            session.add(
                AgencyTrustCheck(
                    organization_id=organization.id,
                    consent_id=consent.id,
                    requested_by_user_id=owner.id,
                    subject_user_id=applicant_one.id,
                )
            )
            session.commit()

        response = owner_client.get(f"/api/v1/organizations/{organization_id}/commercial-overview")
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["organization_name"], "Acme Realty")
        self.assertEqual(payload["active_member_count"], 2)
        self.assertEqual(payload["tracked_property_count"], 2)
        self.assertEqual(payload["total_listings"], 2)
        self.assertEqual(payload["open_listing_count"], 2)
        self.assertEqual(payload["listings_without_applicants_count"], 1)
        self.assertEqual(payload["total_applications"], 2)
        self.assertEqual(payload["applications_last_30_days"], 2)
        self.assertEqual(payload["total_trust_checks"], 1)
        self.assertEqual(payload["trust_checks_last_30_days"], 1)
        self.assertEqual(payload["acceptance_rate_percent"], 50.0)
        self.assertEqual(payload["average_time_to_decision_hours"], 24.0)

    def test_outsider_cannot_read_agency_commercial_overview(self) -> None:
        self.seed_user(
            email="owner@example.com",
            full_name="Agency Owner",
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
        self.assertEqual(create_org.status_code, 201, create_org.text)
        organization_id = create_org.json()["id"]

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        denied = outsider_client.get(f"/api/v1/organizations/{organization_id}/commercial-overview")
        self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()
