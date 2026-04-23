import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import ReferenceRequestStatus

if TYPE_CHECKING:
    from app.models.evidence import EvidenceDocument
    from app.models.tenancy import Tenancy
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class ReferenceRequest(TimestampedModel, table=True):
    __tablename__ = "reference_requests"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenancy_id: uuid.UUID = Field(foreign_key="tenancies.id", nullable=False, index=True)
    subject_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    requested_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    requested_from_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    status: ReferenceRequestStatus = Field(
        default=ReferenceRequestStatus.PENDING,
        nullable=False,
        max_length=32,
    )
    message: Optional[str] = Field(default=None, nullable=True, max_length=1000)
    fulfilled_at: Optional[datetime] = Field(default=None, nullable=True)

    tenancy: "Tenancy" = Relationship(back_populates="reference_requests")
    subject_user: "User" = Relationship(
        back_populates="reference_requests_as_subject",
        sa_relationship_kwargs={"foreign_keys": "ReferenceRequest.subject_user_id"},
    )
    requested_by_user: "User" = Relationship(
        back_populates="reference_requests_created",
        sa_relationship_kwargs={"foreign_keys": "ReferenceRequest.requested_by_user_id"},
    )
    requested_from_user: "User" = Relationship(
        back_populates="reference_requests_to_fulfill",
        sa_relationship_kwargs={"foreign_keys": "ReferenceRequest.requested_from_user_id"},
    )
    evidence_documents: List["EvidenceDocument"] = Relationship(back_populates="reference_request")
    trust_events: List["TrustEvent"] = Relationship(back_populates="reference_request")
