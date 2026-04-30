from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlmodel import select

from app.api.deps import SessionDep, require_system_roles
from app.models import EvidenceDocument, HistoryImport, Tenancy
from app.models import User
from app.models.common import utcnow
from app.schemas.evidence import EvidenceResponse, EvidenceReviewDecisionRequest
from app.schemas.history_import import HistoryImportResponse, HistoryImportReviewDecisionRequest
from app.schemas.internal import (
    InternalAccessResponse,
    InternalUserResponse,
    WorkspaceRolesUpdateRequest,
)
from app.schemas.tenancy import TenancyResponse, TenancyReviewDecisionRequest
from app.services.evidence import build_evidence_response, format_evidence_document_type_label
from app.services.history_imports import build_history_import_response
from app.services.tenancies import build_tenancy_response
from app.services.trust_events import append_tenancy_events, append_user_event
from trustledger_domain import (
    AccountWorkspaceRole,
    EvidenceReviewStatus,
    HistoryImportStatus,
    SystemRole,
    TrustEventType,
    VerificationStatus,
)


router = APIRouter(prefix="/internal", tags=["internal"])


def build_internal_user_response(user: User) -> InternalUserResponse:
    return InternalUserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        system_role=user.system_role,
        workspace_roles=user.workspace_roles,
        is_active=user.is_active,
        email_verified=user.email_verified,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )


@router.get(
    "/access",
    response_model=InternalAccessResponse,
)
def get_internal_access_status(
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> InternalAccessResponse:
    return InternalAccessResponse(
        user_id=current_user.id,
        email=current_user.email,
        system_role=current_user.system_role,
        can_manage_platform=current_user.system_role.can_manage_platform,
    )


@router.get(
    "/users",
    response_model=list[InternalUserResponse],
)
def list_internal_users(
    session: SessionDep,
    query: str | None = None,
    limit: int = 25,
    current_user=Depends(require_system_roles(SystemRole.ADMIN)),
) -> list[InternalUserResponse]:
    statement = select(User).order_by(User.created_at.desc())
    if query and query.strip():
        normalized_query = query.strip()
        statement = (
            select(User)
            .where(
                or_(
                    User.email.ilike(f"%{normalized_query}%"),
                    User.full_name.ilike(f"%{normalized_query}%"),
                )
            )
            .order_by(User.created_at.desc())
        )
    users = session.exec(statement).all()[: max(1, min(limit, 100))]
    return [build_internal_user_response(user) for user in users]


@router.patch(
    "/users/{user_id}/workspace-roles",
    response_model=InternalUserResponse,
)
def update_user_workspace_roles(
    user_id: UUID,
    payload: WorkspaceRolesUpdateRequest,
    session: SessionDep,
    current_user: User = Depends(require_system_roles(SystemRole.ADMIN)),
) -> InternalUserResponse:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    requested_roles = list(payload.workspace_roles)
    if user.id == current_user.id and AccountWorkspaceRole.INTERNAL not in requested_roles:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot remove your own admin workspace role while signed in.",
        )

    user.set_workspace_roles(requested_roles)
    user.system_role = (
        SystemRole.ADMIN
        if AccountWorkspaceRole.INTERNAL in user.workspace_roles
        else SystemRole.USER
    )
    user.updated_at = utcnow()
    session.add(user)
    session.commit()
    session.refresh(user)
    return build_internal_user_response(user)


@router.get(
    "/review-queue/tenancies",
    response_model=list[TenancyResponse],
)
def list_tenancy_review_queue(
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER)),
) -> list[TenancyResponse]:
    tenancies = session.exec(
        select(Tenancy)
        .where(
            Tenancy.review_requested_at.is_not(None),
            Tenancy.reviewed_at.is_(None),
        )
        .order_by(Tenancy.review_requested_at.asc())
    ).all()
    return [build_tenancy_response(session=session, tenancy=tenancy) for tenancy in tenancies]


@router.get(
    "/review-queue/evidence",
    response_model=list[EvidenceResponse],
)
def list_evidence_review_queue(
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER)),
) -> list[EvidenceResponse]:
    evidence_documents = session.exec(
        select(EvidenceDocument)
        .where(
            EvidenceDocument.review_requested_at.is_not(None),
            EvidenceDocument.reviewed_at.is_(None),
        )
        .order_by(EvidenceDocument.review_requested_at.asc())
    ).all()
    return [
        build_evidence_response(session=session, evidence_document=evidence_document)
        for evidence_document in evidence_documents
    ]


@router.get(
    "/review-queue/history-imports",
    response_model=list[HistoryImportResponse],
)
def list_history_import_review_queue(
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER)),
) -> list[HistoryImportResponse]:
    history_imports = session.exec(
        select(HistoryImport)
        .where(
            HistoryImport.status == HistoryImportStatus.SUBMITTED,
            HistoryImport.reviewed_at.is_(None),
        )
        .order_by(HistoryImport.submitted_at.asc())
    ).all()
    return [
        build_history_import_response(session=session, history_import=history_import)
        for history_import in history_imports
    ]


