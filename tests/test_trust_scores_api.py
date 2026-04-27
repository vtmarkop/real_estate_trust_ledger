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
from app.models import TrustScoreHistory, TrustScoreSnapshot, User  # noqa: E402
from trustledger_domain import AccountWorkspaceRole, SystemRole  # noqa: E402


class TrustScoresApiTests(unittest.TestCase):
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

    def build_scored_tenant_state(
        self,
        *,
        tenant: User,
        landlord: User,
        reviewer_email: str,
        reviewer_password: str,
    ) -> None:
        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        reviewer_client = self.new_client()
        self.login(reviewer_client, email=reviewer_email, password=reviewer_password)

        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Current Flat",
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
        current_tenancy_id = create_tenancy.json()["id"]

        confirm = landlord_client.post(f"/api/v1/tenancies/{current_tenancy_id}/confirm")
        self.assertEqual(confirm.status_code, 200, confirm.text)

        request_review = tenant_client.post(f"/api/v1/tenancies/{current_tenancy_id}/request-review")
        self.assertEqual(request_review.status_code, 200, request_review.text)

        verify_tenancy = reviewer_client.post(
            f"/api/v1/internal/review-queue/tenancies/{current_tenancy_id}/decision",
            json={
                "verification_status": "verified",
                "review_notes": "Verified tenancy signal for score testing.",
            },
        )
        self.assertEqual(verify_tenancy.status_code, 200, verify_tenancy.text)

        create_evidence = tenant_client.post(
            f"/api/v1/tenancies/{current_tenancy_id}/evidence",
            json={
                "subject_user_id": str(tenant.id),
                "document_type": "rent_receipt",
                "artifact_name": "receipt.pdf",
                "summary": "Accepted rent receipt for score testing.",
            },
        )
        self.assertEqual(create_evidence.status_code, 201, create_evidence.text)

        accept_evidence = reviewer_client.post(
            f"/api/v1/internal/review-queue/evidence/{create_evidence.json()['id']}/decision",
            json={
                "review_status": "accepted",
                "review_notes": "Accepted tenant evidence for scoring.",
            },
        )
        self.assertEqual(accept_evidence.status_code, 200, accept_evidence.text)

        create_reference_request = tenant_client.post(
            f"/api/v1/reference-requests/tenancies/{current_tenancy_id}",
            json={
                "subject_user_id": str(tenant.id),
                "requested_from_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_reference_request.status_code, 201, create_reference_request.text)

        fulfill_reference = landlord_client.post(
            f"/api/v1/reference-requests/{create_reference_request.json()['id']}/fulfill",
            json={
                "artifact_name": "reference.pdf",
                "summary": "Counterparty reference for score testing.",
            },
        )
        self.assertEqual(fulfill_reference.status_code, 200, fulfill_reference.text)

        accept_reference_evidence = reviewer_client.post(
            f"/api/v1/internal/review-queue/evidence/{fulfill_reference.json()['fulfilled_evidence_document_id']}/decision",
            json={
                "review_status": "accepted",
                "review_notes": "Accepted counterparty reference for scoring.",
            },
        )
        self.assertEqual(accept_reference_evidence.status_code, 200, accept_reference_evidence.text)

        create_history_import = tenant_client.post(
            "/api/v1/history-imports",
            json={"title": "Past tenancy package"},
        )
        self.assertEqual(create_history_import.status_code, 201, create_history_import.text)
        history_import_id = create_history_import.json()["id"]

        create_import_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "history_import_id": history_import_id,
                "property_label": "Archive Flat",
                "address_line1": "8 Archive Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2025-01-01",
                "lease_end_date": "2025-12-31",
                "monthly_rent_minor": 82000,
                "deposit_minor": 164000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_import_tenancy.status_code, 201, create_import_tenancy.text)

        import_evidence = tenant_client.post(
            f"/api/v1/tenancies/{create_import_tenancy.json()['id']}/evidence",
            json={
                "subject_user_id": str(tenant.id),
                "document_type": "lease_agreement",
                "artifact_name": "archive-lease.pdf",
                "summary": "Supporting evidence for accepted history import.",
            },
        )
        self.assertEqual(import_evidence.status_code, 201, import_evidence.text)

        submit_import = tenant_client.post(f"/api/v1/history-imports/{history_import_id}/submit")
        self.assertEqual(submit_import.status_code, 200, submit_import.text)

        accept_import = reviewer_client.post(
            f"/api/v1/internal/review-queue/history-imports/{history_import_id}/decision",
            json={
                "status": "accepted",
                "review_notes": "Accepted history import for score testing.",
            },
        )
        self.assertEqual(accept_import.status_code, 200, accept_import.text)

    def test_trust_score_endpoint_persists_snapshot_and_stable_history(self) -> None:
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

        self.build_scored_tenant_state(
            tenant=tenant,
            landlord=landlord,
            reviewer_email="reviewer@example.com",
            reviewer_password="reviewer-password-123",
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        score_response = tenant_client.get("/api/v1/trust-scores/mine")
        self.assertEqual(score_response.status_code, 200, score_response.text)
        score = score_response.json()
        self.assertEqual(score["tenant_score"], 610)
        self.assertEqual(score["landlord_score"], 500)
        self.assertEqual(score["verification_strength"], 51)
        self.assertEqual(score["scoring_version"], "v1")
        self.assertEqual(score["inputs"]["tenant_counterparty_confirmed_tenancies"], 1)
        self.assertEqual(score["inputs"]["tenant_verified_tenancies"], 1)
        self.assertEqual(score["inputs"]["accepted_tenant_evidence_documents"], 1)
        self.assertEqual(score["inputs"]["accepted_tenant_counterparty_references"], 1)
        self.assertEqual(score["inputs"]["accepted_history_imports"], 1)

        second_score_response = tenant_client.get("/api/v1/trust-scores/mine")
        self.assertEqual(second_score_response.status_code, 200, second_score_response.text)
        self.assertEqual(second_score_response.json()["tenant_score"], 610)

        history_response = tenant_client.get("/api/v1/trust-scores/mine/history")
        self.assertEqual(history_response.status_code, 200, history_response.text)
        self.assertEqual(len(history_response.json()), 1)
        self.assertEqual(history_response.json()[0]["calculation_reason"], "self_service_refresh")

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
        consent = create_consent.json()
        profile_preview = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/profile",
            json={
                "share_token": consent["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(profile_preview.status_code, 200, profile_preview.text)
        self.assertEqual(profile_preview.json()["tenant_score"], 610)
        self.assertEqual(profile_preview.json()["landlord_score"], 500)
        self.assertEqual(profile_preview.json()["verification_strength"], 51)
        self.assertEqual(profile_preview.json()["scoring_version"], "v1")

        with Session(self.engine) as session:
            snapshots = session.exec(select(TrustScoreSnapshot)).all()
            history_entries = session.exec(select(TrustScoreHistory)).all()
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(len(history_entries), 1)
            self.assertEqual(history_entries[0].calculation_reason, "self_service_refresh")
