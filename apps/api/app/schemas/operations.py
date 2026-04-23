from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.worker_run import WorkerRunResponse


class InternalOperationsOverviewResponse(BaseModel):
    pending_tenancy_review_count: int
    pending_evidence_review_count: int
    pending_history_import_review_count: int
    pending_deposit_dispute_count: int
    pending_payment_dispute_count: int
    pending_maintenance_dispute_count: int
    pending_automation_task_count: int
    due_automation_task_count: int
    pending_notification_count: int
    due_notification_count: int
    failed_notification_count: int
    pending_score_request_count: int
    processing_score_request_count: int
    due_score_request_count: int
    running_worker_run_count: int
    failed_worker_run_count: int
    latest_worker_run: WorkerRunResponse | None
    environment: str
    database_backend: str
    artifact_storage_backend: str
    worker_coordination_backend: str
    notification_transport: str
    generated_at: datetime
