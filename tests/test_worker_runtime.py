from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from sqlmodel import SQLModel, Session, select


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"
WORKER_ROOT = ROOT / "apps" / "worker"

for path in (API_ROOT, DOMAIN_ROOT, WORKER_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.core.db import create_engine_from_url  # noqa: E402
from app.core.security import hash_password, hash_token  # noqa: E402
from app.models import (  # noqa: E402
    AuditLog,
    AutomationTask,
    NotificationDelivery,
    Organization,
    TrustReportConsent,
    WorkerRun,
    TrustScoreRecalculationRequest,
    TrustScoreSnapshot,
    User,
)
from app.models.common import utcnow  # noqa: E402
from app.services.scoring import create_user_score_recalculation_request  # noqa: E402
from trustledger_domain import (  # noqa: E402
    AutomationTaskStatus,
    AutomationTaskType,
    ConsentScope,
    NotificationDeliveryStatus,
    OrganizationType,
    ScoreCalculationReason,
    ScoreRecalculationStatus,
)
from worker.runtime import run_worker_cycle  # noqa: E402


class WorkerRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def seed_user(self, *, email: str, full_name: str) -> User:
        with Session(self.engine) as session:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password("super-secret-123"),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def test_worker_cycle_executes_due_automation_and_processes_due_score_requests(self) -> None:
        subject_one = self.seed_user(email="subject-one@example.com", full_name="Subject One")
        subject_two = self.seed_user(email="subject-two@example.com", full_name="Subject Two")

        with Session(self.engine) as session:
            automation_task = AutomationTask(
                task_type=AutomationTaskType.USER_SCORE_RECALCULATION,
                status=AutomationTaskStatus.PENDING,
                title="Queue score refresh for subject one",
                subject_user_id=subject_one.id,
                requested_by_user_id=subject_one.id,
                scheduled_for=utcnow(),
            )
            session.add(automation_task)
            create_user_score_recalculation_request(
                session=session,
                user=session.get(User, subject_two.id),
                calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
                requested_by_user=session.get(User, subject_one.id),
                scheduled_for=utcnow(),
            )
            session.commit()

        with Session(self.engine) as session:
            summary = run_worker_cycle(session=session, limit=10)

        self.assertEqual(summary.claimed_automation_task_count, 1)
        self.assertEqual(summary.completed_automation_task_count, 1)
        self.assertEqual(summary.failed_automation_task_count, 0)
        self.assertEqual(summary.processed_score_request_count, 2)
        self.assertEqual(summary.failed_score_request_count, 0)
        self.assertIsNotNone(summary.worker_run_id)

        with Session(self.engine) as session:
            automation_tasks = session.exec(select(AutomationTask)).all()
            requests = session.exec(select(TrustScoreRecalculationRequest)).all()
            snapshots = session.exec(select(TrustScoreSnapshot)).all()
            worker_runs = session.exec(select(WorkerRun)).all()
            worker_user = session.exec(
                select(User).where(User.email == "worker@trustledger.internal")
            ).first()

            self.assertEqual(len(automation_tasks), 1)
            self.assertEqual(automation_tasks[0].status, AutomationTaskStatus.COMPLETED)
            self.assertIsNotNone(automation_tasks[0].score_recalculation_request_id)
            self.assertEqual(len(requests), 2)
            self.assertTrue(
                all(request.status == ScoreRecalculationStatus.COMPLETED for request in requests)
            )
            self.assertTrue(all(request.attempt_count == 1 for request in requests))
            self.assertTrue(
                all(request.processed_by_user_id == worker_user.id for request in requests)
            )
            self.assertEqual(len(snapshots), 2)
            self.assertIsNotNone(worker_user)
            self.assertEqual(len(worker_runs), 1)
            self.assertEqual(worker_runs[0].id, summary.worker_run_id)
            self.assertEqual(worker_runs[0].status.value, "completed")
            self.assertEqual(worker_runs[0].claimed_automation_task_count, 1)
            self.assertEqual(worker_runs[0].sent_notification_count, 0)
            self.assertEqual(worker_runs[0].processed_score_request_count, 2)
            audit_logs = session.exec(select(AuditLog)).all()
            self.assertTrue(
                any(log.action_type.value == "automation_task_claimed" for log in audit_logs)
            )
            self.assertTrue(
                any(log.action_type.value == "automation_task_executed" for log in audit_logs)
            )
            self.assertTrue(
                any(
                    log.action_type.value == "score_recalculation_request_claimed"
                    for log in audit_logs
                )
            )
            self.assertTrue(
                any(
                    log.action_type.value == "score_recalculation_request_processed"
                    for log in audit_logs
                )
            )

    def test_worker_cycle_dispatches_due_notifications_created_by_consent_reminders(self) -> None:
        requester = self.seed_user(email="requester@example.com", full_name="Requester")
        subject = self.seed_user(email="subject@example.com", full_name="Subject")

        with Session(self.engine) as session:
            organization = Organization(
                name="Reminder Realty",
                slug="reminder-realty",
                organization_type=OrganizationType.AGENCY,
            )
            session.add(organization)
            session.flush()
            consent = TrustReportConsent(
                subject_user_id=subject.id,
                granted_by_user_id=subject.id,
                grantee_organization_id=organization.id,
                scope=ConsentScope.TRUST_REPORT_READ,
                share_token_hash=hash_token("consent-share-token"),
                access_code_hash=hash_password("4829"),
                expires_at=utcnow().replace(year=2027),
            )
            session.add(consent)
            session.flush()
            reminder_task = AutomationTask(
                task_type=AutomationTaskType.CONSENT_EXPIRY_REMINDER,
                status=AutomationTaskStatus.PENDING,
                title="Consent expires soon",
                subject_user_id=subject.id,
                organization_id=organization.id,
                consent_id=consent.id,
                requested_by_user_id=requester.id,
                scheduled_for=utcnow(),
            )
            session.add(reminder_task)
            session.commit()

        with Session(self.engine) as session:
            summary = run_worker_cycle(session=session, limit=10)

        self.assertEqual(summary.claimed_automation_task_count, 1)
        self.assertEqual(summary.completed_automation_task_count, 1)
        self.assertEqual(summary.claimed_notification_count, 1)
        self.assertEqual(summary.sent_notification_count, 1)
        self.assertEqual(summary.failed_notification_count, 0)

        with Session(self.engine) as session:
            notifications = session.exec(select(NotificationDelivery)).all()
            self.assertEqual(len(notifications), 1)
            self.assertEqual(notifications[0].status, NotificationDeliveryStatus.SENT)
            self.assertEqual(notifications[0].recipient_address, "subject@example.com")
            audit_logs = session.exec(select(AuditLog)).all()
            self.assertTrue(
                any(log.action_type.value == "notification_queued" for log in audit_logs)
            )
            self.assertTrue(
                any(log.action_type.value == "notification_delivered" for log in audit_logs)
            )

    def test_worker_cycle_marks_invalid_automation_tasks_failed(self) -> None:
        requester = self.seed_user(email="requester@example.com", full_name="Requester User")

        with Session(self.engine) as session:
            invalid_task = AutomationTask(
                task_type=AutomationTaskType.USER_SCORE_RECALCULATION,
                status=AutomationTaskStatus.PENDING,
                title="Broken score refresh task",
                requested_by_user_id=requester.id,
                scheduled_for=utcnow(),
            )
            session.add(invalid_task)
            session.commit()
            invalid_task_id = invalid_task.id

        with Session(self.engine) as session:
            summary = run_worker_cycle(session=session, limit=10)

        self.assertEqual(summary.claimed_automation_task_count, 1)
        self.assertEqual(summary.completed_automation_task_count, 0)
        self.assertEqual(summary.failed_automation_task_count, 1)
        self.assertEqual(summary.processed_score_request_count, 0)

        with Session(self.engine) as session:
            invalid_task = session.get(AutomationTask, invalid_task_id)
            self.assertIsNotNone(invalid_task)
            self.assertEqual(invalid_task.status, AutomationTaskStatus.FAILED)
            self.assertIn("subject user", (invalid_task.last_error or "").lower())
            audit_logs = session.exec(select(AuditLog)).all()
            self.assertTrue(
                any(
                    log.action_type.value == "automation_task_executed"
                    and log.outcome_status.value == "failed"
                    for log in audit_logs
                )
            )

    def test_worker_cycle_cleans_expired_reminders_and_stale_follow_ups(self) -> None:
        subject = self.seed_user(email="subject@example.com", full_name="Subject User")

        with Session(self.engine) as session:
            organization = Organization(
                name="Cleanup Realty",
                slug="cleanup-realty",
                organization_type=OrganizationType.AGENCY,
            )
            session.add(organization)
            session.flush()

            expired_consent = TrustReportConsent(
                subject_user_id=subject.id,
                granted_by_user_id=subject.id,
                grantee_organization_id=organization.id,
                scope=ConsentScope.TRUST_REPORT_READ,
                share_token_hash=hash_token("expired-consent-token"),
                access_code_hash=hash_password("4829"),
                expires_at=utcnow(),
            )
            session.add(expired_consent)
            session.flush()

            reminder_task = AutomationTask(
                task_type=AutomationTaskType.CONSENT_EXPIRY_REMINDER,
                status=AutomationTaskStatus.PENDING,
                title="Expired reminder",
                subject_user_id=subject.id,
                organization_id=organization.id,
                consent_id=expired_consent.id,
                scheduled_for=utcnow(),
            )
            stale_follow_up = AutomationTask(
                task_type=AutomationTaskType.INTERNAL_FOLLOW_UP,
                status=AutomationTaskStatus.PENDING,
                title="Stale follow up",
                subject_user_id=subject.id,
                scheduled_for=utcnow().replace(year=2025),
            )
            session.add(reminder_task)
            session.add(stale_follow_up)
            session.commit()
            reminder_task_id = reminder_task.id
            stale_follow_up_id = stale_follow_up.id

        with Session(self.engine) as session:
            summary = run_worker_cycle(session=session, limit=10, stale_follow_up_days=14)

        self.assertEqual(summary.cleaned_consent_reminder_count, 1)
        self.assertEqual(summary.cleaned_stale_follow_up_count, 1)

        with Session(self.engine) as session:
            reminder_task = session.get(AutomationTask, reminder_task_id)
            stale_follow_up = session.get(AutomationTask, stale_follow_up_id)
            self.assertIsNotNone(reminder_task)
            self.assertIsNotNone(stale_follow_up)
            self.assertEqual(reminder_task.status, AutomationTaskStatus.CANCELED)
            self.assertEqual(stale_follow_up.status, AutomationTaskStatus.CANCELED)
            audit_logs = session.exec(select(AuditLog)).all()
            self.assertTrue(
                any(log.action_type.value == "automation_task_cleaned_up" for log in audit_logs)
            )

    def test_worker_cycle_records_failed_worker_run_on_unhandled_error(self) -> None:
        with Session(self.engine) as session:
            with self.assertRaisesRegex(RuntimeError, "worker runtime exploded"):
                with patch(
                    "worker.runtime.claim_due_automation_tasks",
                    side_effect=RuntimeError("worker runtime exploded"),
                ):
                    run_worker_cycle(session=session, limit=3)

        with Session(self.engine) as session:
            worker_runs = session.exec(select(WorkerRun)).all()
            self.assertEqual(len(worker_runs), 1)
            self.assertEqual(worker_runs[0].status.value, "failed")
            self.assertIn("worker runtime exploded", worker_runs[0].last_error or "")


if __name__ == "__main__":
    unittest.main()
