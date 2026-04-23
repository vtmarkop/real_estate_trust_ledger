from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import Settings, get_settings
from app.core.security import generate_session_token, hash_password
from app.models import User
from app.models.common import utcnow
from app.services.automation import (
    claim_due_automation_tasks,
    cleanup_expired_consent_reminder_tasks,
    cleanup_stale_follow_up_tasks,
    execute_automation_task,
    fail_automation_task,
)
from app.services.audit_logs import append_audit_log
from app.services.notifications import (
    claim_due_notification_deliveries,
    dispatch_notification_delivery,
    fail_notification_delivery,
)
from app.services.scoring import (
    claim_due_score_recalculation_requests,
    process_score_recalculation_request,
)
from app.services.worker_runs import create_worker_run, finalize_worker_run
from trustledger_domain import (
    AuditActionType,
    AuditOutcomeStatus,
    AutomationTaskStatus,
    AutomationTaskType,
    NotificationDeliveryStatus,
    ScoreRecalculationStatus,
    SystemRole,
    WorkerRunStatus,
)


DEFAULT_WORKER_USER_EMAIL = "worker@trustledger.internal"
DEFAULT_WORKER_USER_NAME = "Trust Ledger Worker"
DEFAULT_STALE_FOLLOW_UP_DAYS = 30
WORKER_EXECUTABLE_TASK_TYPES = [
    AutomationTaskType.CONSENT_EXPIRY_REMINDER,
    AutomationTaskType.USER_SCORE_RECALCULATION,
    AutomationTaskType.ORGANIZATION_SCORE_RECALCULATION_BATCH,
]


@dataclass
class WorkerRunSummary:
    worker_run_id: object
    worker_user_id: object
    claimed_automation_task_count: int
    completed_automation_task_count: int
    failed_automation_task_count: int
    claimed_notification_count: int
    sent_notification_count: int
    failed_notification_count: int
    processed_score_request_count: int
    failed_score_request_count: int
    cleaned_consent_reminder_count: int
    cleaned_stale_follow_up_count: int
    claimed_automation_task_ids: list[object]
    completed_automation_task_ids: list[object]
    failed_automation_task_ids: list[object]
    claimed_notification_ids: list[object]
    sent_notification_ids: list[object]
    failed_notification_ids: list[object]
    processed_score_request_ids: list[object]
    failed_score_request_ids: list[object]
    processed_at: object


def get_or_create_worker_user(
    *,
    session: Session,
    email: str = DEFAULT_WORKER_USER_EMAIL,
    full_name: str = DEFAULT_WORKER_USER_NAME,
) -> User:
    normalized_email = email.lower().strip()
    worker_user = session.exec(
        select(User).where(User.email == normalized_email)
    ).first()
    if worker_user:
        return worker_user

    worker_user = User(
        email=normalized_email,
        full_name=full_name,
        password_hash=hash_password(generate_session_token()),
        system_role=SystemRole.ADMIN,
        email_verified=True,
    )
    session.add(worker_user)
    session.flush()
    return worker_user


