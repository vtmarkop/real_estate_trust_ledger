import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException
from sqlmodel import select, or_
from app.api.deps import SessionDep, CurrentUser
from app.models.ticket import Ticket, TicketStatus
from app.models.property import Property
from app.models.user import User, UserRole
from app.models.score_history import ScoreHistory
from app.schemas import TicketCreate, TicketResponse, TicketStatusUpdate
from datetime import datetime, timezone

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# 1. CREATE TICKET
@router.post("/", response_model=TicketResponse)
def create_ticket(ticket_in: TicketCreate, session: SessionDep, current_user: CurrentUser):
    property_db = session.get(Property, ticket_in.property_id)
    if not property_db:
        raise HTTPException(status_code=404, detail="Το ακίνητο δεν βρέθηκε")

    if property_db.owner_id != current_user.id and property_db.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Δεν έχετε πρόσβαση σε αυτό το ακίνητο")

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%d/%m/%Y %H:%M")
    
    attachment_msg = ""
    if ticket_in.attachment_urls:
        urls_joined = ",".join(ticket_in.attachment_urls)
        attachment_msg = f" 📎 [ΑΡΧΕΙΑ:{urls_joined}]"
        
    initial_log = f"🕒 {timestamp} - [Δημιουργός] -> ΑΝΟΙΓΜΑ: {ticket_in.description}{attachment_msg}"

    new_ticket = Ticket(
        title=ticket_in.title,
        description=ticket_in.description,
        property_id=ticket_in.property_id,
        priority=ticket_in.priority,
        creator_id=current_user.id,
        attachment_urls=ticket_in.attachment_urls,
        dispute_comment=initial_log
    )
    session.add(new_ticket)
    session.commit()
    session.refresh(new_ticket)
    return new_ticket

# 2. GET TICKETS
@router.get("/my-tickets", response_model=List[TicketResponse])
def get_my_tickets(session: SessionDep, current_user: CurrentUser):
    if current_user.role == UserRole.JUDGE:
        statement = select(Ticket).join(Property).where(
            Property.judge_id == current_user.id
        ).order_by(Ticket.created_at.desc())
    else:
        statement = select(Ticket).join(Property).where(
            or_(Property.owner_id == current_user.id, Property.tenant_id == current_user.id)
        ).order_by(Ticket.created_at.desc())
        
    return session.exec(statement).all()

