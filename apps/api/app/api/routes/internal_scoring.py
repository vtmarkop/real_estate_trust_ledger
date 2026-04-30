from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select

from app.api.deps import SessionDep, require_system_roles
from app.models import (
    Organization,
    TrustScoreHistory,
    TrustScoreRecalculationBatch,
    TrustScoreRecalculationRequest,
    User,
)
from app.schemas.score import (
    TrustScoreRecalculationDirectCreateRequest,
    TrustScoreHistoryResponse,
    TrustScoreRecalculationBatchCreateRequest,
    TrustScoreRecalculationBatchResponse,
    TrustScoreRecalculationRequestResponse,
    TrustScoreSummaryResponse,
)
from app.services.scoring import (
    build_score_recalculation_batch_response,
    build_score_recalculation_request_response,
    build_trust_score_history_response,
    build_trust_score_summary_response,
    calculate_user_trust_scores,
    create_score_recalculation_batch,
    create_user_score_recalculation_request,
    process_score_recalculation_request,
)
from trustledger_domain import (
    ScoreCalculationReason,
    ScoreRecalculationStatus,
    ScoreRecalculationScope,
    SystemRole,
)


router = APIRouter(prefix="/internal/scoring", tags=["internal-scoring"])


def get_scoring_user_or_404(
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


def resolve_scoring_user(
    *,
    session: SessionDep,
    user_id: UUID | None,
    user_email: str | None,
) -> User:
    scoring_user = get_scoring_user_or_404(session=session, user_id=user_id) if user_id is not None else None
    if user_email is not None:
        email_match = session.exec(
            select(User).where(User.email == user_email.lower().strip())
        ).first()
        if user_id is not None and email_match and email_match.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="user_id and user_email refer to different users.",
            )
        if email_match is None or not email_match.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        scoring_user = scoring_user or email_match

    if scoring_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )
    return scoring_user


def get_scoring_request_or_404(
    *,
    session: SessionDep,
    request_id: UUID,
) -> TrustScoreRecalculationRequest:
    request = session.get(TrustScoreRecalculationRequest, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score recalculation request not found.",
        )
    return request


def get_scoring_batch_or_404(
    *,
    session: SessionDep,
    batch_id: UUID,
) -> TrustScoreRecalculationBatch:
    batch = session.get(TrustScoreRecalculationBatch, batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Score recalculation batch not found.",
        )
    return batch


def get_scoring_organization_or_404(
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


def parse_score_recalculation_scope(scope_type: str) -> ScoreRecalculationScope:
    try:
        return ScoreRecalculationScope(scope_type)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported score recalculation scope.",
        ) from exc


