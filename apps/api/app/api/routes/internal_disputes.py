from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from app.api.deps import SessionDep, require_system_roles
from app.models import DepositRecord, MaintenanceTicket, PaymentRecord, Tenancy, User
from app.models.common import utcnow
from app.schemas.deposit import DepositResponse, DepositVerdictRequest
from app.schemas.maintenance import MaintenanceTicketResponse, MaintenanceTicketVerdictRequest
from app.schemas.payment import PaymentResponse, PaymentVerdictRequest
from app.services.deposits import build_deposit_response
from app.services.maintenance import build_maintenance_ticket_response
from app.services.payments import build_payment_response
from app.services.scoring import refresh_user_trust_score
from app.services.trust_events import append_user_event
from trustledger_domain import (
    DepositStatus,
    MaintenanceTicketStatus,
    PaymentRecordStatus,
    ScoreCalculationReason,
    SystemRole,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(prefix="/internal/disputes", tags=["internal-disputes"])


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


@router.get("/maintenance", response_model=list[MaintenanceTicketResponse])
def list_maintenance_dispute_queue(
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> list[MaintenanceTicketResponse]:
    maintenance_tickets = session.exec(
        select(MaintenanceTicket)
        .where(
            MaintenanceTicket.ticket_status.in_(
                [MaintenanceTicketStatus.DISPUTED, MaintenanceTicketStatus.UNDER_REVIEW]
            )
        )
        .order_by(MaintenanceTicket.review_requested_at.asc(), MaintenanceTicket.updated_at.asc())
    ).all()
    return [
        build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)
        for maintenance_ticket in maintenance_tickets
    ]


@router.post(
    "/maintenance/{ticket_id}/verdict",
    response_model=MaintenanceTicketResponse,
)
def issue_maintenance_verdict(
    ticket_id: UUID,
    payload: MaintenanceTicketVerdictRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> MaintenanceTicketResponse:
    maintenance_ticket = session.get(MaintenanceTicket, ticket_id)
    if not maintenance_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance ticket not found.",
        )
    if maintenance_ticket.ticket_status not in {
        MaintenanceTicketStatus.DISPUTED,
        MaintenanceTicketStatus.UNDER_REVIEW,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This maintenance ticket is not waiting for a verdict.",
        )

    tenancy = session.get(Tenancy, maintenance_ticket.tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Linked tenancy is unavailable for this maintenance ticket.",
        )

    maintenance_ticket.ticket_status = MaintenanceTicketStatus.VERDICT_ISSUED
    maintenance_ticket.reviewed_by_user_id = current_user.id
    maintenance_ticket.reviewed_at = utcnow()
    maintenance_ticket.verdict_outcome = payload.verdict_outcome
    maintenance_ticket.verdict_summary = payload.verdict_summary.strip()
    maintenance_ticket.verdict_tenant_score_delta = payload.tenant_score_delta
    maintenance_ticket.verdict_landlord_score_delta = payload.landlord_score_delta
    maintenance_ticket.updated_at = utcnow()
    session.add(maintenance_ticket)
    session.flush()

    append_user_event(
        session=session,
        subject_user_id=tenancy.tenant_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_VERDICT_ISSUED,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Maintenance verdict issued for {tenancy.property_label}.",
        details=(
            f"{maintenance_ticket.verdict_summary} "
            f"(Tenant delta {maintenance_ticket.verdict_tenant_score_delta}, "
            f"landlord delta {maintenance_ticket.verdict_landlord_score_delta})."
        ),
        tenancy_id=tenancy.id,
        maintenance_ticket_id=maintenance_ticket.id,
    )
    append_user_event(
        session=session,
        subject_user_id=tenancy.landlord_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_VERDICT_ISSUED,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Maintenance verdict issued for {tenancy.property_label}.",
        details=(
            f"{maintenance_ticket.verdict_summary} "
            f"(Tenant delta {maintenance_ticket.verdict_tenant_score_delta}, "
            f"landlord delta {maintenance_ticket.verdict_landlord_score_delta})."
        ),
        tenancy_id=tenancy.id,
        maintenance_ticket_id=maintenance_ticket.id,
    )
    refresh_tenancy_scores(session=session, tenancy=tenancy)
    session.commit()
    session.refresh(maintenance_ticket)
    return build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)


