from datetime import datetime, timezone, timedelta
from sqlmodel import Session
from passlib.context import CryptContext
from app.core.db import engine  # <-- Αν το engine είναι αλλού, άλλαξε αυτό το import
from app.models.user import User, UserRole
from app.models.property import Property
from app.models.ticket import Ticket, TicketPriority, TicketStatus
from app.models.payment import Payment, PaymentStatus

# Εργαλείο για να κρυπτογραφήσουμε τον κωδικό "123456"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def run_seed():
    with Session(engine) as session:
        print("⏳ Δημιουργία δεδομένων...")
        
        # 1. Δημιουργία 3 Χρηστών
        judge = User(
            email="judge@test.com", 
            hashed_password=pwd_context.hash("123456"), 
            full_name="Σοφία (Δικαστής)", 
            role=UserRole.JUDGE
        )
        landlord = User(
            email="owner@test.com", 
            hashed_password=pwd_context.hash("123456"), 
            full_name="Γιώργος (Ιδιοκτήτης)", 
            role=UserRole.LANDLORD
        )
        tenant = User(
            email="tenant@test.com", 
            hashed_password=pwd_context.hash("123456"), 
            full_name="Μαρία (Ενοικιαστής)", 
            role=UserRole.TENANT
        )
        
        session.add_all([judge, landlord, tenant])
        session.commit()
        
        # 2. Δημιουργία Ακινήτου
        prop = Property(
            title="Διαμέρισμα στο Κέντρο", 
            address="Ερμού 15, Αθήνα", 
            price=600.0, 
            owner_id=landlord.id, 
            tenant_id=tenant.id, 
            judge_id=judge.id
        )
        session.add(prop)
        session.commit()

        # 3. Δημιουργία ενός ανοιχτού Ticket
        now = datetime.now(timezone.utc)
        timestamp = now.strftime("%d/%m/%Y %H:%M")
        
        ticket = Ticket(
            title="Διαρροή στον θερμοσίφωνα",
            description="Στάζει νερό από το ταβάνι του μπάνιου. Χρειάζεται άμεσα υδραυλικός.",
            property_id=prop.id,
            creator_id=tenant.id,
            priority=TicketPriority.HIGH,
            status=TicketStatus.OPEN,
            dispute_comment=f"🕒 {timestamp} - [Δημιουργός] -> ΑΝΟΙΓΜΑ: Διαρροή στον θερμοσίφωνα",
            attachment_urls=[]
        )
        session.add(ticket)
        session.commit()
        
        # 4. Δημιουργία Πληρωμών
        
        # Α. Μία ολοκληρωμένη πληρωμή ενοικίου (πριν 10 μέρες)
        past_date = now - timedelta(days=10)
        past_timestamp = past_date.strftime("%d/%m/%Y %H:%M")
        payment_1 = Payment(
            amount=600.0,
            description="[Ενοίκιο] Ενοίκιο Μαρτίου",
            status=PaymentStatus.COMPLETED,
            due_date=past_date.date(),
            paid_at=past_date,
            property_id=prop.id,
            tenant_id=tenant.id,
            attachment_urls=[],
            dispute_comment=f"🕒 {past_timestamp} - [Ενοικιαστής] -> ΥΠΟΒΟΛΗ: [Ενοίκιο] Ενοίκιο Μαρτίου || 🕒 {past_timestamp} - [Ιδιοκτήτης] -> COMPLETED"
        )
        
        # Β. Μία αμφισβητούμενη πληρωμή (συνδεδεμένη με το ticket)
        short_ticket_id = str(ticket.id)[:6].upper()
        payment_2 = Payment(
            amount=150.0,
            description=f"[Ticket #{short_ticket_id} | Διαρροή στον θερμοσίφωνα] Έξοδα Υδραυλικού",
            status=PaymentStatus.DISPUTED,
            due_date=now.date(),
            paid_at=now,
            property_id=prop.id,
            tenant_id=tenant.id,
            attachment_urls=[],
            dispute_comment=f"🕒 {timestamp} - [Ενοικιαστής] -> ΥΠΟΒΟΛΗ: Απόδειξη υδραυλικού || 🕒 {timestamp} - [Ιδιοκτήτης] -> REJECTED: Δεν είχαμε συμφωνήσει τέτοιο ποσό. || 🕒 {timestamp} - [Ενοικιαστής] -> DISPUTED: Ζητώ παρέμβαση διαιτησίας"
        )
        
        session.add_all([payment_1, payment_2])
        session.commit()

        print("✅ Η βάση γέμισε επιτυχώς με Χρήστες, Ακίνητα, Tickets και Πληρωμές! Μπορείς να συνδεθείς.")

if __name__ == "__main__":
    run_seed()