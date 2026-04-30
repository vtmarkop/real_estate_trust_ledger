from __future__ import annotations

from datetime import datetime
from statistics import fmean

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import Listing, ListingApplication, Organization, Property, User
from app.schemas.listing import (
    AgencyScreeningDashboardResponse,
    ListingApplicationResponse,
    ListingResponse,
)
from app.services.scoring import TrustScoreComputation, calculate_user_trust_scores
from trustledger_domain import ApplicationStatus, ListingStatus


def resolve_listing_manager(
    *,
    session: Session,
    listing: Listing,
) -> tuple[str, str, Organization | None, User | None]:
    organization = session.get(Organization, listing.organization_id) if listing.organization_id else None
    owner_landlord = (
        session.get(User, listing.owner_landlord_user_id)
        if listing.owner_landlord_user_id
        else None
    )
    if organization and not owner_landlord:
        return "agency", organization.name, organization, None
    if owner_landlord and not organization:
        return "landlord", owner_landlord.full_name, None, owner_landlord
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Listing manager is unavailable.",
    )


def build_listing_response(
    *,
    session: Session,
    listing: Listing,
) -> ListingResponse:
    listing_source, manager_name, organization, owner_landlord = resolve_listing_manager(
        session=session,
        listing=listing,
    )
    property_record = session.get(Property, listing.property_id)
    created_by_user = session.get(User, listing.created_by_user_id)
    if not property_record or not created_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Listing dependencies are unavailable.",
        )
    return ListingResponse(
        id=listing.id,
        organization_id=listing.organization_id,
        organization_name=organization.name if organization else None,
        owner_landlord_user_id=listing.owner_landlord_user_id,
        owner_landlord_full_name=owner_landlord.full_name if owner_landlord else None,
        listing_source=listing_source,
        manager_name=manager_name,
        property_id=listing.property_id,
        property_label=property_record.property_label,
        address_line1=property_record.address_line1,
        city=property_record.city,
        country_code=property_record.country_code,
        created_by_user_id=listing.created_by_user_id,
        created_by_user_full_name=created_by_user.full_name,
        listing_status=listing.listing_status,
        title=listing.title,
        description=listing.description,
        monthly_rent_minor=listing.monthly_rent_minor,
        deposit_minor=listing.deposit_minor,
        currency_code=listing.currency_code,
        minimum_tenant_score=listing.minimum_tenant_score,
        minimum_verification_strength=listing.minimum_verification_strength,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


def build_application_response(
    *,
    session: Session,
    application: ListingApplication,
) -> ListingApplicationResponse:
    listing = session.get(Listing, application.listing_id)
    applicant_user = session.get(User, application.applicant_user_id)
    submitted_by_user = session.get(User, application.submitted_by_user_id)
    decided_by_user = session.get(User, application.decided_by_user_id) if application.decided_by_user_id else None
    if not listing:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application dependencies are unavailable.",
        )
    listing_source, manager_name, organization, owner_landlord = resolve_listing_manager(
        session=session,
        listing=listing,
    )
    if not applicant_user or not submitted_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Application dependencies are unavailable.",
        )
    return ListingApplicationResponse(
        id=application.id,
        listing_id=application.listing_id,
        listing_title=listing.title,
        listing_status=listing.listing_status,
        organization_id=listing.organization_id,
        organization_name=organization.name if organization else None,
        owner_landlord_user_id=listing.owner_landlord_user_id,
        owner_landlord_full_name=owner_landlord.full_name if owner_landlord else None,
        listing_source=listing_source,
        manager_name=manager_name,
        applicant_user_id=application.applicant_user_id,
        applicant_full_name=applicant_user.full_name,
        applicant_tenant_score=application.applicant_tenant_score,
        applicant_verification_strength=application.applicant_verification_strength,
        applicant_score_version=application.applicant_score_version,
        applicant_score_calculated_at=application.applicant_score_calculated_at,
        submitted_by_user_id=application.submitted_by_user_id,
        submitted_by_user_full_name=submitted_by_user.full_name,
        application_status=application.application_status,
        eligibility_met=application.eligibility_met,
        eligibility_notes=application.eligibility_notes,
        applicant_note=application.applicant_note,
        status_notes=application.status_notes,
        decided_by_user_id=application.decided_by_user_id,
        decided_by_user_full_name=decided_by_user.full_name if decided_by_user else None,
        decided_at=application.decided_at,
        tenancy_id=application.tenancy_id,
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def evaluate_listing_eligibility(
    *,
    listing: Listing,
    score_computation: TrustScoreComputation,
) -> tuple[bool, str | None]:
    if score_computation.tenant_score < listing.minimum_tenant_score:
        return False, "Tenant score does not meet this listing requirement."
    if score_computation.verification_strength < listing.minimum_verification_strength:
        return False, "Verification strength does not meet this listing requirement."
    return True, None


def ensure_listing_is_open(listing: Listing) -> None:
    if listing.listing_status != ListingStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Listing is not open for applications.",
        )


def ensure_application_status_transition(
    *,
    current_status: ApplicationStatus,
    next_status: ApplicationStatus,
) -> None:
    allowed_transitions = {
        ApplicationStatus.SUBMITTED: {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.UNDER_REVIEW: {
            ApplicationStatus.ACCEPTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.ACCEPTED: set(),
        ApplicationStatus.REJECTED: set(),
        ApplicationStatus.WITHDRAWN: set(),
    }
    if next_status not in allowed_transitions[current_status]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Application status transition is not allowed.",
        )


def build_agency_screening_dashboard_response(
    *,
    session: Session,
    organization: Organization,
    listings: list[Listing],
    applications: list[ListingApplication],
) -> AgencyScreeningDashboardResponse:
    application_responses = [
        build_application_response(session=session, application=application)
        for application in applications[:5]
    ]
    tenant_scores = [
        application.applicant_tenant_score
        for application in applications
        if application.applicant_tenant_score is not None
    ]
    verification_strengths = [
        application.applicant_verification_strength
        for application in applications
        if application.applicant_verification_strength is not None
    ]

    return AgencyScreeningDashboardResponse(
        organization_id=organization.id,
        organization_name=organization.name,
        total_listings=len(listings),
        open_listings=sum(1 for listing in listings if listing.listing_status == ListingStatus.OPEN),
        total_applications=len(applications),
        submitted_applications=sum(
            1 for application in applications if application.application_status == ApplicationStatus.SUBMITTED
        ),
        under_review_applications=sum(
            1
            for application in applications
            if application.application_status == ApplicationStatus.UNDER_REVIEW
        ),
        accepted_applications=sum(
            1 for application in applications if application.application_status == ApplicationStatus.ACCEPTED
        ),
        rejected_applications=sum(
            1 for application in applications if application.application_status == ApplicationStatus.REJECTED
        ),
        withdrawn_applications=sum(
            1 for application in applications if application.application_status == ApplicationStatus.WITHDRAWN
        ),
        average_applicant_tenant_score=(
            round(fmean(tenant_scores), 2) if tenant_scores else None
        ),
        average_applicant_verification_strength=(
            round(fmean(verification_strengths), 2) if verification_strengths else None
        ),
        recent_applications=application_responses,
    )