@router.get("/payments", response_model=list[PaymentResponse])
def list_payment_dispute_queue(
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> list[PaymentResponse]:
    payment_records = session.exec(
        select(PaymentRecord)
        .where(
            PaymentRecord.payment_status.in_(
                [PaymentRecordStatus.DISPUTED, PaymentRecordStatus.UNDER_REVIEW]
            )
        )
        .order_by(PaymentRecord.review_requested_at.asc(), PaymentRecord.updated_at.asc())
    ).all()
    return [
        build_payment_response(session=session, payment_record=payment_record)
        for payment_record in payment_records
    ]


@router.get("/deposits", response_model=list[DepositResponse])
def list_deposit_dispute_queue(
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> list[DepositResponse]:
    deposit_records = session.exec(
        select(DepositRecord)
        .where(DepositRecord.deposit_status.in_([DepositStatus.DISPUTED, DepositStatus.UNDER_REVIEW]))
        .order_by(DepositRecord.review_requested_at.asc(), DepositRecord.updated_at.asc())
    ).all()
    return [
        build_deposit_response(session=session, deposit_record=deposit_record)
        for deposit_record in deposit_records
    ]


@router.post("/deposits/{deposit_id}/verdict", response_model=DepositResponse)
def issue_deposit_verdict(
    deposit_id: UUID,
    payload: DepositVerdictRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> DepositResponse:
    deposit_record = session.get(DepositRecord, deposit_id)
    if not deposit_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deposit record not found.",
        )
    if deposit_record.deposit_status not in {
        DepositStatus.DISPUTED,
        DepositStatus.UNDER_REVIEW,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This deposit record is not waiting for a verdict.",
        )

    tenancy = session.get(Tenancy, deposit_record.tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Linked tenancy is unavailable for this deposit record.",
        )

    deposit_record.deposit_status = DepositStatus.VERDICT_ISSUED
    deposit_record.reviewed_by_user_id = current_user.id
    deposit_record.reviewed_at = utcnow()
    deposit_record.verdict_outcome = payload.verdict_outcome
    deposit_record.verdict_summary = payload.verdict_summary.strip()
    deposit_record.verdict_tenant_score_delta = payload.tenant_score_delta
    deposit_record.verdict_landlord_score_delta = payload.landlord_score_delta
    deposit_record.updated_at = utcnow()
    session.add(deposit_record)
    session.flush()

    append_user_event(
        session=session,
        subject_user_id=tenancy.tenant_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_VERDICT_ISSUED,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Deposit verdict issued for {tenancy.property_label}.",
        details=(
            f"{deposit_record.verdict_summary} "
            f"(Tenant delta {deposit_record.verdict_tenant_score_delta}, "
            f"landlord delta {deposit_record.verdict_landlord_score_delta})."
        ),
        tenancy_id=tenancy.id,
        deposit_record_id=deposit_record.id,
    )
    append_user_event(
        session=session,
        subject_user_id=tenancy.landlord_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.DEPOSIT_VERDICT_ISSUED,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Deposit verdict issued for {tenancy.property_label}.",
        details=(
            f"{deposit_record.verdict_summary} "
            f"(Tenant delta {deposit_record.verdict_tenant_score_delta}, "
            f"landlord delta {deposit_record.verdict_landlord_score_delta})."
        ),
        tenancy_id=tenancy.id,
        deposit_record_id=deposit_record.id,
    )
    refresh_tenancy_scores(session=session, tenancy=tenancy)
    session.commit()
    session.refresh(deposit_record)
    return build_deposit_response(session=session, deposit_record=deposit_record)


@router.post("/payments/{payment_id}/verdict", response_model=PaymentResponse)
def issue_payment_verdict(
    payment_id: UUID,
    payload: PaymentVerdictRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> PaymentResponse:
    payment_record = session.get(PaymentRecord, payment_id)
    if not payment_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment record not found.",
        )
    if payment_record.payment_status not in {
        PaymentRecordStatus.DISPUTED,
        PaymentRecordStatus.UNDER_REVIEW,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This payment record is not waiting for a verdict.",
        )

    tenancy = session.get(Tenancy, payment_record.tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Linked tenancy is unavailable for this payment record.",
        )

    payment_record.payment_status = PaymentRecordStatus.VERDICT_ISSUED
    payment_record.reviewed_by_user_id = current_user.id
    payment_record.reviewed_at = utcnow()
    payment_record.verdict_outcome = payload.verdict_outcome
    payment_record.verdict_summary = payload.verdict_summary.strip()
    payment_record.verdict_tenant_score_delta = payload.tenant_score_delta
    payment_record.verdict_landlord_score_delta = payload.landlord_score_delta
    payment_record.updated_at = utcnow()
    session.add(payment_record)
    session.flush()

    append_user_event(
        session=session,
        subject_user_id=tenancy.tenant_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_VERDICT_ISSUED,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Payment verdict issued for {tenancy.property_label}.",
        details=(
            f"{payment_record.verdict_summary} "
            f"(Tenant delta {payment_record.verdict_tenant_score_delta}, "
            f"landlord delta {payment_record.verdict_landlord_score_delta})."
        ),
        tenancy_id=tenancy.id,
        payment_record_id=payment_record.id,
    )
    append_user_event(
        session=session,
        subject_user_id=tenancy.landlord_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.PAYMENT_VERDICT_ISSUED,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Payment verdict issued for {tenancy.property_label}.",
        details=(
            f"{payment_record.verdict_summary} "
            f"(Tenant delta {payment_record.verdict_tenant_score_delta}, "
            f"landlord delta {payment_record.verdict_landlord_score_delta})."
        ),
        tenancy_id=tenancy.id,
        payment_record_id=payment_record.id,
    )
    refresh_tenancy_scores(session=session, tenancy=tenancy)
    session.commit()
    session.refresh(payment_record)
    return build_payment_response(session=session, payment_record=payment_record)
