from __future__ import annotations

from sqlmodel import Session

from app.models import User, WorkerRun
from app.models.common import utcnow
from app.schemas.worker_run import WorkerRunResponse
from trustledger_domain import WorkerRunStatus


def create_worker_run(
    *,
    session: Session,
    worker_user: User,
    due_before,
    requested_limit: int,
) -> WorkerRun:
    worker_run = WorkerRun(
        worker_user_id=worker_user.id,
        due_before=due_before,
        requested_limit=requested_limit,
    )
    session.add(worker_run)
    session.flush()
    return worker_run


def finalize_worker_run(
    *,
    session: Session,
    worker_run: WorkerRun,
    status: WorkerRunStatus,
    claimed_automation_task_count: int,
    completed_automation_task_count: int,
    failed_automation_task_count: int,
    claimed_notification_count: int,
    sent_notification_count: int,
    failed_notification_count: int,
    processed_score_request_count: int,
    failed_score_request_count: int,
    cleaned_consent_reminder_count: int,
    cleaned_stale_follow_up_count: int,
    last_error: str | None = None,
) -> WorkerRun:
    worker_run.status = status
    worker_run.run_completed_at = utcnow()
    worker_run.claimed_automation_task_count = claimed_automation_task_count
    worker_run.completed_automation_task_count = completed_automation_task_count
    worker_run.failed_automation_task_count = failed_automation_task_count
    worker_run.claimed_notification_count = claimed_notification_count
    worker_run.sent_notification_count = sent_notification_count
    worker_run.failed_notification_count = failed_notification_count
    worker_run.processed_score_request_count = processed_score_request_count
    worker_run.failed_score_request_count = failed_score_request_count
    worker_run.cleaned_consent_reminder_count = cleaned_consent_reminder_count
    worker_run.cleaned_stale_follow_up_count = cleaned_stale_follow_up_count
    worker_run.last_error = last_error
    session.add(worker_run)
    session.flush()
    return worker_run


def build_worker_run_response(
    *,
    session: Session,
    worker_run: WorkerRun,
) -> WorkerRunResponse:
    worker_user = session.get(User, worker_run.worker_user_id)
    return WorkerRunResponse(
        id=worker_run.id,
        worker_user_id=worker_run.worker_user_id,
        worker_user_email=worker_user.email if worker_user else None,
        status=worker_run.status,
        run_started_at=worker_run.run_started_at,
        run_completed_at=worker_run.run_completed_at,
        due_before=worker_run.due_before,
        requested_limit=worker_run.requested_limit,
        claimed_automation_task_count=worker_run.claimed_automation_task_count,
        completed_automation_task_count=worker_run.completed_automation_task_count,
        failed_automation_task_count=worker_run.failed_automation_task_count,
        claimed_notification_count=worker_run.claimed_notification_count,
        sent_notification_count=worker_run.sent_notification_count,
        failed_notification_count=worker_run.failed_notification_count,
        processed_score_request_count=worker_run.processed_score_request_count,
        failed_score_request_count=worker_run.failed_score_request_count,
        cleaned_consent_reminder_count=worker_run.cleaned_consent_reminder_count,
        cleaned_stale_follow_up_count=worker_run.cleaned_stale_follow_up_count,
        last_error=worker_run.last_error,
        created_at=worker_run.created_at,
    )
