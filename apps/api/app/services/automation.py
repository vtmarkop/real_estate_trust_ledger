from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import Settings, get_settings
from app.models import (
    AutomationTask,
    Organization,
    TrustReportConsent,
    TrustScoreRecalculationBatch,
    TrustScoreRecalculationRequest,
    User,
)
from app.models.common import ensure_utc, utcnow
from app.schemas.automation import AutomationCleanupResponse, AutomationTaskResponse
from app.services.notifications import queue_consent_expiry_reminder_notification
from app.services.scoring import create_score_recalculation_batch, create_user_score_recalculation_request
from trustledger_domain import AutomationTaskStatus, AutomationTaskType
from trustledger_domain import ScoreCalculationReason, ScoreRecalculationScope


CONSENT_EXPIRY_REMINDER_LEAD_TIME = timedelta(days=1)


def build_automation_task_response(
    *,
    session: Session,
    automation_task: AutomationTask,
) -> AutomationTaskResponse:
    subject_user = (
        session.get(User, automation_task.subject_user_id)
        if automation_task.subject_user_id
        else None
    )
    organization = (
        session.get(Organization, automation_task.organization_id)
        if automation_task.organization_id
        else None
    )
    consent = (
        session.get(TrustReportConsent, automation_task.consent_id)
        if automation_task.consent_id
        else None
    )
    return AutomationTaskResponse(
        id=automation_task.id,
        task_type=automation_task.task_type,
        status=automation_task.status,
        title=automation_task.title,
        details=automation_task.details,
        result_notes=automation_task.result_notes,
        subject_user_id=automation_task.subject_user_id,
        subject_user_email=subject_user.email if subject_user else None,
        organization_id=automation_task.organization_id,
        organization_name=organization.name if organization else None,
        consent_id=automation_task.consent_id,
        consent_expires_at=consent.expires_at if consent else None,
        score_recalculation_request_id=automation_task.score_recalculation_request_id,
        score_recalculation_batch_id=automation_task.score_recalculation_batch_id,
        requested_by_user_id=automation_task.requested_by_user_id,
        processed_by_user_id=automation_task.processed_by_user_id,
        dedupe_key=automation_task.dedupe_key,
        scheduled_for=automation_task.scheduled_for,
        started_at=automation_task.started_at,
        completed_at=automation_task.completed_at,
        attempt_count=automation_task.attempt_count,
        last_error=automation_task.last_error,
        created_at=automation_task.created_at,
        updated_at=automation_task.updated_at,
    )


def get_due_boundary(
    *,
    due_before: datetime | None = None,
) -> datetime:
    return ensure_utc(due_before) if due_before else utcnow()


def calculate_consent_expiry_reminder_schedule(
    *,
    consent: TrustReportConsent,
    now: datetime | None = None,
) -> datetime:
    current_time = ensure_utc(now or utcnow())
    reminder_time = ensure_utc(consent.expires_at) - CONSENT_EXPIRY_REMINDER_LEAD_TIME
    if reminder_time < current_time:
        return current_time
    return reminder_time


def get_automation_task_by_dedupe_key(
    *,
    session: Session,
    dedupe_key: str,
) -> AutomationTask | None:
    return session.exec(
        select(AutomationTask).where(AutomationTask.dedupe_key == dedupe_key)
    ).first()


def ensure_consent_expiry_reminder(
    *,
    session: Session,
    consent: TrustReportConsent,
) -> AutomationTask:
    if not consent.is_active():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Consent is expired or revoked and cannot be queued for reminder.",
        )

    dedupe_key = f"consent-expiry:{consent.id}"
    reminder_task = get_automation_task_by_dedupe_key(session=session, dedupe_key=dedupe_key)
    scheduled_for = calculate_consent_expiry_reminder_schedule(consent=consent)
    details = (
        f"Consent expires at {ensure_utc(consent.expires_at).isoformat()} "
        f"for organization {consent.grantee_organization_id}."
    )

    if reminder_task is None:
        reminder_task = AutomationTask(
            task_type=AutomationTaskType.CONSENT_EXPIRY_REMINDER,
            title="Trust report consent expiring",
            details=details,
            subject_user_id=consent.subject_user_id,
            organization_id=consent.grantee_organization_id,
            consent_id=consent.id,
            requested_by_user_id=consent.granted_by_user_id,
            dedupe_key=dedupe_key,
            scheduled_for=scheduled_for,
        )
    else:
        reminder_task.title = "Trust report consent expiring"
        reminder_task.details = details
        reminder_task.subject_user_id = consent.subject_user_id
        reminder_task.organization_id = consent.grantee_organization_id
        reminder_task.consent_id = consent.id
        reminder_task.requested_by_user_id = consent.granted_by_user_id
        reminder_task.scheduled_for = scheduled_for
        reminder_task.updated_at = utcnow()
        if reminder_task.status in {
            AutomationTaskStatus.CANCELED,
            AutomationTaskStatus.FAILED,
        }:
            reminder_task.status = AutomationTaskStatus.PENDING
            reminder_task.started_at = None
            reminder_task.completed_at = None
            reminder_task.processed_by_user_id = None
            reminder_task.result_notes = None
            reminder_task.last_error = None

    session.add(reminder_task)
    session.flush()
    return reminder_task


