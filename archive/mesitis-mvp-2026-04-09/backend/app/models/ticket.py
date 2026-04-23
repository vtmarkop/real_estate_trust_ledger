import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Column, String, Relationship
from typing import Optional, List
from sqlalchemy import Column, String, JSON

if TYPE_CHECKING:
    from .property import Property
    from .user import User

# Οι καταστάσεις του αιτήματος
class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    DISPUTED = "disputed"  # <--- ΠΡΟΣΘΗΚΗ
    CLOSED = "closed"

# Οι προτεραιότητες του αιτήματος
class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str
    description: str
    attachment_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    dispute_comment: Optional[str] = Field(default=None)    
    # Η Python βλέπει ENUM, η βάση βλέπει απλό String
    status: TicketStatus = Field(default=TicketStatus.OPEN, sa_column=Column(String))
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM, sa_column=Column(String))
    
    property_id: uuid.UUID = Field(foreign_key="properties.id", nullable=False)
    creator_id: uuid.UUID = Field(foreign_key="users.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    arbitration_notes: Optional[str] = Field(default=None)
    score_impact: float = Field(default=0.0)
    guilty_party_id: Optional[uuid.UUID] = Field(default=None, foreign_key="users.id")

# Οι Συσχετίσεις (Relationships)
    property: "Property" = Relationship(back_populates="tickets")
    
    # --- ΔΙΟΡΘΩΣΗ: Του λέμε ρητά να χρησιμοποιήσει το creator_id ---
    creator: "User" = Relationship(
        back_populates="tickets",
        sa_relationship_kwargs={"foreign_keys": "Ticket.creator_id"}
    )

    # Καλή πρακτική: Ορίζουμε και τη σχέση για τον υπαίτιο (για να μην μπερδευτεί ποτέ ξανά)
    guilty_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Ticket.guilty_party_id"}
    )