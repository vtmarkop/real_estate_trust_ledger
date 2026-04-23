from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse, RedirectResponse

from app.api.deps import CurrentUserDep, SessionDep, SettingsDep
from app.models import EvidenceDocument, StoredArtifact, Tenancy
from app.models.common import utcnow
from app.schemas.artifact import StoredArtifactAccessResponse, StoredArtifactResponse
from app.services.artifacts import (
    LOCAL_STORAGE_BACKEND,
    build_stored_artifact_access_response,
    build_storage_redirect_url,
    build_stored_artifact_response,
    resolve_artifact_path,
    store_uploaded_artifact,
    validate_download_signature,
)


router = APIRouter(prefix="/evidence", tags=["evidence"])


def ensure_tenancy_participant_or_internal(
    *,
    tenancy: Tenancy,
    current_user: CurrentUserDep,
    detail: str,
) -> None:
    if (
        current_user.id in {tenancy.tenant_user_id, tenancy.landlord_user_id}
        or current_user.system_role.can_access_admin_surfaces
    ):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def create_artifact_access_response(
    *,
    stored_artifact: StoredArtifact,
    current_user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
    detail: str,
) -> StoredArtifactAccessResponse:
    tenancy = session.get(Tenancy, stored_artifact.tenancy_id)
    if tenancy is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Linked tenancy is unavailable for this stored artifact.",
        )
    ensure_tenancy_participant_or_internal(
        tenancy=tenancy,
        current_user=current_user,
        detail=detail,
    )
    return build_stored_artifact_access_response(
        stored_artifact=stored_artifact,
        settings=settings,
    )


@router.post(
    "/tenancies/{tenancy_id}/artifacts",
    response_model=StoredArtifactResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_tenancy_evidence_artifact(
    tenancy_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
    artifact_purpose: str = Query(default="evidence_document", min_length=2, max_length=64),
    artifact: UploadFile = File(...),
) -> StoredArtifactResponse:
    tenancy = session.get(Tenancy, tenancy_id)
    if not tenancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenancy not found.",
        )
    ensure_tenancy_participant_or_internal(
        tenancy=tenancy,
        current_user=current_user,
        detail="Only tenancy participants can upload evidence artifacts.",
    )

    stored_artifact = store_uploaded_artifact(
        session=session,
        settings=settings,
        upload=artifact,
        created_by_user_id=current_user.id,
        tenancy_id=tenancy.id,
        artifact_purpose=artifact_purpose.strip(),
    )
    session.commit()
    session.refresh(stored_artifact)
    return build_stored_artifact_response(stored_artifact=stored_artifact)


@router.post(
    "/{evidence_id}/artifact-access",
    response_model=StoredArtifactAccessResponse,
)
def create_evidence_artifact_access(
    evidence_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
) -> StoredArtifactAccessResponse:
    evidence_document = session.get(EvidenceDocument, evidence_id)
    if not evidence_document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence document not found.",
        )
    if evidence_document.stored_artifact_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Evidence document does not have an uploaded artifact.",
        )

    stored_artifact = session.get(StoredArtifact, evidence_document.stored_artifact_id)
    if stored_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored artifact not found.",
        )

    return create_artifact_access_response(
        stored_artifact=stored_artifact,
        current_user=current_user,
        session=session,
        settings=settings,
        detail="You do not have access to this evidence artifact.",
    )


@router.post(
    "/artifacts/{artifact_id}/access",
    response_model=StoredArtifactAccessResponse,
)
def create_general_artifact_access(
    artifact_id: UUID,
    current_user: CurrentUserDep,
    session: SessionDep,
    settings: SettingsDep,
) -> StoredArtifactAccessResponse:
    stored_artifact = session.get(StoredArtifact, artifact_id)
    if stored_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored artifact not found.",
        )

    return create_artifact_access_response(
        stored_artifact=stored_artifact,
        current_user=current_user,
        session=session,
        settings=settings,
        detail="You do not have access to this stored artifact.",
    )


@router.get("/artifacts/download")
def download_evidence_artifact(
    session: SessionDep,
    settings: SettingsDep,
    artifact_id: UUID = Query(...),
    expires: int = Query(..., ge=0),
    signature: str = Query(..., min_length=10),
):
    validate_download_signature(
        artifact_id=artifact_id,
        expires=expires,
        signature=signature,
        settings=settings,
    )

    stored_artifact = session.get(StoredArtifact, artifact_id)
    if stored_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored artifact not found.",
        )

    stored_artifact.last_accessed_at = utcnow()
    stored_artifact.updated_at = utcnow()
    session.add(stored_artifact)
    session.commit()

    if stored_artifact.storage_backend != LOCAL_STORAGE_BACKEND:
        return RedirectResponse(
            build_storage_redirect_url(stored_artifact=stored_artifact, settings=settings),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    artifact_path = resolve_artifact_path(stored_artifact=stored_artifact, settings=settings)
    if not artifact_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored artifact file is unavailable.",
        )

    return FileResponse(
        artifact_path,
        media_type=stored_artifact.content_type,
        filename=stored_artifact.original_file_name,
    )
