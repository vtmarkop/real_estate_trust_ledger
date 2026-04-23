from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.deps import SessionDep, SettingsDep
from app.api.router import api_router
from app.core.health import build_readiness_payload
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, emit_structured_log


CURRENT_STAGE = "sprint-20-page-by-page-conversion-localization-and-ui-semantics-refactor"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging()

    application = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description="Rebuild scaffold for the evidence-verified trust platform.",
    )
    application.state.settings = settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def request_logging_middleware(request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid4().hex
        started_at = perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)
            emit_structured_log(
                "trustledger.request",
                message="request_failed",
                level=40,
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                query=request.url.query,
                status_code=500,
                duration_ms=duration_ms,
                error=str(exc),
            )
            raise

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production_like:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        duration_ms = round((perf_counter() - started_at) * 1000, 2)
        emit_structured_log(
            "trustledger.request",
            message="request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query=request.url.query,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response

    @application.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "api",
            "stage": CURRENT_STAGE,
            "environment": settings.app_env,
        }

    @application.get("/health/live", tags=["system"])
    def liveness_check() -> dict[str, str]:
        return {
            "status": "live",
            "service": "api",
            "stage": CURRENT_STAGE,
            "environment": settings.app_env,
        }

    @application.get("/health/ready", tags=["system"])
    def readiness_check(
        session: SessionDep,
        runtime_settings: SettingsDep,
    ):
        payload = build_readiness_payload(
            session=session,
            settings=runtime_settings,
            stage=CURRENT_STAGE,
        )
        status_code = 200 if payload["status"] == "ready" else 503
        return JSONResponse(
            status_code=status_code,
            content=jsonable_encoder(payload),
        )

    application.include_router(api_router)
    return application


app = create_app()
