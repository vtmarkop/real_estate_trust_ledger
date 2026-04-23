from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import AgencyTrustCheck, Listing, ListingApplication, Organization, OrganizationMembership
from app.models.common import ensure_utc, utcnow
from app.schemas.organization import CommercialOverviewResponse
from trustledger_domain import ApplicationStatus, ListingStatus


def build_commercial_overview(
    *,
    session: Session,
    organization: Organization,
) -> CommercialOverviewResponse:
    now = utcnow()
    recent_threshold = now - timedelta(days=30)

    listings = session.exec(
        select(Listing)
        .where(Listing.organization_id == organization.id)
        .order_by(Listing.created_at.desc())
    ).all()
    listing_ids = [listing.id for listing in listings]

    applications: list[ListingApplication] = []
    if listing_ids:
        applications = session.exec(
            select(ListingApplication)
            .where(ListingApplication.listing_id.in_(listing_ids))
            .order_by(ListingApplication.created_at.desc())
        ).all()

    trust_checks = session.exec(
        select(AgencyTrustCheck)
        .where(AgencyTrustCheck.organization_id == organization.id)
        .order_by(AgencyTrustCheck.created_at.desc())
    ).all()

    active_member_count = int(
        session.exec(
            select(func.count())
            .select_from(OrganizationMembership)
            .where(
                OrganizationMembership.organization_id == organization.id,
                OrganizationMembership.is_active == True,  # noqa: E712
            )
        ).one()
    )

    tracked_property_count = len({listing.property_id for listing in listings})
    open_listing_ids = {
        listing.id for listing in listings if listing.listing_status == ListingStatus.OPEN
    }
    listing_ids_with_applicants = {application.listing_id for application in applications}
    listings_without_applicants_count = sum(
        1 for listing_id in open_listing_ids if listing_id not in listing_ids_with_applicants
    )

    accepted_application_count = sum(
        1 for application in applications if application.application_status == ApplicationStatus.ACCEPTED
    )
    decided_durations = [
        round(
            (
                ensure_utc(application.decided_at) - ensure_utc(application.created_at)
            ).total_seconds()
            / 3600,
            2,
        )
        for application in applications
        if application.decided_at is not None
    ]
    applications_last_30_days = sum(
        1
        for application in applications
        if ensure_utc(application.created_at) >= recent_threshold
    )
    trust_checks_last_30_days = sum(
        1
        for trust_check in trust_checks
        if ensure_utc(trust_check.created_at) >= recent_threshold
    )

    acceptance_rate_percent = None
    if applications:
        acceptance_rate_percent = round((accepted_application_count / len(applications)) * 100, 1)

    average_time_to_decision_hours = None
    if decided_durations:
        average_time_to_decision_hours = round(
            sum(decided_durations) / len(decided_durations),
            2,
        )

    return CommercialOverviewResponse(
        organization_id=organization.id,
        organization_name=organization.name,
        active_member_count=active_member_count,
        tracked_property_count=tracked_property_count,
        total_listings=len(listings),
        open_listing_count=len(open_listing_ids),
        listings_without_applicants_count=listings_without_applicants_count,
        total_applications=len(applications),
        applications_last_30_days=applications_last_30_days,
        total_trust_checks=len(trust_checks),
        trust_checks_last_30_days=trust_checks_last_30_days,
        acceptance_rate_percent=acceptance_rate_percent,
        average_time_to_decision_hours=average_time_to_decision_hours,
        generated_at=now,
    )
