from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import MaintenanceTicket, StoredArtifact, Tenancy, User
from app.models.common import utcnow
from app.schemas.maintenance import (
    MaintenanceTicketAcknowledgeRequest,
    MaintenanceTicketAppealRequest,
    MaintenanceTicketCreateRequest,
    MaintenanceTicketDisputeRequest,
    MaintenanceTicketResolveRequest,
    MaintenanceTicketResponse,
)
from app.services.scoring import refresh_user_trust_score
from app.services.maintenance import build_maintenance_ticket_response
from app.services.trust_events import append_user_event
from trustledger_domain import (
    MaintenanceTicketStatus,
    ScoreCalculationReason,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(prefix="/maintenance-tickets", tags=["maintenance-tickets"])


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


def get_maintenance_ticket_or_404(
    *,
    session: SessionDep,
    ticket_id: UUID,
) -> MaintenanceTicket:
    maintenance_ticket = session.get(MaintenanceTicket, ticket_id)
    if not maintenance_ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Maintenance ticket not found.",
        )
    return maintenance_ticket


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


def append_maintenance_party_events(
    *,
    session: SessionDep,
    tenancy: Tenancy,
    maintenance_ticket: MaintenanceTicket,
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
            maintenance_ticket_id=maintenance_ticket.id,
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


@router.post("/tenancies/{tenancy_id}", response_model=MaintenanceTicketResponse, status_code=201)
def create_maintenance_ticket(
    tenancy_id: UUID,
    payload: MaintenanceTicketCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> MaintenanceTicketResponse:
    tenancy = get_tenancy_or_404(session=session, tenancy_id=tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can report maintenance issues.",
    )

    reported_stored_artifact = None
    if payload.reported_stored_artifact_id:
        reported_stored_artifact = resolve_tenancy_artifact(
            session=session,
            tenancy=tenancy,
            artifact_id=payload.reported_stored_artifact_id,
            detail="Reported maintenance artifact must belong to the same tenancy.",
        )

    maintenance_ticket = MaintenanceTicket(
        tenancy_id=tenancy.id,
        created_by_user_id=current_user.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        priority=payload.priority,
        reported_stored_artifact_id=payload.reported_stored_artifact_id,
        reported_artifact_name=(
            payload.reported_artifact_name.strip()
            if payload.reported_artifact_name
            else (
                reported_stored_artifact.original_file_name
                if reported_stored_artifact is not None
                else None
            )
        ),
    )
    session.add(maintenance_ticket)
    session.flush()

    append_maintenance_party_events(
        session=session,
        tenancy=tenancy,
        maintenance_ticket=maintenance_ticket,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_REPORTED,
        summary=f"Maintenance issue reported for {tenancy.property_label}.",
        details=maintenance_ticket.description,
    )

    session.commit()
    session.refresh(maintenance_ticket)
    return build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)


@router.get("/tenancies/{tenancy_id}", response_model=list[MaintenanceTicketResponse])
def list_maintenance_tickets(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[MaintenanceTicketResponse]:
    tenancy = get_tenancy_or_404(session=session, tenancy_id=tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can view maintenance tickets.",
    )
    maintenance_tickets = session.exec(
        select(MaintenanceTicket)
        .where(MaintenanceTicket.tenancy_id == tenancy.id)
        .order_by(MaintenanceTicket.created_at.desc())
    ).all()
    return [
        build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)
        for maintenance_ticket in maintenance_tickets
    ]


@router.post("/{ticket_id}/acknowledge", response_model=MaintenanceTicketResponse)
def acknowledge_maintenance_ticket(
    ticket_id: UUID,
    payload: MaintenanceTicketAcknowledgeRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> MaintenanceTicketResponse:
    maintenance_ticket = get_maintenance_ticket_or_404(session=session, ticket_id=ticket_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=maintenance_ticket.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can acknowledge maintenance tickets.",
    )
    if current_user.id != tenancy.landlord_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the landlord can acknowledge maintenance tickets here.",
        )
    if maintenance_ticket.ticket_status in {
        MaintenanceTicketStatus.RESOLVED,
        MaintenanceTicketStatus.DISPUTED,
        MaintenanceTicketStatus.UNDER_REVIEW,
        MaintenanceTicketStatus.VERDICT_ISSUED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolved or disputed tickets cannot be acknowledged again.",
        )

    maintenance_ticket.ticket_status = MaintenanceTicketStatus.ACKNOWLEDGED
    maintenance_ticket.acknowledged_by_user_id = current_user.id
    maintenance_ticket.acknowledged_at = utcnow()
    maintenance_ticket.landlord_response_notes = (
        payload.landlord_response_notes.strip() if payload.landlord_response_notes else None
    )
    maintenance_ticket.updated_at = utcnow()
    session.add(maintenance_ticket)

    append_maintenance_party_events(
        session=session,
        tenancy=tenancy,
        maintenance_ticket=maintenance_ticket,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_ACKNOWLEDGED,
        summary=f"Maintenance issue acknowledged for {tenancy.property_label}.",
        details=maintenance_ticket.landlord_response_notes,
    )

    session.commit()
    session.refresh(maintenance_ticket)
    return build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)


