import uuid

from sqlmodel import Field

from app.models.common import TimestampedModel
from trustledger_domain import AuditActionType, AuditOutcomeStatus


class AuditLog(TimestampedModel, table=True):
    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    actor_user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True, index=True)
    organization_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="organizations.id",
        nullable=True,
        index=True,
    )
    subject_user_id: uuid.UUID | None = Field(default=None, foreign_key="users.id", nullable=True, index=True)
    action_type: AuditActionType = Field(nullable=False, max_length=64, index=True)
    outcome_status: AuditOutcomeStatus = Field(nullable=False, max_length=32)
    target_type: str | None = Field(default=None, nullable=True, max_length=64)
    target_id: str | None = Field(default=None, nullable=True, max_length=64)
    details: str | None = Field(default=None, nullable=True, max_length=1000)
