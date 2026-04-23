from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class StoredArtifactResponse(BaseModel):
    id: UUID
    tenancy_id: UUID
    artifact_purpose: str
    storage_backend: str
    original_file_name: str
    content_type: str
    size_bytes: int
    created_by_user_id: UUID
    created_at: datetime
    updated_at: datetime


class StoredArtifactAccessResponse(BaseModel):
    artifact_id: UUID
    storage_backend: str
    download_url: str
    expires_at: datetime