@router.post(
    "/review-queue/tenancies/{tenancy_id}/decision",
    response_model=TenancyResponse,
)
def review_tenancy(
    tenancy_id: UUID,
    payload: TenancyReviewDecisionRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER)),
) -> TenancyResponse:
    if payload.verification_status not in {
        VerificationStatus.REVIEWED,
        VerificationStatus.VERIFIED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer decisions must set status to reviewed or verified.",
        )

    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    if tenancy.review_requested_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenancy has not been submitted for review.",
        )
    if tenancy.reviewed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenancy review is already complete.",
        )

    tenancy.verification_status = payload.verification_status
    tenancy.reviewed_at = utcnow()
    tenancy.reviewed_by_user_id = current_user.id
    tenancy.review_notes = payload.review_notes.strip() if payload.review_notes else None
    tenancy.updated_at = utcnow()
    session.add(tenancy)
    append_tenancy_events(
        session=session,
        tenancy=tenancy,
        actor_user_id=current_user.id,
        event_type=TrustEventType.TENANCY_REVIEWED,
        verification_status=payload.verification_status,
        summary=f"Tenancy reviewed for {tenancy.property_label}.",
        details=tenancy.review_notes,
    )
    session.commit()
    session.refresh(tenancy)
    return build_tenancy_response(session=session, tenancy=tenancy)


@router.post(
    "/review-queue/evidence/{evidence_document_id}/decision",
    response_model=EvidenceResponse,
)
def review_evidence_document(
    evidence_document_id: UUID,
    payload: EvidenceReviewDecisionRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER)),
) -> EvidenceResponse:
    if payload.review_status not in {
        EvidenceReviewStatus.ACCEPTED,
        EvidenceReviewStatus.REJECTED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer decisions must set evidence to accepted or rejected.",
        )

    evidence_document = session.get(EvidenceDocument, evidence_document_id)
    if not evidence_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence document not found.",
        )
    if evidence_document.review_requested_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence document has not been submitted for review.",
        )
    if evidence_document.reviewed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence review is already complete.",
        )

    tenancy = session.get(Tenancy, evidence_document.tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Linked tenancy is unavailable for this evidence document.",
        )

    evidence_document.review_status = payload.review_status
    evidence_document.reviewed_at = utcnow()
    evidence_document.reviewed_by_user_id = current_user.id
    evidence_document.review_notes = payload.review_notes.strip() if payload.review_notes else None
    evidence_document.updated_at = utcnow()
    session.add(evidence_document)
    event_type = (
        TrustEventType.EVIDENCE_ACCEPTED
        if payload.review_status == EvidenceReviewStatus.ACCEPTED
        else TrustEventType.EVIDENCE_REJECTED
    )
    append_user_event(
        session=session,
        subject_user_id=evidence_document.subject_user_id,
        actor_user_id=current_user.id,
        event_type=event_type,
        verification_status=VerificationStatus.REVIEWED,
        summary=(
            f"{format_evidence_document_type_label(evidence_document.document_type).title()} "
            f"{payload.review_status.value} for {tenancy.property_label}."
        ),
        details=evidence_document.review_notes,
        tenancy_id=evidence_document.tenancy_id,
        evidence_document_id=evidence_document.id,
    )
    session.commit()
    session.refresh(evidence_document)
    return build_evidence_response(session=session, evidence_document=evidence_document)


@router.post(
    "/review-queue/history-imports/{history_import_id}/decision",
    response_model=HistoryImportResponse,
)
def review_history_import(
    history_import_id: UUID,
    payload: HistoryImportReviewDecisionRequest,
    session: SessionDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER)),
) -> HistoryImportResponse:
    if payload.status not in {
        HistoryImportStatus.ACCEPTED,
        HistoryImportStatus.REJECTED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer decisions must set history import to accepted or rejected.",
        )

    history_import = session.get(HistoryImport, history_import_id)
    if not history_import:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History import not found.",
        )
    if history_import.status != HistoryImportStatus.SUBMITTED or history_import.submitted_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="History import has not been submitted for review.",
        )
    if history_import.reviewed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="History import review is already complete.",
        )

    history_import.status = payload.status
    history_import.reviewed_at = utcnow()
    history_import.reviewed_by_user_id = current_user.id
    history_import.review_notes = payload.review_notes.strip() if payload.review_notes else None
    history_import.updated_at = utcnow()
    session.add(history_import)
    event_type = (
        TrustEventType.HISTORY_IMPORT_ACCEPTED
        if payload.status == HistoryImportStatus.ACCEPTED
        else TrustEventType.HISTORY_IMPORT_REJECTED
    )
    append_user_event(
        session=session,
        subject_user_id=history_import.subject_user_id,
        actor_user_id=current_user.id,
        event_type=event_type,
        verification_status=VerificationStatus.REVIEWED,
        summary=f"Historical import {payload.status.value}: {history_import.title}.",
        details=history_import.review_notes,
        history_import_id=history_import.id,
    )
    session.commit()
    session.refresh(history_import)
    return build_history_import_response(session=session, history_import=history_import)
