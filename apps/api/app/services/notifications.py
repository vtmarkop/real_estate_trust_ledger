from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.core.config import Settings, get_settings
from app.models import (
    AutomationTask,
    NotificationDelivery,
    Organization,
    TrustReportConsent,
    User,
)
from app.models.common import ensure_utc, utcnow
from app.schemas.notification import NotificationDeliveryResponse
from app.services.audit_logs import append_audit_log
from trustledger_domain import (
    AuditActionType,
    AuditOutcomeStatus,
    NotificationChannel,
    NotificationDeliveryStatus,
)


CONSENT_EXPIRY_TEMPLATE_KEY = "consent_expiry_reminder"


def build_notification_delivery_response(
    *,
    session: Session,
    notification_delivery: NotificationDelivery,
) -> NotificationDeliveryResponse:
    recipient_user = (
        session.get(User, notification_delivery.recipient_user_id)
        if notification_delivery.recipient_user_id
        else None
    )
    organization = (
        session.get(Organization, notification_delivery.organization_id)
        if notification_delivery.organization_id
        else None
    )
    requested_by_user = (
        session.get(User, notification_delivery.requested_by_user_id)
        if notification_delivery.requested_by_user_id
        else None
    )
    processed_by_user = (
        session.get(User, notification_delivery.processed_by_user_id)
        if notification_delivery.processed_by_user_id
        else None
    )
    return NotificationDeliveryResponse(
        id=notification_delivery.id,
        channel=notification_delivery.channel,
        status=notification_delivery.status,
        template_key=notification_delivery.template_key,
        recipient_user_id=notification_delivery.recipient_user_id,
        recipient_user_email=recipient_user.email if recipient_user else None,
        organization_id=notification_delivery.organization_id,
        organization_name=organization.name if organization else None,
        consent_id=notification_delivery.consent_id,
        automation_task_id=notification_delivery.automation_task_id,
        requested_by_user_id=notification_delivery.requested_by_user_id,
        requested_by_user_email=requested_by_user.email if requested_by_user else None,
        processed_by_user_id=notification_delivery.processed_by_user_id,
        processed_by_user_email=processed_by_user.email if processed_by_user else None,
        recipient_address=notification_delivery.recipient_address,
        subject_line=notification_delivery.subject_line,
        body_text=notification_delivery.body_text,
        dedupe_key=notification_delivery.dedupe_key,
        scheduled_for=notification_delivery.scheduled_for,
        started_at=notification_delivery.started_at,
        completed_at=notification_delivery.completed_at,
        sent_at=notification_delivery.sent_at,
        attempt_count=notification_delivery.attempt_count,
        last_error=notification_delivery.last_error,
        created_at=notification_delivery.created_at,
        updated_at=notification_delivery.updated_at,
    )


def get_due_boundary(
    *,
    due_before: datetime | None = None,
) -> datetime:
    return ensure_utc(due_before) if due_before else utcnow()


def get_notification_by_dedupe_key(
    *,
    session: Session,
    dedupe_key: str,
) -> NotificationDelivery | None:
    return session.exec(
        select(NotificationDelivery).where(NotificationDelivery.dedupe_key == dedupe_key)
    ).first()


def build_consent_expiry_notification_body(
    *,
    settings: Settings,
    recipient_user: User,
    organization: Organization,
    consent: TrustReportConsent,
) -> str:
    trust_url = settings.public_web_base_url.rstrip("/") + "/app/trust"
    return (
        f"Hello {recipient_user.full_name},\n\n"
        f"Your shared trust-report consent for {organization.name} is due to expire at "
        f"{ensure_utc(consent.expires_at).isoformat()}.\n\n"
        f"You can review or revoke that sharing record from your Trust Ledger workspace:\n"
        f"{trust_url}\n\n"
        f"{settings.notification_sender_name}"
    )


