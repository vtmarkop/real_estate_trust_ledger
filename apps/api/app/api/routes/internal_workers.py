from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select

from app.api.deps import SessionDep, require_system_roles
from app.models import WorkerRun
from app.schemas.worker_run import WorkerRunResponse
from app.services.worker_runs import build_worker_run_response
from trustledger_domain import SystemRole, WorkerRunStatus


router = APIRouter(prefix="/internal/workers", tags=["internal-workers"])


def get_worker_run_or_404(
    *,
    session: SessionDep,
    worker_run_id: UUID,
) -> WorkerRun:
    worker_run = session.get(WorkerRun, worker_run_id)
    if not worker_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Worker run not found.",
        )
    return worker_run


@router.get(
    "/runs",
    response_model=list[WorkerRunResponse],
)
def list_worker_runs(
    session: SessionDep,
    status_filter: WorkerRunStatus | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> list[WorkerRunResponse]:
    query = select(WorkerRun)
    if status_filter is not None:
        query = query.where(WorkerRun.status == status_filter)

    worker_runs = session.exec(
        query.order_by(WorkerRun.run_started_at.desc(), WorkerRun.created_at.desc())
    ).all()[:limit]
    return [
        build_worker_run_response(session=session, worker_run=worker_run)
        for worker_run in worker_runs
    ]


@router.get(
    "/runs/{worker_run_id}",
    response_model=WorkerRunResponse,
)
def get_worker_run(
    worker_run_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> WorkerRunResponse:
    worker_run = get_worker_run_or_404(session=session, worker_run_id=worker_run_id)
    return build_worker_run_response(session=session, worker_run=worker_run)
