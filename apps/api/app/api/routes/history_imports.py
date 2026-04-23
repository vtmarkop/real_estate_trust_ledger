from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import or_
from sqlmodel import select

from app.api.deps import CurrentUserDep, SessionDep
from app.models import EvidenceDocument, HistoryImport, Tenancy
from app.models.common import utcnow
from app.schemas.history_import import HistoryImportCreateRequest, HistoryImportResponse
from app.services.history_imports import build_history_import_response
from app.services.trust_events import append_user_event
from trustledger_domain import HistoryImportStatus, TrustEventType, VerificationStatus


router = APIRouter(prefix="/history-imports", tags=["history-imports"])


def get_history_import_accessible_to_user(
    *,
    session: SessionDep,
    history_import_id: UUID,
    current_user: CurrentUserDep,
) -> HistoryImport:
    history_import = session.get(HistoryImport, history_import_id)
    if not history_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History import not found.",
        )
    if (
        history_import.subject_user_id != current_user.id
        and history_import.created_by_user_id != current_user.id
        and not current_user.system_role.can_manage_platform
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this history import.",
        )
    return history_import


@router.post("", response_model=HistoryImportResponse, status_code=status.HTTP_201_CREATED)
def create_history_import(
    payload: HistoryImportCreateRequest,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> HistoryImportResponse:
    history_import = HistoryImport(
        subject_user_id=current_user.id,
        created_by_user_id=current_user.id,
        title=payload.title.strip(),
        summary=payload.summary.strip() if payload.summary else None,
        status=HistoryImportStatus.DRAFT,
    )
    session.add(history_import)
    session.commit()
    session.refresh(history_import)
    return build_history_import_response(session=session, history_import=history_import)


@router.get("/mine", response_model=list[HistoryImportResponse])
def list_my_history_imports(
    current_user: CurrentUserDep,
    session: SessionDep,
) -> list[HistoryImportResponse]:
    history_imports = session.exec(
        select(HistoryImport)
        .where(
            or_(
                HistoryImport.subject_user_id == current_user.id,
                HistoryImport.created_by_user_id == current_user.id,
            )
        )
        .order_by(HistoryImport.created_at.desc())
    ).all()
    return [
        build_history_import_response(session=session, history_import=history_import)
        for history_import in history_imports
    ]


@router.post("/{history_import_id}/submit", response_model=HistoryImportResponse)
def submit_history_import(
    history_import_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
) -> HistoryImportResponse:
    history_import = get_history_import_accessible_to_user(
        session=session,
        history_import_id=history_import_id,
        current_user=current_user,
    )
    if history_import.subject_user_id != current_user.id and not current_user.system_role.can_manage_platform:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the history import subject can submit it for review.",
        )
    if history_import.status != HistoryImportStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft history imports can be submitted for review.",
        )

    tenancy_ids = session.exec(
        select(Tenancy.id).where(Tenancy.history_import_id == history_import.id)
    ).all()
    if not tenancy_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="History import must include at least one tenancy record before submission.",
        )
    evidence_document_count = len(
        session.exec(
            select(EvidenceDocument.id).where(EvidenceDocument.tenancy_id.in_(tenancy_ids))
        ).all()
    )
    if evidence_document_count == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="History import must include at least one evidence document before submission.",
        )

    history_import.status = HistoryImportStatus.SUBMITTED
    history_import.submitted_at = utcnow()
    history_import.updated_at = utcnow()
    session.add(history_import)
    append_user_event(
        session=session,
        subject_user_id=history_import.subject_user_id,
        actor_user_id=current_user.id,
        event_type=TrustEventType.HISTORY_IMPORT_SUBMITTED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary=f"Historical import submitted: {history_import.title}.",
        details=history_import.summary,
        history_import_id=history_import.id,
    )
    session.commit()
    session.refresh(history_import)
    return build_history_import_response(session=session, history_import=history_import)
