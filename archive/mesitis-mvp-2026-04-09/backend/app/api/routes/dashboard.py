from fastapi import APIRouter, Query
from sqlmodel import select, func
from typing import List
from app.api.deps import SessionDep, CurrentUser
from app.models.property import Property
from app.models.ticket import Ticket, TicketStatus
from app.models.user import UserRole
from app.schemas import TicketResponse, DashboardSummary
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    session: SessionDep, 
    current_user: CurrentUser, 
    mode: str = Query("tenant")
):
    active_statuses = [TicketStatus.OPEN, TicketStatus.IN_PROGRESS]

    # --- GOD MODE: Αν είναι Δικαστής, μετράει όλη την πλατφόρμα ---
    if current_user.role == UserRole.JUDGE:
        total_props = session.exec(select(func.count(Property.id))).one()
        active_tix = session.exec(select(func.count(Ticket.id)).where(Ticket.status.in_(active_statuses))).one()
        recent = session.exec(select(Ticket).order_by(Ticket.created_at.desc()).limit(5)).all()
        
    elif mode == "landlord" and current_user.role == UserRole.LANDLORD:
        total_props = session.exec(select(func.count(Property.id)).where(Property.owner_id == current_user.id)).one()
        active_tix = session.exec(select(func.count(Ticket.id)).join(Property).where(
            Property.owner_id == current_user.id,
            Ticket.status.in_(active_statuses)
        )).one()
        recent = session.exec(select(Ticket).join(Property).where(
            Property.owner_id == current_user.id
        ).order_by(Ticket.created_at.desc()).limit(3)).all()
    else:
        total_props = session.exec(select(func.count(Property.id)).where(Property.tenant_id == current_user.id)).one()
        active_tix = session.exec(select(func.count(Ticket.id)).join(Property).where(
            Property.tenant_id == current_user.id,
            Ticket.status.in_(active_statuses)
        )).one()
        recent = session.exec(select(Ticket).join(Property).where(
            Property.tenant_id == current_user.id
        ).order_by(Ticket.created_at.desc()).limit(3)).all()

    return {
        "total_properties": total_props,
        "active_tickets": active_tix,
        "wallet_balance": 0.0,
        "recent_tickets": recent
    }