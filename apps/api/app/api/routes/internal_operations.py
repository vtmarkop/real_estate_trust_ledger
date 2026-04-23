from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlmodel import select

from app.api.deps import SessionDep, SettingsDep, require_system_roles
from app.models import (
    AutomationTask,
    DepositRecord,
    EvidenceDocument,
    HistoryImport,
    MaintenanceTicket,
    NotificationDelivery,
    Tenancy,
    TrustScoreRecalculationRequest,
    WorkerRun,
    PaymentRecord,
)
from app.models.common import utcnow
from app.schemas.operations import InternalOperationsOverviewResponse
from app.services.worker_runs import build_worker_run_response
from trustledger_domain import (
    AutomationTaskStatus,
    DepositStatus,
    EvidenceReviewStatus,
    HistoryImportStatus,
    MaintenanceTicketStatus,
    NotificationDeliveryStatus,
    PaymentRecordStatus,
    ScoreRecalculationStatus,
    SystemRole,
    WorkerRunStatus,
)


router = APIRouter(prefix="/internal/operations", tags=["internal-operations"])


def count_scalar(session: SessionDep, statement) -> int:
    return int(session.exec(statement).one())


@router.get(
    "/overview",
    response_model=InternalOperationsOverviewResponse,
)
def get_internal_operations_overview(
    session: SessionDep,
    settings: SettingsDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> InternalOperationsOverviewResponse:
    now = utcnow()

    pending_tenancy_review_count = count_scalar(
        session,
        select(func.count())
        .select_from(Tenancy)
        .where(
            Tenancy.review_requested_at.is_not(None),
            Tenancy.reviewed_at.is_(None),
        ),
    )
    pending_evidence_review_count = count_scalar(
        session,
        select(func.count())
        .select_from(EvidenceDocument)
        .where(
            EvidenceDocument.review_status == EvidenceReviewStatus.SUBMITTED,
            EvidenceDocument.reviewed_at.is_(None),
        ),
    )
    pending_history_import_review_count = count_scalar(
        session,
        select(func.count())
        .select_from(HistoryImport)
        .where(
            HistoryImport.status == HistoryImportStatus.SUBMITTED,
            HistoryImport.reviewed_at.is_(None),
        ),
    )
    pending_deposit_dispute_count = count_scalar(
        session,
        select(func.count())
        .select_from(DepositRecord)
        .where(DepositRecord.deposit_status.in_([DepositStatus.DISPUTED, DepositStatus.UNDER_REVIEW])),
    )
    pending_payment_dispute_count = count_scalar(
        session,
        select(func.count())
        .select_from(PaymentRecord)
        .where(PaymentRecord.payment_status.in_([PaymentRecordStatus.DISPUTED, PaymentRecordStatus.UNDER_REVIEW])),
    )
    pending_maintenance_dispute_count = count_scalar(
        session,
        select(func.count())
        .select_from(MaintenanceTicket)
        .where(
            MaintenanceTicket.ticket_status.in_(
                [MaintenanceTicketStatus.DISPUTED, MaintenanceTicketStatus.UNDER_REVIEW]
            )
        ),
    )
    pending_automation_task_count = count_scalar(
        session,
        select(func.count())
        .select_from(AutomationTask)
        .where(AutomationTask.status == AutomationTaskStatus.PENDING),
    )
    due_automation_task_count = count_scalar(
        session,
        select(func.count())
        .select_from(AutomationTask)
        .where(
            AutomationTask.status == AutomationTaskStatus.PENDING,
            AutomationTask.scheduled_for <= now,
        ),
    )
    pending_notification_count = count_scalar(
        session,
        select(func.count())
        .select_from(NotificationDelivery)
        .where(NotificationDelivery.status == NotificationDeliveryStatus.PENDING),
    )
    due_notification_count = count_scalar(
        session,
        select(func.count())
        .select_from(NotificationDelivery)
        .where(
            NotificationDelivery.status == NotificationDeliveryStatus.PENDING,
            NotificationDelivery.scheduled_for <= now,
        ),
    )
    failed_notification_count = count_scalar(
        session,
        select(func.count())
        .select_from(NotificationDelivery)
        .where(NotificationDelivery.status == NotificationDeliveryStatus.FAILED),
    )
    pending_score_request_count = count_scalar(
        session,
        select(func.count())
        .select_from(TrustScoreRecalculationRequest)
        .where(TrustScoreRecalculationRequest.status == ScoreRecalculationStatus.PENDING),
    )
    processing_score_request_count = count_scalar(
        session,
        select(func.count())
        .select_from(TrustScoreRecalculationRequest)
        .where(TrustScoreRecalculationRequest.status == ScoreRecalculationStatus.PROCESSING),
    )
    due_score_request_count = count_scalar(
        session,
        select(func.count())
        .select_from(TrustScoreRecalculationRequest)
        .where(
            TrustScoreRecalculationRequest.status == ScoreRecalculationStatus.PENDING,
            TrustScoreRecalculationRequest.scheduled_for <= now,
        ),
    )
    running_worker_run_count = count_scalar(
        session,
        select(func.count())
        .select_from(WorkerRun)
        .where(WorkerRun.status == WorkerRunStatus.RUNNING),
    )
    failed_worker_run_count = count_scalar(
        session,
        select(func.count())
        .select_from(WorkerRun)
        .where(WorkerRun.status == WorkerRunStatus.FAILED),
    )
    latest_worker_run = session.exec(
        select(WorkerRun).order_by(WorkerRun.run_started_at.desc(), WorkerRun.created_at.desc())
    ).first()

    return InternalOperationsOverviewResponse(
        pending_tenancy_review_count=pending_tenancy_review_count,
        pending_evidence_review_count=pending_evidence_review_count,
        pending_history_import_review_count=pending_history_import_review_count,
        pending_deposit_dispute_count=pending_deposit_dispute_count,
        pending_payment_dispute_count=pending_payment_dispute_count,
        pending_maintenance_dispute_count=pending_maintenance_dispute_count,
        pending_automation_task_count=pending_automation_task_count,
        due_automation_task_count=due_automation_task_count,
        pending_notification_count=pending_notification_count,
        due_notification_count=due_notification_count,
        failed_notification_count=failed_notification_count,
        pending_score_request_count=pending_score_request_count,
        processing_score_request_count=processing_score_request_count,
        due_score_request_count=due_score_request_count,
        running_worker_run_count=running_worker_run_count,
        failed_worker_run_count=failed_worker_run_count,
        latest_worker_run=(
            build_worker_run_response(session=session, worker_run=latest_worker_run)
            if latest_worker_run
            else None
        ),
        environment=settings.app_env,
        database_backend="sqlite" if settings.database_url.startswith("sqlite") else "postgresql",
        artifact_storage_backend=settings.artifact_storage_backend,
        worker_coordination_backend=settings.resolved_worker_coordination_backend,
        notification_transport=settings.notification_transport,
        generated_at=now,
    )
