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
from app.models import HistoryImport, TrustEvent, User  # noqa: E402
from trustledger_domain import AccountWorkspaceRole, SystemRole  # noqa: E402


class HistoryImportApiTests(unittest.TestCase):
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

    def test_user_can_submit_history_import_and_reviewer_can_accept_it(self) -> None:
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
        create_import = tenant_client.post(
            "/api/v1/history-imports",
            json={
                "title": "2024 rental history",
                "summary": "Cold-start import for my previous tenancy year.",
            },
        )
        self.assertEqual(create_import.status_code, 201, create_import.text)
        history_import = create_import.json()
        self.assertEqual(history_import["status"], "draft")

        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "history_import_id": history_import["id"],
                "property_label": "Old Flat",
                "address_line1": "4 Archive Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2024-01-01",
                "lease_end_date": "2024-12-31",
                "monthly_rent_minor": 82000,
                "deposit_minor": 164000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        self.assertEqual(create_tenancy.json()["history_import_id"], history_import["id"])
        tenancy_id = create_tenancy.json()["id"]

        create_evidence = tenant_client.post(
            f"/api/v1/tenancies/{tenancy_id}/evidence",
            json={
                "subject_user_id": str(tenant.id),
                "document_type": "lease_agreement",
                "artifact_name": "lease-2024.pdf",
                "summary": "Signed lease agreement for the imported tenancy.",
            },
        )
        self.assertEqual(create_evidence.status_code, 201, create_evidence.text)

        list_imports = tenant_client.get("/api/v1/history-imports/mine")
        self.assertEqual(list_imports.status_code, 200, list_imports.text)
        self.assertEqual(len(list_imports.json()), 1)
        self.assertEqual(list_imports.json()[0]["tenancy_count"], 1)
        self.assertEqual(list_imports.json()[0]["evidence_document_count"], 1)

        submit_import = tenant_client.post(f"/api/v1/history-imports/{history_import['id']}/submit")
        self.assertEqual(submit_import.status_code, 200, submit_import.text)
        self.assertEqual(submit_import.json()["status"], "submitted")

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        queue = reviewer_client.get("/api/v1/internal/review-queue/history-imports")
        self.assertEqual(queue.status_code, 200, queue.text)
        self.assertEqual(len(queue.json()), 1)
        self.assertEqual(queue.json()[0]["id"], history_import["id"])

        decision = reviewer_client.post(
            f"/api/v1/internal/review-queue/history-imports/{history_import['id']}/decision",
            json={
                "status": "accepted",
                "review_notes": "Imported tenancy package is coherent and sufficiently documented.",
            },
        )
        self.assertEqual(decision.status_code, 200, decision.text)
        self.assertEqual(decision.json()["status"], "accepted")
        self.assertEqual(decision.json()["reviewed_by_user_full_name"], "Reviewer User")

        tenant_events = tenant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(tenant_events.status_code, 200, tenant_events.text)
        self.assertEqual(tenant_events.json()[0]["event_type"], "history_import:accepted")
        self.assertEqual(tenant_events.json()[0]["history_import_id"], history_import["id"])
        self.assertEqual(tenant_events.json()[0]["history_import_title"], "2024 rental history")

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
        profile = profile_preview.json()
        self.assertEqual(profile["profile_stage"], "reference_flow_foundation")
        self.assertEqual(profile["submitted_evidence_documents"], 1)
        self.assertEqual(profile["accepted_evidence_documents"], 0)
        self.assertEqual(profile["submitted_history_imports"], 0)
        self.assertEqual(profile["accepted_history_imports"], 1)
        self.assertEqual(profile["rejected_history_imports"], 0)
        self.assertEqual(profile["counterparty_reference_documents"], 0)
        self.assertEqual(profile["accepted_counterparty_reference_documents"], 0)

        with Session(self.engine) as session:
            imports = session.exec(select(HistoryImport)).all()
            self.assertEqual(len(imports), 1)
            self.assertEqual(imports[0].status.value, "accepted")
            subject_events = session.exec(
                select(TrustEvent).where(TrustEvent.subject_user_id == tenant.id)
            ).all()
            self.assertEqual(len(subject_events), 4)

    def test_history_import_submission_requires_subject_and_nonempty_bundle(self) -> None:
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
        outsider = self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        create_import = tenant_client.post(
            "/api/v1/history-imports",
            json={"title": "Empty import"},
        )
        self.assertEqual(create_import.status_code, 201, create_import.text)
        history_import_id = create_import.json()["id"]

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        outsider_submit = outsider_client.post(f"/api/v1/history-imports/{history_import_id}/submit")
        self.assertEqual(outsider_submit.status_code, 403)

        empty_submit = tenant_client.post(f"/api/v1/history-imports/{history_import_id}/submit")
        self.assertEqual(empty_submit.status_code, 409)

        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "history_import_id": history_import_id,
                "property_label": "Old Flat",
                "address_line1": "4 Archive Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2024-01-01",
                "lease_end_date": "2024-12-31",
                "monthly_rent_minor": 82000,
                "deposit_minor": 164000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)

        no_evidence_submit = tenant_client.post(f"/api/v1/history-imports/{history_import_id}/submit")
        self.assertEqual(no_evidence_submit.status_code, 409)


if __name__ == "__main__":
    unittest.main()
