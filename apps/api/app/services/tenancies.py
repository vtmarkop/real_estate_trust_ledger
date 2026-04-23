from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import Tenancy, User
from app.schemas.tenancy import TenancyResponse


def build_tenancy_response(
    *,
    session: Session,
    tenancy: Tenancy,
) -> TenancyResponse:
    tenant_user = session.get(User, tenancy.tenant_user_id)
    landlord_user = session.get(User, tenancy.landlord_user_id)
    created_by_user = session.get(User, tenancy.created_by_user_id)
    counterparty_confirmed_by_user = (
        session.get(User, tenancy.counterparty_confirmed_by_user_id)
        if tenancy.counterparty_confirmed_by_user_id
        else None
    )
    reviewed_by_user = (
        session.get(User, tenancy.reviewed_by_user_id) if tenancy.reviewed_by_user_id else None
    )

    if not tenant_user or not landlord_user or not created_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenancy participants are unavailable.",
        )

    return TenancyResponse(
        id=tenancy.id,
        history_import_id=tenancy.history_import_id,
        property_id=tenancy.property_id,
        property_label=tenancy.property_label,
        address_line1=tenancy.address_line1,
        city=tenancy.city,
        country_code=tenancy.country_code,
        tenancy_status=tenancy.tenancy_status,
        verification_status=tenancy.verification_status,
        lease_start_date=tenancy.lease_start_date,
        lease_end_date=tenancy.lease_end_date,
        monthly_rent_minor=tenancy.monthly_rent_minor,
        deposit_minor=tenancy.deposit_minor,
        currency_code=tenancy.currency_code,
        tenant_user_id=tenancy.tenant_user_id,
        tenant_full_name=tenant_user.full_name,
        landlord_user_id=tenancy.landlord_user_id,
        landlord_full_name=landlord_user.full_name,
        created_by_user_id=tenancy.created_by_user_id,
        created_by_user_full_name=created_by_user.full_name,
        counterparty_confirmed_at=tenancy.counterparty_confirmed_at,
        counterparty_confirmed_by_user_id=tenancy.counterparty_confirmed_by_user_id,
        counterparty_confirmed_by_user_full_name=(
            counterparty_confirmed_by_user.full_name if counterparty_confirmed_by_user else None
        ),
        review_requested_at=tenancy.review_requested_at,
        reviewed_at=tenancy.reviewed_at,
        reviewed_by_user_id=tenancy.reviewed_by_user_id,
        reviewed_by_user_full_name=reviewed_by_user.full_name if reviewed_by_user else None,
        review_notes=tenancy.review_notes,
        created_at=tenancy.created_at,
        updated_at=tenancy.updated_at,
    )
