from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import PaymentRecord, StoredArtifact, Tenancy, User
from app.models.common import utcnow
from app.schemas.payment import (
    PaymentAppealRequest,
    PaymentCreateRequest,
    PaymentDecisionRequest,
    PaymentDisputeRequest,
    PaymentProofSubmitRequest,
    PaymentResponse,
)
from app.services.payments import build_payment_response
from app.services.scoring import refresh_user_trust_score
from app.services.trust_events import append_user_event
from trustledger_domain import (
    PaymentProofStatus,
    PaymentRecordStatus,
    ScoreCalculationReason,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(prefix="/payments", tags=["payments"])


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


def get_payment_or_404(
    *,
    session: SessionDep,
    payment_id: UUID,
) -> PaymentRecord:
    payment_record = session.get(PaymentRecord, payment_id)
    if not payment_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found.",
        )
    return payment_record


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


def append_payment_party_events(
    *,
    session: SessionDep,
    tenancy: Tenancy,
    payment_record: PaymentRecord,
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
            payment_record_id=payment_record.id,
        )


def ensure_payment_users(
    *,
    session: SessionDep,
    tenancy: Tenancy,
    payer_user_id: UUID,
    payee_user_id: UUID,
) -> tuple[User, User]:
    if payer_user_id == payee_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payer and payee must be different users.",
        )
    allowed_user_ids = {tenancy.tenant_user_id, tenancy.landlord_user_id}
    if payer_user_id not in allowed_user_ids or payee_user_id not in allowed_user_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment parties must match tenancy participants.",
        )

    payer_user = session.get(User, payer_user_id)
    payee_user = session.get(User, payee_user_id)
    if not payer_user or not payer_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payer user not found.",
        )
    if not payee_user or not payee_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payee user not found.",
        )
    return payer_user, payee_user


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


@router.post("/tenancies/{tenancy_id}", response_model=PaymentResponse, status_code=201)
def create_payment_record(
    tenancy_id: UUID,
    payload: PaymentCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> PaymentResponse:
    tenancy = get_tenancy_or_404(session=session, tenancy_id=tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can create payment records.",
    )

    if payload.period_end_date and payload.period_start_date and payload.period_end_date < payload.period_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment period end date cannot be before the start date.",
        )

    payer_user, payee_user = ensure_payment_users(
        session=session,
        tenancy=tenancy,
        payer_user_id=payload.payer_user_id,
        payee_user_id=payload.payee_user_id,
    )
    if current_user.id not in {payer_user.id, payee_user.id}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the payer or payee can create a payment record.",
        )

    proof_stored_artifact = None
    if payload.proof_stored_artifact_id:
        proof_stored_artifact = resolve_tenancy_artifact(
            session=session,
            tenancy=tenancy,
            artifact_id=payload.proof_stored_artifact_id,
            detail="Payment proof artifact must belong to the same tenancy.",
        )
    proof_artifact_name = payload.proof_artifact_name.strip() if payload.proof_artifact_name else None
    if proof_stored_artifact is not None and proof_artifact_name is None:
        proof_artifact_name = proof_stored_artifact.original_file_name
    proof_summary = payload.proof_summary.strip() if payload.proof_summary else None
    has_proof_payload = any(
        value is not None
        for value in (
            payload.proof_stored_artifact_id,
            proof_artifact_name,
            proof_summary,
        )
    )
    if has_proof_payload and (proof_artifact_name is None or proof_summary is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment proof requires both an artifact name and a proof summary.",
        )
    if payload.paid_at and not has_proof_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment proof is required when paid_at is supplied.",
        )
    if current_user.id == payee_user.id and has_proof_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only the payer can attach payment proof.",
        )

    payment_status = PaymentRecordStatus.PENDING
    proof_status = PaymentProofStatus.NONE
    if current_user.id == payer_user.id and has_proof_payload:
        payment_status = PaymentRecordStatus.SUBMITTED
        proof_status = PaymentProofStatus.PROVIDED

    payment_record = PaymentRecord(
        tenancy_id=tenancy.id,
        payer_user_id=payer_user.id,
        payee_user_id=payee_user.id,
        created_by_user_id=current_user.id,
        payment_type=payload.payment_type,
        payment_status=payment_status,
        proof_status=proof_status,
        amount_minor=payload.amount_minor,
        currency_code=payload.currency_code.strip().upper(),
        due_date=payload.due_date,
        period_start_date=payload.period_start_date,
        period_end_date=payload.period_end_date,
        paid_at=payload.paid_at,
        proof_stored_artifact_id=payload.proof_stored_artifact_id,
        proof_artifact_name=proof_artifact_name,
        proof_summary=proof_summary,
        external_reference=payload.external_reference.strip() if payload.external_reference else None,
    )
    session.add(payment_record)
    session.flush()

    append_payment_party_events(
        session=session,
        tenancy=tenancy,
        payment_record=payment_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_CREATED,
        summary=f"{payload.payment_type.value.replace('_', ' ').title()} payment recorded for {tenancy.property_label}.",
        details=f"Amount: {payment_record.amount_minor} {payment_record.currency_code}.",
    )
    if has_proof_payload:
        append_payment_party_events(
            session=session,
            tenancy=tenancy,
            payment_record=payment_record,
            actor_user_id=current_user.id,
            event_type=TrustEventType.PAYMENT_PROOF_SUBMITTED,
            summary=f"Payment proof submitted for {tenancy.property_label}.",
            details=proof_summary,
        )

    session.commit()
    session.refresh(payment_record)
    return build_payment_response(session=session, payment_record=payment_record)


