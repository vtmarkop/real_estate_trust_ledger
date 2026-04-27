from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import (
    CurrentUserDep,
    OrganizationAgencyOperatorDep,
    SessionDep,
    require_workspace_role_for_user,
)
from app.models import Listing, ListingApplication, Property, TrustEvent
from app.models.common import utcnow
from app.schemas.listing import (
    AgencyScreeningDashboardResponse,
    ApplicationCreateRequest,
    ApplicationUpdateRequest,
    ListingApplicationResponse,
    ListingCreateRequest,
    ListingResponse,
    ListingUpdateRequest,
)
from app.services.listings import (
    build_agency_screening_dashboard_response,
    build_application_response,
    build_listing_response,
    ensure_application_status_transition,
    ensure_listing_is_open,
    evaluate_listing_eligibility,
)
from app.services.scoring import calculate_user_trust_scores
from app.services.trust_events import append_user_event
from trustledger_domain import (
    AccountWorkspaceRole,
    ApplicationStatus,
    ListingStatus,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(tags=["listings"])


def get_listing_for_organization(
    *,
    session: SessionDep,
    organization_id: UUID,
    listing_id: UUID,
) -> Listing:
    listing = session.exec(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.organization_id == organization_id,
        )
    ).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found.",
        )
    return listing


@router.post(
    "/organizations/{organization_id}/listings",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_listing(
    organization_id: UUID,
    payload: ListingCreateRequest,
    current_user: CurrentUserDep,
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> ListingResponse:
    property_record = session.get(Property, payload.property_id)
    if not property_record or not property_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )

    listing = Listing(
        organization_id=organization_id,
        property_id=payload.property_id,
        created_by_user_id=current_user.id,
        listing_status=ListingStatus.OPEN,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        monthly_rent_minor=payload.monthly_rent_minor,
        deposit_minor=payload.deposit_minor,
        currency_code=payload.currency_code.strip().upper(),
        minimum_counterparty_confirmed_tenancies=0,
        minimum_verified_tenancies=0,
        minimum_tenant_score=payload.minimum_tenant_score,
        minimum_verification_strength=payload.minimum_verification_strength,
    )
    session.add(listing)
    session.flush()
    append_user_event(
        session=session,
        subject_user_id=current_user.id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.LISTING_PUBLISHED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary=f"Listing published for {property_record.property_label}.",
        listing_id=listing.id,
    )
    session.commit()
    session.refresh(listing)
    return build_listing_response(session=session, listing=listing)


@router.get(
    "/organizations/{organization_id}/listings",
    response_model=list[ListingResponse],
)
def list_organization_listings(
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> list[ListingResponse]:
    listings = session.exec(
        select(Listing)
        .where(Listing.organization_id == access.organization.id)
        .order_by(Listing.created_at.desc())
    ).all()
    return [build_listing_response(session=session, listing=listing) for listing in listings]


@router.patch(
    "/organizations/{organization_id}/listings/{listing_id}",
    response_model=ListingResponse,
)
def update_listing(
    organization_id: UUID,
    listing_id: UUID,
    payload: ListingUpdateRequest,
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> ListingResponse:
    if (
        payload.listing_status is None
        and payload.description is None
        and payload.minimum_tenant_score is None
        and payload.minimum_verification_strength is None
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one listing field must be updated.",
        )

    listing = get_listing_for_organization(
        session=session,
        organization_id=organization_id,
        listing_id=listing_id,
    )
    if payload.listing_status is not None:
        listing.listing_status = payload.listing_status
    if payload.description is not None:
        listing.description = payload.description.strip() if payload.description else None
    if payload.minimum_tenant_score is not None:
        listing.minimum_tenant_score = payload.minimum_tenant_score
    if payload.minimum_verification_strength is not None:
        listing.minimum_verification_strength = payload.minimum_verification_strength
    listing.updated_at = utcnow()
    session.add(listing)
    session.commit()
    session.refresh(listing)
    return build_listing_response(session=session, listing=listing)


@router.get("/listings/open", response_model=list[ListingResponse])
def list_open_listings(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[ListingResponse]:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.TENANT,
        detail="Your account does not have the tenant role for listings.",
    )
    listings = session.exec(
        select(Listing)
        .where(Listing.listing_status == ListingStatus.OPEN)
        .order_by(Listing.created_at.desc())
    ).all()
    return [build_listing_response(session=session, listing=listing) for listing in listings]


@router.post(
    "/listings/{listing_id}/applications",
    response_model=ListingApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_listing_application(
    listing_id: UUID,
    payload: ApplicationCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ListingApplicationResponse:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.TENANT,
        detail="Your account does not have the tenant role for applications.",
    )
    listing = session.get(Listing, listing_id)
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found.",
        )
    ensure_listing_is_open(listing)

    existing = session.exec(
        select(ListingApplication).where(
            ListingApplication.listing_id == listing_id,
            ListingApplication.applicant_user_id == current_user.id,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied for this listing.",
        )

    applicant_score = calculate_user_trust_scores(
        session=session,
        user=current_user,
    )
    eligibility_met, eligibility_notes = evaluate_listing_eligibility(
        listing=listing,
        score_computation=applicant_score,
    )
    if not eligibility_met:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=eligibility_notes or "Listing requirements are not met.",
        )

    application = ListingApplication(
        listing_id=listing_id,
        applicant_user_id=current_user.id,
        submitted_by_user_id=current_user.id,
        application_status=ApplicationStatus.SUBMITTED,
        applicant_tenant_score=applicant_score.tenant_score,
        applicant_verification_strength=applicant_score.verification_strength,
        applicant_score_version=applicant_score.scoring_version,
        applicant_score_calculated_at=applicant_score.calculated_at,
        eligibility_met=eligibility_met,
        eligibility_notes=eligibility_notes,
        applicant_note=payload.applicant_note.strip() if payload.applicant_note else None,
    )
    session.add(application)
    session.flush()
    append_user_event(
        session=session,
        subject_user_id=current_user.id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.APPLICATION_SUBMITTED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary=f"Application submitted for {listing.title}.",
        details=payload.applicant_note.strip() if payload.applicant_note else None,
        listing_id=listing.id,
    )
    session.commit()
    session.refresh(application)
    return build_application_response(session=session, application=application)


@router.get("/applications/mine", response_model=list[ListingApplicationResponse])
def list_my_applications(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[ListingApplicationResponse]:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.TENANT,
        detail="Your account does not have the tenant role for applications.",
    )
    applications = session.exec(
        select(ListingApplication)
        .where(ListingApplication.applicant_user_id == current_user.id)
        .order_by(ListingApplication.created_at.desc())
    ).all()
    return [
        build_application_response(session=session, application=application)
        for application in applications
    ]


@router.get(
    "/organizations/{organization_id}/applications",
    response_model=list[ListingApplicationResponse],
)
def list_organization_applications(
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> list[ListingApplicationResponse]:
    listing_ids = session.exec(
        select(Listing.id).where(Listing.organization_id == access.organization.id)
    ).all()
    if not listing_ids:
        return []
    applications = session.exec(
        select(ListingApplication)
        .where(ListingApplication.listing_id.in_(listing_ids))
        .order_by(ListingApplication.created_at.desc())
    ).all()
    return [
        build_application_response(session=session, application=application)
        for application in applications
    ]


@router.get(
    "/organizations/{organization_id}/screening-dashboard",
    response_model=AgencyScreeningDashboardResponse,
)
def get_organization_screening_dashboard(
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> AgencyScreeningDashboardResponse:
    listings = session.exec(
        select(Listing)
        .where(Listing.organization_id == access.organization.id)
        .order_by(Listing.created_at.desc())
    ).all()
    listing_ids = [listing.id for listing in listings]
    applications = []
    if listing_ids:
        applications = session.exec(
            select(ListingApplication)
            .where(ListingApplication.listing_id.in_(listing_ids))
            .order_by(ListingApplication.created_at.desc())
        ).all()
    return build_agency_screening_dashboard_response(
        session=session,
        organization=access.organization,
        listings=listings,
        applications=applications,
    )


@router.patch(
    "/organizations/{organization_id}/applications/{application_id}",
    response_model=ListingApplicationResponse,
)
def update_organization_application(
    organization_id: UUID,
    application_id: UUID,
    payload: ApplicationUpdateRequest,
    current_user: CurrentUserDep,
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> ListingApplicationResponse:
    application = session.get(ListingApplication, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )
    listing = session.get(Listing, application.listing_id)
    if not listing or listing.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found for this organization.",
        )
    ensure_application_status_transition(
        current_status=application.application_status,
        next_status=payload.application_status,
    )

    application.application_status = payload.application_status
    application.status_notes = payload.status_notes.strip() if payload.status_notes else None
    application.decided_by_user_id = current_user.id
    application.decided_at = utcnow()
    application.updated_at = utcnow()
    session.add(application)
    append_user_event(
        session=session,
        subject_user_id=application.applicant_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.APPLICATION_STATUS_UPDATED,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Application status updated to {payload.application_status.value} for {listing.title}.",
        details=application.status_notes,
        listing_id=listing.id,
    )
    session.commit()
    session.refresh(application)
    return build_application_response(session=session, application=application)
