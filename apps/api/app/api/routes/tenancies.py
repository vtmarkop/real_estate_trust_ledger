from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_
from sqlmodel import select

from app.api.deps import (
    CurrentUserDep,
    SessionDep,
    require_tenancy_workspace_access,
    require_workspace_role_for_user,
)
from app.models import EvidenceDocument, HistoryImport, Property, Tenancy, User
from app.models.common import utcnow
from app.schemas.evidence import EvidenceCreateRequest, EvidenceResponse
from app.schemas.tenancy import TenancyCreateRequest, TenancyResponse
from app.services.artifacts import resolve_attachable_tenancy_artifact
from app.services.evidence import build_evidence_response, format_evidence_document_type_label
from app.services.tenancies import build_tenancy_response
from app.services.trust_events import append_tenancy_events, append_user_event
from trustledger_domain import (
    AccountWorkspaceRole,
    EvidenceReviewStatus,
    HistoryImportStatus,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(prefix="/tenancies", tags=["tenancies"])


def resolve_tenancy_user(
    *,
    session: SessionDep,
    user_id: UUID | None,
    email: str | None,
    role_label: str,
) -> User:
    user = None
    if user_id is not None:
        user = session.get(User, user_id)
    if email is not None:
        candidate = session.exec(
            select(User).where(User.email == email.lower().strip())
        ).first()
        if user is None:
            user = candidate
        elif candidate is None or candidate.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{role_label} user ID and email do not match the same user.",
            )

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{role_label} user not found.",
        )
    return user


def ensure_tenancy_participants(
    *,
    session: SessionDep,
    payload: TenancyCreateRequest,
) -> tuple[User, User]:
    tenant_user = resolve_tenancy_user(
        session=session,
        user_id=payload.tenant_user_id,
        email=payload.tenant_email,
        role_label="Tenant",
    )
    landlord_user = resolve_tenancy_user(
        session=session,
        user_id=payload.landlord_user_id,
        email=payload.landlord_email,
        role_label="Landlord",
    )
    tenant_user_id = tenant_user.id
    landlord_user_id = landlord_user.id
    if tenant_user_id == landlord_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant and landlord must be different users.",
        )
    return tenant_user, landlord_user


def resolve_property_for_tenancy(
    *,
    payload: TenancyCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> Property:
    if payload.property_id:
        property_record = session.get(Property, payload.property_id)
        if not property_record or not property_record.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found.",
            )
        if (
            property_record.created_by_user_id != current_user.id
            and property_record.owner_landlord_user_id != current_user.id
            and not current_user.system_role.can_manage_platform
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to reuse this property record.",
            )
        return property_record

    required_fields = {
        "property_label": payload.property_label,
        "address_line1": payload.address_line1,
        "city": payload.city,
        "country_code": payload.country_code,
    }
    missing_fields = [field for field, value in required_fields.items() if not value]
    if missing_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing property fields: {', '.join(missing_fields)}.",
        )

    property_record = Property(
        property_label=payload.property_label.strip(),
        address_line1=payload.address_line1.strip(),
        city=payload.city.strip(),
        country_code=payload.country_code.strip().upper(),
        created_by_user_id=current_user.id,
    )
    session.add(property_record)
    session.flush()
    return property_record


def ensure_tenancy_access(
    *,
    tenancy: Tenancy,
    current_user: CurrentUserDep,
    detail: str,
) -> None:
    require_tenancy_workspace_access(
        tenancy=tenancy,
        current_user=current_user,
        detail=detail,
    )


def ensure_tenancy_subject(
    *,
    tenancy: Tenancy,
    subject_user_id: UUID,
) -> None:
    if subject_user_id in {tenancy.tenant_user_id, tenancy.landlord_user_id}:
        return
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Evidence subject must be a tenancy participant.",
    )


def resolve_history_import_for_tenancy(
    *,
    payload: TenancyCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
    tenant_user_id: UUID,
    landlord_user_id: UUID,
) -> HistoryImport | None:
    if payload.history_import_id is None:
        return None

    history_import = session.get(HistoryImport, payload.history_import_id)
    if not history_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History import not found.",
        )
    if (
        history_import.subject_user_id != current_user.id
        and not current_user.system_role.can_manage_platform
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the history import subject can attach tenancies to it.",
        )
    if history_import.status != HistoryImportStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenancies can only be attached to draft history imports.",
        )
    if history_import.subject_user_id not in {tenant_user_id, landlord_user_id}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="History import subject must participate in the tenancy being attached.",
        )
    return history_import