def run_worker_cycle(
    *,
    session: Session,
    settings: Settings | None = None,
    due_before: datetime | None = None,
    limit: int = 100,
    stale_follow_up_days: int = DEFAULT_STALE_FOLLOW_UP_DAYS,
) -> WorkerRunSummary:
    runtime_settings = settings or get_settings()
    worker_user = get_or_create_worker_user(session=session)
    due_boundary = due_before or utcnow()
    worker_run = create_worker_run(
        session=session,
        worker_user=worker_user,
        due_before=due_boundary,
        requested_limit=limit,
    )

    claimed_tasks: list[object] = []
    completed_task_ids: list[object] = []
    failed_task_ids: list[object] = []
    claimed_notification_ids: list[object] = []
    sent_notification_ids: list[object] = []
    failed_notification_ids: list[object] = []
    processed_score_request_ids: list[object] = []
    failed_score_request_ids: list[object] = []
    cleaned_consent_reminder_count = 0
    cleaned_stale_follow_up_count = 0

    try:
        consent_cleanup = cleanup_expired_consent_reminder_tasks(
            session=session,
            processed_by_user=worker_user,
            due_before=due_boundary,
        )
        stale_follow_up_cleanup = cleanup_stale_follow_up_tasks(
            session=session,
            processed_by_user=worker_user,
            stale_after_days=stale_follow_up_days,
            due_before=due_boundary,
        )
        cleaned_consent_reminder_count = consent_cleanup.processed_task_count
        cleaned_stale_follow_up_count = stale_follow_up_cleanup.processed_task_count
        if consent_cleanup.processed_task_count > 0:
            append_audit_log(
                session=session,
                action_type=AuditActionType.AUTOMATION_TASK_CLEANED_UP,
                outcome_status=AuditOutcomeStatus.CANCELED,
                actor_user_id=worker_user.id,
                target_type="automation_task_cleanup",
                details=(
                    f"Worker cleaned up {consent_cleanup.processed_task_count} expired consent reminder tasks."
                ),
            )
        if stale_follow_up_cleanup.processed_task_count > 0:
            append_audit_log(
                session=session,
                action_type=AuditActionType.AUTOMATION_TASK_CLEANED_UP,
                outcome_status=AuditOutcomeStatus.CANCELED,
                actor_user_id=worker_user.id,
                target_type="automation_task_cleanup",
                details=(
                    f"Worker cleaned up {stale_follow_up_cleanup.processed_task_count} stale follow-up tasks."
                ),
            )

        remaining_limit = limit
        for task_type in WORKER_EXECUTABLE_TASK_TYPES:
            if remaining_limit <= 0:
                break
            claimed_for_type = claim_due_automation_tasks(
                session=session,
                processed_by_user=worker_user,
                task_type=task_type,
                limit=remaining_limit,
                due_before=due_boundary,
            )
            claimed_tasks.extend(claimed_for_type)
            remaining_limit -= len(claimed_for_type)
        for automation_task in claimed_tasks:
            append_audit_log(
                session=session,
                action_type=AuditActionType.AUTOMATION_TASK_CLAIMED,
                outcome_status=AuditOutcomeStatus.SUCCEEDED,
                actor_user_id=worker_user.id,
                organization_id=automation_task.organization_id,
                subject_user_id=automation_task.subject_user_id,
                target_type="automation_task",
                target_id=automation_task.id,
                details=f"Worker claimed automation task {automation_task.task_type.value}.",
            )
            try:
                executed_task = execute_automation_task(
                    session=session,
                    automation_task=automation_task,
                    processed_by_user=worker_user,
                    settings=runtime_settings,
                )
                completed_task_ids.append(automation_task.id)
                append_audit_log(
                    session=session,
                    action_type=AuditActionType.AUTOMATION_TASK_EXECUTED,
                    outcome_status=(
                        AuditOutcomeStatus.CANCELED
                        if executed_task.status == AutomationTaskStatus.CANCELED
                        else AuditOutcomeStatus.SUCCEEDED
                    ),
                    actor_user_id=worker_user.id,
                    organization_id=executed_task.organization_id,
                    subject_user_id=executed_task.subject_user_id,
                    target_type="automation_task",
                    target_id=executed_task.id,
                    details=f"Worker executed automation task with resulting status {executed_task.status.value}.",
                )
            except HTTPException as exc:
                failed_task = fail_automation_task(
                    session=session,
                    automation_task=automation_task,
                    processed_by_user=worker_user,
                    error_message=str(exc.detail),
                )
                failed_task_ids.append(automation_task.id)
                append_audit_log(
                    session=session,
                    action_type=AuditActionType.AUTOMATION_TASK_EXECUTED,
                    outcome_status=AuditOutcomeStatus.FAILED,
                    actor_user_id=worker_user.id,
                    organization_id=failed_task.organization_id,
                    subject_user_id=failed_task.subject_user_id,
                    target_type="automation_task",
                    target_id=failed_task.id,
                    details=f"Worker failed automation task: {failed_task.last_error}.",
                )

        notification_deliveries = claim_due_notification_deliveries(
            session=session,
            processed_by_user=worker_user,
            limit=min(limit, runtime_settings.notification_batch_limit),
            due_before=due_boundary,
        )
        claimed_notification_ids.extend(
            notification_delivery.id for notification_delivery in notification_deliveries
        )
        for notification_delivery in notification_deliveries:
            try:
                dispatched_delivery = dispatch_notification_delivery(
                    session=session,
                    notification_delivery=notification_delivery,
                    processed_by_user=worker_user,
                    settings=runtime_settings,
                )
                if dispatched_delivery.status == NotificationDeliveryStatus.SENT:
                    sent_notification_ids.append(dispatched_delivery.id)
            except HTTPException as exc:
                failed_delivery = fail_notification_delivery(
                    session=session,
                    notification_delivery=notification_delivery,
                    processed_by_user=worker_user,
                    error_message=str(exc.detail),
                )
                failed_notification_ids.append(failed_delivery.id)
            except Exception as exc:
                failed_delivery = fail_notification_delivery(
                    session=session,
                    notification_delivery=notification_delivery,
                    processed_by_user=worker_user,
                    error_message=str(exc),
                )
                failed_notification_ids.append(failed_delivery.id)

        score_requests = claim_due_score_recalculation_requests(
            session=session,
            processed_by_user=worker_user,
            limit=limit,
            due_before=due_boundary,
        )
        for recalculation_request in score_requests:
            append_audit_log(
                session=session,
                action_type=AuditActionType.SCORE_RECALCULATION_REQUEST_CLAIMED,
                outcome_status=AuditOutcomeStatus.SUCCEEDED,
                actor_user_id=worker_user.id,
                subject_user_id=recalculation_request.user_id,
                target_type="trust_score_recalculation_request",
                target_id=recalculation_request.id,
                details="Worker claimed score recalculation request.",
            )
            processed_request = process_score_recalculation_request(
                session=session,
                recalculation_request=recalculation_request,
                processed_by_user=worker_user,
            )
            if processed_request.status == ScoreRecalculationStatus.FAILED:
                failed_score_request_ids.append(processed_request.id)
                append_audit_log(
                    session=session,
                    action_type=AuditActionType.SCORE_RECALCULATION_REQUEST_PROCESSED,
                    outcome_status=AuditOutcomeStatus.FAILED,
                    actor_user_id=worker_user.id,
                    subject_user_id=processed_request.user_id,
                    target_type="trust_score_recalculation_request",
                    target_id=processed_request.id,
                    details=processed_request.last_error or "Score recalculation request failed during worker execution.",
                )
            else:
                processed_score_request_ids.append(processed_request.id)
                append_audit_log(
                    session=session,
                    action_type=AuditActionType.SCORE_RECALCULATION_REQUEST_PROCESSED,
                    outcome_status=AuditOutcomeStatus.SUCCEEDED,
                    actor_user_id=worker_user.id,
                    subject_user_id=processed_request.user_id,
                    target_type="trust_score_recalculation_request",
                    target_id=processed_request.id,
                    details="Score recalculation request processed by worker.",
                )

        finalize_worker_run(
            session=session,
            worker_run=worker_run,
            status=WorkerRunStatus.COMPLETED,
            claimed_automation_task_count=len(claimed_tasks),
            completed_automation_task_count=len(completed_task_ids),
            failed_automation_task_count=len(failed_task_ids),
            claimed_notification_count=len(claimed_notification_ids),
            sent_notification_count=len(sent_notification_ids),
            failed_notification_count=len(failed_notification_ids),
            processed_score_request_count=len(processed_score_request_ids),
            failed_score_request_count=len(failed_score_request_ids),
            cleaned_consent_reminder_count=cleaned_consent_reminder_count,
            cleaned_stale_follow_up_count=cleaned_stale_follow_up_count,
        )
        session.commit()
        return WorkerRunSummary(
            worker_run_id=worker_run.id,
            worker_user_id=worker_user.id,
            claimed_automation_task_count=len(claimed_tasks),
            completed_automation_task_count=len(completed_task_ids),
            failed_automation_task_count=len(failed_task_ids),
            claimed_notification_count=len(claimed_notification_ids),
            sent_notification_count=len(sent_notification_ids),
            failed_notification_count=len(failed_notification_ids),
            processed_score_request_count=len(processed_score_request_ids),
            failed_score_request_count=len(failed_score_request_ids),
            cleaned_consent_reminder_count=cleaned_consent_reminder_count,
            cleaned_stale_follow_up_count=cleaned_stale_follow_up_count,
            claimed_automation_task_ids=[task.id for task in claimed_tasks],
            completed_automation_task_ids=completed_task_ids,
            failed_automation_task_ids=failed_task_ids,
            claimed_notification_ids=claimed_notification_ids,
            sent_notification_ids=sent_notification_ids,
            failed_notification_ids=failed_notification_ids,
            processed_score_request_ids=processed_score_request_ids,
            failed_score_request_ids=failed_score_request_ids,
            processed_at=utcnow(),
        )
    except Exception as exc:
        finalize_worker_run(
            session=session,
            worker_run=worker_run,
            status=WorkerRunStatus.FAILED,
            claimed_automation_task_count=len(claimed_tasks),
            completed_automation_task_count=len(completed_task_ids),
            failed_automation_task_count=len(failed_task_ids),
            claimed_notification_count=len(claimed_notification_ids),
            sent_notification_count=len(sent_notification_ids),
            failed_notification_count=len(failed_notification_ids),
            processed_score_request_count=len(processed_score_request_ids),
            failed_score_request_count=len(failed_score_request_ids),
            cleaned_consent_reminder_count=cleaned_consent_reminder_count,
            cleaned_stale_follow_up_count=cleaned_stale_follow_up_count,
            last_error=str(exc)[:1000],
        )
        session.commit()
        raise
