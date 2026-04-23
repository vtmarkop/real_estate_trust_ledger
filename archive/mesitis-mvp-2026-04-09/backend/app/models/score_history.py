import uuid
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime

if TYPE_CHECKING:
    from .user import User

class ScoreHistory(SQLModel, table=True):
    __tablename__ = "score_history"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id")
    amount_changed: float = Field(nullable=False)
    reason: str = Field(nullable=False)
    reference_id: Optional[uuid.UUID] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: "User" = Relationship(back_populates="score_history")