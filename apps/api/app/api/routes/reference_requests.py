from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import EvidenceDocument, ReferenceRequest, Tenancy
from app.models.common import utcnow
from app.schemas.reference_request import (
    ReferenceRequestCreateRequest,
    ReferenceRequestFulfillmentRequest,
    ReferenceRequestResponse,
)
from app.services.artifacts import resolve_attachable_tenancy_artifact
from app.services.reference_requests import build_reference_request_response
from app.services.trust_events import append_user_event
from trustledger_domain import (
    EvidenceDocumentType,
    EvidenceReviewStatus,
    ReferenceRequestStatus,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(prefix="/reference-requests", tags=["reference-requests"])


def ensure_reference_request_tenancy_participants(
    *,
    tenancy: Tenancy,
    subject_user_id: UUID,
    requested_from_user_id: UUID,
) -> None:
    participant_ids = {tenancy.tenant_user_id, tenancy.landlord_user_id}
    if subject_user_id not in participant_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reference subject must be a tenancy participant.",
        )
    if requested_from_user_id not in participant_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reference counterparty must be a tenancy participant.",
        )
    if subject_user_id == requested_from_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reference request must target the other tenancy participant.",
        )


def get_reference_request_accessible_to_user(
    *,
    session: SessionDep,
    reference_request_id: UUID,
    current_user: CurrentUserDep,
) -> ReferenceRequest:
    reference_request = session.get(ReferenceRequest, reference_request_id)
    if not reference_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reference request not found.",
        )
    if (
        current_user.id
        not in {
            reference_request.subject_user_id,
            reference_request.requested_by_user_id,
            reference_request.requested_from_user_id,
        }
        and not current_user.system_role.can_manage_platform
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this reference request.",
        )
    return reference_request


@router.post(
    "/tenancies/{tenancy_id}",
    response_model=ReferenceRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reference_request(
    tenancy_id: UUID,
    payload: ReferenceRequestCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ReferenceRequestResponse:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    if current_user.id != payload.subject_user_id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the reference subject can request a counterparty reference.",
        )

    ensure_reference_request_tenancy_participants(
        tenancy=tenancy,
        subject_user_id=payload.subject_user_id,
        requested_from_user_id=payload.requested_from_user_id,
    )

    existing_pending = session.exec(
        select(ReferenceRequest).where(
            ReferenceRequest.tenancy_id == tenancy_id,
            ReferenceRequest.subject_user_id == payload.subject_user_id,
            ReferenceRequest.requested_from_user_id == payload.requested_from_user_id,
            ReferenceRequest.status == ReferenceRequestStatus.PENDING,
        )
    ).first()
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending reference request already exists for this tenancy and counterparty.",
        )

    reference_request = ReferenceRequest(
        tenancy_id=tenancy.id,
        subject_user_id=payload.subject_user_id,
        requested_by_user_id=current_user.id,
        requested_from_user_id=payload.requested_from_user_id,
        status=ReferenceRequestStatus.PENDING,
        message=payload.message.strip() if payload.message else None,
    )
    session.add(reference_request)
    session.flush()
    append_user_event(
        session=session,
        subject_user_id=reference_request.subject_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.REFERENCE_REQUEST_CREATED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary=f"Counterparty reference requested for {tenancy.property_label}.",
        details=reference_request.message,
        tenancy_id=tenancy.id,
        reference_request_id=reference_request.id,
    )
    session.commit()
    session.refresh(reference_request)
    return build_reference_request_response(session=session, reference_request=reference_request)


@router.get("/mine", response_model=list[ReferenceRequestResponse])
def list_my_reference_requests(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[ReferenceRequestResponse]:
    reference_requests = session.exec(
        select(ReferenceRequest)
        .where(
            or_(
                ReferenceRequest.subject_user_id == current_user.id,
                ReferenceRequest.requested_by_user_id == current_user.id,
                ReferenceRequest.requested_from_user_id == current_user.id,
            )
        )
        .order_by(ReferenceRequest.created_at.desc())
    ).all()
    return [
        build_reference_request_response(session=session, reference_request=reference_request)
        for reference_request in reference_requests
    ]


@router.post(
    "/{reference_request_id}/fulfill",
    response_model=ReferenceRequestResponse,
)
def fulfill_reference_request(
    reference_request_id: UUID,
    payload: ReferenceRequestFulfillmentRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> ReferenceRequestResponse:
    reference_request = get_reference_request_accessible_to_user(
        session=session,
        reference_request_id=reference_request_id,
        current_user=current_user,
    )
    if (
        current_user.id != reference_request.requested_from_user_id
        and not current_user.system_role.can_manage_platform
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the requested counterparty can fulfill this reference request.",
        )
    if reference_request.status != ReferenceRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending reference requests can be fulfilled.",
        )

    tenancy = session.get(Tenancy, reference_request.tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Linked tenancy is unavailable for this reference request.",
        )
    stored_artifact = resolve_attachable_tenancy_artifact(
        session=session,
        artifact_id=payload.stored_artifact_id,
        tenancy=tenancy,
        current_user=current_user,
    )

    evidence_document = EvidenceDocument(
        tenancy_id=reference_request.tenancy_id,
        subject_user_id=reference_request.subject_user_id,
        uploaded_by_user_id=current_user.id,
        stored_artifact_id=stored_artifact.id if stored_artifact else None,
        reference_request_id=reference_request.id,
        document_type=EvidenceDocumentType.LANDLORD_REFERENCE,
        review_status=EvidenceReviewStatus.SUBMITTED,
        artifact_name=(
            stored_artifact.original_file_name if stored_artifact else payload.artifact_name.strip()
        ),
        summary=payload.summary.strip(),
        issuer_name=payload.issuer_name.strip() if payload.issuer_name else current_user.full_name,
        external_reference=payload.external_reference.strip() if payload.external_reference else None,
        review_requested_at=utcnow(),
    )
    session.add(evidence_document)
    session.flush()

    reference_request.status = ReferenceRequestStatus.FULFILLED
    reference_request.fulfilled_at = utcnow()
    reference_request.updated_at = utcnow()
    session.add(reference_request)
    append_user_event(
        session=session,
        subject_user_id=reference_request.subject_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.REFERENCE_REQUEST_FULFILLED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary=f"Counterparty reference submitted for {tenancy.property_label}.",
        details=evidence_document.summary,
        tenancy_id=tenancy.id,
        reference_request_id=reference_request.id,
        evidence_document_id=evidence_document.id,
    )
    session.commit()
    session.refresh(reference_request)
    return build_reference_request_response(session=session, reference_request=reference_request)
