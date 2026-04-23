from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import DepositRecord, StoredArtifact, Tenancy, User
from app.models.common import utcnow
from app.schemas.deposit import (
    DepositAppealRequest,
    DepositCreateRequest,
    DepositDisputeRequest,
    DepositResponse,
    DepositSettlementRequest,
)
from app.services.deposits import build_deposit_response
from app.services.scoring import refresh_user_trust_score
from app.services.trust_events import append_user_event
from trustledger_domain import (
    DepositStatus,
    ScoreCalculationReason,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(prefix="/deposits", tags=["deposits"])


def get_tenancy_or_404(
    *,
    session: SessionDep,
    tenancy_id: UUID,
) -> Tenancy:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    return tenancy


def get_deposit_record_or_404(
    *,
    session: SessionDep,
    deposit_id: UUID,
) -> DepositRecord:
    deposit_record = session.get(DepositRecord, deposit_id)
    if not deposit_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit record not found.",
        )
    return deposit_record


def get_deposit_record_for_tenancy(
    *,
    session: SessionDep,
    tenancy_id: UUID,
) -> DepositRecord | None:
    return session.exec(
        select(DepositRecord).where(DepositRecord.tenancy_id == tenancy_id)
    ).first()


def ensure_tenancy_access(
    *,
    tenancy: Tenancy,
    current_user: CurrentUserDep,
    detail: str,
) -> None:
    if (
        current_user.id in {tenancy.tenant_user_id, tenancy.landlord_user_id}
        or current_user.system_role.can_manage_platform
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def append_deposit_party_events(
    *,
    session: SessionDep,
    tenancy: Tenancy,
    deposit_record: DepositRecord,
    actor_user_id: UUID,
    event_type: TrustEventType,
    summary: str,
    details: str | None = None,
) -> None:
    for subject_user_id in {tenancy.tenant_user_id, tenancy.landlord_user_id}:
        verification_status = (
            VerificationStatus.SELF_REPORTED
            if subject_user_id == actor_user_id
            else VerificationStatus.COUNTERPARTY_CONFIRMED
        )
        append_user_event(
            session=session,
            subject_user_id=subject_user_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            verification_status=verification_status,
            summary=summary,
            details=details,
            tenancy_id=tenancy.id,
            deposit_record_id=deposit_record.id,
        )


def refresh_tenancy_scores(*, session: SessionDep, tenancy: Tenancy) -> None:
    tenant_user = session.get(User, tenancy.tenant_user_id)
    landlord_user = session.get(User, tenancy.landlord_user_id)
    if tenant_user is not None:
        refresh_user_trust_score(
            session=session,
            user=tenant_user,
            calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
        )
    if landlord_user is not None:
        refresh_user_trust_score(
            session=session,
            user=landlord_user,
            calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
        )


def resolve_tenancy_artifact(
    *,
    session: SessionDep,
    tenancy: Tenancy,
    artifact_id: UUID,
    detail: str,
) -> StoredArtifact:
    stored_artifact = session.get(StoredArtifact, artifact_id)
    if stored_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored artifact not found.",
        )
    if stored_artifact.tenancy_id != tenancy.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
    return stored_artifact


@router.post("/tenancies/{tenancy_id}", response_model=DepositResponse, status_code=201)
def create_deposit_record(
    tenancy_id: UUID,
    payload: DepositCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> DepositResponse:
    tenancy = get_tenancy_or_404(session=session, tenancy_id=tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can create a deposit record.",
    )
    if tenancy.deposit_minor <= 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This tenancy does not have a recorded deposit amount.",
        )
    existing_record = get_deposit_record_for_tenancy(session=session, tenancy_id=tenancy.id)
    if existing_record:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A deposit record already exists for this tenancy.",
        )

    deposit_record = DepositRecord(
        tenancy_id=tenancy.id,
        created_by_user_id=current_user.id,
        held_amount_minor=tenancy.deposit_minor,
        currency_code=tenancy.currency_code,
        deposit_status=DepositStatus.HELD,
        move_out_date=payload.move_out_date,
        return_due_date=payload.return_due_date,
        settlement_notes=payload.settlement_notes.strip() if payload.settlement_notes else None,
    )
    session.add(deposit_record)
    session.flush()

    append_deposit_party_events(
        session=session,
        tenancy=tenancy,
        deposit_record=deposit_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_RECORDED,
        summary=f"Deposit record opened for {tenancy.property_label}.",
        details=deposit_record.settlement_notes,
    )

    session.commit()
    session.refresh(deposit_record)
    return build_deposit_response(session=session, deposit_record=deposit_record)


