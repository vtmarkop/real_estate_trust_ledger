import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel

if TYPE_CHECKING:
    from app.models.evidence import EvidenceDocument


class StoredArtifact(TimestampedModel, table=True):
    __tablename__ = "stored_artifacts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    tenancy_id: uuid.UUID = Field(foreign_key="tenancies.id", nullable=False, index=True)
    artifact_purpose: str = Field(default="evidence_document", nullable=False, max_length=64)
    storage_backend: str = Field(default="local_private", nullable=False, max_length=32)
    storage_key: str = Field(nullable=False, unique=True, max_length=500, index=True)
    original_file_name: str = Field(nullable=False, max_length=255)
    content_type: str = Field(nullable=False, max_length=255)
    size_bytes: int = Field(nullable=False, ge=1)
    sha256_hex: str = Field(nullable=False, max_length=64)
    last_accessed_at: Optional[datetime] = Field(default=None, nullable=True)

    evidence_document: Optional["EvidenceDocument"] = Relationship(back_populates="stored_artifact")
