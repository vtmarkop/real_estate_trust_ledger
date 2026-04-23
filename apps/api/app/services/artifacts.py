from __future__ import annotations

import base64
import hashlib
import hmac
import re
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session

from app.core.config import Settings
from app.models import StoredArtifact, Tenancy, User
from app.models.common import utcnow
from app.schemas.artifact import StoredArtifactAccessResponse, StoredArtifactResponse


CHUNK_SIZE = 1024 * 1024
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")
LOCAL_STORAGE_BACKEND = "local_private"
S3_STORAGE_BACKEND = "s3_compatible"


def sanitize_filename(file_name: str) -> str:
    cleaned = SAFE_FILENAME_PATTERN.sub("-", Path(file_name).name.strip())
    return cleaned or "artifact"


def ensure_upload_allowed(*, upload: UploadFile, settings: Settings) -> None:
    if not upload.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a name.",
        )
    content_type = (upload.content_type or "").strip().lower()
    if not content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must include a content type.",
        )
    if content_type not in settings.artifact_allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Uploaded file type is not allowed.",
        )


def get_artifact_storage_root(*, settings: Settings) -> Path:
    root = Path(settings.artifact_storage_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def create_s3_client(*, settings: Settings):
    import boto3
    from botocore.config import Config

    addressing_style = "path" if settings.artifact_s3_force_path_style else "auto"
    return boto3.client(
        "s3",
        endpoint_url=settings.artifact_s3_endpoint_url,
        region_name=settings.artifact_s3_region,
        aws_access_key_id=settings.artifact_s3_access_key_id,
        aws_secret_access_key=settings.artifact_s3_secret_access_key,
        use_ssl=settings.artifact_s3_use_ssl,
        config=Config(signature_version="s3v4", s3={"addressing_style": addressing_style}),
    )


def read_upload_bytes(
    *,
    upload: UploadFile,
    settings: Settings,
) -> tuple[bytes, int, str]:
    upload.file.seek(0)
    digest = hashlib.sha256()
    payload = bytearray()
    while True:
        chunk = upload.file.read(CHUNK_SIZE)
        if not chunk:
            break
        payload.extend(chunk)
        if len(payload) > settings.artifact_max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Uploaded file exceeds the maximum allowed size.",
            )
        digest.update(chunk)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    return bytes(payload), len(payload), digest.hexdigest()


def build_storage_key(
    *,
    artifact: StoredArtifact,
) -> str:
    return (
        f"{artifact.artifact_purpose}/{artifact.tenancy_id}/"
        f"{artifact.id}-{artifact.original_file_name}"
    )


def store_local_artifact_payload(
    *,
    payload: bytes,
    storage_key: str,
    settings: Settings,
) -> None:
    destination = get_artifact_storage_root(settings=settings) / storage_key
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.write_bytes(payload)
    except Exception:
        if destination.exists():
            destination.unlink()
        raise


def store_s3_artifact_payload(
    *,
    payload: bytes,
    storage_key: str,
    content_type: str,
    sha256_hex: str,
    settings: Settings,
) -> None:
    client = create_s3_client(settings=settings)
    client.put_object(
        Bucket=settings.artifact_s3_bucket_name,
        Key=storage_key,
        Body=payload,
        ContentType=content_type,
        Metadata={"sha256": sha256_hex},
    )


def store_uploaded_artifact(
    *,
    session: Session,
    settings: Settings,
    upload: UploadFile,
    created_by_user_id,
    tenancy_id,
    artifact_purpose: str = "evidence_document",
) -> StoredArtifact:
    ensure_upload_allowed(upload=upload, settings=settings)
    payload, size_bytes, sha256_hex = read_upload_bytes(upload=upload, settings=settings)

    artifact = StoredArtifact(
        created_by_user_id=created_by_user_id,
        tenancy_id=tenancy_id,
        artifact_purpose=artifact_purpose,
        storage_backend=settings.artifact_storage_backend,
        original_file_name=sanitize_filename(upload.filename or "artifact"),
        content_type=(upload.content_type or "application/octet-stream").strip().lower(),
        size_bytes=size_bytes,
        sha256_hex=sha256_hex,
        storage_key="pending",
    )
    session.add(artifact)
    session.flush()

    storage_key = build_storage_key(artifact=artifact)
    if settings.artifact_storage_backend == LOCAL_STORAGE_BACKEND:
        store_local_artifact_payload(
            payload=payload,
            storage_key=storage_key,
            settings=settings,
        )
    else:
        store_s3_artifact_payload(
            payload=payload,
            storage_key=storage_key,
            content_type=artifact.content_type,
            sha256_hex=sha256_hex,
            settings=settings,
        )

    artifact.storage_key = storage_key
    artifact.updated_at = utcnow()
    session.add(artifact)
    session.flush()
    return artifact


