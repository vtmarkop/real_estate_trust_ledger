import uuid
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime

if TYPE_CHECKING:
    from .user import User
    from .ticket import Ticket
    from .payment import Payment

class Property(SQLModel, table=True):
    __tablename__ = "properties"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(nullable=False)
    address: str = Field(nullable=False)
    price: float = Field(nullable=False) # <--- ΠΡΟΣΘΗΚΗ ΤΙΜΗΣ
    owner_id: uuid.UUID = Field(foreign_key="users.id")
    tenant_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    manager_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    judge_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    owner: "User" = Relationship(back_populates="properties_owned", sa_relationship_kwargs={"foreign_keys": "[Property.owner_id]"})
    tenant: Optional["User"] = Relationship(back_populates="properties_rented", sa_relationship_kwargs={"foreign_keys": "[Property.tenant_id]"})
    manager: Optional["User"] = Relationship(back_populates="properties_managed", sa_relationship_kwargs={"foreign_keys": "[Property.manager_id]"})
    tickets: List["Ticket"] = Relationship(back_populates="property", cascade_delete=True)
    payments: List["Payment"] = Relationship(back_populates="property", cascade_delete=True)