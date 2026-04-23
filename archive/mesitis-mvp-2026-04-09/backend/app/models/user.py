import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime

if TYPE_CHECKING:
    from .property import Property
    from .ticket import Ticket
    from .payment import Payment
    from .score_history import ScoreHistory

class UserRole(str, Enum):
    TENANT = "tenant"
    LANDLORD = "landlord"
    JUDGE = "judge"

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.TENANT, nullable=False)
    landlord_score: float = Field(default=100.0)
    tenant_score: float = Field(default=100.0)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    properties_owned: List["Property"] = Relationship(back_populates="owner", sa_relationship_kwargs={"foreign_keys": "Property.owner_id"})
    properties_rented: List["Property"] = Relationship(back_populates="tenant", sa_relationship_kwargs={"foreign_keys": "Property.tenant_id"})
    properties_managed: List["Property"] = Relationship(back_populates="manager", sa_relationship_kwargs={"foreign_keys": "Property.manager_id"})
    tickets: List["Ticket"] = Relationship(
        back_populates="creator", 
        cascade_delete=True, 
        sa_relationship_kwargs={"foreign_keys": "Ticket.creator_id"}
    )
    payments_made: List["Payment"] = Relationship(back_populates="tenant")
    score_history: List["ScoreHistory"] = Relationship(back_populates="user")