@router.get("/tenancies/{tenancy_id}", response_model=list[PaymentResponse])
def list_tenancy_payments(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[PaymentResponse]:
    tenancy = get_tenancy_or_404(session=session, tenancy_id=tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can view payments.",
    )

    payment_records = session.exec(
        select(PaymentRecord)
        .where(PaymentRecord.tenancy_id == tenancy.id)
        .order_by(PaymentRecord.created_at.desc())
    ).all()
    return [
        build_payment_response(session=session, payment_record=payment_record)
        for payment_record in payment_records
    ]


@router.post("/{payment_id}/proof", response_model=PaymentResponse)
def submit_payment_proof(
    payment_id: UUID,
    payload: PaymentProofSubmitRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> PaymentResponse:
    payment_record = get_payment_or_404(session=session, payment_id=payment_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=payment_record.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can update payment proof.",
    )
    if current_user.id != payment_record.payer_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the payer can submit payment proof.",
        )
    if payment_record.payment_status == PaymentRecordStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Confirmed payments cannot be resubmitted.",
        )
    if payment_record.payment_status in {
        PaymentRecordStatus.DISPUTED,
        PaymentRecordStatus.UNDER_REVIEW,
        PaymentRecordStatus.VERDICT_ISSUED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payments already in dispute or verdict review cannot be resubmitted here.",
        )

    if payload.proof_stored_artifact_id:
        resolve_tenancy_artifact(
            session=session,
            tenancy=tenancy,
            artifact_id=payload.proof_stored_artifact_id,
            detail="Payment proof artifact must belong to the same tenancy.",
        )

    payment_record.proof_stored_artifact_id = payload.proof_stored_artifact_id
    payment_record.proof_artifact_name = payload.proof_artifact_name.strip()
    payment_record.proof_summary = payload.proof_summary.strip()
    payment_record.external_reference = (
        payload.external_reference.strip() if payload.external_reference else None
    )
    payment_record.paid_at = payload.paid_at or payment_record.paid_at or utcnow()
    payment_record.proof_status = PaymentProofStatus.PROVIDED
    payment_record.payment_status = PaymentRecordStatus.SUBMITTED
    payment_record.counterparty_action_by_user_id = None
    payment_record.counterparty_notes = None
    payment_record.counterparty_action_at = None
    payment_record.counterparty_stored_artifact_id = None
    payment_record.counterparty_artifact_name = None
    payment_record.disputed_by_user_id = None
    payment_record.disputed_at = None
    payment_record.dispute_notes = None
    payment_record.review_requested_by_user_id = None
    payment_record.review_requested_at = None
    payment_record.reviewed_by_user_id = None
    payment_record.reviewed_at = None
    payment_record.verdict_outcome = None
    payment_record.verdict_summary = None
    payment_record.verdict_tenant_score_delta = 0
    payment_record.verdict_landlord_score_delta = 0
    payment_record.appeal_requested_by_user_id = None
    payment_record.appeal_requested_at = None
    payment_record.appeal_notes = None
    payment_record.updated_at = utcnow()
    session.add(payment_record)

    append_payment_party_events(
        session=session,
        tenancy=tenancy,
        payment_record=payment_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_PROOF_SUBMITTED,
        summary=f"Payment proof submitted for {tenancy.property_label}.",
        details=payment_record.proof_summary,
    )

    session.commit()
    session.refresh(payment_record)
    return build_payment_response(session=session, payment_record=payment_record)


