from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import EvidenceDocument, ReferenceRequest, User
from app.schemas.evidence import EvidenceResponse


def format_evidence_document_type_label(document_type) -> str:
    return document_type.value.replace("_", " ")


def build_evidence_response(
    *,
    session: Session,
    evidence_document: EvidenceDocument,
) -> EvidenceResponse:
    subject_user = session.get(User, evidence_document.subject_user_id)
    uploaded_by_user = session.get(User, evidence_document.uploaded_by_user_id)
    reference_request = (
        session.get(ReferenceRequest, evidence_document.reference_request_id)
        if evidence_document.reference_request_id
        else None
    )
    reference_requested_from_user = (
        session.get(User, reference_request.requested_from_user_id)
        if reference_request
        else None
    )
    reviewed_by_user = (
        session.get(User, evidence_document.reviewed_by_user_id)
        if evidence_document.reviewed_by_user_id
        else None
    )
    if not subject_user or not uploaded_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Evidence dependencies are unavailable.",
        )

    return EvidenceResponse(
        id=evidence_document.id,
        tenancy_id=evidence_document.tenancy_id,
        subject_user_id=evidence_document.subject_user_id,
        subject_user_full_name=subject_user.full_name,
        uploaded_by_user_id=evidence_document.uploaded_by_user_id,
        uploaded_by_user_full_name=uploaded_by_user.full_name,
        reference_request_id=evidence_document.reference_request_id,
        reference_requested_from_user_id=(
            reference_request.requested_from_user_id if reference_request else None
        ),
        reference_requested_from_user_full_name=(
            reference_requested_from_user.full_name if reference_requested_from_user else None
        ),
        document_type=evidence_document.document_type,
        review_status=evidence_document.review_status,
        artifact_name=evidence_document.artifact_name,
        stored_artifact_id=evidence_document.stored_artifact_id,
        has_uploaded_artifact=evidence_document.stored_artifact_id is not None,
        artifact_content_type=(
            evidence_document.stored_artifact.content_type if evidence_document.stored_artifact else None
        ),
        artifact_size_bytes=(
            evidence_document.stored_artifact.size_bytes if evidence_document.stored_artifact else None
        ),
        summary=evidence_document.summary,
        issuer_name=evidence_document.issuer_name,
        document_date=evidence_document.document_date,
        amount_minor=evidence_document.amount_minor,
        currency_code=evidence_document.currency_code,
        external_reference=evidence_document.external_reference,
        review_requested_at=evidence_document.review_requested_at,
        reviewed_at=evidence_document.reviewed_at,
        reviewed_by_user_id=evidence_document.reviewed_by_user_id,
        reviewed_by_user_full_name=reviewed_by_user.full_name if reviewed_by_user else None,
        review_notes=evidence_document.review_notes,
        created_at=evidence_document.created_at,
        updated_at=evidence_document.updated_at,
    )
