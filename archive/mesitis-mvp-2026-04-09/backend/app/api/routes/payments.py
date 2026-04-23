import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.api.deps import SessionDep, CurrentUser
from app.models.payment import Payment, PaymentStatus
from app.models.property import Property
from app.models.user import User, UserRole
from app.models.score_history import ScoreHistory
from app.schemas import PaymentCreate, PaymentResponse, PaymentStatusUpdate

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("", response_model=PaymentResponse)
def create_payment(payment_in: PaymentCreate, session: SessionDep, current_user: CurrentUser):
    property_db = session.get(Property, payment_in.property_id)
    if not property_db:
        raise HTTPException(status_code=404, detail="Το ακίνητο δεν βρέθηκε")

    if property_db.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Δεν είσαι ο ενοικιαστής")

    now = datetime.now(timezone.utc)
    
# --- ΝΕΟ: Προσθήκη ένδειξης και ΤΩΝ ΙΔΙΩΝ ΤΩΝ LINKS στο ιστορικό ---
    timestamp = now.strftime("%d/%m/%Y %H:%M")
    attachment_msg = ""
    if payment_in.attachment_urls:
        urls_joined = ",".join(payment_in.attachment_urls)
        attachment_msg = f" 📎 [ΑΡΧΕΙΑ:{urls_joined}]"
        
    initial_log = f"🕒 {timestamp} - [Ενοικιαστής] -> ΥΠΟΒΟΛΗ: {payment_in.description}{attachment_msg}"
    
    new_payment = Payment(
        property_id=payment_in.property_id,
        tenant_id=current_user.id,
        amount=payment_in.amount,
        description=payment_in.description,
        due_date=now.date(),
        paid_at=now,
        status=PaymentStatus.PENDING.value,
        dispute_comment=initial_log,
        attachment_urls=payment_in.attachment_urls # ΣΩΣΤΟ (ΠΛΗΘΥΝΤΙΚΟΣ)
    )
    session.add(new_payment)
    session.commit()
    session.refresh(new_payment)
    return new_payment

# 2. ΛΗΨΗ ΠΛΗΡΩΜΩΝ
@router.get("/my-payments", response_model=List[PaymentResponse])
def get_my_payments(
    session: SessionDep, 
    current_user: CurrentUser,
    mode: str = Query("tenant")
):
    if current_user.role == UserRole.JUDGE:
        statement = select(Payment).join(Property).where(Property.judge_id == current_user.id)
    elif mode == "landlord":
        statement = select(Payment).join(Property).where(Property.owner_id == current_user.id)
    else:
        statement = select(Payment).where(Payment.tenant_id == current_user.id)
        
    payments = session.exec(statement).all()
    return payments


# 3. ΕΝΗΜΕΡΩΣΗ ΚΑΤΑΣΤΑΣΗΣ ΚΑΙ ΠΟΙΝΩΝ (Απόφαση / Έγκριση / Απόρριψη)
@router.patch("/{payment_id}/status", response_model=PaymentResponse)
def update_payment_status(
    payment_id: uuid.UUID, 
    status_update: PaymentStatusUpdate, 
    session: SessionDep, 
    current_user: CurrentUser
):
    payment_db = session.get(Payment, payment_id)
    if not payment_db:
        raise HTTPException(status_code=404, detail="Η πληρωμή δεν βρέθηκε")
        
    property_db = session.get(Property, payment_db.property_id)
    current_s = payment_db.status.name if hasattr(payment_db.status, 'name') else str(payment_db.status).upper()

    # --- ΕΛΕΓΧΟΣ ΔΙΚΑΙΩΜΑΤΩΝ ---
    if current_user.role == UserRole.JUDGE:
        if property_db.judge_id != current_user.id:
            raise HTTPException(status_code=403, detail="Δεν έχετε δικαιοδοσία")
        if current_s not in ["DISPUTED", "REJECTED"]:
            raise HTTPException(status_code=400, detail="Μόνο αμφισβητούμενες πληρωμές δικάζονται")
    elif current_user.id == property_db.owner_id:
        if current_s != "PENDING":
            raise HTTPException(status_code=400, detail="Η πληρωμή έχει ήδη υποστεί επεξεργασία")
    else:
        # Ενοικιαστής
        if current_s != "REJECTED" and status_update.status.upper() != "DISPUTED":
             raise HTTPException(status_code=400, detail="Μόνο ένσταση επιτρέπεται")

    # --- ΕΠΙΒΟΛΗ ΠΟΙΝΗΣ ΒΑΘΜΟΛΟΓΙΑΣ (Μόνο από Δικαστή) ---
    if current_user.role == UserRole.JUDGE and status_update.score_impact != 0 and status_update.guilty_party_id:
        guilty_user = session.get(User, status_update.guilty_party_id)
        if guilty_user:
            if guilty_user.role == UserRole.LANDLORD:
                guilty_user.landlord_score += status_update.score_impact
            else:
                guilty_user.tenant_score += status_update.score_impact
            
            score_entry = ScoreHistory(
                user_id=guilty_user.id,
                amount_changed=status_update.score_impact,
                reason=f"Απόφαση Διαιτησίας (Πληρωμή): {status_update.comment or 'Χωρίς σχόλιο'}",
                reference_id=payment_db.id
            )
            session.add(guilty_user)
            session.add(score_entry)

# --- ΙΣΤΟΡΙΚΟ ΣΧΟΛΙΩΝ ΜΕ TIMESTAMPS ΚΑΙ ΑΡΧΕΙΑ ---
    timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
    
    if current_user.role == UserRole.JUDGE:
        role_str = "Δικαστής"
    elif current_user.id == property_db.owner_id:
        role_str = "Ιδιοκτήτης"
    else:
        role_str = "Ενοικιαστής"

    attachment_msg = ""
    if status_update.new_attachment_urls:
        urls_joined = ",".join(status_update.new_attachment_urls)
        attachment_msg = f" 📎 [ΑΡΧΕΙΑ:{urls_joined}]"

    new_log = f"🕒 {timestamp} - [{role_str}] -> {status_update.status.upper()}{attachment_msg}"
    
    if status_update.comment:
        new_log += f": {status_update.comment}"

    if payment_db.dispute_comment:
        payment_db.dispute_comment = f"{payment_db.dispute_comment} || {new_log}"
    else:
        payment_db.dispute_comment = new_log

    # --- ΕΝΗΜΕΡΩΣΗ ΑΡΧΕΙΩΝ (Append) ---
    if status_update.new_attachment_urls:
        current_urls = payment_db.attachment_urls or []
        # Ξαναδηλώνουμε τη λίστα για να καταλάβει το SQLModel/PostgreSQL την αλλαγή στο JSON
        payment_db.attachment_urls = list(current_urls) + status_update.new_attachment_urls

    # --- ΕΝΗΜΕΡΩΣΗ STATUS ---
    try:
        new_status_enum = PaymentStatus[status_update.status.upper()]
# ... (συνεχίζει κανονικά)
        payment_db.status = new_status_enum.value
    except KeyError:
        raise HTTPException(status_code=422, detail="Άκυρο status")

    session.add(payment_db)
    session.commit()
    session.refresh(payment_db)
    return payment_db