@router.post("", response_model=TenancyResponse, status_code=status.HTTP_201_CREATED)
def create_tenancy(
    payload: TenancyCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> TenancyResponse:
    if payload.lease_end_date and payload.lease_end_date < payload.lease_start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lease end date cannot be before lease start date.",
        )

    tenant_user, landlord_user = ensure_tenancy_participants(
        session=session,
        payload=payload,
    )
    if current_user.id == tenant_user.id:
        require_workspace_role_for_user(
            user=current_user,
            role=AccountWorkspaceRole.TENANT,
            detail="Your account does not have the tenant role.",
            allow_platform_admin=True,
        )
    if current_user.id == landlord_user.id:
        require_workspace_role_for_user(
            user=current_user,
            role=AccountWorkspaceRole.LANDLORD,
            detail="Your account does not have the landlord role.",
            allow_platform_admin=True,
        )
    if (
        current_user.id not in {tenant_user.id, landlord_user.id}
        and not current_user.system_role.can_manage_platform
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenancy participants can create a tenancy record.",
        )
    property_record = resolve_property_for_tenancy(
        payload=payload,
        current_user=current_user,
        session=session,
    )
    history_import = resolve_history_import_for_tenancy(
        payload=payload,
        current_user=current_user,
        session=session,
        tenant_user_id=tenant_user.id,
        landlord_user_id=landlord_user.id,
    )

    tenancy = Tenancy(
        history_import_id=history_import.id if history_import else None,
        property_id=property_record.id,
        property_label=property_record.property_label,
        address_line1=property_record.address_line1,
        city=property_record.city,
        country_code=property_record.country_code,
        tenancy_status=payload.tenancy_status,
        lease_start_date=payload.lease_start_date,
        lease_end_date=payload.lease_end_date,
        monthly_rent_minor=payload.monthly_rent_minor,
        deposit_minor=payload.deposit_minor,
        currency_code=payload.currency_code.strip().upper(),
        tenant_user_id=tenant_user.id,
        landlord_user_id=landlord_user.id,
        created_by_user_id=current_user.id,
    )
    session.add(tenancy)
    property_record.assigned_tenant_user_id = tenant_user.id
    property_record.updated_at = utcnow()
    session.add(property_record)
    session.flush()
    append_tenancy_events(
        session=session,
        tenancy=tenancy,
        actor_user_id=current_user.id,
        event_type=TrustEventType.TENANCY_CREATED,
        verification_status=tenancy.verification_status,
        summary=f"Tenancy reported for {tenancy.property_label}.",
    )
    session.commit()
    session.refresh(tenancy)
    return build_tenancy_response(session=session, tenancy=tenancy)


@router.post(
    "/{tenancy_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_tenancy_evidence(
    tenancy_id: UUID,
    payload: EvidenceCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> EvidenceResponse:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can submit evidence.",
    )
    ensure_tenancy_subject(tenancy=tenancy, subject_user_id=payload.subject_user_id)

    currency_code = payload.currency_code.strip().upper() if payload.currency_code else None
    if payload.amount_minor is not None and currency_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Currency code is required when an amount is supplied.",
        )
    stored_artifact = resolve_attachable_tenancy_artifact(
        session=session,
        artifact_id=payload.stored_artifact_id,
        tenancy=tenancy,
        current_user=current_user,
    )

    evidence_document = EvidenceDocument(
        tenancy_id=tenancy.id,
        subject_user_id=payload.subject_user_id,
        uploaded_by_user_id=current_user.id,
        stored_artifact_id=stored_artifact.id if stored_artifact else None,
        document_type=payload.document_type,
        review_status=EvidenceReviewStatus.SUBMITTED,
        artifact_name=(
            stored_artifact.original_file_name if stored_artifact else payload.artifact_name.strip()
        ),
        summary=payload.summary.strip(),
        issuer_name=payload.issuer_name.strip() if payload.issuer_name else None,
        document_date=payload.document_date,
        amount_minor=payload.amount_minor,
        currency_code=currency_code,
        external_reference=payload.external_reference.strip() if payload.external_reference else None,
        review_requested_at=utcnow(),
    )
    session.add(evidence_document)
    session.flush()
    append_user_event(
        session=session,
        subject_user_id=evidence_document.subject_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.EVIDENCE_SUBMITTED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary=(
            f"{format_evidence_document_type_label(payload.document_type).title()} "
            f"submitted for {tenancy.property_label}."
        ),
        details=evidence_document.summary,
        tenancy_id=tenancy.id,
        evidence_document_id=evidence_document.id,
    )
    session.commit()
    session.refresh(evidence_document)
    return build_evidence_response(session=session, evidence_document=evidence_document)


