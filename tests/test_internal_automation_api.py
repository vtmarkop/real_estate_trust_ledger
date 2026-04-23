from __future__ import annotations

from pathlib import Path
import sys
import unittest
import uuid

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
from app.models import (  # noqa: E402
    AutomationTask,
    NotificationDelivery,
    TrustReportConsent,
    TrustScoreRecalculationBatch,
    TrustScoreRecalculationRequest,
    User,
)
from app.models.common import utcnow  # noqa: E402
from trustledger_domain import (  # noqa: E402
    AutomationTaskStatus,
    AutomationTaskType,
    SystemRole,
)


class InternalAutomationApiTests(unittest.TestCase):
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

    def test_consent_creation_queues_expiry_reminder_and_revocation_cancels_it(self) -> None:
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
        subject = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        subject_client = self.new_client()
        self.login(subject_client, email="tenant@example.com", password="tenant-password-123")
        create_consent = subject_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 7,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_payload = create_consent.json()

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        queue = reviewer_client.get(
            "/api/v1/internal/automation/tasks",
            params={"task_type": "consent_expiry_reminder"},
        )
        self.assertEqual(queue.status_code, 200, queue.text)
        self.assertEqual(len(queue.json()), 1)
        reminder_payload = queue.json()[0]
        self.assertEqual(reminder_payload["task_type"], "consent_expiry_reminder")
        self.assertEqual(reminder_payload["status"], "pending")
        self.assertEqual(reminder_payload["subject_user_id"], str(subject.id))
        self.assertEqual(reminder_payload["organization_id"], agency["id"])
        self.assertEqual(reminder_payload["consent_id"], consent_payload["id"])
        self.assertEqual(reminder_payload["subject_user_email"], "tenant@example.com")
        self.assertEqual(reminder_payload["organization_name"], "Acme Realty")
        self.assertTrue(reminder_payload["dedupe_key"].startswith("consent-expiry:"))

        ensure_again = reviewer_client.post(
            f"/api/v1/internal/automation/consents/{consent_payload['id']}/ensure-expiry-reminder"
        )
        self.assertEqual(ensure_again.status_code, 200, ensure_again.text)
        self.assertEqual(ensure_again.json()["id"], reminder_payload["id"])

        revoke = subject_client.post(
            f"/api/v1/consents/trust-report/{consent_payload['id']}/revoke"
        )
        self.assertEqual(revoke.status_code, 200, revoke.text)

        updated_task = reviewer_client.get(
            f"/api/v1/internal/automation/tasks/{reminder_payload['id']}"
        )
        self.assertEqual(updated_task.status_code, 200, updated_task.text)
        self.assertEqual(updated_task.json()["status"], "canceled")
        self.assertIn("revoked", updated_task.json()["result_notes"].lower())

        with Session(self.engine) as session:
            tasks = session.exec(select(AutomationTask)).all()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].status, AutomationTaskStatus.CANCELED)

    def test_reviewer_can_create_and_process_follow_up_task(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        subject = self.seed_user(
            email="subject@example.com",
            full_name="Subject User",
            password="subject-password-123",
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        create_follow_up = reviewer_client.post(
            "/api/v1/internal/automation/tasks/follow-ups",
            json={
                "title": "Review stalled verification trail",
                "details": "Check why the subject did not finish the import bundle.",
                "subject_user_id": str(subject.id),
                "organization_id": agency["id"],
                "scheduled_for": "2026-04-15T09:00:00Z",
            },
        )
        self.assertEqual(create_follow_up.status_code, 201, create_follow_up.text)
        task_payload = create_follow_up.json()
        self.assertEqual(task_payload["task_type"], "internal_follow_up")
        self.assertEqual(task_payload["status"], "pending")
        self.assertEqual(task_payload["attempt_count"], 0)

        pending_queue = reviewer_client.get(
            "/api/v1/internal/automation/tasks",
            params={"task_status": "pending"},
        )
        self.assertEqual(pending_queue.status_code, 200, pending_queue.text)
        self.assertEqual(len(pending_queue.json()), 1)

        mark_processing = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/{task_payload['id']}/process",
            json={
                "status": "processing",
                "result_notes": "Picked up for reviewer follow-up.",
            },
        )
        self.assertEqual(mark_processing.status_code, 200, mark_processing.text)
        self.assertEqual(mark_processing.json()["status"], "processing")
        self.assertEqual(mark_processing.json()["attempt_count"], 1)
        self.assertEqual(mark_processing.json()["processed_by_user_id"], mark_processing.json()["requested_by_user_id"])

        complete_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/{task_payload['id']}/process",
            json={
                "status": "completed",
                "result_notes": "Subject contacted and follow-up closed.",
            },
        )
        self.assertEqual(complete_task.status_code, 200, complete_task.text)
        self.assertEqual(complete_task.json()["status"], "completed")
        self.assertEqual(complete_task.json()["attempt_count"], 1)
        self.assertEqual(
            complete_task.json()["result_notes"],
            "Subject contacted and follow-up closed.",
        )
        self.assertIsNotNone(complete_task.json()["completed_at"])

        with Session(self.engine) as session:
            task = session.exec(select(AutomationTask)).first()
            self.assertIsNotNone(task)
            self.assertEqual(task.task_type, AutomationTaskType.INTERNAL_FOLLOW_UP)
            self.assertEqual(task.status, AutomationTaskStatus.COMPLETED)

    def test_non_reviewer_is_denied_internal_automation_access(self) -> None:
        self.seed_user(
            email="plain@example.com",
            full_name="Plain User",
            password="plain-password-123",
        )

        plain_client = self.new_client()
        self.login(plain_client, email="plain@example.com", password="plain-password-123")

        denied = plain_client.get("/api/v1/internal/automation/tasks")
        self.assertEqual(denied.status_code, 403, denied.text)

    def test_reviewer_can_claim_due_tasks_without_claiming_future_tasks(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        subject = self.seed_user(
            email="subject@example.com",
            full_name="Subject User",
            password="subject-password-123",
        )

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        due_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/score-refresh/users/{subject.id}",
            json={"scheduled_for": "2026-04-10T07:00:00Z"},
        )
        self.assertEqual(due_task.status_code, 201, due_task.text)

        future_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/score-refresh/users/{subject.id}",
            json={"scheduled_for": "2026-04-20T07:00:00Z"},
        )
        self.assertEqual(future_task.status_code, 201, future_task.text)

        claimed = reviewer_client.post(
            "/api/v1/internal/automation/tasks/claim",
            json={
                "task_type": "user_score_recalculation",
                "limit": 5,
                "due_before": "2026-04-11T12:00:00Z",
            },
        )
        self.assertEqual(claimed.status_code, 200, claimed.text)
        claimed_payload = claimed.json()
        self.assertEqual(len(claimed_payload), 1)
        self.assertEqual(claimed_payload[0]["id"], due_task.json()["id"])
        self.assertEqual(claimed_payload[0]["status"], "processing")
        self.assertEqual(claimed_payload[0]["attempt_count"], 1)

        with Session(self.engine) as session:
            due_record = session.get(AutomationTask, uuid.UUID(due_task.json()["id"]))
            future_record = session.get(AutomationTask, uuid.UUID(future_task.json()["id"]))
            self.assertIsNotNone(due_record)
            self.assertIsNotNone(future_record)
            self.assertEqual(due_record.status, AutomationTaskStatus.PROCESSING)
            self.assertEqual(future_record.status, AutomationTaskStatus.PENDING)

    def test_reviewer_can_execute_active_consent_reminder_and_cleanup_expired_one(self) -> None:
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
        self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        subject_client = self.new_client()
        self.login(subject_client, email="tenant@example.com", password="tenant-password-123")
        create_consent = subject_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 1,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_payload = create_consent.json()

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        tasks_before = reviewer_client.get(
            "/api/v1/internal/automation/tasks",
            params={"task_type": "consent_expiry_reminder"},
        )
        self.assertEqual(tasks_before.status_code, 200, tasks_before.text)
        reminder_id = tasks_before.json()[0]["id"]

        execute_active = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/{reminder_id}/execute"
        )
        self.assertEqual(execute_active.status_code, 200, execute_active.text)
        self.assertEqual(execute_active.json()["status"], "completed")
        self.assertIn("queued notification delivery", execute_active.json()["result_notes"].lower())

        with Session(self.engine) as session:
            notifications = session.exec(select(NotificationDelivery)).all()
            self.assertEqual(len(notifications), 1)
            self.assertEqual(notifications[0].recipient_address, "tenant@example.com")

        ensure_again = reviewer_client.post(
            f"/api/v1/internal/automation/consents/{consent_payload['id']}/ensure-expiry-reminder"
        )
        self.assertEqual(ensure_again.status_code, 200, ensure_again.text)
        refreshed_reminder_id = ensure_again.json()["id"]

        with Session(self.engine) as session:
            consent = session.get(TrustReportConsent, uuid.UUID(consent_payload["id"]))
            reminder = session.get(AutomationTask, uuid.UUID(refreshed_reminder_id))
            self.assertIsNotNone(consent)
            self.assertIsNotNone(reminder)
            consent.expires_at = utcnow()
            session.add(consent)
            reminder.status = AutomationTaskStatus.PENDING
            reminder.completed_at = None
            reminder.result_notes = None
            reminder.updated_at = utcnow()
            session.add(reminder)
            session.commit()

        cleanup = reviewer_client.post(
            "/api/v1/internal/automation/cleanup/expired-consent-reminders",
            json={"due_before": "2099-04-11T12:00:00Z", "stale_after_days": 30},
        )
        self.assertEqual(cleanup.status_code, 200, cleanup.text)
        self.assertEqual(cleanup.json()["processed_task_count"], 1)
        self.assertEqual(cleanup.json()["task_ids"], [refreshed_reminder_id])

        cleaned_task = reviewer_client.get(
            f"/api/v1/internal/automation/tasks/{refreshed_reminder_id}"
        )
        self.assertEqual(cleaned_task.status_code, 200, cleaned_task.text)
        self.assertEqual(cleaned_task.json()["status"], "canceled")
        self.assertIn("expired", cleaned_task.json()["result_notes"].lower())

    def test_reviewer_can_cleanup_stale_follow_up_tasks(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        subject = self.seed_user(
            email="subject@example.com",
            full_name="Subject User",
            password="subject-password-123",
        )

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        stale_task = reviewer_client.post(
            "/api/v1/internal/automation/tasks/follow-ups",
            json={
                "title": "Old follow-up",
                "details": "This one should auto-close.",
                "subject_user_id": str(subject.id),
                "scheduled_for": "2026-03-01T09:00:00Z",
            },
        )
        self.assertEqual(stale_task.status_code, 201, stale_task.text)

        fresh_task = reviewer_client.post(
            "/api/v1/internal/automation/tasks/follow-ups",
            json={
                "title": "Fresh follow-up",
                "details": "This one should remain open.",
                "subject_user_id": str(subject.id),
                "scheduled_for": "2026-04-10T09:00:00Z",
            },
        )
        self.assertEqual(fresh_task.status_code, 201, fresh_task.text)

        cleanup = reviewer_client.post(
            "/api/v1/internal/automation/cleanup/stale-follow-ups",
            json={
                "due_before": "2026-04-11T12:00:00Z",
                "stale_after_days": 14,
            },
        )
        self.assertEqual(cleanup.status_code, 200, cleanup.text)
        self.assertEqual(cleanup.json()["processed_task_count"], 1)
        self.assertEqual(cleanup.json()["task_ids"], [stale_task.json()["id"]])

        stale_after_cleanup = reviewer_client.get(
            f"/api/v1/internal/automation/tasks/{stale_task.json()['id']}"
        )
        self.assertEqual(stale_after_cleanup.status_code, 200, stale_after_cleanup.text)
        self.assertEqual(stale_after_cleanup.json()["status"], "canceled")
        self.assertIn("auto-closed", stale_after_cleanup.json()["result_notes"].lower())

        fresh_after_cleanup = reviewer_client.get(
            f"/api/v1/internal/automation/tasks/{fresh_task.json()['id']}"
        )
        self.assertEqual(fresh_after_cleanup.status_code, 200, fresh_after_cleanup.text)
        self.assertEqual(fresh_after_cleanup.json()["status"], "pending")

    def test_reviewer_can_create_follow_up_task_by_subject_email(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        subject = self.seed_user(
            email="subject@example.com",
            full_name="Subject User",
            password="subject-password-123",
        )

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        create_follow_up = reviewer_client.post(
            "/api/v1/internal/automation/tasks/follow-ups",
            json={
                "title": "Email based follow-up",
                "details": "Reach out after a stalled evidence upload.",
                "subject_user_email": "subject@example.com",
            },
        )
        self.assertEqual(create_follow_up.status_code, 201, create_follow_up.text)
        self.assertEqual(create_follow_up.json()["subject_user_id"], str(subject.id))
        self.assertEqual(create_follow_up.json()["subject_user_email"], "subject@example.com")

    def test_reviewer_can_schedule_and_execute_user_score_refresh_task(self) -> None:
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        subject = self.seed_user(
            email="subject@example.com",
            full_name="Subject User",
            password="subject-password-123",
        )

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        create_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/score-refresh/users/{subject.id}",
            json={"scheduled_for": "2026-04-15T07:00:00Z"},
        )
        self.assertEqual(create_task.status_code, 201, create_task.text)
        task_payload = create_task.json()
        self.assertEqual(task_payload["task_type"], "user_score_recalculation")
        self.assertEqual(task_payload["status"], "pending")
        self.assertEqual(task_payload["score_recalculation_request_id"], None)

        execute_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/{task_payload['id']}/execute"
        )
        self.assertEqual(execute_task.status_code, 200, execute_task.text)
        executed_payload = execute_task.json()
        self.assertEqual(executed_payload["status"], "completed")
        self.assertIsNotNone(executed_payload["score_recalculation_request_id"])
        self.assertEqual(executed_payload["score_recalculation_batch_id"], None)
        self.assertEqual(executed_payload["processed_by_user_id"], str(reviewer.id))

        with Session(self.engine) as session:
            task = session.get(AutomationTask, uuid.UUID(task_payload["id"]))
            request = session.get(
                TrustScoreRecalculationRequest,
                uuid.UUID(executed_payload["score_recalculation_request_id"]),
            )
            self.assertIsNotNone(task)
            self.assertIsNotNone(request)
            self.assertEqual(task.status, AutomationTaskStatus.COMPLETED)
            self.assertEqual(request.user_id, subject.id)
            self.assertEqual(request.requested_by_user_id, reviewer.id)
            self.assertEqual(request.calculation_reason, "scheduled_automation_refresh")
            self.assertEqual(request.status.value, "pending")

    def test_reviewer_can_schedule_and_execute_organization_score_batch_task(self) -> None:
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        owner = self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
        )
        member = self.seed_user(
            email="member@agency.example",
            full_name="Agency Member",
            password="member-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client, name="Batch Realty")
        add_member = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/memberships",
            json={"user_id": str(member.id), "role": "member"},
        )
        self.assertEqual(add_member.status_code, 201, add_member.text)

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        create_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/score-refresh/organizations/{agency['id']}",
            json={"scheduled_for": "2026-04-15T08:00:00Z"},
        )
        self.assertEqual(create_task.status_code, 201, create_task.text)
        task_payload = create_task.json()
        self.assertEqual(
            task_payload["task_type"],
            "organization_score_recalculation_batch",
        )

        execute_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/{task_payload['id']}/execute"
        )
        self.assertEqual(execute_task.status_code, 200, execute_task.text)
        executed_payload = execute_task.json()
        self.assertEqual(executed_payload["status"], "completed")
        self.assertIsNotNone(executed_payload["score_recalculation_batch_id"])
        self.assertEqual(executed_payload["score_recalculation_request_id"], None)

        with Session(self.engine) as session:
            task = session.get(AutomationTask, uuid.UUID(task_payload["id"]))
            batch = session.get(
                TrustScoreRecalculationBatch,
                uuid.UUID(executed_payload["score_recalculation_batch_id"]),
            )
            requests = session.exec(select(TrustScoreRecalculationRequest)).all()
            self.assertIsNotNone(task)
            self.assertIsNotNone(batch)
            self.assertEqual(task.status, AutomationTaskStatus.COMPLETED)
            self.assertEqual(batch.organization_id, uuid.UUID(agency["id"]))
            self.assertEqual(batch.requested_by_user_id, reviewer.id)
            self.assertEqual(batch.requested_user_count, 2)
            self.assertEqual(len(requests), 2)


if __name__ == "__main__":
    unittest.main()