@router.post("/{ticket_id}/resolve", response_model=MaintenanceTicketResponse)
def resolve_maintenance_ticket(
    ticket_id: UUID,
    payload: MaintenanceTicketResolveRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> MaintenanceTicketResponse:
    maintenance_ticket = get_maintenance_ticket_or_404(session=session, ticket_id=ticket_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=maintenance_ticket.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can resolve maintenance tickets.",
    )
    if current_user.id != tenancy.landlord_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the landlord can resolve maintenance tickets here.",
        )
    if maintenance_ticket.ticket_status in {
        MaintenanceTicketStatus.DISPUTED,
        MaintenanceTicketStatus.UNDER_REVIEW,
        MaintenanceTicketStatus.VERDICT_ISSUED,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tickets already in dispute or review cannot be resolved here.",
        )

    resolution_stored_artifact = None
    if payload.resolution_stored_artifact_id:
        resolution_stored_artifact = resolve_tenancy_artifact(
            session=session,
            tenancy=tenancy,
            artifact_id=payload.resolution_stored_artifact_id,
            detail="Resolution artifact must belong to the same tenancy.",
        )

    maintenance_ticket.ticket_status = MaintenanceTicketStatus.RESOLVED
    maintenance_ticket.acknowledged_by_user_id = (
        maintenance_ticket.acknowledged_by_user_id or current_user.id
    )
    maintenance_ticket.acknowledged_at = maintenance_ticket.acknowledged_at or utcnow()
    maintenance_ticket.resolved_by_user_id = current_user.id
    maintenance_ticket.resolved_at = utcnow()
    maintenance_ticket.resolution_summary = payload.resolution_summary.strip()
    maintenance_ticket.resolution_stored_artifact_id = payload.resolution_stored_artifact_id
    maintenance_ticket.resolution_artifact_name = (
        payload.resolution_artifact_name.strip()
        if payload.resolution_artifact_name
        else (
            resolution_stored_artifact.original_file_name
            if resolution_stored_artifact is not None
            else None
        )
    )
    maintenance_ticket.landlord_response_notes = (
        payload.landlord_response_notes.strip()
        if payload.landlord_response_notes
        else maintenance_ticket.landlord_response_notes
    )
    maintenance_ticket.dispute_notes = None
    maintenance_ticket.disputed_by_user_id = None
    maintenance_ticket.disputed_at = None
    maintenance_ticket.updated_at = utcnow()
    session.add(maintenance_ticket)

    append_maintenance_party_events(
        session=session,
        tenancy=tenancy,
        maintenance_ticket=maintenance_ticket,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_RESOLVED,
        summary=f"Maintenance issue resolved for {tenancy.property_label}.",
        details=maintenance_ticket.resolution_summary,
    )

    session.commit()
    session.refresh(maintenance_ticket)
    return build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)


