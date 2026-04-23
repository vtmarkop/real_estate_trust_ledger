from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ReleaseReadinessCheckStatus = Literal["pass", "warning", "fail"]
ReleaseReadinessStatus = Literal["ready", "needs_attention"]


class ReleaseReadinessCheckResponse(BaseModel):
    key: str
    label: str
    status: ReleaseReadinessCheckStatus
    detail: str


class ReleaseReadinessResponse(BaseModel):
    status: ReleaseReadinessStatus
    environment: str
    public_api_base_url: str
    public_web_base_url: str
    blocking_issue_count: int
    warning_count: int
    checks: list[ReleaseReadinessCheckResponse]
    generated_at: datetime
