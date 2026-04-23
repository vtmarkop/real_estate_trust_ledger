import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from app.models.common import TimestampedModel, ensure_utc, utcnow

if TYPE_CHECKING:
    from app.models.user import User


class AuthSession(TimestampedModel, table=True):
    __tablename__ = "auth_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(index=True, unique=True, nullable=False, max_length=64)
    expires_at: datetime = Field(nullable=False)
    revoked_at: Optional[datetime] = Field(default=None, nullable=True)
    last_seen_at: datetime = Field(default_factory=utcnow, nullable=False)
    ip_address: Optional[str] = Field(default=None, max_length=64)
    user_agent: Optional[str] = Field(default=None, max_length=512)

    user: "User" = Relationship(back_populates="sessions")

    def is_active(self, *, now: Optional[datetime] = None) -> bool:
        current = ensure_utc(now or utcnow())
        expires_at = ensure_utc(self.expires_at)
        return self.revoked_at is None and current < expires_at
