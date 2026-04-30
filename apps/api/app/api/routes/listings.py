from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import or_, select

from app.api.deps import (
    CurrentUserDep,
    OrganizationAgencyOperatorDep,
    SessionDep,
    require_workspace_role_for_user,
)
from app.models import Listing, ListingApplication, Property, Tenancy, TrustEvent, User
from app.models.common import utcnow
from app.schemas.listing import (
    AgencyScreeningDashboardResponse,
    ApplicationCreateRequest,
    ApplicationTenancyCreateRequest,
    ApplicationUpdateRequest,
    ListingApplicationResponse,
    ListingCreateRequest,
    ListingResponse,
    ListingUpdateRequest,
)
from app.schemas.tenancy import TenancyResponse
from app.services.listings import (
    build_agency_screening_dashboard_response,
    build_application_response,
    build_listing_response,
    ensure_application_status_transition,
    ensure_listing_is_open,
    evaluate_listing_eligibility,
)
from app.services.scoring import calculate_user_trust_scores
from app.services.tenancies import build_tenancy_response
from app.services.trust_events import append_tenancy_events, append_user_event
from trustledger_domain import (
    AccountWorkspaceRole,
    ApplicationStatus,
    ListingStatus,
    PropertyManagementMode,
    TenancyStatus,
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


def get_listing_for_landlord(
    *,
    session: SessionDep,
    current_user: CurrentUserDep,
    listing_id: UUID,
) -> Listing:
    listing = session.exec(
        select(Listing).where(
            Listing.id == listing_id,
            Listing.owner_landlord_user_id == current_user.id,
        )
    ).first()
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Listing not found.",
        )
    return listing


def ensure_property_can_be_owner_listed(
    *,
    property_record: Property | None,
    current_user: CurrentUserDep,
) -> Property:
    if not property_record or not property_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )
    if property_record.management_mode != PropertyManagementMode.OWNER_MANAGED.value:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only owner-managed properties can be published directly by a landlord.",
        )
    if (
        property_record.owner_landlord_user_id != current_user.id
        and property_record.created_by_user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property must belong to the signed-in landlord before publishing.",
        )
    return property_record


def resolve_listing_landlord_for_tenancy(
    *,
    session: SessionDep,
    listing: Listing,
    property_record: Property,
) -> User:
    landlord_user_id = listing.owner_landlord_user_id or property_record.owner_landlord_user_id
    if landlord_user_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Link a landlord owner to this property before creating a tenancy.",
        )
    landlord_user = session.get(User, landlord_user_id)
    if not landlord_user or not landlord_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The landlord owner account is unavailable.",
        )
    require_workspace_role_for_user(
        user=landlord_user,
        role=AccountWorkspaceRole.LANDLORD,
        detail="The landlord owner account does not have the landlord role.",
    )
    return landlord_user