def build_stored_artifact_response(*, stored_artifact: StoredArtifact) -> StoredArtifactResponse:
    return StoredArtifactResponse(
        id=stored_artifact.id,
        tenancy_id=stored_artifact.tenancy_id,
        artifact_purpose=stored_artifact.artifact_purpose,
        storage_backend=stored_artifact.storage_backend,
        original_file_name=stored_artifact.original_file_name,
        content_type=stored_artifact.content_type,
        size_bytes=stored_artifact.size_bytes,
        created_by_user_id=stored_artifact.created_by_user_id,
        created_at=stored_artifact.created_at,
        updated_at=stored_artifact.updated_at,
    )


def build_download_signature(*, artifact_id: UUID, expires_at: datetime, settings: Settings) -> str:
    payload = f"{artifact_id}:{int(expires_at.timestamp())}"
    digest = hmac.new(
        settings.secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def validate_download_signature(
    *,
    artifact_id: UUID,
    expires: int,
    signature: str,
    settings: Settings,
) -> None:
    expires_at = datetime.fromtimestamp(expires, tz=utcnow().tzinfo)
    if expires_at <= utcnow():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Artifact access token has expired.",
        )

    expected = build_download_signature(
        artifact_id=artifact_id,
        expires_at=expires_at,
        settings=settings,
    )
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Artifact access token is invalid.",
        )


def build_stored_artifact_access_response(
    *,
    stored_artifact: StoredArtifact,
    settings: Settings,
) -> StoredArtifactAccessResponse:
    expires_at = utcnow() + timedelta(seconds=settings.artifact_signed_url_ttl_seconds)
    signature = build_download_signature(
        artifact_id=stored_artifact.id,
        expires_at=expires_at,
        settings=settings,
    )
    download_url = (
        "/api/v1/evidence/artifacts/download"
        f"?artifact_id={stored_artifact.id}"
        f"&expires={int(expires_at.timestamp())}"
        f"&signature={signature}"
    )
    return StoredArtifactAccessResponse(
        artifact_id=stored_artifact.id,
        storage_backend=stored_artifact.storage_backend,
        download_url=download_url,
        expires_at=expires_at,
    )


def resolve_artifact_path(*, stored_artifact: StoredArtifact, settings: Settings) -> Path:
    return get_artifact_storage_root(settings=settings) / stored_artifact.storage_key


def build_storage_redirect_url(
    *,
    stored_artifact: StoredArtifact,
    settings: Settings,
) -> str:
    if stored_artifact.storage_backend != S3_STORAGE_BACKEND:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This stored artifact is not backed by redirectable object storage.",
        )

    client = create_s3_client(settings=settings)
    return client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": settings.artifact_s3_bucket_name,
            "Key": stored_artifact.storage_key,
            "ResponseContentType": stored_artifact.content_type,
            "ResponseContentDisposition": (
                f'attachment; filename="{stored_artifact.original_file_name}"'
            ),
        },
        ExpiresIn=settings.artifact_signed_url_ttl_seconds,
    )


def resolve_attachable_tenancy_artifact(
    *,
    session: Session,
    artifact_id: UUID | None,
    tenancy: Tenancy,
    current_user: User,
) -> StoredArtifact | None:
    if artifact_id is None:
        return None

    stored_artifact = session.get(StoredArtifact, artifact_id)
    if stored_artifact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored artifact not found.",
        )
    if stored_artifact.tenancy_id != tenancy.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Stored artifact does not belong to this tenancy.",
        )
    if (
        stored_artifact.created_by_user_id != current_user.id
        and not current_user.system_role.can_access_admin_surfaces
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to attach this stored artifact.",
        )
    return stored_artifact
