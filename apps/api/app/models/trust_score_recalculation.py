import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel, utcnow
from trustledger_domain import ScoreRecalculationScope, ScoreRecalculationStatus

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class TrustScoreRecalculationBatch(TimestampedModel, table=True):
    __tablename__ = "trust_score_recalculation_batches"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    requested_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    organization_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="organizations.id",
        nullable=True,
        index=True,
    )
    scope_type: ScoreRecalculationScope = Field(nullable=False, max_length=50)
    calculation_reason: str = Field(nullable=False, max_length=100)
    status: ScoreRecalculationStatus = Field(
        default=ScoreRecalculationStatus.PENDING,
        nullable=False,
        max_length=32,
    )
    requested_user_count: int = Field(default=0, nullable=False, ge=0)
    scheduled_for: datetime = Field(default_factory=utcnow, nullable=False)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    last_error: str | None = Field(default=None, nullable=True, max_length=500)

    requested_by_user: "User" = Relationship(
        back_populates="requested_trust_score_recalculation_batches",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationBatch.requested_by_user_id"},
    )
    organization: "Organization" = Relationship(back_populates="trust_score_recalculation_batches")
    recalculation_requests: List["TrustScoreRecalculationRequest"] = Relationship(back_populates="batch")


class TrustScoreRecalculationRequest(TimestampedModel, table=True):
    __tablename__ = "trust_score_recalculation_requests"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    batch_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="trust_score_recalculation_batches.id",
        nullable=True,
        index=True,
    )
    requested_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    processed_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    calculation_reason: str = Field(nullable=False, max_length=100)
    status: ScoreRecalculationStatus = Field(
        default=ScoreRecalculationStatus.PENDING,
        nullable=False,
        max_length=32,
    )
    attempt_count: int = Field(default=0, nullable=False, ge=0)
    scheduled_for: datetime = Field(default_factory=utcnow, nullable=False)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    last_error: str | None = Field(default=None, nullable=True, max_length=500)
    result_tenant_score: int | None = Field(default=None, nullable=True, ge=0, le=1000)
    result_landlord_score: int | None = Field(default=None, nullable=True, ge=0, le=1000)
    result_verification_strength: int | None = Field(default=None, nullable=True, ge=0, le=100)
    result_scoring_version: str | None = Field(default=None, nullable=True, max_length=32)
    result_calculated_at: datetime | None = Field(default=None, nullable=True)

    user: "User" = Relationship(
        back_populates="trust_score_recalculation_requests",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationRequest.user_id"},
    )
    requested_by_user: "User" = Relationship(
        back_populates="requested_trust_score_recalculation_requests",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationRequest.requested_by_user_id"},
    )
    processed_by_user: "User" = Relationship(
        back_populates="processed_trust_score_recalculation_requests",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationRequest.processed_by_user_id"},
    )
    batch: "TrustScoreRecalculationBatch" = Relationship(back_populates="recalculation_requests")
