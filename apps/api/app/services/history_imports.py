from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import EvidenceDocument, HistoryImport, Tenancy, User
from app.schemas.history_import import HistoryImportResponse


def build_history_import_response(
    *,
    session: Session,
    history_import: HistoryImport,
) -> HistoryImportResponse:
    subject_user = session.get(User, history_import.subject_user_id)
    created_by_user = session.get(User, history_import.created_by_user_id)
    reviewed_by_user = (
        session.get(User, history_import.reviewed_by_user_id)
        if history_import.reviewed_by_user_id
        else None
    )
    if not subject_user or not created_by_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="History import dependencies are unavailable.",
        )

    tenancies = session.exec(
        select(Tenancy.id).where(Tenancy.history_import_id == history_import.id)
    ).all()
    evidence_document_count = 0
    if tenancies:
        evidence_document_count = len(
            session.exec(
                select(EvidenceDocument.id).where(EvidenceDocument.tenancy_id.in_(tenancies))
            ).all()
        )

    return HistoryImportResponse(
        id=history_import.id,
        subject_user_id=history_import.subject_user_id,
        subject_user_full_name=subject_user.full_name,
        created_by_user_id=history_import.created_by_user_id,
        created_by_user_full_name=created_by_user.full_name,
        title=history_import.title,
        summary=history_import.summary,
        status=history_import.status,
        submitted_at=history_import.submitted_at,
        reviewed_at=history_import.reviewed_at,
        reviewed_by_user_id=history_import.reviewed_by_user_id,
        reviewed_by_user_full_name=reviewed_by_user.full_name if reviewed_by_user else None,
        review_notes=history_import.review_notes,
        tenancy_count=len(tenancies),
        evidence_document_count=evidence_document_count,
        created_at=history_import.created_at,
        updated_at=history_import.updated_at,
    )
