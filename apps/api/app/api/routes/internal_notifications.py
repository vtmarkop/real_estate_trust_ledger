from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select

from app.api.deps import SessionDep, require_system_roles
from app.models import NotificationDelivery
from app.schemas.notification import NotificationDeliveryResponse
from app.services.notifications import build_notification_delivery_response
from trustledger_domain import NotificationDeliveryStatus, SystemRole


router = APIRouter(prefix="/internal/notifications", tags=["internal-notifications"])


def get_notification_delivery_or_404(
    *,
    session: SessionDep,
    notification_delivery_id: UUID,
) -> NotificationDelivery:
    notification_delivery = session.get(NotificationDelivery, notification_delivery_id)
    if not notification_delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification delivery not found.",
        )
    return notification_delivery


@router.get(
    "",
    response_model=list[NotificationDeliveryResponse],
)
def list_notification_deliveries(
    session: SessionDep,
    status_filter: NotificationDeliveryStatus | None = Query(default=None),
    due_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> list[NotificationDeliveryResponse]:
    query = select(NotificationDelivery)
    if status_filter is not None:
        query = query.where(NotificationDelivery.status == status_filter)
    if due_only:
        from app.models.common import utcnow

        query = query.where(NotificationDelivery.scheduled_for <= utcnow())

    notification_deliveries = session.exec(
        query.order_by(
            NotificationDelivery.scheduled_for.asc(),
            NotificationDelivery.created_at.asc(),
        )
    ).all()[:limit]
    return [
        build_notification_delivery_response(
            session=session,
            notification_delivery=notification_delivery,
        )
        for notification_delivery in notification_deliveries
    ]


@router.get(
    "/{notification_delivery_id}",
    response_model=NotificationDeliveryResponse,
)
def get_notification_delivery(
    notification_delivery_id: UUID,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> NotificationDeliveryResponse:
    notification_delivery = get_notification_delivery_or_404(
        session=session,
        notification_delivery_id=notification_delivery_id,
    )
    return build_notification_delivery_response(
        session=session,
        notification_delivery=notification_delivery,
    )