@router.post(
    "/requests",
    response_model=TrustScoreRecalculationRequestResponse,
    status_code=201,
)
def create_direct_score_recalculation_request(
    payload: TrustScoreRecalculationDirectCreateRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreRecalculationRequestResponse:
    user = resolve_scoring_user(
        session=session,
        user_id=payload.user_id,
        user_email=payload.user_email,
    )
    request = create_user_score_recalculation_request(
        session=session,
        user=user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
        requested_by_user=current_user,
        scheduled_for=payload.scheduled_for,
    )
    session.commit()
    session.refresh(request)
    return build_score_recalculation_request_response(recalculation_request=request)


@router.get(
    "/requests",
    response_model=list[TrustScoreRecalculationRequestResponse],
)
def list_score_recalculation_requests(
    session: SessionDep,
    status_filter: ScoreRecalculationStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> list[TrustScoreRecalculationRequestResponse]:
    query = select(TrustScoreRecalculationRequest)
    if status_filter is not None:
        query = query.where(TrustScoreRecalculationRequest.status == status_filter)
    requests = session.exec(
        query.order_by(
            TrustScoreRecalculationRequest.scheduled_for.asc(),
            TrustScoreRecalculationRequest.created_at.desc(),
        )
    ).all()[:limit]
    return [
        build_score_recalculation_request_response(recalculation_request=request)
        for request in requests
    ]


@router.get(
    "/batches",
    response_model=list[TrustScoreRecalculationBatchResponse],
)
def list_score_recalculation_batches(
    session: SessionDep,
    status_filter: ScoreRecalculationStatus | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> list[TrustScoreRecalculationBatchResponse]:
    query = select(TrustScoreRecalculationBatch)
    if status_filter is not None:
        query = query.where(TrustScoreRecalculationBatch.status == status_filter)
    batches = session.exec(
        query.order_by(
            TrustScoreRecalculationBatch.scheduled_for.desc(),
            TrustScoreRecalculationBatch.created_at.desc(),
        )
    ).all()[:limit]
    return [
        build_score_recalculation_batch_response(session=session, batch=batch)
        for batch in batches
    ]


@router.post(
    "/users/{user_id}/requests",
    response_model=TrustScoreRecalculationRequestResponse,
    status_code=201,
)
def create_user_score_recalculation_request_endpoint(
    user_id: UUID,
    session: SessionDep,
    scheduled_for: datetime | None = None,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreRecalculationRequestResponse:
    user = get_scoring_user_or_404(session=session, user_id=user_id)
    request = create_user_score_recalculation_request(
        session=session,
        user=user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
        requested_by_user=current_user,
        scheduled_for=scheduled_for,
    )
    session.commit()
    session.refresh(request)
    return build_score_recalculation_request_response(recalculation_request=request)


@router.get(
    "/requests/{request_id}",
    response_model=TrustScoreRecalculationRequestResponse,
)
def get_user_score_recalculation_request(
    request_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreRecalculationRequestResponse:
    request = get_scoring_request_or_404(session=session, request_id=request_id)
    return build_score_recalculation_request_response(recalculation_request=request)


@router.post(
    "/requests/{request_id}/process",
    response_model=TrustScoreRecalculationRequestResponse,
)
def process_user_score_recalculation_request(
    request_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreRecalculationRequestResponse:
    request = get_scoring_request_or_404(session=session, request_id=request_id)
    processed_request = process_score_recalculation_request(
        session=session,
        recalculation_request=request,
        processed_by_user=current_user,
    )
    session.commit()
    session.refresh(processed_request)
    return build_score_recalculation_request_response(recalculation_request=processed_request)


@router.post(
    "/batches",
    response_model=TrustScoreRecalculationBatchResponse,
    status_code=201,
)
def create_score_recalculation_batch_endpoint(
    payload: TrustScoreRecalculationBatchCreateRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreRecalculationBatchResponse:
    scope_type = parse_score_recalculation_scope(payload.scope_type)
    organization = None
    if scope_type == ScoreRecalculationScope.ORGANIZATION_MEMBERS:
        if payload.organization_id is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="organization_id is required for organization member batches.",
            )
        organization = get_scoring_organization_or_404(
            session=session,
            organization_id=payload.organization_id,
        )
    elif payload.organization_id is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="organization_id is only valid for organization member batches.",
        )

    batch, _requests = create_score_recalculation_batch(
        session=session,
        scope_type=scope_type,
        requested_by_user=current_user,
        organization=organization,
        scheduled_for=payload.scheduled_for,
    )
    session.commit()
    session.refresh(batch)
    return build_score_recalculation_batch_response(session=session, batch=batch)


@router.get(
    "/batches/{batch_id}",
    response_model=TrustScoreRecalculationBatchResponse,
)
def get_score_recalculation_batch(
    batch_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreRecalculationBatchResponse:
    batch = get_scoring_batch_or_404(session=session, batch_id=batch_id)
    return build_score_recalculation_batch_response(session=session, batch=batch)


@router.post(
    "/recalculate",
    response_model=TrustScoreSummaryResponse,
)
def recalculate_user_trust_score_direct(
    payload: TrustScoreRecalculationDirectCreateRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreSummaryResponse:
    user = resolve_scoring_user(
        session=session,
        user_id=payload.user_id,
        user_email=payload.user_email,
    )
    request = create_user_score_recalculation_request(
        session=session,
        user=user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
        requested_by_user=current_user,
        scheduled_for=payload.scheduled_for,
    )
    process_score_recalculation_request(
        session=session,
        recalculation_request=request,
        processed_by_user=current_user,
    )
    session.commit()
    computation = calculate_user_trust_scores(session=session, user=user)
    return build_trust_score_summary_response(computation=computation)


@router.post(
    "/users/{user_id}/recalculate",
    response_model=TrustScoreSummaryResponse,
)
def recalculate_user_trust_score(
    user_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> TrustScoreSummaryResponse:
    user = get_scoring_user_or_404(session=session, user_id=user_id)
    request = create_user_score_recalculation_request(
        session=session,
        user=user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
        requested_by_user=current_user,
    )
    process_score_recalculation_request(
        session=session,
        recalculation_request=request,
        processed_by_user=current_user,
    )
    session.commit()
    computation = calculate_user_trust_scores(session=session, user=user)
    return build_trust_score_summary_response(computation=computation)


@router.get(
    "/users/{user_id}/history",
    response_model=list[TrustScoreHistoryResponse],
)
def list_user_trust_score_history(
    user_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> list[TrustScoreHistoryResponse]:
    user = get_scoring_user_or_404(session=session, user_id=user_id)
    history_entries = session.exec(
        select(TrustScoreHistory)
        .where(TrustScoreHistory.user_id == user.id)
        .order_by(TrustScoreHistory.calculated_at.desc())
    ).all()
    return [
        build_trust_score_history_response(history_entry=history_entry)
        for history_entry in history_entries
    ]
