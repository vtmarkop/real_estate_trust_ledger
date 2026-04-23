from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import MaintenanceTicket, StoredArtifact, User
from app.schemas.maintenance import MaintenanceTicketResponse


def build_maintenance_ticket_response(
    *,
    session: Session,
    maintenance_ticket: MaintenanceTicket,
) -> MaintenanceTicketResponse:
    created_by_user = session.get(User, maintenance_ticket.created_by_user_id)
    acknowledged_by_user = (
        session.get(User, maintenance_ticket.acknowledged_by_user_id)
        if maintenance_ticket.acknowledged_by_user_id
        else None
    )
    resolved_by_user = (
        session.get(User, maintenance_ticket.resolved_by_user_id)
        if maintenance_ticket.resolved_by_user_id
        else None
    )
    disputed_by_user = (
        session.get(User, maintenance_ticket.disputed_by_user_id)
        if maintenance_ticket.disputed_by_user_id
        else None
    )
    review_requested_by_user = (
        session.get(User, maintenance_ticket.review_requested_by_user_id)
        if maintenance_ticket.review_requested_by_user_id
        else None
    )
    reviewed_by_user = (
        session.get(User, maintenance_ticket.reviewed_by_user_id)
        if maintenance_ticket.reviewed_by_user_id
        else None
    )
    appeal_requested_by_user = (
        session.get(User, maintenance_ticket.appeal_requested_by_user_id)
        if maintenance_ticket.appeal_requested_by_user_id
        else None
    )
    reported_stored_artifact = (
        session.get(StoredArtifact, maintenance_ticket.reported_stored_artifact_id)
        if maintenance_ticket.reported_stored_artifact_id
        else None
    )
    resolution_stored_artifact = (
        session.get(StoredArtifact, maintenance_ticket.resolution_stored_artifact_id)
        if maintenance_ticket.resolution_stored_artifact_id
        else None
    )

    if not created_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Maintenance ticket creator is unavailable.",
        )

    return MaintenanceTicketResponse(
        id=maintenance_ticket.id,
        tenancy_id=maintenance_ticket.tenancy_id,
        created_by_user_id=maintenance_ticket.created_by_user_id,
        created_by_user_full_name=created_by_user.full_name,
        acknowledged_by_user_id=maintenance_ticket.acknowledged_by_user_id,
        acknowledged_by_user_full_name=(
            acknowledged_by_user.full_name if acknowledged_by_user else None
        ),
        resolved_by_user_id=maintenance_ticket.resolved_by_user_id,
        resolved_by_user_full_name=resolved_by_user.full_name if resolved_by_user else None,
        disputed_by_user_id=maintenance_ticket.disputed_by_user_id,
        disputed_by_user_full_name=disputed_by_user.full_name if disputed_by_user else None,
        review_requested_by_user_id=maintenance_ticket.review_requested_by_user_id,
        review_requested_by_user_full_name=(
            review_requested_by_user.full_name if review_requested_by_user else None
        ),
        reviewed_by_user_id=maintenance_ticket.reviewed_by_user_id,
        reviewed_by_user_full_name=reviewed_by_user.full_name if reviewed_by_user else None,
        appeal_requested_by_user_id=maintenance_ticket.appeal_requested_by_user_id,
        appeal_requested_by_user_full_name=(
            appeal_requested_by_user.full_name if appeal_requested_by_user else None
        ),
        title=maintenance_ticket.title,
        description=maintenance_ticket.description,
        priority=maintenance_ticket.priority,
        ticket_status=maintenance_ticket.ticket_status,
        reported_stored_artifact_id=maintenance_ticket.reported_stored_artifact_id,
        reported_artifact_name=maintenance_ticket.reported_artifact_name,
        reported_artifact_content_type=(
            reported_stored_artifact.content_type if reported_stored_artifact else None
        ),
        reported_artifact_size_bytes=(
            reported_stored_artifact.size_bytes if reported_stored_artifact else None
        ),
        landlord_response_notes=maintenance_ticket.landlord_response_notes,
        acknowledged_at=maintenance_ticket.acknowledged_at,
        resolution_summary=maintenance_ticket.resolution_summary,
        resolution_stored_artifact_id=maintenance_ticket.resolution_stored_artifact_id,
        resolution_artifact_name=maintenance_ticket.resolution_artifact_name,
        resolution_artifact_content_type=(
            resolution_stored_artifact.content_type if resolution_stored_artifact else None
        ),
        resolution_artifact_size_bytes=(
            resolution_stored_artifact.size_bytes if resolution_stored_artifact else None
        ),
        resolved_at=maintenance_ticket.resolved_at,
        dispute_notes=maintenance_ticket.dispute_notes,
        disputed_at=maintenance_ticket.disputed_at,
        review_requested_at=maintenance_ticket.review_requested_at,
        verdict_outcome=maintenance_ticket.verdict_outcome,
        verdict_summary=maintenance_ticket.verdict_summary,
        verdict_tenant_score_delta=maintenance_ticket.verdict_tenant_score_delta,
        verdict_landlord_score_delta=maintenance_ticket.verdict_landlord_score_delta,
        reviewed_at=maintenance_ticket.reviewed_at,
        appeal_notes=maintenance_ticket.appeal_notes,
        appeal_requested_at=maintenance_ticket.appeal_requested_at,
        created_at=maintenance_ticket.created_at,
        updated_at=maintenance_ticket.updated_at,
    )
