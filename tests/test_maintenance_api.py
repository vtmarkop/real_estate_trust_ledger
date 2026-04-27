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
from app.models import MaintenanceTicket, StoredArtifact, TrustEvent, TrustScoreSnapshot, User  # noqa: E402
from trustledger_domain import AccountWorkspaceRole, SystemRole  # noqa: E402


class MaintenanceApiTests(unittest.TestCase):
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

    def create_tenancy(self, *, tenant: User, landlord: User) -> str:
        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Maintenance Flat",
                "address_line1": "5 Repair Lane",
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
        content_type: str = "image/jpeg",
    ) -> StoredArtifact:
        with Session(self.engine) as session:
            artifact = StoredArtifact(
                tenancy_id=uuid.UUID(tenancy_id) if isinstance(tenancy_id, str) else tenancy_id,
                created_by_user_id=created_by_user_id,
                artifact_purpose=artifact_purpose,
                storage_backend="local_private",
                storage_key="tests/" + original_file_name,
                original_file_name=original_file_name,
                content_type=content_type,
                size_bytes=4096,
                sha256_hex="c" * 64,
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            return artifact

    def test_tenant_can_report_and_landlord_can_resolve_maintenance_ticket(self) -> None:
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

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        create_ticket = tenant_client.post(
            f"/api/v1/maintenance-tickets/tenancies/{tenancy_id}",
            json={
                "title": "Leaking kitchen pipe",
                "description": "Water is leaking under the kitchen sink every morning.",
                "priority": "high",
                "reported_artifact_name": "sink-leak-photo.jpg",
            },
        )
        self.assertEqual(create_ticket.status_code, 201, create_ticket.text)
        ticket_payload = create_ticket.json()
        self.assertEqual(ticket_payload["ticket_status"], "open")
        self.assertEqual(ticket_payload["priority"], "high")

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        acknowledge = landlord_client.post(
            f"/api/v1/maintenance-tickets/{ticket_payload['id']}/acknowledge",
            json={"landlord_response_notes": "Plumber visit booked for tomorrow morning."},
        )
        self.assertEqual(acknowledge.status_code, 200, acknowledge.text)
        self.assertEqual(acknowledge.json()["ticket_status"], "acknowledged")

        resolve = landlord_client.post(
            f"/api/v1/maintenance-tickets/{ticket_payload['id']}/resolve",
            json={
                "resolution_summary": "Faulty valve replaced and area dried.",
                "resolution_artifact_name": "plumber-report.pdf",
            },
        )
        self.assertEqual(resolve.status_code, 200, resolve.text)
        self.assertEqual(resolve.json()["ticket_status"], "resolved")
        self.assertEqual(resolve.json()["resolved_by_user_full_name"], "Landlord User")

        tenant_events = tenant_client.get("/api/v1/trust-events/mine")
        self.assertEqual(tenant_events.status_code, 200, tenant_events.text)
        self.assertEqual(tenant_events.json()[0]["event_type"], "maintenance:resolved")
        self.assertEqual(tenant_events.json()[0]["maintenance_ticket_status"], "resolved")
        self.assertEqual(tenant_events.json()[0]["maintenance_ticket_priority"], "high")

    def test_tenant_can_dispute_resolved_maintenance_ticket(self) -> None:
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
        self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant2@example.com", password="tenant-password-123")
        create_ticket = tenant_client.post(
            f"/api/v1/maintenance-tickets/tenancies/{tenancy_id}",
            json={
                "title": "Broken balcony door lock",
                "description": "The balcony door no longer locks properly.",
            },
        )
        self.assertEqual(create_ticket.status_code, 201, create_ticket.text)
        ticket_id = create_ticket.json()["id"]

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord2@example.com", password="landlord-password-123")
        resolve = landlord_client.post(
            f"/api/v1/maintenance-tickets/{ticket_id}/resolve",
            json={"resolution_summary": "Lock tightened and aligned."},
        )
        self.assertEqual(resolve.status_code, 200, resolve.text)

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        outsider_dispute = outsider_client.post(
            f"/api/v1/maintenance-tickets/{ticket_id}/dispute",
            json={"dispute_notes": "Should not be allowed."},
        )
        self.assertEqual(outsider_dispute.status_code, 403)

        dispute = tenant_client.post(
            f"/api/v1/maintenance-tickets/{ticket_id}/dispute",
            json={"dispute_notes": "The door still fails to lock after the visit."},
        )
        self.assertEqual(dispute.status_code, 200, dispute.text)
        self.assertEqual(dispute.json()["ticket_status"], "disputed")
        self.assertEqual(
            dispute.json()["dispute_notes"],
            "The door still fails to lock after the visit.",
        )

        with Session(self.engine) as session:
            tickets = session.exec(select(MaintenanceTicket)).all()
            landlord_events = session.exec(
                select(TrustEvent).where(TrustEvent.subject_user_id == landlord.id)
            ).all()
            self.assertEqual(len(tickets), 1)
            self.assertEqual(tickets[0].ticket_status.value, "disputed")
            event_counts = Counter(event.event_type for event in landlord_events)
            self.assertEqual(event_counts["maintenance:reported"], 1)
            self.assertEqual(event_counts["maintenance:resolved"], 1)
            self.assertEqual(event_counts["maintenance:disputed"], 1)

    def test_maintenance_ticket_can_link_report_and_resolution_artifacts(self) -> None:
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
        reported_artifact = self.seed_artifact(
            tenancy_id=tenancy_id,
            created_by_user_id=tenant.id,
            artifact_purpose="maintenance_report",
            original_file_name="leak-photo.jpg",
        )
        resolution_artifact = self.seed_artifact(
            tenancy_id=tenancy_id,
            created_by_user_id=landlord.id,
            artifact_purpose="maintenance_resolution",
            original_file_name="repair-report.pdf",
            content_type="application/pdf",
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant3@example.com", password="tenant-password-123")
        create_ticket = tenant_client.post(
            f"/api/v1/maintenance-tickets/tenancies/{tenancy_id}",
            json={
                "title": "Leaking bathroom tap",
                "description": "The tap keeps dripping overnight.",
                "reported_stored_artifact_id": str(reported_artifact.id),
            },
        )
        self.assertEqual(create_ticket.status_code, 201, create_ticket.text)
        ticket_payload = create_ticket.json()
        self.assertEqual(ticket_payload["reported_stored_artifact_id"], str(reported_artifact.id))
        self.assertEqual(ticket_payload["reported_artifact_name"], "leak-photo.jpg")
        self.assertEqual(ticket_payload["reported_artifact_content_type"], "image/jpeg")
        self.assertEqual(ticket_payload["reported_artifact_size_bytes"], 4096)

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord3@example.com", password="landlord-password-123")
        resolve = landlord_client.post(
            f"/api/v1/maintenance-tickets/{ticket_payload['id']}/resolve",
            json={
                "resolution_summary": "Tap washer replaced and leak stopped.",
                "resolution_stored_artifact_id": str(resolution_artifact.id),
            },
        )
        self.assertEqual(resolve.status_code, 200, resolve.text)
        resolve_payload = resolve.json()
        self.assertEqual(resolve_payload["resolution_stored_artifact_id"], str(resolution_artifact.id))
        self.assertEqual(resolve_payload["resolution_artifact_name"], "repair-report.pdf")
        self.assertEqual(resolve_payload["resolution_artifact_content_type"], "application/pdf")
        self.assertEqual(resolve_payload["resolution_artifact_size_bytes"], 4096)

    def test_maintenance_dispute_can_receive_reviewer_verdict_and_appeal(self) -> None:
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
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )
        tenancy_id = self.create_tenancy(tenant=tenant, landlord=landlord)

        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        create_ticket = tenant_client.post(
            f"/api/v1/maintenance-tickets/tenancies/{tenancy_id}",
            json={
                "title": "Heating system still failing",
                "description": "The radiators remain cold after the repair visit.",
                "priority": "urgent",
            },
        )
        self.assertEqual(create_ticket.status_code, 201, create_ticket.text)
        ticket_id = create_ticket.json()["id"]

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        resolve = landlord_client.post(
            f"/api/v1/maintenance-tickets/{ticket_id}/resolve",
            json={
                "resolution_summary": "Boiler settings adjusted and the system reset."
            },
        )
        self.assertEqual(resolve.status_code, 200, resolve.text)

        dispute = tenant_client.post(
            f"/api/v1/maintenance-tickets/{ticket_id}/dispute",
            json={
                "dispute_notes": "The heat failed again within a few hours of the visit."
            },
        )
        self.assertEqual(dispute.status_code, 200, dispute.text)
        self.assertEqual(dispute.json()["ticket_status"], "disputed")

        reviewer_client = self.new_client()
        self.login(reviewer_client, email=reviewer.email, password="reviewer-password-123")
        dispute_queue = reviewer_client.get("/api/v1/internal/disputes/maintenance")
        self.assertEqual(dispute_queue.status_code, 200, dispute_queue.text)
        self.assertEqual(len(dispute_queue.json()), 1)

        first_verdict = reviewer_client.post(
            f"/api/v1/internal/disputes/maintenance/{ticket_id}/verdict",
            json={
                "verdict_outcome": "favors_tenant",
                "verdict_summary": "The landlord closed the repair too early and must follow up properly.",
                "tenant_score_delta": 0,
                "landlord_score_delta": -30,
            },
        )
        self.assertEqual(first_verdict.status_code, 200, first_verdict.text)
        self.assertEqual(first_verdict.json()["ticket_status"], "verdict_issued")

        appeal = landlord_client.post(
            f"/api/v1/maintenance-tickets/{ticket_id}/appeal",
            json={
                "appeal_notes": "A second contractor report should be considered before the case is closed."
            },
        )
        self.assertEqual(appeal.status_code, 200, appeal.text)
        self.assertEqual(appeal.json()["ticket_status"], "under_review")

        final_verdict = reviewer_client.post(
            f"/api/v1/internal/disputes/maintenance/{ticket_id}/verdict",
            json={
                "verdict_outcome": "shared_fault",
                "verdict_summary": "The repair response was late, but the final remediation effort was genuine.",
                "tenant_score_delta": 0,
                "landlord_score_delta": -15,
            },
        )
        self.assertEqual(final_verdict.status_code, 200, final_verdict.text)
        self.assertEqual(final_verdict.json()["ticket_status"], "verdict_issued")
        self.assertEqual(final_verdict.json()["verdict_outcome"], "shared_fault")

        with Session(self.engine) as session:
            maintenance_ticket = session.get(MaintenanceTicket, uuid.UUID(ticket_id))
            self.assertIsNotNone(maintenance_ticket)
            self.assertEqual(maintenance_ticket.ticket_status.value, "verdict_issued")
            landlord_snapshot = session.exec(
                select(TrustScoreSnapshot).where(TrustScoreSnapshot.user_id == landlord.id)
            ).first()
            self.assertIsNotNone(landlord_snapshot)
            self.assertEqual(landlord_snapshot.landlord_score, 485)


if __name__ == "__main__":
    unittest.main()