# 3. UPDATE STATUS & TIMELINE
@router.patch("/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(
    ticket_id: uuid.UUID, 
    status_update: TicketStatusUpdate, 
    session: SessionDep, 
    current_user: CurrentUser
):
    ticket_db = session.get(Ticket, ticket_id)
    if not ticket_db:
        raise HTTPException(status_code=404, detail="Το αίτημα δεν βρέθηκε")
    
    # 1. FETCH PROPERTY FIRST (Fixes the 500 error!)
    property_db = session.get(Property, ticket_db.property_id)
    if not property_db:
        raise HTTPException(status_code=404, detail="Το ακίνητο δεν βρέθηκε")

    # 2. LOCK IF CLOSED
    if ticket_db.status == TicketStatus.CLOSED or ticket_db.status == "closed":
        raise HTTPException(status_code=400, detail="Η υπόθεση έχει κλείσει οριστικά και δεν επιδέχεται αλλαγές.")

    # 3. ROLE IDENTIFICATION
    is_judge = current_user.role == UserRole.JUDGE
    is_owner = current_user.id == property_db.owner_id
    is_tenant = current_user.id == property_db.tenant_id

    if not (is_judge or is_owner or is_tenant):
        raise HTTPException(status_code=403, detail="Δεν έχετε πρόσβαση σε αυτό το αίτημα.")

    status_to_check = status_update.status.value.lower() if hasattr(status_update.status, 'value') else str(status_update.status).lower()
    ticket_current_status = ticket_db.status.value.lower() if hasattr(ticket_db.status, 'value') else str(ticket_db.status).lower()

    # 4. STRICT PERMISSION LOGIC (Matches Payments perfectly)
    if is_tenant:
        # Tenant can ONLY appeal (Resolved/Rejected -> Disputed)
        if status_to_check == "disputed" and ticket_current_status in ["resolved", "rejected"]:
            pass 
        else:
            raise HTTPException(status_code=403, detail="Ως ενοικιαστής, μπορείτε μόνο να κάνετε ένσταση σε επιλυμένα/απορριφθέντα αιτήματα.")

    if is_owner:
        # Landlord cannot permanently close a ticket
        if status_to_check == "closed":
            raise HTTPException(status_code=403, detail="Μόνο ο Δικαστής μπορεί να κλείσει οριστικά ένα αίτημα.")

    # Helper for penalty scores
    def adjust_user_score(u_id, amount, reason):
        target_user = session.get(User, u_id)
        if not target_user: return
        
        if u_id == property_db.owner_id:
            target_user.landlord_score = max(0.0, min(100.0, target_user.landlord_score + amount))
        elif u_id == property_db.tenant_id:
            target_user.tenant_score = max(0.0, min(100.0, target_user.tenant_score + amount))
        
        log = ScoreHistory(
            user_id=u_id,
            reference_id=ticket_db.id,
            amount_changed=amount,
            reason=reason
        )
        session.add(target_user)
        session.add(log)

    # JUDGE VERDICT LOGIC
    if is_judge:
        if ticket_db.guilty_party_id and ticket_db.score_impact > 0:
            adjust_user_score(ticket_db.guilty_party_id, abs(ticket_db.score_impact), "Αναθεώρηση απόφασης: Ακύρωση προηγούμενης ποινής.")

        if status_update.guilty_party_id is not None and status_update.score_impact > 0:
            clean_impact = abs(status_update.score_impact)
            adjust_user_score(status_update.guilty_party_id, -clean_impact, status_update.arbitration_notes or "Έκδοση τελικής απόφασης Διαιτησίας.")
            ticket_db.score_impact = clean_impact
            ticket_db.guilty_party_id = status_update.guilty_party_id
            ticket_db.arbitration_notes = status_update.arbitration_notes
        else:
            ticket_db.score_impact = 0.0
            ticket_db.guilty_party_id = None
            ticket_db.arbitration_notes = status_update.arbitration_notes

    # --- TIMELINE LOG GENERATION ---
    timestamp = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M")
    
    if is_judge: role_str = "Δικαστής"
    elif is_owner: role_str = "Ιδιοκτήτης"
    else: role_str = "Ενοικιαστής"

    attachment_msg = ""
    if status_update.new_attachment_urls:
        urls_joined = ",".join(status_update.new_attachment_urls)
        attachment_msg = f" 📎 [ΑΡΧΕΙΑ:{urls_joined}]"

    status_str = status_update.status.value.upper() if hasattr(status_update.status, 'value') else str(status_update.status).upper()
    
    new_log = f"🕒 {timestamp} - [{role_str}] -> {status_str}{attachment_msg}"
    
    if status_update.comment:
        new_log += f": {status_update.comment}"

    if ticket_db.dispute_comment:
        ticket_db.dispute_comment = f"{ticket_db.dispute_comment} || {new_log}"
    else:
        ticket_db.dispute_comment = new_log
        
    # Append files
    if status_update.new_attachment_urls:
        current_urls = ticket_db.attachment_urls or []
        ticket_db.attachment_urls = list(current_urls) + status_update.new_attachment_urls

    ticket_db.status = status_update.status
    
    session.add(ticket_db)
    session.commit()
    session.refresh(ticket_db)
    return ticket_db

@router.get("/{ticket_id}/timeline")
def get_ticket_timeline(ticket_id: uuid.UUID, session: SessionDep, current_user: CurrentUser):
    statement = select(ScoreHistory).where(ScoreHistory.reference_id == ticket_id).order_by(ScoreHistory.created_at.asc())
    history = session.exec(statement).all()
    
    timeline = []
    for entry in history:
        target_user = session.get(User, entry.user_id)
        timeline.append({
            "id": entry.id,
            "amount": entry.amount_changed,
            "reason": entry.reason,
            "created_at": entry.created_at,
            "user_name": target_user.full_name if target_user else "Άγνωστος"
        })
    return timeline