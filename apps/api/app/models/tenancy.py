import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import TenancyStatus, VerificationStatus

if TYPE_CHECKING:
    from app.models.deposit import DepositRecord
    from app.models.evidence import EvidenceDocument
    from app.models.history_import import HistoryImport
    from app.models.maintenance_ticket import MaintenanceTicket
    from app.models.payment import PaymentRecord
    from app.models.property import Property
    from app.models.reference_request import ReferenceRequest
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class Tenancy(TimestampedModel, table=True):
    __tablename__ = "tenancies"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    property_label: str = Field(nullable=False, max_length=255)
    address_line1: str = Field(nullable=False, max_length=255)
    city: str = Field(nullable=False, max_length=120)
    country_code: str = Field(nullable=False, max_length=2)
    tenancy_status: TenancyStatus = Field(default=TenancyStatus.ACTIVE, nullable=False, max_length=32)
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.SELF_REPORTED,
        nullable=False,
        max_length=50,
    )
    lease_start_date: date = Field(nullable=False)
    lease_end_date: Optional[date] = Field(default=None, nullable=True)
    monthly_rent_minor: int = Field(nullable=False, ge=0)
    deposit_minor: int = Field(default=0, nullable=False, ge=0)
    currency_code: str = Field(default="EUR", nullable=False, max_length=3)
    history_import_id: Optional[uuid.UUID] = Field(
        foreign_key="history_imports.id",
        default=None,
        nullable=True,
        index=True,
    )
    property_id: Optional[uuid.UUID] = Field(
        foreign_key="properties.id",
        default=None,
        nullable=True,
        index=True,
    )
    tenant_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    landlord_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    created_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    counterparty_confirmed_at: Optional[datetime] = Field(default=None, nullable=True)
    counterparty_confirmed_by_user_id: Optional[uuid.UUID] = Field(
        foreign_key="users.id",
        default=None,
        nullable=True,
    )
    review_requested_at: Optional[datetime] = Field(default=None, nullable=True)
    reviewed_at: Optional[datetime] = Field(default=None, nullable=True)
    reviewed_by_user_id: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None, nullable=True)
    review_notes: Optional[str] = Field(default=None, nullable=True, max_length=1000)

    tenant_user: "User" = Relationship(
        back_populates="tenancies_as_tenant",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.tenant_user_id"},
    )
    landlord_user: "User" = Relationship(
        back_populates="tenancies_as_landlord",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.landlord_user_id"},
    )
    created_by_user: "User" = Relationship(
        back_populates="tenancies_created",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.created_by_user_id"},
    )
    reviewed_by_user: "User" = Relationship(
        back_populates="tenancies_reviewed",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.reviewed_by_user_id"},
    )
    counterparty_confirmed_by_user: "User" = Relationship(
        back_populates="tenancies_counterparty_confirmed",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.counterparty_confirmed_by_user_id"},
    )
    history_import: Optional["HistoryImport"] = Relationship(back_populates="tenancies")
    property_record: Optional["Property"] = Relationship(back_populates="tenancies")
    deposit_records: List["DepositRecord"] = Relationship(back_populates="tenancy")
    evidence_documents: List["EvidenceDocument"] = Relationship(back_populates="tenancy")
    maintenance_tickets: List["MaintenanceTicket"] = Relationship(back_populates="tenancy")
    payment_records: List["PaymentRecord"] = Relationship(back_populates="tenancy")
    reference_requests: List["ReferenceRequest"] = Relationship(back_populates="tenancy")
    trust_events: List["TrustEvent"] = Relationship(back_populates="tenancy")

    @property
    def is_pending_review(self) -> bool:
        return self.review_requested_at is not None and self.reviewed_at is None
