import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship, Column, DateTime, Enum as SAEnum
from sqlalchemy import Column, JSON

if TYPE_CHECKING:
    from .user import User
    from .property import Property

class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    SUBMITTED = "submitted" # Διατήρηση παλιών αν χρειάζεται
    VERIFIED = "verified"

class Payment(SQLModel, table=True):
    __tablename__ = "payments"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    amount: float = Field(nullable=False)
    description: str = Field(nullable=False)
    # Χρήση sa_column για να εξαναγκάσουμε τη σωστή συμπεριφορά στην PostgreSQL
    # Χρήση sa_column για να εξαναγκάσουμε τη σωστή συμπεριφορά στην PostgreSQL
    status: PaymentStatus = Field(
        sa_column=Column(
            # ΠΡΟΣΘΗΚΗ: values_callable για να στέλνει τα μικρά γράμματα στη βάση
            SAEnum(PaymentStatus, values_callable=lambda obj: [e.value for e in obj]), 
            nullable=False, 
            server_default="pending"
        ),
        default=PaymentStatus.PENDING
    )
    dispute_comment: Optional[str] = Field(default=None)
    due_date: date = Field(nullable=False)
    paid_at: Optional[datetime] = Field(default=None)
    receipt_url: Optional[str] = Field(default=None)
    attachment_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    property_id: uuid.UUID = Field(foreign_key="properties.id")
    tenant_id: uuid.UUID = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    property: "Property" = Relationship(back_populates="payments")
    tenant: "User" = Relationship(back_populates="payments_made")