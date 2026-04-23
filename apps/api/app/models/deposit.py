import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import DepositStatus, DisputeVerdictOutcome

if TYPE_CHECKING:
    from app.models.stored_artifact import StoredArtifact
    from app.models.tenancy import Tenancy
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class DepositRecord(TimestampedModel, table=True):
    __tablename__ = "deposit_records"
    __table_args__ = (UniqueConstraint("tenancy_id", name="uq_deposit_records_tenancy_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenancy_id: uuid.UUID = Field(foreign_key="tenancies.id", nullable=False, index=True)
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
    held_amount_minor: int = Field(nullable=False, ge=0)
    proposed_return_minor: int = Field(default=0, nullable=False, ge=0)
    withheld_amount_minor: int = Field(default=0, nullable=False, ge=0)
    currency_code: str = Field(nullable=False, max_length=3)
    deposit_status: DepositStatus = Field(default=DepositStatus.HELD, nullable=False, max_length=32)
    move_out_date: date | None = Field(default=None, nullable=True)
    return_due_date: date | None = Field(default=None, nullable=True)
    returned_at: datetime | None = Field(default=None, nullable=True)
    settlement_stored_artifact_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="stored_artifacts.id",
        nullable=True,
        index=True,
    )
    settlement_artifact_name: str | None = Field(default=None, nullable=True, max_length=255)
    settlement_summary: str | None = Field(default=None, nullable=True, max_length=1000)
    settlement_notes: str | None = Field(default=None, nullable=True, max_length=1000)
    dispute_notes: str | None = Field(default=None, nullable=True, max_length=1000)
    counterparty_action_at: datetime | None = Field(default=None, nullable=True)
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

    tenancy: "Tenancy" = Relationship(back_populates="deposit_records")
    created_by_user: "User" = Relationship(
        back_populates="deposit_records_created",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.created_by_user_id"},
    )
    counterparty_action_by_user: "User" = Relationship(
        back_populates="deposit_records_counterparty_actioned",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.counterparty_action_by_user_id"},
    )
    disputed_by_user: "User" = Relationship(
        back_populates="deposit_records_disputed",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.disputed_by_user_id"},
    )
    review_requested_by_user: "User" = Relationship(
        back_populates="deposit_records_review_requested",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.review_requested_by_user_id"},
    )
    reviewed_by_user: "User" = Relationship(
        back_populates="deposit_records_reviewed",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.reviewed_by_user_id"},
    )
    appeal_requested_by_user: "User" = Relationship(
        back_populates="deposit_records_appealed",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.appeal_requested_by_user_id"},
    )
    settlement_stored_artifact: "StoredArtifact" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.settlement_stored_artifact_id"},
    )
    trust_events: List["TrustEvent"] = Relationship(back_populates="deposit_record")