@router.post("/{payment_id}/decision", response_model=PaymentResponse)
def decide_payment_record(
    payment_id: UUID,
    payload: PaymentDecisionRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> PaymentResponse:
    payment_record = get_payment_or_404(session=session, payment_id=payment_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=payment_record.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can update payment status.",
    )
    if current_user.id != payment_record.payee_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the payee can confirm or reject a payment record.",
        )
    if payload.payment_status not in {
        PaymentRecordStatus.CONFIRMED,
        PaymentRecordStatus.REJECTED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only confirmed or rejected decisions are supported here.",
        )
    if payment_record.payment_status in {
        PaymentRecordStatus.DISPUTED,
        PaymentRecordStatus.UNDER_REVIEW,
        PaymentRecordStatus.VERDICT_ISSUED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment disputes already in review must stay in the reviewer flow.",
        )
    if payment_record.payment_status == payload.payment_status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already has that counterparty decision.",
        )
    counterparty_stored_artifact = None
    if payload.counterparty_stored_artifact_id:
        counterparty_stored_artifact = resolve_tenancy_artifact(
            session=session,
            tenancy=tenancy,
            artifact_id=payload.counterparty_stored_artifact_id,
            detail="Counterparty payment evidence must belong to the same tenancy.",
        )

    payment_record.payment_status = payload.payment_status
    payment_record.counterparty_action_by_user_id = current_user.id
    payment_record.counterparty_notes = (
        payload.counterparty_notes.strip() if payload.counterparty_notes else None
    )
    payment_record.counterparty_stored_artifact_id = payload.counterparty_stored_artifact_id
    payment_record.counterparty_artifact_name = (
        payload.counterparty_artifact_name.strip()
        if payload.counterparty_artifact_name
        else (
            counterparty_stored_artifact.original_file_name
            if counterparty_stored_artifact is not None
            else None
        )
    )
    payment_record.counterparty_action_at = utcnow()
    if (
        payload.payment_status == PaymentRecordStatus.CONFIRMED
        and payment_record.proof_status == PaymentProofStatus.PROVIDED
    ):
        payment_record.proof_status = PaymentProofStatus.COUNTERPARTY_CONFIRMED
    payment_record.disputed_by_user_id = None
    payment_record.disputed_at = None
    payment_record.dispute_notes = None
    payment_record.review_requested_by_user_id = None
    payment_record.review_requested_at = None
    payment_record.reviewed_by_user_id = None
    payment_record.reviewed_at = None
    payment_record.verdict_outcome = None
    payment_record.verdict_summary = None
    payment_record.verdict_tenant_score_delta = 0
    payment_record.verdict_landlord_score_delta = 0
    payment_record.appeal_requested_by_user_id = None
    payment_record.appeal_requested_at = None
    payment_record.appeal_notes = None
    payment_record.updated_at = utcnow()
    session.add(payment_record)

    event_type = (
        TrustEventType.PAYMENT_CONFIRMED
        if payload.payment_status == PaymentRecordStatus.CONFIRMED
        else TrustEventType.PAYMENT_REJECTED
    )
    append_payment_party_events(
        session=session,
        tenancy=tenancy,
        payment_record=payment_record,
        actor_user_id=current_user.id,
        event_type=event_type,
        summary=(
            f"Payment {payload.payment_status.value} for {tenancy.property_label}."
        ),
        details=payment_record.counterparty_notes,
    )

    session.commit()
    session.refresh(payment_record)
    return build_payment_response(session=session, payment_record=payment_record)