@router.post("/{ticket_id}/dispute", response_model=MaintenanceTicketResponse)
def dispute_maintenance_ticket(
    ticket_id: UUID,
    payload: MaintenanceTicketDisputeRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> MaintenanceTicketResponse:
    maintenance_ticket = get_maintenance_ticket_or_404(session=session, ticket_id=ticket_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=maintenance_ticket.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can dispute maintenance tickets.",
    )
    if current_user.id != tenancy.tenant_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the tenant can dispute maintenance tickets here.",
        )
    if maintenance_ticket.ticket_status != MaintenanceTicketStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only resolved tickets can move into the dispute state.",
        )

    maintenance_ticket.ticket_status = MaintenanceTicketStatus.DISPUTED
    maintenance_ticket.disputed_by_user_id = current_user.id
    maintenance_ticket.disputed_at = utcnow()
    maintenance_ticket.dispute_notes = payload.dispute_notes.strip()
    maintenance_ticket.review_requested_by_user_id = current_user.id
    maintenance_ticket.review_requested_at = utcnow()
    maintenance_ticket.reviewed_by_user_id = None
    maintenance_ticket.reviewed_at = None
    maintenance_ticket.verdict_outcome = None
    maintenance_ticket.verdict_summary = None
    maintenance_ticket.verdict_tenant_score_delta = 0
    maintenance_ticket.verdict_landlord_score_delta = 0
    maintenance_ticket.updated_at = utcnow()
    session.add(maintenance_ticket)

    append_maintenance_party_events(
        session=session,
        tenancy=tenancy,
        maintenance_ticket=maintenance_ticket,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_DISPUTED,
        summary=f"Maintenance resolution disputed for {tenancy.property_label}.",
        details=maintenance_ticket.dispute_notes,
    )
    append_maintenance_party_events(
        session=session,
        tenancy=tenancy,
        maintenance_ticket=maintenance_ticket,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_REVIEW_REQUESTED,
        summary=f"Maintenance dispute sent to review for {tenancy.property_label}.",
        details=maintenance_ticket.dispute_notes,
    )

    session.commit()
    session.refresh(maintenance_ticket)
    return build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)


@router.post("/{ticket_id}/appeal", response_model=MaintenanceTicketResponse)
def appeal_maintenance_verdict(
    ticket_id: UUID,
    payload: MaintenanceTicketAppealRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> MaintenanceTicketResponse:
    maintenance_ticket = get_maintenance_ticket_or_404(session=session, ticket_id=ticket_id)
    tenancy = get_tenancy_or_404(session=session, tenancy_id=maintenance_ticket.tenancy_id)
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can appeal maintenance verdicts.",
    )
    if maintenance_ticket.ticket_status != MaintenanceTicketStatus.VERDICT_ISSUED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only issued verdicts can be appealed.",
        )
    if maintenance_ticket.appeal_requested_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This maintenance verdict already has an appeal on record.",
        )

    maintenance_ticket.ticket_status = MaintenanceTicketStatus.UNDER_REVIEW
    maintenance_ticket.appeal_requested_by_user_id = current_user.id
    maintenance_ticket.appeal_requested_at = utcnow()
    maintenance_ticket.appeal_notes = payload.appeal_notes.strip()
    maintenance_ticket.review_requested_by_user_id = current_user.id
    maintenance_ticket.review_requested_at = maintenance_ticket.appeal_requested_at
    maintenance_ticket.reviewed_by_user_id = None
    maintenance_ticket.reviewed_at = None
    maintenance_ticket.updated_at = utcnow()
    session.add(maintenance_ticket)

    append_maintenance_party_events(
        session=session,
        tenancy=tenancy,
        maintenance_ticket=maintenance_ticket,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_APPEALED,
        summary=f"Maintenance verdict appealed for {tenancy.property_label}.",
        details=maintenance_ticket.appeal_notes,
    )
    append_maintenance_party_events(
        session=session,
        tenancy=tenancy,
        maintenance_ticket=maintenance_ticket,
        actor_user_id=current_user.id,
        event_type=TrustEventType.MAINTENANCE_REVIEW_REQUESTED,
        summary=f"Maintenance appeal sent to review for {tenancy.property_label}.",
        details=maintenance_ticket.appeal_notes,
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
    session.refresh(maintenance_ticket)
    return build_maintenance_ticket_response(session=session, maintenance_ticket=maintenance_ticket)
