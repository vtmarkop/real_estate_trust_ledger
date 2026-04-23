import uuid
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
import jwt

from app.core.config import settings
from app.core.db import engine
from app.models.user import User

# --- 120% Bulletproof: Custom OAuth2 Class ---
class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> Optional[str]:
        # 1. Πρώτη γραμμή άμυνας: Αναζήτηση στο HttpOnly Cookie
        authorization = request.cookies.get("access_token")
        
        # 2. Εναλλακτική: Αναζήτηση στον Header (Για να δουλεύει το Swagger UI)
        if not authorization:
            authorization = request.headers.get("Authorization")
        
        if not authorization:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Μη εξουσιοδοτημένη πρόσβαση (Δεν βρέθηκε Token)"
                )
            else:
                return None
        
        # Αφαίρεση του προθέματος "Bearer " αν υπάρχει
        if authorization.startswith("Bearer "):
            return authorization.split(" ")[1]
        return authorization

# Εφαρμογή του νέου "Έξυπνου Φρουρού"
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/auth/login")

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Μη έγκυρο token (Απουσιάζει το Subject)")
    except jwt.ExpiredSignatureError:
         raise HTTPException(status_code=401, detail="Το token έχει λήξει. Απαιτείται νέα σύνδεση.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Παραποιημένο ή μη έγκυρο token.")
    
    user = session.get(User, uuid.UUID(user_id_str))
    if not user:
        raise HTTPException(status_code=404, detail="Ο χρήστης δεν βρέθηκε στο σύστημα.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Ο λογαριασμός είναι απενεργοποιημένος.")
    
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]