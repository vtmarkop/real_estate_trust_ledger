from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import PaymentRecord, StoredArtifact, User
from app.schemas.payment import PaymentResponse


def build_payment_response(
    *,
    session: Session,
    payment_record: PaymentRecord,
) -> PaymentResponse:
    payer_user = session.get(User, payment_record.payer_user_id)
    payee_user = session.get(User, payment_record.payee_user_id)
    created_by_user = session.get(User, payment_record.created_by_user_id)
    counterparty_action_by_user = (
        session.get(User, payment_record.counterparty_action_by_user_id)
        if payment_record.counterparty_action_by_user_id
        else None
    )
    disputed_by_user = (
        session.get(User, payment_record.disputed_by_user_id)
        if payment_record.disputed_by_user_id
        else None
    )
    review_requested_by_user = (
        session.get(User, payment_record.review_requested_by_user_id)
        if payment_record.review_requested_by_user_id
        else None
    )
    reviewed_by_user = (
        session.get(User, payment_record.reviewed_by_user_id)
        if payment_record.reviewed_by_user_id
        else None
    )
    appeal_requested_by_user = (
        session.get(User, payment_record.appeal_requested_by_user_id)
        if payment_record.appeal_requested_by_user_id
        else None
    )
    proof_stored_artifact = (
        session.get(StoredArtifact, payment_record.proof_stored_artifact_id)
        if payment_record.proof_stored_artifact_id
        else None
    )
    counterparty_stored_artifact = (
        session.get(StoredArtifact, payment_record.counterparty_stored_artifact_id)
        if payment_record.counterparty_stored_artifact_id
        else None
    )

    if not payer_user or not payee_user or not created_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Payment participants are unavailable.",
        )

    return PaymentResponse(
        id=payment_record.id,
        tenancy_id=payment_record.tenancy_id,
        payer_user_id=payment_record.payer_user_id,
        payer_user_full_name=payer_user.full_name,
        payee_user_id=payment_record.payee_user_id,
        payee_user_full_name=payee_user.full_name,
        created_by_user_id=payment_record.created_by_user_id,
        created_by_user_full_name=created_by_user.full_name,
        counterparty_action_by_user_id=payment_record.counterparty_action_by_user_id,
        counterparty_action_by_user_full_name=(
            counterparty_action_by_user.full_name if counterparty_action_by_user else None
        ),
        disputed_by_user_id=payment_record.disputed_by_user_id,
        disputed_by_user_full_name=disputed_by_user.full_name if disputed_by_user else None,
        review_requested_by_user_id=payment_record.review_requested_by_user_id,
        review_requested_by_user_full_name=(
            review_requested_by_user.full_name if review_requested_by_user else None
        ),
        reviewed_by_user_id=payment_record.reviewed_by_user_id,
        reviewed_by_user_full_name=reviewed_by_user.full_name if reviewed_by_user else None,
        appeal_requested_by_user_id=payment_record.appeal_requested_by_user_id,
        appeal_requested_by_user_full_name=(
            appeal_requested_by_user.full_name if appeal_requested_by_user else None
        ),
        payment_type=payment_record.payment_type,
        payment_status=payment_record.payment_status,
        proof_status=payment_record.proof_status,
        amount_minor=payment_record.amount_minor,
        currency_code=payment_record.currency_code,
        due_date=payment_record.due_date,
        period_start_date=payment_record.period_start_date,
        period_end_date=payment_record.period_end_date,
        paid_at=payment_record.paid_at,
        proof_stored_artifact_id=payment_record.proof_stored_artifact_id,
        counterparty_stored_artifact_id=payment_record.counterparty_stored_artifact_id,
        proof_artifact_name=payment_record.proof_artifact_name,
        counterparty_artifact_name=payment_record.counterparty_artifact_name,
        proof_artifact_content_type=(
            proof_stored_artifact.content_type if proof_stored_artifact else None
        ),
        proof_artifact_size_bytes=(
            proof_stored_artifact.size_bytes if proof_stored_artifact else None
        ),
        counterparty_artifact_content_type=(
            counterparty_stored_artifact.content_type if counterparty_stored_artifact else None
        ),
        counterparty_artifact_size_bytes=(
            counterparty_stored_artifact.size_bytes if counterparty_stored_artifact else None
        ),
        proof_summary=payment_record.proof_summary,
        external_reference=payment_record.external_reference,
        counterparty_notes=payment_record.counterparty_notes,
        counterparty_action_at=payment_record.counterparty_action_at,
        dispute_notes=payment_record.dispute_notes,
        disputed_at=payment_record.disputed_at,
        review_requested_at=payment_record.review_requested_at,
        verdict_outcome=payment_record.verdict_outcome,
        verdict_summary=payment_record.verdict_summary,
        verdict_tenant_score_delta=payment_record.verdict_tenant_score_delta,
        verdict_landlord_score_delta=payment_record.verdict_landlord_score_delta,
        reviewed_at=payment_record.reviewed_at,
        appeal_notes=payment_record.appeal_notes,
        appeal_requested_at=payment_record.appeal_requested_at,
        created_at=payment_record.created_at,
        updated_at=payment_record.updated_at,
    )
