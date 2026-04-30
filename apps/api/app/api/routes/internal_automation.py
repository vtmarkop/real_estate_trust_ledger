from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select

from app.api.deps import SessionDep, SettingsDep, require_system_roles
from app.models import AutomationTask, Organization, TrustReportConsent, User
from app.schemas.automation import (
    AutomationCleanupRequest,
    AutomationCleanupResponse,
    AutomationFollowUpCreateRequest,
    AutomationTaskClaimRequest,
    ScheduledScoreRefreshTaskCreateRequest,
    AutomationTaskProcessRequest,
    AutomationTaskResponse,
)
from app.services.automation import (
    build_automation_task_response,
    claim_due_automation_tasks,
    cleanup_expired_consent_reminder_tasks,
    cleanup_stale_follow_up_tasks,
    create_organization_score_batch_refresh_task,
    create_internal_follow_up_task,
    create_user_score_refresh_task,
    execute_automation_task,
    ensure_consent_expiry_reminder,
    transition_automation_task,
)
from app.services.audit_logs import append_audit_log
from app.models.common import utcnow
from trustledger_domain import (
    AuditActionType,
    AuditOutcomeStatus,
    AutomationTaskStatus,
    AutomationTaskType,
    SystemRole,
)


router = APIRouter(prefix="/internal/automation", tags=["internal-automation"])


def get_automation_task_or_404(
    *,
    session: SessionDep,
    task_id: UUID,
) -> AutomationTask:
    automation_task = session.get(AutomationTask, task_id)
    if not automation_task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation task not found.",
        )
    return automation_task


def get_user_or_404(
    *,
    session: SessionDep,
    user_id: UUID,
) -> User:
    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return user


def resolve_subject_user(
    *,
    session: SessionDep,
    user_id: UUID | None,
    user_email: str | None,
) -> User | None:
    subject_user = get_user_or_404(session=session, user_id=user_id) if user_id is not None else None
    if user_email is not None:
        email_match = session.exec(
            select(User).where(User.email == user_email.lower().strip())
        ).first()
        if user_id is not None and email_match and email_match.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="subject_user_id and subject_user_email refer to different users.",
            )
        if email_match is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        subject_user = subject_user or email_match
    return subject_user


def get_organization_or_404(
    *,
    session: SessionDep,
    organization_id: UUID,
) -> Organization:
    organization = session.get(Organization, organization_id)
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found.",
        )
    return organization


def get_consent_or_404(
    *,
    session: SessionDep,
    consent_id: UUID,
) -> TrustReportConsent:
    consent = session.get(TrustReportConsent, consent_id)
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent not found.",
        )
    return consent