def create_tenancy_from_accepted_application(
    *,
    session: SessionDep,
    application: ListingApplication,
    listing: Listing,
    payload: ApplicationTenancyCreateRequest,
    current_user: CurrentUserDep,
) -> TenancyResponse:
    if payload.lease_end_date and payload.lease_end_date < payload.lease_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lease end date cannot be before lease start date.",
        )
    if application.application_status != ApplicationStatus.ACCEPTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only an accepted application can create a tenancy.",
        )
    if application.tenancy_id is not None:
        existing_tenancy = session.get(Tenancy, application.tenancy_id)
        if existing_tenancy:
            return build_tenancy_response(session=session, tenancy=existing_tenancy)

    property_record = session.get(Property, listing.property_id)
    applicant_user = session.get(User, application.applicant_user_id)
    if not property_record or not property_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found.",
        )
    if not applicant_user or not applicant_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The accepted applicant account is unavailable.",
        )

    landlord_user = resolve_listing_landlord_for_tenancy(
        session=session,
        listing=listing,
        property_record=property_record,
    )
    if landlord_user.id == applicant_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant and landlord must be different users.",
        )

    existing_active_tenancy = session.exec(
        select(Tenancy).where(
            Tenancy.property_id == property_record.id,
            Tenancy.tenant_user_id == applicant_user.id,
            Tenancy.landlord_user_id == landlord_user.id,
            Tenancy.tenancy_status == TenancyStatus.ACTIVE,
        )
    ).first()
    if existing_active_tenancy:
        application.tenancy_id = existing_active_tenancy.id
        application.updated_at = utcnow()
        listing.listing_status = ListingStatus.CLOSED
        listing.updated_at = utcnow()
        property_record.assigned_tenant_user_id = applicant_user.id
        property_record.updated_at = utcnow()
        session.add(application)
        session.add(listing)
        session.add(property_record)
        session.commit()
        session.refresh(existing_active_tenancy)
        return build_tenancy_response(session=session, tenancy=existing_active_tenancy)

    tenancy = Tenancy(
        property_id=property_record.id,
        property_label=property_record.property_label,
        address_line1=property_record.address_line1,
        city=property_record.city,
        country_code=property_record.country_code,
        tenancy_status=payload.tenancy_status,
        lease_start_date=payload.lease_start_date,
        lease_end_date=payload.lease_end_date,
        monthly_rent_minor=listing.monthly_rent_minor,
        deposit_minor=listing.deposit_minor,
        currency_code=listing.currency_code,
        tenant_user_id=applicant_user.id,
        landlord_user_id=landlord_user.id,
        created_by_user_id=current_user.id,
    )
    session.add(tenancy)
    session.flush()

    application.tenancy_id = tenancy.id
    application.updated_at = utcnow()
    listing.listing_status = ListingStatus.CLOSED
    listing.updated_at = utcnow()
    property_record.assigned_tenant_user_id = applicant_user.id
    property_record.updated_at = utcnow()
    session.add(application)
    session.add(listing)
    session.add(property_record)
    append_tenancy_events(
        session=session,
        tenancy=tenancy,
        actor_user_id=current_user.id,
        event_type=TrustEventType.TENANCY_CREATED,
        verification_status=tenancy.verification_status,
        summary=f"Tenancy created from accepted application for {listing.title}.",
    )
    session.commit()
    session.refresh(tenancy)
    return build_tenancy_response(session=session, tenancy=tenancy)


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
    if property_record.assigned_agency_organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Property must be assigned to this agency before publishing a listing.",
        )

    listing = Listing(
        organization_id=organization_id,
        owner_landlord_user_id=None,
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


@router.post(
    "/landlord/listings",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_landlord_listing(
    payload: ListingCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ListingResponse:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.LANDLORD,
        detail="Your account does not have the landlord role for listing publication.",
    )
    property_record = ensure_property_can_be_owner_listed(
        property_record=session.get(Property, payload.property_id),
        current_user=current_user,
    )
    existing_listing = session.exec(
        select(Listing).where(
            Listing.property_id == payload.property_id,
            Listing.owner_landlord_user_id == current_user.id,
            Listing.listing_status != ListingStatus.CLOSED,
        )
    ).first()
    if existing_listing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This owner-managed property already has an active landlord listing.",
        )

    listing = Listing(
        organization_id=None,
        owner_landlord_user_id=current_user.id,
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
        summary=f"Owner listing published for {property_record.property_label}.",
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


@router.get(
    "/landlord/listings",
    response_model=list[ListingResponse],
)
def list_landlord_listings(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[ListingResponse]:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.LANDLORD,
        detail="Your account does not have the landlord role for listing publication.",
    )
    listings = session.exec(
        select(Listing)
        .where(Listing.owner_landlord_user_id == current_user.id)
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


@router.patch(
    "/landlord/listings/{listing_id}",
    response_model=ListingResponse,
)
def update_landlord_listing(
    listing_id: UUID,
    payload: ListingUpdateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ListingResponse:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.LANDLORD,
        detail="Your account does not have the landlord role for listing publication.",
    )
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

    listing = get_listing_for_landlord(
        session=session,
        current_user=current_user,
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
        .where(
            or_(
                Listing.owner_landlord_user_id == None,  # noqa: E711
                Listing.owner_landlord_user_id != current_user.id,
            )
        )
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
    if listing.owner_landlord_user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot apply to your own landlord listing.",
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
    "/landlord/applications",
    response_model=list[ListingApplicationResponse],
)
def list_landlord_applications(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[ListingApplicationResponse]:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.LANDLORD,
        detail="Your account does not have the landlord role for listing applications.",
    )
    listing_ids = session.exec(
        select(Listing.id).where(Listing.owner_landlord_user_id == current_user.id)
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


@router.post(
    "/organizations/{organization_id}/applications/{application_id}/tenancy",
    response_model=TenancyResponse,
)
def create_organization_application_tenancy(
    organization_id: UUID,
    application_id: UUID,
    payload: ApplicationTenancyCreateRequest,
    current_user: CurrentUserDep,
    access: OrganizationAgencyOperatorDep,
    session: SessionDep,
) -> TenancyResponse:
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
    return create_tenancy_from_accepted_application(
        session=session,
        application=application,
        listing=listing,
        payload=payload,
        current_user=current_user,
    )


@router.patch(
    "/landlord/applications/{application_id}",
    response_model=ListingApplicationResponse,
)
def update_landlord_application(
    application_id: UUID,
    payload: ApplicationUpdateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ListingApplicationResponse:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.LANDLORD,
        detail="Your account does not have the landlord role for listing applications.",
    )
    application = session.get(ListingApplication, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )
    listing = session.get(Listing, application.listing_id)
    if not listing or listing.owner_landlord_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found for this landlord listing.",
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
        summary=f"Landlord application status updated to {payload.application_status.value} for {listing.title}.",
        details=application.status_notes,
        listing_id=listing.id,
    )
    session.commit()
    session.refresh(application)
    return build_application_response(session=session, application=application)


@router.post(
    "/landlord/applications/{application_id}/tenancy",
    response_model=TenancyResponse,
)
def create_landlord_application_tenancy(
    application_id: UUID,
    payload: ApplicationTenancyCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> TenancyResponse:
    require_workspace_role_for_user(
        user=current_user,
        role=AccountWorkspaceRole.LANDLORD,
        detail="Your account does not have the landlord role for listing applications.",
    )
    application = session.get(ListingApplication, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found.",
        )
    listing = session.get(Listing, application.listing_id)
    if not listing or listing.owner_landlord_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found for this landlord listing.",
        )
    return create_tenancy_from_accepted_application(
        session=session,
        application=application,
        listing=listing,
        payload=payload,
        current_user=current_user,
    )
