import uuid
from typing import List
from fastapi import APIRouter, HTTPException
from sqlmodel import select
from app.api.deps import SessionDep, CurrentUser
from app.models.user import User, UserRole
from app.schemas import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/judges", response_model=List[UserResponse])
def get_all_judges(session: SessionDep, current_user: CurrentUser):
    """Επιστρέφει όλους τους χρήστες που έχουν ρόλο JUDGE."""
    statement = select(User).where(User.role == UserRole.JUDGE)
    judges = session.exec(statement).all()
    return judges