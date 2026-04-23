from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import EvidenceDocument, ReferenceRequest, User
from app.schemas.reference_request import ReferenceRequestResponse


def build_reference_request_response(
    *,
    session: Session,
    reference_request: ReferenceRequest,
) -> ReferenceRequestResponse:
    subject_user = session.get(User, reference_request.subject_user_id)
    requested_by_user = session.get(User, reference_request.requested_by_user_id)
    requested_from_user = session.get(User, reference_request.requested_from_user_id)
    fulfilled_evidence_document = session.exec(
        select(EvidenceDocument.id).where(EvidenceDocument.reference_request_id == reference_request.id)
    ).first()

    if not subject_user or not requested_by_user or not requested_from_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Reference request dependencies are unavailable.",
        )

    return ReferenceRequestResponse(
        id=reference_request.id,
        tenancy_id=reference_request.tenancy_id,
        subject_user_id=reference_request.subject_user_id,
        subject_user_full_name=subject_user.full_name,
        requested_by_user_id=reference_request.requested_by_user_id,
        requested_by_user_full_name=requested_by_user.full_name,
        requested_from_user_id=reference_request.requested_from_user_id,
        requested_from_user_full_name=requested_from_user.full_name,
        status=reference_request.status,
        message=reference_request.message,
        fulfilled_at=reference_request.fulfilled_at,
        fulfilled_evidence_document_id=fulfilled_evidence_document,
        created_at=reference_request.created_at,
        updated_at=reference_request.updated_at,
    )
