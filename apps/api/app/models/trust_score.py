import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel

if TYPE_CHECKING:
    from app.models.user import User


class TrustScoreSnapshot(TimestampedModel, table=True):
    __tablename__ = "trust_score_snapshots"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True, unique=True)
    tenant_score: int = Field(nullable=False, ge=0, le=1000)
    landlord_score: int = Field(nullable=False, ge=0, le=1000)
    verification_strength: int = Field(nullable=False, ge=0, le=100)
    scoring_version: str = Field(nullable=False, max_length=32)
    calculated_at: datetime = Field(nullable=False)

    user: "User" = Relationship(back_populates="trust_score_snapshots")


class TrustScoreHistory(TimestampedModel, table=True):
    __tablename__ = "trust_score_history"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    tenant_score: int = Field(nullable=False, ge=0, le=1000)
    landlord_score: int = Field(nullable=False, ge=0, le=1000)
    verification_strength: int = Field(nullable=False, ge=0, le=100)
    scoring_version: str = Field(nullable=False, max_length=32)
    calculation_reason: str = Field(nullable=False, max_length=100)
    calculated_at: datetime = Field(nullable=False)

    user: "User" = Relationship(back_populates="trust_score_history_entries")
