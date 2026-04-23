from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"
WORKER_ROOT = ROOT / "apps" / "worker"

for path in (API_ROOT, DOMAIN_ROOT, WORKER_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.core.db import create_engine_from_url, get_session  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import (  # noqa: E402
    AutomationTask,
    EvidenceDocument,
    HistoryImport,
    NotificationDelivery,
    Tenancy,
    TrustScoreRecalculationRequest,
    User,
)
from app.models.common import utcnow  # noqa: E402
from trustledger_domain import (  # noqa: E402
    AutomationTaskStatus,
    AutomationTaskType,
    EvidenceDocumentType,
    EvidenceReviewStatus,
    HistoryImportStatus,
    NotificationChannel,
    NotificationDeliveryStatus,
    ScoreCalculationReason,
    ScoreRecalculationStatus,
    SystemRole,
)
from worker.runtime import run_worker_cycle  # noqa: E402


class InternalOperationsApiTests(unittest.TestCase):
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

    def test_reviewer_can_read_operations_overview(self) -> None:
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )
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

        with Session(self.engine) as session:
            summary = run_worker_cycle(session=session, limit=5)

        with Session(self.engine) as session:
            tenancy = Tenancy(
                property_label="Ops Overview Flat",
                address_line1="101 Queue Street",
                city="Athens",
                country_code="GR",
                lease_start_date=date(2026, 1, 1),
                lease_end_date=date(2026, 12, 31),
                monthly_rent_minor=95000,
                deposit_minor=190000,
                currency_code="EUR",
                tenant_user_id=tenant.id,
                landlord_user_id=landlord.id,
                created_by_user_id=tenant.id,
                review_requested_at=utcnow(),
            )
            session.add(tenancy)
            session.flush()

            session.add(
                EvidenceDocument(
                    tenancy_id=tenancy.id,
                    subject_user_id=tenant.id,
                    uploaded_by_user_id=tenant.id,
                    document_type=EvidenceDocumentType.RENT_RECEIPT,
                    review_status=EvidenceReviewStatus.SUBMITTED,
                    artifact_name="Rent receipt",
                    summary="Pending evidence review.",
                    review_requested_at=utcnow(),
                )
            )
            session.add(
                HistoryImport(
                    subject_user_id=tenant.id,
                    created_by_user_id=tenant.id,
                    title="Imported tenancy history",
                    status=HistoryImportStatus.SUBMITTED,
                    submitted_at=utcnow(),
                )
            )
            session.add(
                AutomationTask(
                    task_type=AutomationTaskType.INTERNAL_FOLLOW_UP,
                    status=AutomationTaskStatus.PENDING,
                    title="Pending follow up",
                    requested_by_user_id=reviewer.id,
                    scheduled_for=utcnow(),
                )
            )
            session.add(
                TrustScoreRecalculationRequest(
                    user_id=tenant.id,
                    requested_by_user_id=reviewer.id,
                    calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION.value,
                    status=ScoreRecalculationStatus.PENDING,
                    scheduled_for=utcnow(),
                )
            )
            session.add(
                NotificationDelivery(
                    channel=NotificationChannel.EMAIL,
                    status=NotificationDeliveryStatus.PENDING,
                    template_key="consent_expiry_reminder",
                    recipient_user_id=tenant.id,
                    requested_by_user_id=reviewer.id,
                    recipient_address="tenant@example.com",
                    subject_line="Trust report consent expires soon",
                    body_text="Reminder body",
                    scheduled_for=utcnow(),
                )
            )
            session.commit()

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        overview = reviewer_client.get("/api/v1/internal/operations/overview")
        self.assertEqual(overview.status_code, 200, overview.text)
        payload = overview.json()
        self.assertEqual(payload["pending_tenancy_review_count"], 1)
        self.assertEqual(payload["pending_evidence_review_count"], 1)
        self.assertEqual(payload["pending_history_import_review_count"], 1)
        self.assertEqual(payload["pending_automation_task_count"], 1)
        self.assertEqual(payload["due_automation_task_count"], 1)
        self.assertEqual(payload["pending_notification_count"], 1)
        self.assertEqual(payload["due_notification_count"], 1)
        self.assertEqual(payload["failed_notification_count"], 0)
        self.assertEqual(payload["pending_score_request_count"], 1)
        self.assertEqual(payload["processing_score_request_count"], 0)
        self.assertEqual(payload["due_score_request_count"], 1)
        self.assertEqual(payload["running_worker_run_count"], 0)
        self.assertEqual(payload["failed_worker_run_count"], 0)
        self.assertEqual(payload["environment"], "development")
        self.assertEqual(payload["database_backend"], "sqlite")
        self.assertEqual(payload["artifact_storage_backend"], "local_private")
        self.assertEqual(payload["worker_coordination_backend"], "none")
        self.assertEqual(payload["notification_transport"], "log")
        self.assertEqual(payload["latest_worker_run"]["id"], str(summary.worker_run_id))
        self.assertEqual(payload["latest_worker_run"]["status"], "completed")

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        denied = outsider_client.get("/api/v1/internal/operations/overview")
        self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()
