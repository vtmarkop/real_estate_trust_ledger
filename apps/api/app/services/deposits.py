from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import DepositRecord, StoredArtifact, User
from app.schemas.deposit import DepositResponse


def build_deposit_response(
    *,
    session: Session,
    deposit_record: DepositRecord,
) -> DepositResponse:
    created_by_user = session.get(User, deposit_record.created_by_user_id)
    counterparty_action_by_user = (
        session.get(User, deposit_record.counterparty_action_by_user_id)
        if deposit_record.counterparty_action_by_user_id
        else None
    )
    disputed_by_user = (
        session.get(User, deposit_record.disputed_by_user_id)
        if deposit_record.disputed_by_user_id
        else None
    )
    review_requested_by_user = (
        session.get(User, deposit_record.review_requested_by_user_id)
        if deposit_record.review_requested_by_user_id
        else None
    )
    reviewed_by_user = (
        session.get(User, deposit_record.reviewed_by_user_id)
        if deposit_record.reviewed_by_user_id
        else None
    )
    appeal_requested_by_user = (
        session.get(User, deposit_record.appeal_requested_by_user_id)
        if deposit_record.appeal_requested_by_user_id
        else None
    )
    settlement_stored_artifact = (
        session.get(StoredArtifact, deposit_record.settlement_stored_artifact_id)
        if deposit_record.settlement_stored_artifact_id
        else None
    )

    if not created_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Deposit creator is unavailable.",
        )

    return DepositResponse(
        id=deposit_record.id,
        tenancy_id=deposit_record.tenancy_id,
        created_by_user_id=deposit_record.created_by_user_id,
        created_by_user_full_name=created_by_user.full_name,
        counterparty_action_by_user_id=deposit_record.counterparty_action_by_user_id,
        counterparty_action_by_user_full_name=(
            counterparty_action_by_user.full_name if counterparty_action_by_user else None
        ),
        disputed_by_user_id=deposit_record.disputed_by_user_id,
        disputed_by_user_full_name=disputed_by_user.full_name if disputed_by_user else None,
        review_requested_by_user_id=deposit_record.review_requested_by_user_id,
        review_requested_by_user_full_name=(
            review_requested_by_user.full_name if review_requested_by_user else None
        ),
        reviewed_by_user_id=deposit_record.reviewed_by_user_id,
        reviewed_by_user_full_name=reviewed_by_user.full_name if reviewed_by_user else None,
        appeal_requested_by_user_id=deposit_record.appeal_requested_by_user_id,
        appeal_requested_by_user_full_name=(
            appeal_requested_by_user.full_name if appeal_requested_by_user else None
        ),
        held_amount_minor=deposit_record.held_amount_minor,
        proposed_return_minor=deposit_record.proposed_return_minor,
        withheld_amount_minor=deposit_record.withheld_amount_minor,
        currency_code=deposit_record.currency_code,
        deposit_status=deposit_record.deposit_status,
        move_out_date=deposit_record.move_out_date,
        return_due_date=deposit_record.return_due_date,
        returned_at=deposit_record.returned_at,
        settlement_stored_artifact_id=deposit_record.settlement_stored_artifact_id,
        settlement_artifact_name=deposit_record.settlement_artifact_name,
        settlement_artifact_content_type=(
            settlement_stored_artifact.content_type if settlement_stored_artifact else None
        ),
        settlement_artifact_size_bytes=(
            settlement_stored_artifact.size_bytes if settlement_stored_artifact else None
        ),
        settlement_summary=deposit_record.settlement_summary,
        settlement_notes=deposit_record.settlement_notes,
        dispute_notes=deposit_record.dispute_notes,
        counterparty_action_at=deposit_record.counterparty_action_at,
        disputed_at=deposit_record.disputed_at,
        review_requested_at=deposit_record.review_requested_at,
        verdict_outcome=deposit_record.verdict_outcome,
        verdict_summary=deposit_record.verdict_summary,
        verdict_tenant_score_delta=deposit_record.verdict_tenant_score_delta,
        verdict_landlord_score_delta=deposit_record.verdict_landlord_score_delta,
        reviewed_at=deposit_record.reviewed_at,
        appeal_notes=deposit_record.appeal_notes,
        appeal_requested_at=deposit_record.appeal_requested_at,
        created_at=deposit_record.created_at,
        updated_at=deposit_record.updated_at,
    )