@router.post("/{payment_id}/dispute", response_model=PaymentResponse)
def dispute_payment_record(
    payment_id: UUID,
    payload: PaymentDisputeRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> PaymentResponse:
    payment_record = get_payment_or_404(session=session, payment_id=payment_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=payment_record.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can dispute payments.",
    )
    if current_user.id == payment_record.counterparty_action_by_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The party that made the current payment decision cannot dispute it here.",
        )
    if payment_record.payment_status != PaymentRecordStatus.REJECTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only rejected payments can be disputed here.",
        )

    payment_record.payment_status = PaymentRecordStatus.DISPUTED
    payment_record.disputed_by_user_id = current_user.id
    payment_record.disputed_at = utcnow()
    payment_record.dispute_notes = payload.dispute_notes.strip()
    payment_record.review_requested_by_user_id = current_user.id
    payment_record.review_requested_at = utcnow()
    payment_record.reviewed_by_user_id = None
    payment_record.reviewed_at = None
    payment_record.verdict_outcome = None
    payment_record.verdict_summary = None
    payment_record.verdict_tenant_score_delta = 0
    payment_record.verdict_landlord_score_delta = 0
    payment_record.appeal_requested_by_user_id = None
    payment_record.appeal_requested_at = None
    payment_record.appeal_notes = None
    payment_record.updated_at = utcnow()
    session.add(payment_record)

    append_payment_party_events(
        session=session,
        tenancy=tenancy,
        payment_record=payment_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_DISPUTED,
        summary=f"Payment disputed for {tenancy.property_label}.",
        details=payment_record.dispute_notes,
    )
    append_payment_party_events(
        session=session,
        tenancy=tenancy,
        payment_record=payment_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_REVIEW_REQUESTED,
        summary=f"Payment dispute sent to review for {tenancy.property_label}.",
        details=payment_record.dispute_notes,
    )

    session.commit()
    session.refresh(payment_record)
    return build_payment_response(session=session, payment_record=payment_record)


@router.post("/{payment_id}/appeal", response_model=PaymentResponse)
def appeal_payment_verdict(
    payment_id: UUID,
    payload: PaymentAppealRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> PaymentResponse:
    payment_record = get_payment_or_404(session=session, payment_id=payment_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=payment_record.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can appeal payment verdicts.",
    )
    if payment_record.payment_status != PaymentRecordStatus.VERDICT_ISSUED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only issued payment verdicts can be appealed.",
        )
    if payment_record.appeal_requested_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This payment verdict already has an appeal on record.",
        )

    payment_record.payment_status = PaymentRecordStatus.UNDER_REVIEW
    payment_record.appeal_requested_by_user_id = current_user.id
    payment_record.appeal_requested_at = utcnow()
    payment_record.appeal_notes = payload.appeal_notes.strip()
    payment_record.review_requested_by_user_id = current_user.id
    payment_record.review_requested_at = payment_record.appeal_requested_at
    payment_record.reviewed_by_user_id = None
    payment_record.reviewed_at = None
    payment_record.updated_at = utcnow()
    session.add(payment_record)

    append_payment_party_events(
        session=session,
        tenancy=tenancy,
        payment_record=payment_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_APPEALED,
        summary=f"Payment verdict appealed for {tenancy.property_label}.",
        details=payment_record.appeal_notes,
    )
    append_payment_party_events(
        session=session,
        tenancy=tenancy,
        payment_record=payment_record,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_REVIEW_REQUESTED,
        summary=f"Payment appeal sent to review for {tenancy.property_label}.",
        details=payment_record.appeal_notes,
    )
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

    session.commit()
    session.refresh(payment_record)
    return build_payment_response(session=session, payment_record=payment_record)
