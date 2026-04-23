from __future__ import annotations

from sqlmodel import Session

from app.models import (
    DepositRecord,
    EvidenceDocument,
    HistoryImport,
    Listing,
    MaintenanceTicket,
    PaymentRecord,
    Property,
    ReferenceRequest,
    Tenancy,
    TrustEvent,
    User,
)
from app.schemas.trust_event import TrustEventResponse
from trustledger_domain import TrustEventType, VerificationStatus


def append_tenancy_events(
    *,
    session: Session,
    tenancy: Tenancy,
    actor_user_id,
    event_type: TrustEventType,
    verification_status: VerificationStatus,
    summary: str,
    details: str | None = None,
) -> None:
    subject_user_ids = [tenancy.tenant_user_id, tenancy.landlord_user_id]
    for subject_user_id in subject_user_ids:
        session.add(
            TrustEvent(
                subject_user_id=subject_user_id,
                actor_user_id=actor_user_id,
                tenancy_id=tenancy.id,
                event_type=event_type,
                verification_status=verification_status,
                summary=summary,
                details=details,
            )
        )


def append_user_event(
    *,
    session: Session,
    subject_user_id,
    actor_user_id,
    event_type: TrustEventType,
    verification_status: VerificationStatus,
    summary: str,
    details: str | None = None,
    tenancy_id=None,
    history_import_id=None,
    reference_request_id=None,
    evidence_document_id=None,
    payment_record_id=None,
    deposit_record_id=None,
    maintenance_ticket_id=None,
    listing_id=None,
) -> None:
    session.add(
        TrustEvent(
            subject_user_id=subject_user_id,
            actor_user_id=actor_user_id,
            tenancy_id=tenancy_id,
            history_import_id=history_import_id,
            reference_request_id=reference_request_id,
            evidence_document_id=evidence_document_id,
            payment_record_id=payment_record_id,
            deposit_record_id=deposit_record_id,
            maintenance_ticket_id=maintenance_ticket_id,
            listing_id=listing_id,
            event_type=event_type,
            verification_status=verification_status,
            summary=summary,
            details=details,
        )
    )


def build_trust_event_response(
    *,
    session: Session,
    trust_event: TrustEvent,
) -> TrustEventResponse:
    actor_user = session.get(User, trust_event.actor_user_id) if trust_event.actor_user_id else None
    tenancy = session.get(Tenancy, trust_event.tenancy_id) if trust_event.tenancy_id else None
    history_import = (
        session.get(HistoryImport, trust_event.history_import_id)
        if trust_event.history_import_id
        else None
    )
    reference_request = (
        session.get(ReferenceRequest, trust_event.reference_request_id)
        if trust_event.reference_request_id
        else None
    )
    evidence_document = (
        session.get(EvidenceDocument, trust_event.evidence_document_id)
        if trust_event.evidence_document_id
        else None
    )
    payment_record = (
        session.get(PaymentRecord, trust_event.payment_record_id)
        if trust_event.payment_record_id
        else None
    )
    deposit_record = (
        session.get(DepositRecord, trust_event.deposit_record_id)
        if trust_event.deposit_record_id
        else None
    )
    maintenance_ticket = (
        session.get(MaintenanceTicket, trust_event.maintenance_ticket_id)
        if trust_event.maintenance_ticket_id
        else None
    )
    listing = session.get(Listing, trust_event.listing_id) if trust_event.listing_id else None
    property_id = tenancy.property_id if tenancy else (listing.property_id if listing else None)
    property_record = session.get(Property, property_id) if property_id else None

    return TrustEventResponse(
        id=trust_event.id,
        subject_user_id=trust_event.subject_user_id,
        actor_user_id=trust_event.actor_user_id,
        actor_user_full_name=actor_user.full_name if actor_user else None,
        tenancy_id=trust_event.tenancy_id,
        history_import_id=trust_event.history_import_id,
        history_import_title=history_import.title if history_import else None,
        reference_request_id=trust_event.reference_request_id,
        reference_request_status=reference_request.status if reference_request else None,
        evidence_document_id=trust_event.evidence_document_id,
        evidence_document_type=evidence_document.document_type if evidence_document else None,
        evidence_artifact_name=evidence_document.artifact_name if evidence_document else None,
        payment_record_id=trust_event.payment_record_id,
        payment_type=payment_record.payment_type if payment_record else None,
        payment_status=payment_record.payment_status if payment_record else None,
        payment_proof_status=payment_record.proof_status if payment_record else None,
        deposit_record_id=trust_event.deposit_record_id,
        deposit_status=deposit_record.deposit_status if deposit_record else None,
        maintenance_ticket_id=trust_event.maintenance_ticket_id,
        maintenance_ticket_status=maintenance_ticket.ticket_status if maintenance_ticket else None,
        maintenance_ticket_priority=maintenance_ticket.priority if maintenance_ticket else None,
        listing_id=trust_event.listing_id,
        listing_title=listing.title if listing else None,
        property_id=property_id,
        property_label=property_record.property_label if property_record else None,
        event_type=trust_event.event_type,
        verification_status=trust_event.verification_status,
        summary=trust_event.summary,
        details=trust_event.details,
        created_at=trust_event.created_at,
    )
