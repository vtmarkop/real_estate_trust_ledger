import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import (
    DisputeVerdictOutcome,
    MaintenanceTicketPriority,
    MaintenanceTicketStatus,
)

if TYPE_CHECKING:
    from app.models.stored_artifact import StoredArtifact
    from app.models.tenancy import Tenancy
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class MaintenanceTicket(TimestampedModel, table=True):
    __tablename__ = "maintenance_tickets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenancy_id: uuid.UUID = Field(foreign_key="tenancies.id", nullable=False, index=True)
    created_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    acknowledged_by_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="users.id",
        nullable=True,
        index=True,
    )
    resolved_by_user_id: uuid.UUID | None = Field(
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
    title: str = Field(nullable=False, max_length=255)
    description: str = Field(nullable=False, max_length=1000)
    priority: MaintenanceTicketPriority = Field(
        default=MaintenanceTicketPriority.NORMAL,
        nullable=False,
        max_length=32,
    )
    ticket_status: MaintenanceTicketStatus = Field(
        default=MaintenanceTicketStatus.OPEN,
        nullable=False,
        max_length=32,
    )
    reported_stored_artifact_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="stored_artifacts.id",
        nullable=True,
        index=True,
    )
    reported_artifact_name: str | None = Field(default=None, nullable=True, max_length=255)
    landlord_response_notes: str | None = Field(default=None, nullable=True, max_length=1000)
    acknowledged_at: datetime | None = Field(default=None, nullable=True)
    resolution_summary: str | None = Field(default=None, nullable=True, max_length=1000)
    resolution_stored_artifact_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="stored_artifacts.id",
        nullable=True,
        index=True,
    )
    resolution_artifact_name: str | None = Field(default=None, nullable=True, max_length=255)
    resolved_at: datetime | None = Field(default=None, nullable=True)
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

    tenancy: "Tenancy" = Relationship(back_populates="maintenance_tickets")
    created_by_user: "User" = Relationship(
        back_populates="maintenance_tickets_created",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.created_by_user_id"},
    )
    acknowledged_by_user: "User" = Relationship(
        back_populates="maintenance_tickets_acknowledged",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.acknowledged_by_user_id"},
    )
    resolved_by_user: "User" = Relationship(
        back_populates="maintenance_tickets_resolved",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.resolved_by_user_id"},
    )
    disputed_by_user: "User" = Relationship(
        back_populates="maintenance_tickets_disputed",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.disputed_by_user_id"},
    )
    review_requested_by_user: "User" = Relationship(
        back_populates="maintenance_tickets_review_requested",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.review_requested_by_user_id"},
    )
    reviewed_by_user: "User" = Relationship(
        back_populates="maintenance_tickets_reviewed",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.reviewed_by_user_id"},
    )
    appeal_requested_by_user: "User" = Relationship(
        back_populates="maintenance_tickets_appealed",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.appeal_requested_by_user_id"},
    )
    reported_stored_artifact: "StoredArtifact" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.reported_stored_artifact_id"},
    )
    resolution_stored_artifact: "StoredArtifact" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.resolution_stored_artifact_id"},
    )
    trust_events: List["TrustEvent"] = Relationship(back_populates="maintenance_ticket")
