from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.consents import router as consents_router
from app.api.routes.deposits import router as deposits_router
from app.api.routes.evidence import router as evidence_router
from app.api.routes.history_imports import router as history_imports_router
from app.api.routes.internal import router as internal_router
from app.api.routes.internal_audit import router as internal_audit_router
from app.api.routes.internal_automation import router as internal_automation_router
from app.api.routes.internal_disputes import router as internal_disputes_router
from app.api.routes.internal_notifications import router as internal_notifications_router
from app.api.routes.internal_operations import router as internal_operations_router
from app.api.routes.internal_release import router as internal_release_router
from app.api.routes.internal_scoring import router as internal_scoring_router
from app.api.routes.internal_workers import router as internal_workers_router
from app.api.routes.listings import router as listings_router
from app.api.routes.maintenance import router as maintenance_router
from app.api.routes.organizations import router as organizations_router
from app.api.routes.payments import router as payments_router
from app.api.routes.properties import router as properties_router
from app.api.routes.reference_requests import router as reference_requests_router
from app.api.routes.tenancies import router as tenancies_router
from app.api.routes.trust_checks import router as trust_checks_router
from app.api.routes.trust_scores import router as trust_scores_router
from app.api.routes.trust_events import router as trust_events_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(consents_router)
api_router.include_router(deposits_router)
api_router.include_router(evidence_router)
api_router.include_router(history_imports_router)
api_router.include_router(listings_router)
api_router.include_router(maintenance_router)
api_router.include_router(organizations_router)
api_router.include_router(payments_router)
api_router.include_router(properties_router)
api_router.include_router(reference_requests_router)
api_router.include_router(tenancies_router)
api_router.include_router(internal_router)
api_router.include_router(internal_audit_router)
api_router.include_router(internal_automation_router)
api_router.include_router(internal_disputes_router)
api_router.include_router(internal_notifications_router)
api_router.include_router(internal_operations_router)
api_router.include_router(internal_release_router)
api_router.include_router(internal_scoring_router)
api_router.include_router(internal_workers_router)
api_router.include_router(trust_checks_router)
api_router.include_router(trust_scores_router)
api_router.include_router(trust_events_router)