def cancel_consent_expiry_reminder(
    *,
    session: Session,
    consent: TrustReportConsent,
    result_notes: str,
) -> AutomationTask | None:
    dedupe_key = f"consent-expiry:{consent.id}"
    reminder_task = get_automation_task_by_dedupe_key(session=session, dedupe_key=dedupe_key)
    if reminder_task is None or reminder_task.status.is_final:
        return reminder_task

    current_time = utcnow()
    reminder_task.status = AutomationTaskStatus.CANCELED
    reminder_task.result_notes = result_notes.strip()
    reminder_task.last_error = None
    reminder_task.completed_at = current_time
    reminder_task.updated_at = current_time
    session.add(reminder_task)
    session.flush()
    return reminder_task


def create_internal_follow_up_task(
    *,
    session: Session,
    requested_by_user: User,
    title: str,
    details: str | None,
    scheduled_for: datetime | None = None,
    subject_user: User | None = None,
    organization: Organization | None = None,
) -> AutomationTask:
    automation_task = AutomationTask(
        task_type=AutomationTaskType.INTERNAL_FOLLOW_UP,
        title=title.strip(),
        details=details.strip() if details else None,
        subject_user_id=subject_user.id if subject_user else None,
        organization_id=organization.id if organization else None,
        requested_by_user_id=requested_by_user.id,
        scheduled_for=ensure_utc(scheduled_for) if scheduled_for else utcnow(),
    )
    session.add(automation_task)
    session.flush()
    return automation_task


def create_user_score_refresh_task(
    *,
    session: Session,
    requested_by_user: User,
    subject_user: User,
    scheduled_for: datetime | None = None,
) -> AutomationTask:
    automation_task = AutomationTask(
        task_type=AutomationTaskType.USER_SCORE_RECALCULATION,
        title="Scheduled user trust score refresh",
        details=f"Queue a recalculation request for user {subject_user.email}.",
        subject_user_id=subject_user.id,
        requested_by_user_id=requested_by_user.id,
        scheduled_for=ensure_utc(scheduled_for) if scheduled_for else utcnow(),
    )
    session.add(automation_task)
    session.flush()
    return automation_task


def create_organization_score_batch_refresh_task(
    *,
    session: Session,
    requested_by_user: User,
    organization: Organization,
    scheduled_for: datetime | None = None,
) -> AutomationTask:
    automation_task = AutomationTask(
        task_type=AutomationTaskType.ORGANIZATION_SCORE_RECALCULATION_BATCH,
        title="Scheduled organization trust score batch refresh",
        details=f"Queue a recalculation batch for organization {organization.name}.",
        organization_id=organization.id,
        requested_by_user_id=requested_by_user.id,
        scheduled_for=ensure_utc(scheduled_for) if scheduled_for else utcnow(),
    )
    session.add(automation_task)
    session.flush()
    return automation_task


def claim_due_automation_tasks(
    *,
    session: Session,
    processed_by_user: User,
    task_type: AutomationTaskType | None = None,
    limit: int = 1,
    due_before: datetime | None = None,
) -> list[AutomationTask]:
    due_boundary = get_due_boundary(due_before=due_before)
    query = (
        select(AutomationTask)
        .where(
            AutomationTask.status == AutomationTaskStatus.PENDING,
            AutomationTask.scheduled_for <= due_boundary,
        )
        .order_by(AutomationTask.scheduled_for.asc(), AutomationTask.created_at.asc())
    )
    if task_type is not None:
        query = query.where(AutomationTask.task_type == task_type)

    automation_tasks = session.exec(query).all()[:limit]
    claimed_at = utcnow()
    claimed_tasks: list[AutomationTask] = []
    for automation_task in automation_tasks:
        automation_task.status = AutomationTaskStatus.PROCESSING
        automation_task.processed_by_user_id = processed_by_user.id
        automation_task.started_at = automation_task.started_at or claimed_at
        automation_task.attempt_count += 1
        automation_task.updated_at = claimed_at
        session.add(automation_task)
        claimed_tasks.append(automation_task)

    session.flush()
    return claimed_tasks