@router.get("/{tenancy_id}/evidence", response_model=list[EvidenceResponse])
def list_tenancy_evidence(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[EvidenceResponse]:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    if current_user.system_role.can_access_admin_surfaces:
        pass
    else:
        ensure_tenancy_access(
            tenancy=tenancy,
            current_user=current_user,
            detail="Only tenancy participants can view tenancy evidence.",
        )

    evidence_documents = session.exec(
        select(EvidenceDocument)
        .where(EvidenceDocument.tenancy_id == tenancy_id)
        .order_by(EvidenceDocument.created_at.desc())
    ).all()
    return [
        build_evidence_response(session=session, evidence_document=evidence_document)
        for evidence_document in evidence_documents
    ]


@router.get("/mine", response_model=list[TenancyResponse])
def list_my_tenancies(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[TenancyResponse]:
    tenancy_filters = []
    if AccountWorkspaceRole.TENANT in current_user.workspace_roles:
        tenancy_filters.append(Tenancy.tenant_user_id == current_user.id)
    if AccountWorkspaceRole.LANDLORD in current_user.workspace_roles:
        tenancy_filters.append(Tenancy.landlord_user_id == current_user.id)
    if current_user.system_role.can_manage_platform:
        tenancy_filters.append(Tenancy.created_by_user_id == current_user.id)
    if not tenancy_filters:
        return []

    tenancies = session.exec(
        select(Tenancy)
        .where(or_(*tenancy_filters))
        .order_by(Tenancy.created_at.desc())
    ).all()
    return [build_tenancy_response(session=session, tenancy=tenancy) for tenancy in tenancies]


@router.post("/{tenancy_id}/request-review", response_model=TenancyResponse)
def request_tenancy_review(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> TenancyResponse:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can request review.",
    )

    if tenancy.verification_status.is_reviewer_final:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenancy has already completed internal review.",
        )

    if tenancy.review_requested_at is None:
        tenancy.review_requested_at = utcnow()
        tenancy.updated_at = utcnow()
        session.add(tenancy)
        append_tenancy_events(
            session=session,
            tenancy=tenancy,
            actor_user_id=current_user.id,
            event_type=TrustEventType.TENANCY_REVIEW_REQUESTED,
            verification_status=tenancy.verification_status,
            summary=f"Internal review requested for {tenancy.property_label}.",
        )
        session.commit()
        session.refresh(tenancy)

    return build_tenancy_response(session=session, tenancy=tenancy)


@router.post("/{tenancy_id}/confirm", response_model=TenancyResponse)
def confirm_tenancy_counterparty(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> TenancyResponse:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    ensure_tenancy_access(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can confirm a tenancy record.",
    )

    if current_user.id == tenancy.created_by_user_id and tenancy.created_by_user_id in {
        tenancy.tenant_user_id,
        tenancy.landlord_user_id,
    }:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenancy creator cannot counterparty-confirm their own record.",
        )
    if tenancy.verification_status == VerificationStatus.COUNTERPARTY_CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenancy already has counterparty confirmation.",
        )
    if tenancy.verification_status.is_reviewer_final:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenancy already completed internal review.",
        )

    tenancy.verification_status = VerificationStatus.COUNTERPARTY_CONFIRMED
    tenancy.counterparty_confirmed_at = utcnow()
    tenancy.counterparty_confirmed_by_user_id = current_user.id
    tenancy.review_requested_at = None
    tenancy.updated_at = utcnow()
    session.add(tenancy)
    append_tenancy_events(
        session=session,
        tenancy=tenancy,
        actor_user_id=current_user.id,
        event_type=TrustEventType.TENANCY_COUNTERPARTY_CONFIRMED,
        verification_status=tenancy.verification_status,
        summary=f"Counterparty confirmed tenancy for {tenancy.property_label}.",
    )
    session.commit()
    session.refresh(tenancy)
    return build_tenancy_response(session=session, tenancy=tenancy)
