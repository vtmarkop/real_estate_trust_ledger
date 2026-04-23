from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import Tenancy, TrustEvent
from app.schemas.trust_event import TrustEventResponse
from app.services.trust_events import build_trust_event_response


router = APIRouter(prefix="/trust-events", tags=["trust-events"])


def ensure_tenancy_history_access(
    *,
    tenancy: Tenancy,
    current_user,
) -> None:
    if current_user.system_role.can_access_admin_surfaces:
        return
    if current_user.id in {
        tenancy.tenant_user_id,
        tenancy.landlord_user_id,
        tenancy.created_by_user_id,
    }:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have access to this tenancy history.",
    )


@router.get("/mine", response_model=list[TrustEventResponse])
def list_my_trust_events(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[TrustEventResponse]:
    trust_events = session.exec(
        select(TrustEvent)
        .where(TrustEvent.subject_user_id == current_user.id)
        .order_by(TrustEvent.created_at.desc())
    ).all()
    return [
        build_trust_event_response(session=session, trust_event=trust_event)
        for trust_event in trust_events
    ]


@router.get("/tenancies/{tenancy_id}", response_model=list[TrustEventResponse])
def list_tenancy_trust_events(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[TrustEventResponse]:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    ensure_tenancy_history_access(tenancy=tenancy, current_user=current_user)

    trust_events = session.exec(
        select(TrustEvent)
        .where(TrustEvent.tenancy_id == tenancy_id)
        .order_by(TrustEvent.created_at.asc())
    ).all()
    return [
        build_trust_event_response(session=session, trust_event=trust_event)
        for trust_event in trust_events
    ]
