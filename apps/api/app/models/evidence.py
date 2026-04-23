import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import EvidenceDocumentType, EvidenceReviewStatus

if TYPE_CHECKING:
    from app.models.reference_request import ReferenceRequest
    from app.models.stored_artifact import StoredArtifact
    from app.models.tenancy import Tenancy
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class EvidenceDocument(TimestampedModel, table=True):
    __tablename__ = "evidence_documents"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    tenancy_id: uuid.UUID = Field(foreign_key="tenancies.id", nullable=False, index=True)
    subject_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    uploaded_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    stored_artifact_id: Optional[uuid.UUID] = Field(
        foreign_key="stored_artifacts.id",
        default=None,
        nullable=True,
        index=True,
    )
    reference_request_id: Optional[uuid.UUID] = Field(
        foreign_key="reference_requests.id",
        default=None,
        nullable=True,
        unique=True,
    )
    document_type: EvidenceDocumentType = Field(nullable=False, max_length=64)
    review_status: EvidenceReviewStatus = Field(
        default=EvidenceReviewStatus.SUBMITTED,
        nullable=False,
        max_length=32,
    )
    artifact_name: str = Field(nullable=False, max_length=255)
    summary: str = Field(nullable=False, max_length=1000)
    issuer_name: Optional[str] = Field(default=None, nullable=True, max_length=255)
    document_date: Optional[date] = Field(default=None, nullable=True)
    amount_minor: Optional[int] = Field(default=None, nullable=True, ge=0)
    currency_code: Optional[str] = Field(default=None, nullable=True, max_length=3)
    external_reference: Optional[str] = Field(default=None, nullable=True, max_length=255)
    review_requested_at: datetime = Field(nullable=False)
    reviewed_at: Optional[datetime] = Field(default=None, nullable=True)
    reviewed_by_user_id: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None, nullable=True)
    review_notes: Optional[str] = Field(default=None, nullable=True, max_length=1000)

    tenancy: "Tenancy" = Relationship(back_populates="evidence_documents")
    subject_user: "User" = Relationship(
        back_populates="evidence_documents_as_subject",
        sa_relationship_kwargs={"foreign_keys": "EvidenceDocument.subject_user_id"},
    )
    uploaded_by_user: "User" = Relationship(
        back_populates="evidence_documents_uploaded",
        sa_relationship_kwargs={"foreign_keys": "EvidenceDocument.uploaded_by_user_id"},
    )
    stored_artifact: Optional["StoredArtifact"] = Relationship(back_populates="evidence_document")
    reviewed_by_user: "User" = Relationship(
        back_populates="evidence_documents_reviewed",
        sa_relationship_kwargs={"foreign_keys": "EvidenceDocument.reviewed_by_user_id"},
    )
    reference_request: Optional["ReferenceRequest"] = Relationship(back_populates="evidence_documents")
    trust_events: List["TrustEvent"] = Relationship(back_populates="evidence_document")