def transition_automation_task(
    *,
    session: Session,
    automation_task: AutomationTask,
    target_status: AutomationTaskStatus,
    processed_by_user: User,
    result_notes: str | None = None,
) -> AutomationTask:
    if target_status == AutomationTaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automation tasks cannot transition back to pending through processing.",
        )

    if automation_task.status.is_final:
        if automation_task.status == target_status:
            return automation_task
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Automation task is already in a final state.",
        )

    current_time = utcnow()
    stripped_notes = result_notes.strip() if result_notes else None

    if automation_task.status == target_status:
        if stripped_notes:
            automation_task.result_notes = stripped_notes
            automation_task.updated_at = current_time
            session.add(automation_task)
            session.flush()
        return automation_task

    if automation_task.started_at is None:
        automation_task.started_at = current_time
    if automation_task.status != AutomationTaskStatus.PROCESSING:
        automation_task.attempt_count += 1

    automation_task.processed_by_user_id = processed_by_user.id
    automation_task.status = target_status
    automation_task.updated_at = current_time

    if target_status == AutomationTaskStatus.PROCESSING:
        if stripped_notes:
            automation_task.result_notes = stripped_notes
    else:
        automation_task.completed_at = current_time
        automation_task.result_notes = stripped_notes
        if target_status == AutomationTaskStatus.FAILED:
            automation_task.last_error = stripped_notes or "Automation task failed."
        else:
            automation_task.last_error = None

    session.add(automation_task)
    session.flush()
    return automation_task


def fail_automation_task(
    *,
    session: Session,
    automation_task: AutomationTask,
    processed_by_user: User,
    error_message: str,
) -> AutomationTask:
    current_time = utcnow()
    automation_task.status = AutomationTaskStatus.FAILED
    automation_task.processed_by_user_id = processed_by_user.id
    automation_task.started_at = automation_task.started_at or current_time
    automation_task.completed_at = current_time
    automation_task.updated_at = current_time
    automation_task.last_error = error_message[:500]
    automation_task.result_notes = error_message[:1000]
    session.add(automation_task)
    session.flush()
    return automation_task


def resolve_automation_task_requester(
    *,
    session: Session,
    automation_task: AutomationTask,
    fallback_user: User,
) -> User:
    if automation_task.requested_by_user_id:
        requested_by_user = session.get(User, automation_task.requested_by_user_id)
        if requested_by_user and requested_by_user.is_active:
            return requested_by_user
    return fallback_user


def execute_automation_task(
    *,
    session: Session,
    automation_task: AutomationTask,
    processed_by_user: User,
    settings: Settings | None = None,
) -> AutomationTask:
    runtime_settings = settings or get_settings()
    if automation_task.status == AutomationTaskStatus.COMPLETED:
        return automation_task
    if automation_task.status.is_final:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending or processing automation tasks can be executed.",
        )

    requested_by_user = resolve_automation_task_requester(
        session=session,
        automation_task=automation_task,
        fallback_user=processed_by_user,
    )

    current_time = utcnow()
    if automation_task.started_at is None:
        automation_task.started_at = current_time
    if automation_task.status != AutomationTaskStatus.PROCESSING:
        automation_task.attempt_count += 1
    automation_task.status = AutomationTaskStatus.PROCESSING
    automation_task.processed_by_user_id = processed_by_user.id
    automation_task.updated_at = current_time
    automation_task.last_error = None
    session.add(automation_task)
    session.flush()

    if automation_task.task_type == AutomationTaskType.USER_SCORE_RECALCULATION:
        if automation_task.subject_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User score refresh tasks require a subject user.",
            )
        subject_user = session.get(User, automation_task.subject_user_id)
        if not subject_user or not subject_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subject user is unavailable for score refresh.",
            )
        recalculation_request = create_user_score_recalculation_request(
            session=session,
            user=subject_user,
            calculation_reason=ScoreCalculationReason.SCHEDULED_AUTOMATION_REFRESH,
            requested_by_user=requested_by_user,
            scheduled_for=automation_task.scheduled_for,
        )
        automation_task.score_recalculation_request_id = recalculation_request.id
        automation_task.result_notes = (
            f"Queued score recalculation request {recalculation_request.id} for {subject_user.email}."
        )
    elif automation_task.task_type == AutomationTaskType.ORGANIZATION_SCORE_RECALCULATION_BATCH:
        if automation_task.organization_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Organization score refresh tasks require an organization.",
            )
        organization = session.get(Organization, automation_task.organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization is unavailable for score batch refresh.",
            )
        recalculation_batch, _requests = create_score_recalculation_batch(
            session=session,
            scope_type=ScoreRecalculationScope.ORGANIZATION_MEMBERS,
            requested_by_user=requested_by_user,
            organization=organization,
            scheduled_for=automation_task.scheduled_for,
        )
        automation_task.score_recalculation_batch_id = recalculation_batch.id
        automation_task.result_notes = (
            f"Queued score recalculation batch {recalculation_batch.id} for {organization.name}."
        )
    elif automation_task.task_type == AutomationTaskType.CONSENT_EXPIRY_REMINDER:
        if automation_task.consent_id is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Consent reminder tasks require a linked consent.",
            )
        consent = session.get(TrustReportConsent, automation_task.consent_id)
        if consent is None or not consent.is_active(now=current_time):
            automation_task.status = AutomationTaskStatus.CANCELED
            automation_task.completed_at = current_time
            automation_task.updated_at = current_time
            automation_task.last_error = None
            automation_task.result_notes = (
                "Consent reminder closed because the linked consent is no longer active."
            )
            session.add(automation_task)
            session.flush()
            return automation_task
        notification_delivery = queue_consent_expiry_reminder_notification(
            session=session,
            automation_task=automation_task,
            consent=consent,
            requested_by_user=requested_by_user,
            settings=runtime_settings,
        )
        automation_task.result_notes = (
            f"Queued notification delivery {notification_delivery.id} "
            f"for consent {consent.id}."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This automation task type does not have an executable system action.",
        )

    automation_task.status = AutomationTaskStatus.COMPLETED
    automation_task.completed_at = utcnow()
    automation_task.updated_at = utcnow()
    automation_task.last_error = None
    session.add(automation_task)
    session.flush()
    return automation_task


