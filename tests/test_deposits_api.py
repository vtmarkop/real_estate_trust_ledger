from __future__ import annotations

from collections import Counter
from pathlib import Path
import uuid
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
from app.models import DepositRecord, StoredArtifact, TrustEvent, User  # noqa: E402
from trustledger_domain import AccountWorkspaceRole, SystemRole  # noqa: E402


class DepositsApiTests(unittest.TestCase):
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

    def create_tenancy(self, *, tenant: User, landlord: User, deposit_minor: int = 196000) -> str:
        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Deposit Flat",
                "address_line1": "7 Return Road",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 98000,
                "deposit_minor": deposit_minor,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        return create_tenancy.json()["id"]

    def seed_artifact(
        self,
        *,
        tenancy_id: str,
        created_by_user_id,
        artifact_purpose: str,
        original_file_name: str,
    ) -> StoredArtifact:
        with Session(self.engine) as session:
            artifact = StoredArtifact(
                tenancy_id=uuid.UUID(tenancy_id) if isinstance(tenancy_id, str) else tenancy_id,
                created_by_user_id=created_by_user_id,
                artifact_purpose=artifact_purpose,
                storage_backend="local_private",
                storage_key="tests/" + original_file_name,
                original_file_name=original_file_name,
                content_type="application/pdf",
                size_bytes=3072,
                sha256_hex="b" * 64,
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            return artifact

    def test_deposit_record_can_be_settled_and_disputed(self) -> None:
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
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        create_record = landlord_client.post(
            f"/api/v1/deposits/tenancies/{tenancy_id}",
            json={
                "move_out_date": "2026-12-31",
                "return_due_date": "2027-01-15",
                "settlement_notes": "Deposit recorded at move-out.",
            },
        )
        self.assertEqual(create_record.status_code, 201, create_record.text)
        deposit_payload = create_record.json()
        self.assertEqual(deposit_payload["deposit_status"], "held")
        self.assertEqual(deposit_payload["held_amount_minor"], 196000)

        settlement = landlord_client.post(
            f"/api/v1/deposits/{deposit_payload['id']}/settlement",
            json={
                "proposed_return_minor": 146000,
                "withheld_amount_minor": 50000,
                "returned_at": "2027-01-10T08:30:00Z",
                "settlement_artifact_name": "deposit-settlement.pdf",
                "settlement_summary": "Cleaning and wall repair deductions documented.",
                "settlement_notes": "EUR 50,000 withheld for documented repainting and cleaning.",
            },
        )
        self.assertEqual(settlement.status_code, 200, settlement.text)
        settlement_payload = settlement.json()
        self.assertEqual(settlement_payload["deposit_status"], "partially_withheld")
        self.assertEqual(settlement_payload["withheld_amount_minor"], 50000)

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        dispute = tenant_client.post(
            f"/api/v1/deposits/{deposit_payload['id']}/dispute",
            json={"dispute_notes": "The repainting deduction is disputed and needs review."},
        )
        self.assertEqual(dispute.status_code, 200, dispute.text)
        self.assertEqual(dispute.json()["deposit_status"], "disputed")
        self.assertEqual(
            dispute.json()["dispute_notes"],
            "The repainting deduction is disputed and needs review.",
        )

        tenant_events = tenant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(tenant_events.status_code, 200, tenant_events.text)
        recent_event_types = [event["event_type"] for event in tenant_events.json()[:2]]
        self.assertIn("deposit:disputed", recent_event_types)
        self.assertIn("deposit:review_requested", recent_event_types)

        with Session(self.engine) as session:
            deposit_records = session.exec(select(DepositRecord)).all()
            landlord_events = session.exec(
                select(TrustEvent).where(TrustEvent.subject_user_id == landlord.id)
            ).all()
            self.assertEqual(len(deposit_records), 1)
            event_counts = Counter(event.event_type for event in landlord_events)
            self.assertEqual(event_counts["deposit:recorded"], 1)
            self.assertEqual(event_counts["deposit:settlement_submitted"], 1)
            self.assertEqual(event_counts["deposit:disputed"], 1)

    def test_deposit_record_is_unique_per_tenancy_and_requires_a_real_deposit(self) -> None:
        tenant = self.seed_user(
            email="tenant2@example.com",
            full_name="Tenant Two",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord2@example.com",
            full_name="Landlord Two",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        zero_deposit_tenancy_id = self.create_tenancy(
            tenant=tenant,
            landlord=landlord,
            deposit_minor=0,
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord2@example.com", password="landlord-password-123")
        zero_deposit_attempt = landlord_client.post(
            f"/api/v1/deposits/tenancies/{zero_deposit_tenancy_id}",
            json={},
        )
        self.assertEqual(zero_deposit_attempt.status_code, 409)

        valid_tenancy_id = self.create_tenancy(
            tenant=tenant,
            landlord=landlord,
            deposit_minor=120000,
        )
        first_record = landlord_client.post(f"/api/v1/deposits/tenancies/{valid_tenancy_id}", json={})
        self.assertEqual(first_record.status_code, 201, first_record.text)

        duplicate_record = landlord_client.post(f"/api/v1/deposits/tenancies/{valid_tenancy_id}", json={})
        self.assertEqual(duplicate_record.status_code, 409)

    def test_deposit_settlement_can_link_uploaded_artifact_metadata(self) -> None:
        tenant = self.seed_user(
            email="tenant3@example.com",
            full_name="Tenant Three",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord3@example.com",
            full_name="Landlord Three",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)
        artifact = self.seed_artifact(
            tenancy_id=tenancy_id,
            created_by_user_id=landlord.id,
            artifact_purpose="deposit_settlement",
            original_file_name="deposit-statement.pdf",
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord3@example.com", password="landlord-password-123")
        create_record = landlord_client.post(f"/api/v1/deposits/tenancies/{tenancy_id}", json={})
        self.assertEqual(create_record.status_code, 201, create_record.text)

        settlement = landlord_client.post(
            f"/api/v1/deposits/{create_record.json()['id']}/settlement",
            json={
                "proposed_return_minor": 196000,
                "withheld_amount_minor": 0,
                "settlement_summary": "Full return supported by uploaded settlement proof.",
                "settlement_stored_artifact_id": str(artifact.id),
            },
        )
        self.assertEqual(settlement.status_code, 200, settlement.text)
        settlement_payload = settlement.json()
        self.assertEqual(settlement_payload["settlement_stored_artifact_id"], str(artifact.id))
        self.assertEqual(settlement_payload["settlement_artifact_name"], "deposit-statement.pdf")
        self.assertEqual(settlement_payload["settlement_artifact_content_type"], "application/pdf")
        self.assertEqual(settlement_payload["settlement_artifact_size_bytes"], 3072)

    def test_deposit_dispute_supports_verdict_and_appeal(self) -> None:
        tenant = self.seed_user(
            email="tenant4@example.com",
            full_name="Tenant Four",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord4@example.com",
            full_name="Landlord Four",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Internal Reviewer",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        create_record = landlord_client.post(
            f"/api/v1/deposits/tenancies/{tenancy_id}",
            json={
                "move_out_date": "2026-12-31",
                "return_due_date": "2027-01-15",
            },
        )
        self.assertEqual(create_record.status_code, 201, create_record.text)
        deposit_id = create_record.json()["id"]

        settlement = landlord_client.post(
            f"/api/v1/deposits/{deposit_id}/settlement",
            json={
                "proposed_return_minor": 126000,
                "withheld_amount_minor": 70000,
                "settlement_artifact_name": "deposit-review-notes.pdf",
                "settlement_summary": "Landlord claims repainting and cleaning deductions.",
            },
        )
        self.assertEqual(settlement.status_code, 200, settlement.text)

        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        dispute = tenant_client.post(
            f"/api/v1/deposits/{deposit_id}/dispute",
            json={"dispute_notes": "Tenant disputes the repainting deduction."},
        )
        self.assertEqual(dispute.status_code, 200, dispute.text)
        self.assertEqual(dispute.json()["deposit_status"], "disputed")

        reviewer_client = self.new_client()
        self.login(reviewer_client, email=reviewer.email, password="reviewer-password-123")
        verdict = reviewer_client.post(
            f"/api/v1/internal/disputes/deposits/{deposit_id}/verdict",
            json={
                "verdict_outcome": "favors_landlord",
                "verdict_summary": "Reviewer accepts most deductions after checking the record.",
                "tenant_score_delta": -12,
                "landlord_score_delta": 6,
            },
        )
        self.assertEqual(verdict.status_code, 200, verdict.text)
        verdict_payload = verdict.json()
        self.assertEqual(verdict_payload["deposit_status"], "verdict_issued")
        self.assertEqual(verdict_payload["verdict_outcome"], "favors_landlord")
        self.assertEqual(verdict_payload["reviewed_by_user_id"], str(reviewer.id))

        appeal = tenant_client.post(
            f"/api/v1/deposits/{deposit_id}/appeal",
            json={"appeal_notes": "Tenant appeals with additional move-out evidence."},
        )
        self.assertEqual(appeal.status_code, 200, appeal.text)
        appeal_payload = appeal.json()
        self.assertEqual(appeal_payload["deposit_status"], "under_review")
        self.assertEqual(appeal_payload["appeal_notes"], "Tenant appeals with additional move-out evidence.")
        self.assertEqual(appeal_payload["appeal_requested_by_user_id"], str(tenant.id))


if __name__ == "__main__":
    unittest.main()
