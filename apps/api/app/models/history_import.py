import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel
from trustledger_domain import HistoryImportStatus

if TYPE_CHECKING:
    from app.models.tenancy import Tenancy
    from app.models.trust_event import TrustEvent
    from app.models.user import User


class HistoryImport(TimestampedModel, table=True):
    __tablename__ = "history_imports"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    subject_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False, index=True)
    created_by_user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    title: str = Field(nullable=False, max_length=255)
    summary: Optional[str] = Field(default=None, nullable=True, max_length=1000)
    status: HistoryImportStatus = Field(default=HistoryImportStatus.DRAFT, nullable=False, max_length=32)
    submitted_at: Optional[datetime] = Field(default=None, nullable=True)
    reviewed_at: Optional[datetime] = Field(default=None, nullable=True)
    reviewed_by_user_id: Optional[uuid.UUID] = Field(foreign_key="users.id", default=None, nullable=True)
    review_notes: Optional[str] = Field(default=None, nullable=True, max_length=1000)

    subject_user: "User" = Relationship(
        back_populates="history_imports_as_subject",
        sa_relationship_kwargs={"foreign_keys": "HistoryImport.subject_user_id"},
    )
    created_by_user: "User" = Relationship(
        back_populates="history_imports_created",
        sa_relationship_kwargs={"foreign_keys": "HistoryImport.created_by_user_id"},
    )
    reviewed_by_user: "User" = Relationship(
        back_populates="history_imports_reviewed",
        sa_relationship_kwargs={"foreign_keys": "HistoryImport.reviewed_by_user_id"},
    )
    tenancies: List["Tenancy"] = Relationship(back_populates="history_import")
    trust_events: List["TrustEvent"] = Relationship(back_populates="history_import")