def queue_consent_expiry_reminder_notification(
    *,
    session: Session,
    automation_task: AutomationTask,
    consent: TrustReportConsent,
    requested_by_user: User,
    settings: Settings | None = None,
) -> NotificationDelivery:
    runtime_settings = settings or get_settings()
    recipient_user = session.get(User, consent.subject_user_id)
    organization = session.get(Organization, consent.grantee_organization_id)
    if recipient_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent reminder recipient is unavailable.",
        )
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consent reminder organization is unavailable.",
        )

    dedupe_key = f"consent-expiry-notification:{automation_task.id}"
    subject_line = "Trust report consent expires soon"
    body_text = build_consent_expiry_notification_body(
        settings=runtime_settings,
        recipient_user=recipient_user,
        organization=organization,
        consent=consent,
    )
    existing_delivery = get_notification_by_dedupe_key(session=session, dedupe_key=dedupe_key)
    current_time = utcnow()
    scheduled_for = (
        ensure_utc(automation_task.scheduled_for)
        if ensure_utc(automation_task.scheduled_for) <= current_time
        else current_time
    )
    if existing_delivery is None:
        notification_delivery = NotificationDelivery(
            channel=NotificationChannel.EMAIL,
            template_key=CONSENT_EXPIRY_TEMPLATE_KEY,
            recipient_user_id=recipient_user.id,
            organization_id=organization.id,
            consent_id=consent.id,
            automation_task_id=automation_task.id,
            requested_by_user_id=requested_by_user.id,
            recipient_address=recipient_user.email,
            subject_line=subject_line,
            body_text=body_text,
            dedupe_key=dedupe_key,
            scheduled_for=scheduled_for,
        )
    else:
        notification_delivery = existing_delivery
        notification_delivery.channel = NotificationChannel.EMAIL
        notification_delivery.template_key = CONSENT_EXPIRY_TEMPLATE_KEY
        notification_delivery.recipient_user_id = recipient_user.id
        notification_delivery.organization_id = organization.id
        notification_delivery.consent_id = consent.id
        notification_delivery.automation_task_id = automation_task.id
        notification_delivery.requested_by_user_id = requested_by_user.id
        notification_delivery.recipient_address = recipient_user.email
        notification_delivery.subject_line = subject_line
        notification_delivery.body_text = body_text
        notification_delivery.scheduled_for = scheduled_for
        notification_delivery.updated_at = current_time
        if notification_delivery.status in {
            NotificationDeliveryStatus.CANCELED,
            NotificationDeliveryStatus.FAILED,
        }:
            notification_delivery.status = NotificationDeliveryStatus.PENDING
            notification_delivery.started_at = None
            notification_delivery.completed_at = None
            notification_delivery.sent_at = None
            notification_delivery.processed_by_user_id = None
            notification_delivery.last_error = None

    session.add(notification_delivery)
    session.flush()
    append_audit_log(
        session=session,
        action_type=AuditActionType.NOTIFICATION_QUEUED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=requested_by_user.id,
        organization_id=notification_delivery.organization_id,
        subject_user_id=notification_delivery.recipient_user_id,
        target_type="notification_delivery",
        target_id=notification_delivery.id,
        details=f"Queued {notification_delivery.template_key} notification for {notification_delivery.recipient_address}.",
    )
    return notification_delivery


def claim_due_notification_deliveries(
    *,
    session: Session,
    processed_by_user: User,
    limit: int = 1,
    due_before: datetime | None = None,
) -> list[NotificationDelivery]:
    due_boundary = get_due_boundary(due_before=due_before)
    notification_deliveries = session.exec(
        select(NotificationDelivery)
        .where(
            NotificationDelivery.status == NotificationDeliveryStatus.PENDING,
            NotificationDelivery.scheduled_for <= due_boundary,
        )
        .order_by(NotificationDelivery.scheduled_for.asc(), NotificationDelivery.created_at.asc())
    ).all()[:limit]
    claimed_at = utcnow()
    claimed_deliveries: list[NotificationDelivery] = []
    for notification_delivery in notification_deliveries:
        notification_delivery.status = NotificationDeliveryStatus.PROCESSING
        notification_delivery.processed_by_user_id = processed_by_user.id
        notification_delivery.started_at = notification_delivery.started_at or claimed_at
        notification_delivery.attempt_count += 1
        notification_delivery.updated_at = claimed_at
        session.add(notification_delivery)
        claimed_deliveries.append(notification_delivery)

    session.flush()
    return claimed_deliveries