def cleanup_expired_consent_reminder_tasks(
    *,
    session: Session,
    processed_by_user: User,
    due_before: datetime | None = None,
) -> AutomationCleanupResponse:
    due_boundary = get_due_boundary(due_before=due_before)
    automation_tasks = session.exec(
        select(AutomationTask)
        .where(
            AutomationTask.task_type == AutomationTaskType.CONSENT_EXPIRY_REMINDER,
            AutomationTask.status.in_(
                [AutomationTaskStatus.PENDING, AutomationTaskStatus.PROCESSING]
            ),
            AutomationTask.scheduled_for <= due_boundary,
        )
        .order_by(AutomationTask.scheduled_for.asc(), AutomationTask.created_at.asc())
    ).all()

    processed_ids: list[object] = []
    current_time = utcnow()
    for automation_task in automation_tasks:
        consent = (
            session.get(TrustReportConsent, automation_task.consent_id)
            if automation_task.consent_id
            else None
        )
        if consent is not None and consent.is_active(now=current_time):
            continue
        automation_task.status = AutomationTaskStatus.CANCELED
        automation_task.processed_by_user_id = processed_by_user.id
        automation_task.completed_at = current_time
        automation_task.updated_at = current_time
        automation_task.last_error = None
        automation_task.result_notes = (
            "Consent reminder auto-closed because the linked consent expired or was revoked."
        )
        session.add(automation_task)
        processed_ids.append(automation_task.id)

    session.flush()
    return AutomationCleanupResponse(
        task_type=AutomationTaskType.CONSENT_EXPIRY_REMINDER,
        processed_task_count=len(processed_ids),
        task_ids=processed_ids,
        processed_at=current_time,
    )


def cleanup_stale_follow_up_tasks(
    *,
    session: Session,
    processed_by_user: User,
    stale_after_days: int,
    due_before: datetime | None = None,
) -> AutomationCleanupResponse:
    due_boundary = get_due_boundary(due_before=due_before)
    stale_boundary = due_boundary - timedelta(days=stale_after_days)
    automation_tasks = session.exec(
        select(AutomationTask)
        .where(
            AutomationTask.task_type == AutomationTaskType.INTERNAL_FOLLOW_UP,
            AutomationTask.status.in_(
                [AutomationTaskStatus.PENDING, AutomationTaskStatus.PROCESSING]
            ),
            AutomationTask.scheduled_for <= stale_boundary,
        )
        .order_by(AutomationTask.scheduled_for.asc(), AutomationTask.created_at.asc())
    ).all()

    processed_ids: list[object] = []
    current_time = utcnow()
    for automation_task in automation_tasks:
        automation_task.status = AutomationTaskStatus.CANCELED
        automation_task.processed_by_user_id = processed_by_user.id
        automation_task.completed_at = current_time
        automation_task.updated_at = current_time
        automation_task.last_error = None
        automation_task.result_notes = (
            f"Follow-up auto-closed after exceeding {stale_after_days} days without manual closure."
        )
        session.add(automation_task)
        processed_ids.append(automation_task.id)

    session.flush()
    return AutomationCleanupResponse(
        task_type=AutomationTaskType.INTERNAL_FOLLOW_UP,
        processed_task_count=len(processed_ids),
        task_ids=processed_ids,
        processed_at=current_time,
    )