@router.get(
    "/tasks",
    response_model=list[AutomationTaskResponse],
)
def list_automation_tasks(
    session: SessionDep,
    task_type: AutomationTaskType | None = Query(default=None),
    task_status: AutomationTaskStatus | None = Query(default=None),
    due_only: bool = Query(default=False),
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> list[AutomationTaskResponse]:
    query = select(AutomationTask)
    if task_type is not None:
        query = query.where(AutomationTask.task_type == task_type)
    if task_status is not None:
        query = query.where(AutomationTask.status == task_status)
    if due_only:
        query = query.where(AutomationTask.scheduled_for <= utcnow())

    automation_tasks = session.exec(
        query.order_by(AutomationTask.scheduled_for.asc(), AutomationTask.created_at.asc())
    ).all()
    return [
        build_automation_task_response(session=session, automation_task=automation_task)
        for automation_task in automation_tasks
    ]


@router.get(
    "/tasks/{task_id}",
    response_model=AutomationTaskResponse,
)
def get_automation_task(
    task_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationTaskResponse:
    automation_task = get_automation_task_or_404(session=session, task_id=task_id)
    return build_automation_task_response(session=session, automation_task=automation_task)


@router.post(
    "/tasks/claim",
    response_model=list[AutomationTaskResponse],
)
def claim_automation_tasks(
    payload: AutomationTaskClaimRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> list[AutomationTaskResponse]:
    automation_tasks = claim_due_automation_tasks(
        session=session,
        processed_by_user=current_user,
        task_type=payload.task_type,
        limit=payload.limit,
        due_before=payload.due_before,
    )
    for automation_task in automation_tasks:
        append_audit_log(
            session=session,
            action_type=AuditActionType.AUTOMATION_TASK_CLAIMED,
            outcome_status=AuditOutcomeStatus.SUCCEEDED,
            actor_user_id=current_user.id,
            organization_id=automation_task.organization_id,
            subject_user_id=automation_task.subject_user_id,
            target_type="automation_task",
            target_id=automation_task.id,
            details=f"Automation task claimed with type {automation_task.task_type.value}.",
        )
    session.commit()
    for automation_task in automation_tasks:
        session.refresh(automation_task)
    return [
        build_automation_task_response(session=session, automation_task=automation_task)
        for automation_task in automation_tasks
    ]


@router.post(
    "/tasks/follow-ups",
    response_model=AutomationTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_follow_up_task(
    payload: AutomationFollowUpCreateRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationTaskResponse:
    subject_user = resolve_subject_user(
        session=session,
        user_id=payload.subject_user_id,
        user_email=payload.subject_user_email,
    )

    organization = None
    if payload.organization_id is not None:
        organization = get_organization_or_404(
            session=session,
            organization_id=payload.organization_id,
        )

    automation_task = create_internal_follow_up_task(
        session=session,
        requested_by_user=current_user,
        title=payload.title,
        details=payload.details,
        scheduled_for=payload.scheduled_for,
        subject_user=subject_user,
        organization=organization,
    )
    session.commit()
    session.refresh(automation_task)
    return build_automation_task_response(session=session, automation_task=automation_task)


@router.post(
    "/cleanup/expired-consent-reminders",
    response_model=AutomationCleanupResponse,
)
def cleanup_expired_consent_reminders(
    payload: AutomationCleanupRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationCleanupResponse:
    cleanup_result = cleanup_expired_consent_reminder_tasks(
        session=session,
        processed_by_user=current_user,
        due_before=payload.due_before,
    )
    if cleanup_result.processed_task_count > 0:
        append_audit_log(
            session=session,
            action_type=AuditActionType.AUTOMATION_TASK_CLEANED_UP,
            outcome_status=AuditOutcomeStatus.CANCELED,
            actor_user_id=current_user.id,
            target_type="automation_task_cleanup",
            details=(
                f"Expired consent reminder cleanup closed "
                f"{cleanup_result.processed_task_count} tasks."
            ),
        )
    session.commit()
    return cleanup_result


@router.post(
    "/cleanup/stale-follow-ups",
    response_model=AutomationCleanupResponse,
)
def cleanup_stale_follow_ups(
    payload: AutomationCleanupRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationCleanupResponse:
    cleanup_result = cleanup_stale_follow_up_tasks(
        session=session,
        processed_by_user=current_user,
        stale_after_days=payload.stale_after_days,
        due_before=payload.due_before,
    )
    if cleanup_result.processed_task_count > 0:
        append_audit_log(
            session=session,
            action_type=AuditActionType.AUTOMATION_TASK_CLEANED_UP,
            outcome_status=AuditOutcomeStatus.CANCELED,
            actor_user_id=current_user.id,
            target_type="automation_task_cleanup",
            details=(
                f"Stale follow-up cleanup closed "
                f"{cleanup_result.processed_task_count} tasks."
            ),
        )
    session.commit()
    return cleanup_result


@router.post(
    "/tasks/score-refresh/users/{user_id}",
    response_model=AutomationTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_score_refresh_automation_task(
    user_id: UUID,
    payload: ScheduledScoreRefreshTaskCreateRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationTaskResponse:
    subject_user = get_user_or_404(session=session, user_id=user_id)
    automation_task = create_user_score_refresh_task(
        session=session,
        requested_by_user=current_user,
        subject_user=subject_user,
        scheduled_for=payload.scheduled_for,
    )
    session.commit()
    session.refresh(automation_task)
    return build_automation_task_response(session=session, automation_task=automation_task)


@router.post(
    "/tasks/score-refresh/organizations/{organization_id}",
    response_model=AutomationTaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization_score_batch_refresh_automation_task(
    organization_id: UUID,
    payload: ScheduledScoreRefreshTaskCreateRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationTaskResponse:
    organization = get_organization_or_404(session=session, organization_id=organization_id)
    automation_task = create_organization_score_batch_refresh_task(
        session=session,
        requested_by_user=current_user,
        organization=organization,
        scheduled_for=payload.scheduled_for,
    )
    session.commit()
    session.refresh(automation_task)
    return build_automation_task_response(session=session, automation_task=automation_task)


@router.post(
    "/consents/{consent_id}/ensure-expiry-reminder",
    response_model=AutomationTaskResponse,
)
def ensure_consent_expiry_task(
    consent_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationTaskResponse:
    consent = get_consent_or_404(session=session, consent_id=consent_id)
    automation_task = ensure_consent_expiry_reminder(session=session, consent=consent)
    session.commit()
    session.refresh(automation_task)
    return build_automation_task_response(session=session, automation_task=automation_task)


@router.post(
    "/tasks/{task_id}/execute",
    response_model=AutomationTaskResponse,
)
def execute_automation_task_endpoint(
    task_id: UUID,
    session: SessionDep,
    settings: SettingsDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationTaskResponse:
    automation_task = get_automation_task_or_404(session=session, task_id=task_id)
    automation_task = execute_automation_task(
        session=session,
        automation_task=automation_task,
        processed_by_user=current_user,
        settings=settings,
    )
    append_audit_log(
        session=session,
        action_type=AuditActionType.AUTOMATION_TASK_EXECUTED,
        outcome_status=(
            AuditOutcomeStatus.CANCELED
            if automation_task.status == AutomationTaskStatus.CANCELED
            else AuditOutcomeStatus.SUCCEEDED
        ),
        actor_user_id=current_user.id,
        organization_id=automation_task.organization_id,
        subject_user_id=automation_task.subject_user_id,
        target_type="automation_task",
        target_id=automation_task.id,
        details=f"Automation task executed with resulting status {automation_task.status.value}.",
    )
    session.commit()
    session.refresh(automation_task)
    return build_automation_task_response(session=session, automation_task=automation_task)


@router.post(
    "/tasks/{task_id}/process",
    response_model=AutomationTaskResponse,
)
def process_automation_task(
    task_id: UUID,
    payload: AutomationTaskProcessRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> AutomationTaskResponse:
    automation_task = get_automation_task_or_404(session=session, task_id=task_id)
    automation_task = transition_automation_task(
        session=session,
        automation_task=automation_task,
        target_status=payload.status,
        processed_by_user=current_user,
        result_notes=payload.result_notes,
    )
    session.commit()
    session.refresh(automation_task)
    return build_automation_task_response(session=session, automation_task=automation_task)