def dispatch_notification_delivery(
    *,
    session: Session,
    notification_delivery: NotificationDelivery,
    processed_by_user: User,
    settings: Settings | None = None,
) -> NotificationDelivery:
    runtime_settings = settings or get_settings()
    current_time = utcnow()
    if notification_delivery.status == NotificationDeliveryStatus.SENT:
        return notification_delivery
    if notification_delivery.status.is_final:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending or processing notifications can be dispatched.",
        )
    if notification_delivery.started_at is None:
        notification_delivery.started_at = current_time
    if notification_delivery.status != NotificationDeliveryStatus.PROCESSING:
        notification_delivery.attempt_count += 1
    notification_delivery.status = NotificationDeliveryStatus.PROCESSING
    notification_delivery.processed_by_user_id = processed_by_user.id
    notification_delivery.updated_at = current_time
    notification_delivery.last_error = None
    session.add(notification_delivery)
    session.flush()

    if runtime_settings.notification_transport == "disabled":
        notification_delivery.status = NotificationDeliveryStatus.CANCELED
        notification_delivery.completed_at = current_time
        notification_delivery.sent_at = None
        notification_delivery.updated_at = current_time
        session.add(notification_delivery)
        session.flush()
        append_audit_log(
            session=session,
            action_type=AuditActionType.NOTIFICATION_DELIVERED,
            outcome_status=AuditOutcomeStatus.CANCELED,
            actor_user_id=processed_by_user.id,
            organization_id=notification_delivery.organization_id,
            subject_user_id=notification_delivery.recipient_user_id,
            target_type="notification_delivery",
            target_id=notification_delivery.id,
            details="Notification delivery canceled because notifications are disabled in runtime settings.",
        )
        return notification_delivery

    if runtime_settings.notification_transport != "log":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported notification transport.",
        )

    notification_delivery.status = NotificationDeliveryStatus.SENT
    notification_delivery.sent_at = current_time
    notification_delivery.completed_at = current_time
    notification_delivery.updated_at = current_time
    session.add(notification_delivery)
    session.flush()
    append_audit_log(
        session=session,
        action_type=AuditActionType.NOTIFICATION_DELIVERED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=processed_by_user.id,
        organization_id=notification_delivery.organization_id,
        subject_user_id=notification_delivery.recipient_user_id,
        target_type="notification_delivery",
        target_id=notification_delivery.id,
        details=f"Notification delivered via {runtime_settings.notification_transport} transport to {notification_delivery.recipient_address}.",
    )
    return notification_delivery


def fail_notification_delivery(
    *,
    session: Session,
    notification_delivery: NotificationDelivery,
    processed_by_user: User,
    error_message: str,
) -> NotificationDelivery:
    current_time = utcnow()
    notification_delivery.status = NotificationDeliveryStatus.FAILED
    notification_delivery.processed_by_user_id = processed_by_user.id
    notification_delivery.started_at = notification_delivery.started_at or current_time
    notification_delivery.completed_at = current_time
    notification_delivery.updated_at = current_time
    notification_delivery.last_error = error_message[:500]
    session.add(notification_delivery)
    session.flush()
    append_audit_log(
        session=session,
        action_type=AuditActionType.NOTIFICATION_DELIVERED,
        outcome_status=AuditOutcomeStatus.FAILED,
        actor_user_id=processed_by_user.id,
        organization_id=notification_delivery.organization_id,
        subject_user_id=notification_delivery.recipient_user_id,
        target_type="notification_delivery",
        target_id=notification_delivery.id,
        details=f"Notification delivery failed: {notification_delivery.last_error}.",
    )
    return notification_delivery
