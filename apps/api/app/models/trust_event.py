import uuid
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import TrustEventType, VerificationStatus

if TYPE_CHECKING:
    from app.models.deposit import DepositRecord
    from app.models.evidence import EvidenceDocument
    from app.models.history_import import HistoryImport
    from app.models.listing import Listing
    from app.models.maintenance_ticket import MaintenanceTicket
    from app.models.payment import PaymentRecord
    from app.models.reference_request import ReferenceRequest
    from app.models.tenancy import Tenancy
    from app.models.user import User


class TrustEvent(TimestampedModel, table=True):
    __tablename__ = "trust_events"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subject_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    actor_user_id: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None, nullable=True)
    tenancy_id: Optional[uuid.UUID] = Field(foreign_key="tenancies.id", default=None, nullable=True, index=True)
    history_import_id: Optional[uuid.UUID] = Field(
        foreign_key="history_imports.id",
        default=None,
        nullable=True,
        index=True,
    )
    reference_request_id: Optional[uuid.UUID] = Field(
        foreign_key="reference_requests.id",
        default=None,
        nullable=True,
        index=True,
    )
    evidence_document_id: Optional[uuid.UUID] = Field(
        foreign_key="evidence_documents.id",
        default=None,
        nullable=True,
        index=True,
    )
    payment_record_id: Optional[uuid.UUID] = Field(
        foreign_key="payment_records.id",
        default=None,
        nullable=True,
        index=True,
    )
    deposit_record_id: Optional[uuid.UUID] = Field(
        foreign_key="deposit_records.id",
        default=None,
        nullable=True,
        index=True,
    )
    maintenance_ticket_id: Optional[uuid.UUID] = Field(
        foreign_key="maintenance_tickets.id",
        default=None,
        nullable=True,
        index=True,
    )
    listing_id: Optional[uuid.UUID] = Field(foreign_key="listings.id", default=None, nullable=True, index=True)
    event_type: TrustEventType = Field(nullable=False, max_length=64)
    verification_status: VerificationStatus = Field(nullable=False, max_length=50)
    summary: str = Field(nullable=False, max_length=255)
    details: Optional[str] = Field(default=None, nullable=True, max_length=1000)

    subject_user: "User" = Relationship(
        back_populates="trust_events_as_subject",
        sa_relationship_kwargs={"foreign_keys": "TrustEvent.subject_user_id"},
    )
    actor_user: "User" = Relationship(
        back_populates="trust_events_as_actor",
        sa_relationship_kwargs={"foreign_keys": "TrustEvent.actor_user_id"},
    )
    tenancy: Optional["Tenancy"] = Relationship(back_populates="trust_events")
    history_import: Optional["HistoryImport"] = Relationship(back_populates="trust_events")
    reference_request: Optional["ReferenceRequest"] = Relationship(back_populates="trust_events")
    evidence_document: Optional["EvidenceDocument"] = Relationship(back_populates="trust_events")
    payment_record: Optional["PaymentRecord"] = Relationship(back_populates="trust_events")
    deposit_record: Optional["DepositRecord"] = Relationship(back_populates="trust_events")
    maintenance_ticket: Optional["MaintenanceTicket"] = Relationship(back_populates="trust_events")
    listing: Optional["Listing"] = Relationship(back_populates="trust_events")
