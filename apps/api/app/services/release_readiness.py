from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.config import DEV_SECRET_KEY, Settings
from app.models import NotificationDelivery, WorkerRun
from app.models.common import utcnow
from app.schemas.release import (
    ReleaseReadinessCheckResponse,
    ReleaseReadinessResponse,
)
from trustledger_domain import NotificationDeliveryStatus, WorkerRunStatus


@dataclass(frozen=True)
class ReleaseCheck:
    key: str
    label: str
    status: str
    detail: str


def build_release_readiness(
    *,
    session: Session,
    settings: Settings,
) -> ReleaseReadinessResponse:
    latest_worker_run = session.exec(
        select(WorkerRun).order_by(WorkerRun.run_started_at.desc(), WorkerRun.created_at.desc())
    ).first()
    failed_worker_run_count = _count_scalar(
        session,
        select(func.count())
        .select_from(WorkerRun)
        .where(WorkerRun.status == WorkerRunStatus.FAILED),
    )
    failed_notification_count = _count_scalar(
        session,
        select(func.count())
        .select_from(NotificationDelivery)
        .where(NotificationDelivery.status == NotificationDeliveryStatus.FAILED),
    )

    checks = [
        _check_environment(settings=settings),
        _check_secret_key(settings=settings),
        _check_secure_cookie(settings=settings),
        _check_public_urls(settings=settings),
        _check_database_backend(settings=settings),
        _check_worker_coordination(settings=settings),
        _check_notification_transport(settings=settings),
        _check_latest_worker_run(latest_worker_run=latest_worker_run),
        _check_failed_worker_runs(failed_worker_run_count=failed_worker_run_count),
        _check_failed_notifications(failed_notification_count=failed_notification_count),
    ]

    blocking_issue_count = sum(1 for check in checks if check.status == "fail")
    warning_count = sum(1 for check in checks if check.status == "warning")

    return ReleaseReadinessResponse(
        status="ready" if blocking_issue_count == 0 else "needs_attention",
        environment=settings.app_env,
        public_api_base_url=settings.public_api_base_url,
        public_web_base_url=settings.public_web_base_url,
        blocking_issue_count=blocking_issue_count,
        warning_count=warning_count,
        checks=[
            ReleaseReadinessCheckResponse(
                key=check.key,
                label=check.label,
                status=check.status,
                detail=check.detail,
            )
            for check in checks
        ],
        generated_at=utcnow(),
    )


def _count_scalar(session: Session, statement) -> int:
    return int(session.exec(statement).one())


def _check_environment(*, settings: Settings) -> ReleaseCheck:
    if settings.app_env in {"staging", "production"}:
        return ReleaseCheck(
            key="environment",
            label="Runtime environment",
            status="pass",
            detail=f"Environment is '{settings.app_env}', which is valid for hosted rehearsal.",
        )
    return ReleaseCheck(
        key="environment",
        label="Runtime environment",
        status="fail",
        detail="Hosted pilot rehearsal should run in staging or production mode, not development.",
    )


def _check_secret_key(*, settings: Settings) -> ReleaseCheck:
    if settings.secret_key != DEV_SECRET_KEY and len(settings.secret_key) >= 32:
        return ReleaseCheck(
            key="secret_key",
            label="Secret key hygiene",
            status="pass",
            detail="Secret key is non-default and long enough for hosted use.",
        )
    return ReleaseCheck(
        key="secret_key",
        label="Secret key hygiene",
        status="fail",
        detail="Replace the development secret key with a long environment-managed secret before pilot hosting.",
    )


def _check_secure_cookie(*, settings: Settings) -> ReleaseCheck:
    if settings.cookie_secure:
        return ReleaseCheck(
            key="secure_cookie",
            label="Secure session cookies",
            status="pass",
            detail="Session cookie is marked secure.",
        )
    return ReleaseCheck(
        key="secure_cookie",
        label="Secure session cookies",
        status="fail",
        detail="Set TRUST_LEDGER_COOKIE_SECURE=true before internet-facing deployment.",
    )


