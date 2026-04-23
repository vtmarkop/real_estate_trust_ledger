# app/schemas.py
import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.models.user import UserRole
from app.models.ticket import TicketStatus, TicketPriority
from app.models.payment import PaymentStatus
from sqlmodel import Field, SQLModel, Column, JSON

# 1. Τι στέλνει ο χρήστης για να γραφτεί
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.TENANT

# 2. Τι του επιστρέφουμε (ΧΩΡΙΣ ΤΟΝ ΚΩΔΙΚΟ ΤΟΥ!)
class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    # Αλλαγή: Αντικατάσταση του score με τα πεδία της βάσης για να μη βγάζει ValidationError
    landlord_score: float
    tenant_score: float

# 3. Το ψηφιακό κλειδί
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class PropertyCreate(BaseModel):
    title: str
    address: str
    price: float
    tenant_id: Optional[uuid.UUID] = None
    judge_id: Optional[uuid.UUID] = None # Προσθήκη για τη βάση

class PropertyResponse(BaseModel):
    id: uuid.UUID
    title: str
    address: str
    price: float
    owner_id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    judge_id: Optional[uuid.UUID] = None # Προσθήκη για τη βάση

class TicketCreate(BaseModel):
    title: str
    description: str
    property_id: uuid.UUID
    priority: TicketPriority = TicketPriority.MEDIUM
    attachment_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))

class TicketResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    property_id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime
    arbitration_notes: Optional[str] = None
    score_impact: float = 0.0
    guilty_party_id: Optional[uuid.UUID] = None
    attachment_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    dispute_comment: Optional[str] = None

class PaymentCreate(BaseModel):
    property_id: uuid.UUID
    amount: float
    description: str
    attachment_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))

# Βεβαιώσου ότι έχεις κάνει import το ConfigDict στην αρχή του αρχείου:
# from pydantic import BaseModel, ConfigDict, Field

class PaymentResponse(BaseModel):
    id: uuid.UUID
    property_id: uuid.UUID
    tenant_id: uuid.UUID
    amount: float
    description: str
    status: PaymentStatus  # Αν το έχεις κάνει str, άστο str
    dispute_comment: Optional[str] = None
    created_at: datetime
    attachment_urls: List[str] = Field(default_factory=list, sa_column=Column(JSON))

    # Για Pydantic V2
    model_config = ConfigDict(from_attributes=True)

class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    arbitration_notes: Optional[str] = None
    score_impact: Optional[float] = 0.0
    guilty_party_id: Optional[uuid.UUID] = None
    # --- NEW FIELDS FOR TIMELINE ---
    comment: Optional[str] = None
    new_attachment_urls: Optional[List[str]] = Field(default_factory=list)

# 1. Το Schema για την ανάθεση ενοικιαστή
class AssignTenantRequest(BaseModel):
    tenant_id: uuid.UUID

# 2. Το Schema για το Dashboard
class DashboardSummary(BaseModel):
    total_properties: int
    active_tickets: int
    wallet_balance: float
    recent_tickets: List[TicketResponse]

class PaymentStatusUpdate(BaseModel):
    status: str
    comment: Optional[str] = None # Νέο πεδίο στο αίτημα
    score_impact: Optional[float] = 0.0          # ΠΡΟΣΘΗΚΗ: Ποινή πόντων
    guilty_party_id: Optional[uuid.UUID] = None
    new_attachment_urls: Optional[List[str]] = [] # <--- ΑΥΤΗ Η ΓΡΑΜΜΗ ΠΡΕΠΕΙ ΝΑ ΥΠΑΡΧΕΙ