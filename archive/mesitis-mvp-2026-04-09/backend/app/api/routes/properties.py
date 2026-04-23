# app/api/routes/properties.py
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query # Προσθήκη Query
from sqlmodel import select, or_
from app.api.deps import SessionDep, CurrentUser
from app.models.property import Property
from app.models.user import User, UserRole
from app.schemas import PropertyCreate, PropertyResponse, AssignTenantRequest

router = APIRouter(prefix="/properties", tags=["Properties"])

# 1. ΔΗΜΙΟΥΡΓΙΑ ΑΚΙΝΗΤΟΥ
@router.post("/", response_model=PropertyResponse)
def create_property(property_in: PropertyCreate, session: SessionDep, current_user: CurrentUser):
    # Μόνο οι ιδιοκτήτες μπορούν να προσθέσουν ακίνητα
    if current_user.role != UserRole.LANDLORD:
        raise HTTPException(status_code=403, detail="Μόνο οι ιδιοκτήτες μπορούν να προσθέσουν ακίνητα.")
    
    new_property = Property(
        title=property_in.title,
        address=property_in.address,
        price=property_in.price,
        owner_id=current_user.id,
        tenant_id=property_in.tenant_id,
        judge_id=property_in.judge_id # Προσθήκη judge_id αν οριστεί κατά τη δημιουργία
    )
    session.add(new_property)
    session.commit()
    session.refresh(new_property)
    return new_property

# 2. ΛΙΣΤΑ ΑΚΙΝΗΤΩΝ (ΜΕ ΦΙΛΤΡΟ ΡΟΛΟΥ ΚΑΙ MODE)
@router.get("/my-properties", response_model=List[PropertyResponse])
def get_my_properties(
    session: SessionDep, 
    current_user: CurrentUser,
    mode: str = Query("landlord") # <--- ΠΡΟΣΘΗΚΗ: Mode από το Frontend
):
    # Αν είναι Δικαστής, βλέπει ΜΟΝΟ τα ακίνητα που του έχουν ανατεθεί
    if current_user.role == UserRole.JUDGE:
        statement = select(Property).where(Property.judge_id == current_user.id)
    else:
        # Landlords και Tenants βλέπουν μόνο όσα αφορούν το τρέχον mode τους
        if mode == "landlord":
            statement = select(Property).where(Property.owner_id == current_user.id)
        else:
            statement = select(Property).where(Property.tenant_id == current_user.id)
        
    properties = session.exec(statement).all()
    return properties

# 3. ΑΝΑΘΕΣΗ ΕΝΟΙΚΙΑΣΤΗ (ΑΠΟ ΤΟΝ ΙΔΙΟΚΤΗΤΗ)
@router.patch("/{property_id}/assign-tenant", response_model=PropertyResponse)
def assign_tenant(
    property_id: uuid.UUID, 
    req: AssignTenantRequest, 
    session: SessionDep, 
    current_user: CurrentUser
):
    property_db = session.get(Property, property_id)
    if not property_db:
        raise HTTPException(status_code=404, detail="Το ακίνητο δεν βρέθηκε")
        
    if property_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Δεν έχετε δικαίωμα διαχείρισης σε αυτό το ακίνητο")
        
    property_db.tenant_id = req.tenant_id
    session.add(property_db)
    session.commit()
    session.refresh(property_db)
    return property_db

# 4. ΑΝΑΘΕΣΗ ΔΙΚΑΣΤΗ (ΑΠΟ ΤΟΝ ΙΔΙΟΚΤΗΤΗ)
@router.patch("/{property_id}/assign-judge/{judge_id}", response_model=PropertyResponse)
def assign_judge(
    property_id: uuid.UUID, 
    judge_id: uuid.UUID, 
    session: SessionDep, 
    current_user: CurrentUser
):
    # Εύρεση ακινήτου
    property_db = session.get(Property, property_id)
    if not property_db:
        raise HTTPException(status_code=404, detail="Το ακίνητο δεν βρέθηκε")
    
    # Μόνο ο ιδιοκτήτης μπορεί να ορίσει δικαστή
    if property_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Δεν έχετε δικαίωμα διαχείρισης σε αυτό το ακίνητο")

    # Έλεγχος αν ο επιλεγμένος χρήστης είναι πράγματι Δικαστής
    judge_user = session.get(User, judge_id)
    if not judge_user or judge_user.role != UserRole.JUDGE:
        raise HTTPException(status_code=400, detail="Ο επιλεγμένος χρήστης δεν είναι Δικαστής")

    # Ενημέρωση
    property_db.judge_id = judge_id
    session.add(property_db)
    session.commit()
    session.refresh(property_db)
    return property_db