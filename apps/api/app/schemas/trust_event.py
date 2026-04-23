from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from trustledger_domain import (
    DepositStatus,
    EvidenceDocumentType,
    MaintenanceTicketPriority,
    MaintenanceTicketStatus,
    PaymentProofStatus,
    PaymentRecordStatus,
    PaymentRecordType,
    TrustEventType,
    VerificationStatus,
)


class TrustEventResponse(BaseModel):
    id: UUID
    subject_user_id: UUID
    actor_user_id: UUID | None = None
    actor_user_full_name: str | None = None
    tenancy_id: UUID | None = None
    history_import_id: UUID | None = None
    history_import_title: str | None = None
    reference_request_id: UUID | None = None
    reference_request_status: str | None = None
    evidence_document_id: UUID | None = None
    evidence_document_type: EvidenceDocumentType | None = None
    evidence_artifact_name: str | None = None
    payment_record_id: UUID | None = None
    payment_type: PaymentRecordType | None = None
    payment_status: PaymentRecordStatus | None = None
    payment_proof_status: PaymentProofStatus | None = None
    deposit_record_id: UUID | None = None
    deposit_status: DepositStatus | None = None
    maintenance_ticket_id: UUID | None = None
    maintenance_ticket_status: MaintenanceTicketStatus | None = None
    maintenance_ticket_priority: MaintenanceTicketPriority | None = None
    listing_id: UUID | None = None
    listing_title: str | None = None
    property_id: UUID | None = None
    property_label: str | None = None
    event_type: TrustEventType
    verification_status: VerificationStatus
    summary: str
    details: str | None = None
    created_at: datetime