@router.get("/tenancies/{tenancy_id}", response_model=DepositResponse)
def get_deposit_record_by_tenancy(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> DepositResponse:
    tenancy = get_tenancy_or_404(session=session, tenancy_id=tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can view deposit records.",
    )
    deposit_record = get_deposit_record_for_tenancy(session=session, tenancy_id=tenancy.id)
    if not deposit_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit record not found.",
        )
    return build_deposit_response(session=session, deposit_record=deposit_record)


@router.post("/{deposit_id}/settlement", response_model=DepositResponse)
def submit_deposit_settlement(
    deposit_id: UUID,
    payload: DepositSettlementRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> DepositResponse:
    deposit_record = get_deposit_record_or_404(session=session, deposit_id=deposit_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=deposit_record.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can update deposit settlement.",
    )
    if current_user.id != tenancy.landlord_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the landlord can submit deposit settlement details.",
        )
    if deposit_record.deposit_status in {
        DepositStatus.DISPUTED,
        DepositStatus.UNDER_REVIEW,
        DepositStatus.VERDICT_ISSUED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deposits already in dispute or review cannot be updated here.",
        )
    if payload.proposed_return_minor + payload.withheld_amount_minor != deposit_record.held_amount_minor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Proposed return plus withheld amount must equal the held deposit amount.",
        )
    settlement_stored_artifact = None
    if payload.settlement_stored_artifact_id:
        settlement_stored_artifact = resolve_tenancy_artifact(
            session=session,
            tenancy=tenancy,
            artifact_id=payload.settlement_stored_artifact_id,
            detail="Deposit settlement artifact must belong to the same tenancy.",
        )
    settlement_artifact_name = (
        payload.settlement_artifact_name.strip() if payload.settlement_artifact_name else None
    )
    if settlement_stored_artifact is not None and settlement_artifact_name is None:
        settlement_artifact_name = settlement_stored_artifact.original_file_name
    has_settlement_artifact = any(
        value is not None
        for value in (
            payload.settlement_stored_artifact_id,
            settlement_artifact_name,
            payload.settlement_summary,
        )
    )
    if has_settlement_artifact and (
        settlement_artifact_name is None or payload.settlement_summary is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit settlement proof requires both an artifact name and a settlement summary.",
        )

    deposit_record.proposed_return_minor = payload.proposed_return_minor
    deposit_record.withheld_amount_minor = payload.withheld_amount_minor
    deposit_record.move_out_date = payload.move_out_date or deposit_record.move_out_date
    deposit_record.return_due_date = payload.return_due_date or deposit_record.return_due_date
    deposit_record.returned_at = payload.returned_at
    deposit_record.settlement_stored_artifact_id = payload.settlement_stored_artifact_id
    deposit_record.settlement_artifact_name = settlement_artifact_name
    deposit_record.settlement_summary = (
        payload.settlement_summary.strip() if payload.settlement_summary else None
    )
    deposit_record.settlement_notes = (
        payload.settlement_notes.strip() if payload.settlement_notes else None
    )
    deposit_record.counterparty_action_by_user_id = current_user.id
    deposit_record.counterparty_action_at = utcnow()
    deposit_record.dispute_notes = None
    deposit_record.disputed_by_user_id = None
    deposit_record.disputed_at = None
    deposit_record.review_requested_by_user_id = None
    deposit_record.review_requested_at = None
    deposit_record.reviewed_by_user_id = None
    deposit_record.reviewed_at = None
    deposit_record.verdict_outcome = None
    deposit_record.verdict_summary = None
    deposit_record.verdict_tenant_score_delta = 0
    deposit_record.verdict_landlord_score_delta = 0
    deposit_record.appeal_requested_by_user_id = None
    deposit_record.appeal_requested_at = None
    deposit_record.appeal_notes = None
    if payload.withheld_amount_minor > 0:
        deposit_record.deposit_status = DepositStatus.PARTIALLY_WITHHELD
    elif payload.returned_at is not None:
        deposit_record.deposit_status = DepositStatus.RETURNED
    else:
        deposit_record.deposit_status = DepositStatus.RETURN_SUBMITTED
    deposit_record.updated_at = utcnow()
    session.add(deposit_record)

    append_deposit_party_events(
        session=session,
        tenancy=tenancy,
        deposit_record=deposit_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_SETTLEMENT_SUBMITTED,
        summary=f"Deposit settlement submitted for {tenancy.property_label}.",
        details=deposit_record.settlement_notes or deposit_record.settlement_summary,
    )

    session.commit()
    session.refresh(deposit_record)
    return build_deposit_response(session=session, deposit_record=deposit_record)


