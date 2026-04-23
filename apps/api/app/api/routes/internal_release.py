from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, SettingsDep, require_system_roles
from app.schemas.release import ReleaseReadinessResponse
from app.services.release_readiness import build_release_readiness
from trustledger_domain import SystemRole


router = APIRouter(prefix="/internal/release-readiness", tags=["internal-release"])


@router.get(
    "",
    response_model=ReleaseReadinessResponse,
)
def get_release_readiness(
    session: SessionDep,
    settings: SettingsDep,
    current_user=Depends(require_system_roles(SystemRole.REVIEWER, SystemRole.ADMIN)),
) -> ReleaseReadinessResponse:
    return build_release_readiness(session=session, settings=settings)
