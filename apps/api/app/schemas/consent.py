from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from trustledger_domain import ConsentScope


class TrustReportConsentCreateRequest(BaseModel):
    grantee_organization_id: UUID
    access_code: str = Field(min_length=4, max_length=64)
    expires_in_days: int = Field(default=30, ge=1, le=365)


class TrustReportConsentResponse(BaseModel):
    id: UUID
    subject_user_id: UUID
    granted_by_user_id: UUID
    grantee_organization_id: UUID
    grantee_organization_name: str
    grantee_organization_slug: str
    scope: ConsentScope
    failed_access_attempt_count: int
    last_access_attempt_at: datetime | None = None
    access_locked_until: datetime | None = None
    last_validated_at: datetime | None = None
    expires_at: datetime
    revoked_at: datetime | None = None
    is_active: bool
    created_at: datetime


class TrustReportConsentCreateResponse(TrustReportConsentResponse):
    share_token: str
