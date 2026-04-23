from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select, desc
from app.api.deps import SessionDep, CurrentUser
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, UserRole
from app.schemas import UserCreate, UserResponse, Token
from typing import List, Optional
from app.models.score_history import ScoreHistory

router = APIRouter(prefix="/auth", tags=["Authentication"])

# 1. ΕΓΓΡΑΦΗ ΧΡΗΣΤΗ
@router.post("/register", response_model=UserResponse)
def register_user(user_in: UserCreate, session: SessionDep):
    # Έλεγχος αν υπάρχει ήδη το email
    user_exists = session.exec(select(User).where(User.email == user_in.email)).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Το email χρησιμοποιείται ήδη")
    
    # Δημιουργία χρήστη (Πλήρης λίστα πεδίων για αποφυγή σφαλμάτων)
    new_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
        landlord_score=100.0,
        tenant_score=100.0,
        is_active=True
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

# 2. LOGIN (ΜΕ HTTP-ONLY COOKIE)
@router.post("/login", response_model=Token)
def login(response: Response, session: SessionDep, form_data: OAuth2PasswordRequestForm = Depends()):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Λάθος email ή κωδικός")
    
    # Δημιουργία Token (Χρησιμοποιούμε το email ή το ID ως subject)
    access_token = create_access_token(subject=str(user.id))
    
    # Set HttpOnly Cookie για ασφάλεια
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Αλλαγή σε True αν έχεις HTTPS
        samesite="lax",
        max_age=3600
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# 3. LOGOUT
@router.post("/logout")
def logout(response: Response):
    """Διαγράφει το HttpOnly Cookie"""
    response.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return {"message": "Επιτυχής αποσύνδεση."}

# 4. ΠΡΟΦΙΛ ΧΡΗΣΤΗ
@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: CurrentUser):
    return current_user

# 5. ΙΣΤΟΡΙΚΟ SCORE
@router.get("/me/score-history")
def get_my_score_history(session: SessionDep, current_user: CurrentUser):
    statement = select(ScoreHistory).where(
        ScoreHistory.user_id == current_user.id
    ).order_by(desc(ScoreHistory.created_at))
    history = session.exec(statement).all()
    return history

# 6. ΛΙΣΤΑ ΧΡΗΣΤΩΝ (ΓΙΑ DROPDOWNS)
@router.get("/users", response_model=List[UserResponse])
def get_users_by_role(
    session: SessionDep, 
    current_user: CurrentUser,
    role: Optional[UserRole] = Query(None, description="Φιλτράρισμα βάσει ρόλου")
):
    statement = select(User)
    if role:
        statement = statement.where(User.role == role)
    users = session.exec(statement).all()
    return users

# 7. ΕΙΔΙΚΟ ENDPOINT ΓΙΑ ΔΙΚΑΣΤΕΣ (Για να μην κρασάρει το Frontend)
@router.get("/judges", response_model=List[UserResponse])
def get_all_judges(session: SessionDep, current_user: CurrentUser):
    """Επιστρέφει μόνο τους Δικαστές για το dropdown ανάθεσης"""
    statement = select(User).where(User.role == UserRole.JUDGE)
    judges = session.exec(statement).all()
    return judges