import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import (
    DisputeVerdictOutcome,
    PaymentProofStatus,
    PaymentRecordStatus,
    PaymentRecordType,
)

if TYPE_CHECKING:
    from app.models.stored_artifact import StoredArtifact
    from app.models.tenancy import Tenancy
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class PaymentRecord(TimestampedModel, table=True):
    __tablename__ = "payment_records"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenancy_id: uuid.UUID = Field(foreign_key="tenancies.id", nullable=False, index=True)
    payer_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    payee_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    created_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    counterparty_action_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    disputed_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    review_requested_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    reviewed_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    appeal_requested_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    payment_type: PaymentRecordType = Field(nullable=False, max_length=50)
    payment_status: PaymentRecordStatus = Field(
        default=PaymentRecordStatus.PENDING,
        nullable=False,
        max_length=32,
    )
    proof_status: PaymentProofStatus = Field(
        default=PaymentProofStatus.NONE,
        nullable=False,
        max_length=32,
    )
    amount_minor: int = Field(nullable=False, ge=0)
    currency_code: str = Field(nullable=False, max_length=3)
    due_date: date = Field(nullable=False)
    period_start_date: date | None = Field(default=None, nullable=True)
    period_end_date: date | None = Field(default=None, nullable=True)
    paid_at: datetime | None = Field(default=None, nullable=True)
    proof_stored_artifact_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="stored_artifacts.id",
        nullable=True,
        index=True,
    )
    counterparty_stored_artifact_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="stored_artifacts.id",
        nullable=True,
        index=True,
    )
    proof_artifact_name: str | None = Field(default=None, nullable=True, max_length=255)
    counterparty_artifact_name: str | None = Field(default=None, nullable=True, max_length=255)
    proof_summary: str | None = Field(default=None, nullable=True, max_length=1000)
    external_reference: str | None = Field(default=None, nullable=True, max_length=255)
    counterparty_notes: str | None = Field(default=None, nullable=True, max_length=1000)
    counterparty_action_at: datetime | None = Field(default=None, nullable=True)
    dispute_notes: str | None = Field(default=None, nullable=True, max_length=1000)
    disputed_at: datetime | None = Field(default=None, nullable=True)
    review_requested_at: datetime | None = Field(default=None, nullable=True)
    verdict_outcome: DisputeVerdictOutcome | None = Field(
        default=None,
        nullable=True,
        max_length=32,
    )
    verdict_summary: str | None = Field(default=None, nullable=True, max_length=1000)
    verdict_tenant_score_delta: int = Field(default=0, nullable=False)
    verdict_landlord_score_delta: int = Field(default=0, nullable=False)
    reviewed_at: datetime | None = Field(default=None, nullable=True)
    appeal_notes: str | None = Field(default=None, nullable=True, max_length=1000)
    appeal_requested_at: datetime | None = Field(default=None, nullable=True)

    tenancy: "Tenancy" = Relationship(back_populates="payment_records")
    payer_user: "User" = Relationship(
        back_populates="payments_as_payer",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.payer_user_id"},
    )
    payee_user: "User" = Relationship(
        back_populates="payments_as_payee",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.payee_user_id"},
    )
    created_by_user: "User" = Relationship(
        back_populates="payments_created",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.created_by_user_id"},
    )
    counterparty_action_by_user: "User" = Relationship(
        back_populates="payments_counterparty_actioned",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.counterparty_action_by_user_id"},
    )
    disputed_by_user: "User" = Relationship(
        back_populates="payments_disputed",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.disputed_by_user_id"},
    )
    review_requested_by_user: "User" = Relationship(
        back_populates="payments_review_requested",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.review_requested_by_user_id"},
    )
    reviewed_by_user: "User" = Relationship(
        back_populates="payments_reviewed",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.reviewed_by_user_id"},
    )
    appeal_requested_by_user: "User" = Relationship(
        back_populates="payments_appealed",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.appeal_requested_by_user_id"},
    )
    proof_stored_artifact: "StoredArtifact" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.proof_stored_artifact_id"},
    )
    counterparty_stored_artifact: "StoredArtifact" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.counterparty_stored_artifact_id"},
    )
    trust_events: List["TrustEvent"] = Relationship(back_populates="payment_record")