def _check_public_urls(*, settings: Settings) -> ReleaseCheck:
    api_url = urlparse(settings.public_api_base_url)
    web_url = urlparse(settings.public_web_base_url)
    if api_url.scheme == "https" and web_url.scheme == "https":
        return ReleaseCheck(
            key="public_urls",
            label="Public HTTPS URLs",
            status="pass",
            detail="Public API and web URLs both use HTTPS.",
        )
    return ReleaseCheck(
        key="public_urls",
        label="Public HTTPS URLs",
        status="fail",
        detail="Hosted pilot cutover requires HTTPS public API and web base URLs.",
    )


def _check_database_backend(*, settings: Settings) -> ReleaseCheck:
    if settings.database_url.startswith("postgresql"):
        return ReleaseCheck(
            key="database_backend",
            label="Primary database backend",
            status="pass",
            detail="Runtime is pointed at PostgreSQL.",
        )
    return ReleaseCheck(
        key="database_backend",
        label="Primary database backend",
        status="fail",
        detail="SQLite is still configured. Use PostgreSQL for staging and pilot hosting.",
    )


def _check_worker_coordination(*, settings: Settings) -> ReleaseCheck:
    if settings.resolved_worker_coordination_backend == "redis":
        return ReleaseCheck(
            key="worker_coordination",
            label="Worker coordination",
            status="pass",
            detail="Redis-backed worker coordination is enabled.",
        )
    return ReleaseCheck(
        key="worker_coordination",
        label="Worker coordination",
        status="fail",
        detail="Hosted worker execution should use Redis-backed coordination before pilot launch.",
    )


def _check_notification_transport(*, settings: Settings) -> ReleaseCheck:
    if settings.notification_transport == "disabled":
        return ReleaseCheck(
            key="notification_transport",
            label="Notification transport",
            status="fail",
            detail="Notifications are disabled. Pilot users need at least an auditable transport path.",
        )
    if settings.notification_transport == "log":
        return ReleaseCheck(
            key="notification_transport",
            label="Notification transport",
            status="warning",
            detail="Notifications still terminate in structured logs. Add a real provider before wider pilot rollout.",
        )
    return ReleaseCheck(
        key="notification_transport",
        label="Notification transport",
        status="pass",
        detail=f"Notification transport '{settings.notification_transport}' is enabled.",
    )


def _check_latest_worker_run(*, latest_worker_run: WorkerRun | None) -> ReleaseCheck:
    if latest_worker_run is None:
        return ReleaseCheck(
            key="latest_worker_run",
            label="Latest worker execution",
            status="warning",
            detail="No worker run has been recorded yet in this environment.",
        )
    if latest_worker_run.status == WorkerRunStatus.COMPLETED:
        return ReleaseCheck(
            key="latest_worker_run",
            label="Latest worker execution",
            status="pass",
            detail="The latest recorded worker cycle completed successfully.",
        )
    if latest_worker_run.status == WorkerRunStatus.RUNNING:
        return ReleaseCheck(
            key="latest_worker_run",
            label="Latest worker execution",
            status="warning",
            detail="A worker cycle is currently running; verify it completes cleanly before cutover.",
        )
    return ReleaseCheck(
        key="latest_worker_run",
        label="Latest worker execution",
        status="fail",
        detail="The latest recorded worker cycle failed. Investigate before pilot cutover.",
    )


def _check_failed_worker_runs(*, failed_worker_run_count: int) -> ReleaseCheck:
    if failed_worker_run_count == 0:
        return ReleaseCheck(
            key="failed_worker_runs",
            label="Failed worker backlog",
            status="pass",
            detail="No failed worker runs are currently recorded.",
        )
    return ReleaseCheck(
        key="failed_worker_runs",
        label="Failed worker backlog",
        status="warning",
        detail=f"{failed_worker_run_count} failed worker runs are still recorded for follow-up.",
    )


def _check_failed_notifications(*, failed_notification_count: int) -> ReleaseCheck:
    if failed_notification_count == 0:
        return ReleaseCheck(
            key="failed_notifications",
            label="Failed notifications",
            status="pass",
            detail="No failed notification deliveries are currently recorded.",
        )
    return ReleaseCheck(
        key="failed_notifications",
        label="Failed notifications",
        status="warning",
        detail=f"{failed_notification_count} failed notification deliveries need operational review.",
    )