@router.post("/{deposit_id}/dispute", response_model=DepositResponse)
def dispute_deposit_record(
    deposit_id: UUID,
    payload: DepositDisputeRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> DepositResponse:
    deposit_record = get_deposit_record_or_404(session=session, deposit_id=deposit_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=deposit_record.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can dispute deposit settlement.",
    )
    if current_user.id != tenancy.tenant_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the tenant can dispute deposit settlement here.",
        )
    if deposit_record.deposit_status not in {
        DepositStatus.RETURN_SUBMITTED,
        DepositStatus.RETURNED,
        DepositStatus.PARTIALLY_WITHHELD,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Deposit settlement must exist before it can be disputed.",
        )

    deposit_record.deposit_status = DepositStatus.DISPUTED
    deposit_record.dispute_notes = payload.dispute_notes.strip()
    deposit_record.disputed_by_user_id = current_user.id
    deposit_record.disputed_at = utcnow()
    deposit_record.review_requested_by_user_id = current_user.id
    deposit_record.review_requested_at = deposit_record.disputed_at
    deposit_record.reviewed_by_user_id = None
    deposit_record.reviewed_at = None
    deposit_record.verdict_outcome = None
    deposit_record.verdict_summary = None
    deposit_record.verdict_tenant_score_delta = 0
    deposit_record.verdict_landlord_score_delta = 0
    deposit_record.appeal_requested_by_user_id = None
    deposit_record.appeal_requested_at = None
    deposit_record.appeal_notes = None
    deposit_record.updated_at = utcnow()
    session.add(deposit_record)

    append_deposit_party_events(
        session=session,
        tenancy=tenancy,
        deposit_record=deposit_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_DISPUTED,
        summary=f"Deposit settlement disputed for {tenancy.property_label}.",
        details=deposit_record.dispute_notes,
    )
    append_deposit_party_events(
        session=session,
        tenancy=tenancy,
        deposit_record=deposit_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_REVIEW_REQUESTED,
        summary=f"Deposit dispute sent to review for {tenancy.property_label}.",
        details=deposit_record.dispute_notes,
    )

    session.commit()
    session.refresh(deposit_record)
    return build_deposit_response(session=session, deposit_record=deposit_record)


@router.post("/{deposit_id}/appeal", response_model=DepositResponse)
def appeal_deposit_verdict(
    deposit_id: UUID,
    payload: DepositAppealRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> DepositResponse:
    deposit_record = get_deposit_record_or_404(session=session, deposit_id=deposit_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=deposit_record.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can appeal deposit verdicts.",
    )
    if deposit_record.deposit_status != DepositStatus.VERDICT_ISSUED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only issued deposit verdicts can be appealed.",
        )
    if deposit_record.appeal_requested_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This deposit verdict already has an appeal on record.",
        )

    deposit_record.deposit_status = DepositStatus.UNDER_REVIEW
    deposit_record.appeal_requested_by_user_id = current_user.id
    deposit_record.appeal_requested_at = utcnow()
    deposit_record.appeal_notes = payload.appeal_notes.strip()
    deposit_record.review_requested_by_user_id = current_user.id
    deposit_record.review_requested_at = deposit_record.appeal_requested_at
    deposit_record.reviewed_by_user_id = None
    deposit_record.reviewed_at = None
    deposit_record.updated_at = utcnow()
    session.add(deposit_record)

    append_deposit_party_events(
        session=session,
        tenancy=tenancy,
        deposit_record=deposit_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_APPEALED,
        summary=f"Deposit verdict appealed for {tenancy.property_label}.",
        details=deposit_record.appeal_notes,
    )
    append_deposit_party_events(
        session=session,
        tenancy=tenancy,
        deposit_record=deposit_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_REVIEW_REQUESTED,
        summary=f"Deposit appeal sent to review for {tenancy.property_label}.",
        details=deposit_record.appeal_notes,
    )
    refresh_tenancy_scores(session=session, tenancy=tenancy)

    session.commit()
    session.refresh(deposit_record)
    return build_deposit_response(session=session, deposit_record=deposit_record)
