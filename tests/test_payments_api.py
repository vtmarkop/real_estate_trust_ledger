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
from app.models import PaymentRecord, StoredArtifact, TrustEvent, TrustScoreSnapshot, User  # noqa: E402
from trustledger_domain import SystemRole  # noqa: E402


class PaymentsApiTests(unittest.TestCase):
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

    def create_tenancy(self, *, tenant: User, landlord: User) -> str:
        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Payment Flat",
                "address_line1": "20 Ledger Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 98000,
                "deposit_minor": 196000,
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
                size_bytes=2048,
                sha256_hex="a" * 64,
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            return artifact

    def test_payer_can_submit_payment_with_proof_and_payee_can_confirm(self) -> None:
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
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        create_payment = tenant_client.post(
            f"/api/v1/payments/tenancies/{tenancy_id}",
            json={
                "payer_user_id": str(tenant.id),
                "payee_user_id": str(landlord.id),
                "payment_type": "rent",
                "amount_minor": 98000,
                "currency_code": "EUR",
                "due_date": "2026-02-01",
                "period_start_date": "2026-02-01",
                "period_end_date": "2026-02-28",
                "paid_at": "2026-02-01T09:30:00Z",
                "proof_artifact_name": "rent-receipt-feb.pdf",
                "proof_summary": "Bank transfer receipt for February rent.",
            },
        )
        self.assertEqual(create_payment.status_code, 201, create_payment.text)
        payment_payload = create_payment.json()
        self.assertEqual(payment_payload["payment_status"], "submitted")
        self.assertEqual(payment_payload["proof_status"], "provided")
        self.assertEqual(payment_payload["payer_user_full_name"], "Tenant User")

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        list_payments = landlord_client.get(f"/api/v1/payments/tenancies/{tenancy_id}")
        self.assertEqual(list_payments.status_code, 200, list_payments.text)
        self.assertEqual(len(list_payments.json()), 1)

        confirm_payment = landlord_client.post(
            f"/api/v1/payments/{payment_payload['id']}/decision",
            json={
                "payment_status": "confirmed",
                "counterparty_notes": "Transfer matched the expected rent amount.",
            },
        )
        self.assertEqual(confirm_payment.status_code, 200, confirm_payment.text)
        confirmed_payload = confirm_payment.json()
        self.assertEqual(confirmed_payload["payment_status"], "confirmed")
        self.assertEqual(confirmed_payload["proof_status"], "counterparty_confirmed")
        self.assertEqual(confirmed_payload["counterparty_action_by_user_full_name"], "Landlord User")

        trust_events = tenant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(trust_events.status_code, 200, trust_events.text)
        self.assertEqual(trust_events.json()[0]["event_type"], "payment:confirmed")
        self.assertEqual(trust_events.json()[0]["payment_type"], "rent")
        self.assertEqual(trust_events.json()[0]["payment_status"], "confirmed")

        with Session(self.engine) as session:
            payment_records = session.exec(select(PaymentRecord)).all()
            tenant_events = session.exec(
                select(TrustEvent).where(TrustEvent.subject_user_id == tenant.id)
            ).all()
            self.assertEqual(len(payment_records), 1)
            self.assertEqual(len(tenant_events), 4)
            event_counts = Counter(event.event_type for event in tenant_events)
            self.assertEqual(event_counts["payment:created"], 1)
            self.assertEqual(event_counts["payment:proof_submitted"], 1)
            self.assertEqual(event_counts["payment:confirmed"], 1)

    def test_payee_can_record_pending_payment_and_payer_can_resubmit_after_rejection(self) -> None:
        tenant = self.seed_user(
            email="tenant2@example.com",
            full_name="Tenant Two",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord2@example.com",
            full_name="Landlord Two",
            password="landlord-password-123",
        )
        self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord2@example.com", password="landlord-password-123")
        create_payment = landlord_client.post(
            f"/api/v1/payments/tenancies/{tenancy_id}",
            json={
                "payer_user_id": str(tenant.id),
                "payee_user_id": str(landlord.id),
                "payment_type": "rent",
                "amount_minor": 98000,
                "currency_code": "EUR",
                "due_date": "2026-03-01",
            },
        )
        self.assertEqual(create_payment.status_code, 201, create_payment.text)
        payment_payload = create_payment.json()
        self.assertEqual(payment_payload["payment_status"], "pending")
        self.assertEqual(payment_payload["proof_status"], "none")

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        denied = outsider_client.post(
            f"/api/v1/payments/{payment_payload['id']}/proof",
            json={
                "proof_artifact_name": "bad.pdf",
                "proof_summary": "Should be denied.",
            },
        )
        self.assertEqual(denied.status_code, 403)

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant2@example.com", password="tenant-password-123")
        submit_proof = tenant_client.post(
            f"/api/v1/payments/{payment_payload['id']}/proof",
            json={
                "proof_artifact_name": "rent-proof-mar.pdf",
                "proof_summary": "Initial proof submission for March rent.",
                "paid_at": "2026-03-01T10:00:00Z",
            },
        )
        self.assertEqual(submit_proof.status_code, 200, submit_proof.text)
        self.assertEqual(submit_proof.json()["payment_status"], "submitted")
        self.assertEqual(submit_proof.json()["proof_status"], "provided")

        reject_payment = landlord_client.post(
            f"/api/v1/payments/{payment_payload['id']}/decision",
            json={
                "payment_status": "rejected",
                "counterparty_notes": "Reference number was missing from the transfer.",
            },
        )
        self.assertEqual(reject_payment.status_code, 200, reject_payment.text)
        self.assertEqual(reject_payment.json()["payment_status"], "rejected")
        self.assertEqual(
            reject_payment.json()["counterparty_notes"],
            "Reference number was missing from the transfer.",
        )

        resubmit_proof = tenant_client.post(
            f"/api/v1/payments/{payment_payload['id']}/proof",
            json={
                "proof_artifact_name": "rent-proof-mar-v2.pdf",
                "proof_summary": "Updated proof with the missing transfer reference.",
                "external_reference": "TRX-2026-03-001",
            },
        )
        self.assertEqual(resubmit_proof.status_code, 200, resubmit_proof.text)
        self.assertEqual(resubmit_proof.json()["payment_status"], "submitted")
        self.assertEqual(resubmit_proof.json()["proof_status"], "provided")
        self.assertIsNone(resubmit_proof.json()["counterparty_notes"])

        with Session(self.engine) as session:
            tenant_events = session.exec(
                select(TrustEvent).where(TrustEvent.subject_user_id == tenant.id)
            ).all()
            event_counts = Counter(event.event_type for event in tenant_events)
            self.assertEqual(event_counts["payment:created"], 1)
            self.assertEqual(event_counts["payment:proof_submitted"], 2)
            self.assertEqual(event_counts["payment:rejected"], 1)

    def test_payment_can_link_uploaded_artifact_metadata(self) -> None:
        tenant = self.seed_user(
            email="tenant3@example.com",
            full_name="Tenant Three",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord3@example.com",
            full_name="Landlord Three",
            password="landlord-password-123",
        )
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)
        artifact = self.seed_artifact(
            tenancy_id=tenancy_id,
            created_by_user_id=tenant.id,
            artifact_purpose="payment_proof",
            original_file_name="rent-proof-apr.pdf",
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant3@example.com", password="tenant-password-123")
        create_payment = tenant_client.post(
            f"/api/v1/payments/tenancies/{tenancy_id}",
            json={
                "payer_user_id": str(tenant.id),
                "payee_user_id": str(landlord.id),
                "payment_type": "rent",
                "amount_minor": 98000,
                "currency_code": "EUR",
                "due_date": "2026-04-01",
                "proof_stored_artifact_id": str(artifact.id),
                "proof_summary": "Uploaded bank receipt for April rent.",
            },
        )
        self.assertEqual(create_payment.status_code, 201, create_payment.text)
        payment_payload = create_payment.json()
        self.assertEqual(payment_payload["proof_stored_artifact_id"], str(artifact.id))
        self.assertEqual(payment_payload["proof_artifact_name"], "rent-proof-apr.pdf")
        self.assertEqual(payment_payload["proof_artifact_content_type"], "application/pdf")
        self.assertEqual(payment_payload["proof_artifact_size_bytes"], 2048)

    def test_payment_dispute_can_receive_reviewer_verdict_and_appeal(self) -> None:
        tenant = self.seed_user(
            email="tenant4@example.com",
            full_name="Tenant Four",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord4@example.com",
            full_name="Landlord Four",
            password="landlord-password-123",
        )
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)

        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        create_payment = tenant_client.post(
            f"/api/v1/payments/tenancies/{tenancy_id}",
            json={
                "payer_user_id": str(tenant.id),
                "payee_user_id": str(landlord.id),
                "payment_type": "rent",
                "amount_minor": 98000,
                "currency_code": "EUR",
                "due_date": "2026-05-01",
                "proof_artifact_name": "rent-proof-may.pdf",
                "proof_summary": "Receipt for May rent."
            },
        )
        self.assertEqual(create_payment.status_code, 201, create_payment.text)
        payment_id = create_payment.json()["id"]

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        reject_payment = landlord_client.post(
            f"/api/v1/payments/{payment_id}/decision",
            json={
                "payment_status": "rejected",
                "counterparty_notes": "The transfer destination account did not match."
            },
        )
        self.assertEqual(reject_payment.status_code, 200, reject_payment.text)

        dispute_payment = tenant_client.post(
            f"/api/v1/payments/{payment_id}/dispute",
            json={
                "dispute_notes": "The funds were sent to the agreed account and the bank receipt proves it."
            },
        )
        self.assertEqual(dispute_payment.status_code, 200, dispute_payment.text)
        self.assertEqual(dispute_payment.json()["payment_status"], "disputed")

        reviewer_client = self.new_client()
        self.login(reviewer_client, email=reviewer.email, password="reviewer-password-123")
        dispute_queue = reviewer_client.get("/api/v1/internal/disputes/payments")
        self.assertEqual(dispute_queue.status_code, 200, dispute_queue.text)
        self.assertEqual(len(dispute_queue.json()), 1)

        first_verdict = reviewer_client.post(
            f"/api/v1/internal/disputes/payments/{payment_id}/verdict",
            json={
                "verdict_outcome": "favors_landlord",
                "verdict_summary": "Evidence was incomplete, so the landlord decision stands for now.",
                "tenant_score_delta": -25,
                "landlord_score_delta": 0,
            },
        )
        self.assertEqual(first_verdict.status_code, 200, first_verdict.text)
        self.assertEqual(first_verdict.json()["payment_status"], "verdict_issued")

        appeal = landlord_client.post(
            f"/api/v1/payments/{payment_id}/appeal",
            json={
                "appeal_notes": "Please review the final bank trace and transfer metadata one more time."
            },
        )
        self.assertEqual(appeal.status_code, 200, appeal.text)
        self.assertEqual(appeal.json()["payment_status"], "under_review")

        blocked_counterparty_override = landlord_client.post(
            f"/api/v1/payments/{payment_id}/decision",
            json={
                "payment_status": "confirmed",
                "counterparty_notes": "Counterparty should not be able to bypass reviewer re-review."
            },
        )
        self.assertEqual(blocked_counterparty_override.status_code, 409, blocked_counterparty_override.text)

        final_verdict = reviewer_client.post(
            f"/api/v1/internal/disputes/payments/{payment_id}/verdict",
            json={
                "verdict_outcome": "shared_fault",
                "verdict_summary": "Both parties contributed to the confusion, but the payment itself is treated as settled.",
                "tenant_score_delta": -10,
                "landlord_score_delta": -10,
            },
        )
        self.assertEqual(final_verdict.status_code, 200, final_verdict.text)
        self.assertEqual(final_verdict.json()["payment_status"], "verdict_issued")
        self.assertEqual(final_verdict.json()["verdict_outcome"], "shared_fault")

        with Session(self.engine) as session:
            payment_record = session.get(PaymentRecord, uuid.UUID(payment_id))
            self.assertIsNotNone(payment_record)
            self.assertEqual(payment_record.payment_status.value, "verdict_issued")
            tenant_snapshot = session.exec(
                select(TrustScoreSnapshot).where(TrustScoreSnapshot.user_id == tenant.id)
            ).first()
            landlord_snapshot = session.exec(
                select(TrustScoreSnapshot).where(TrustScoreSnapshot.user_id == landlord.id)
            ).first()
            self.assertIsNotNone(tenant_snapshot)
            self.assertIsNotNone(landlord_snapshot)
            self.assertEqual(tenant_snapshot.tenant_score, 490)
            self.assertEqual(landlord_snapshot.landlord_score, 490)


if __name__ == "__main__":
    unittest.main()
