from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

DEV_SECRET_KEY = "dev-only-change-before-production"
API_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = API_ROOT / ".env"
DEFAULT_DATABASE_URL = f"sqlite:///{(API_ROOT / 'trust_ledger.db').as_posix()}"
DEFAULT_ARTIFACT_STORAGE_ROOT = str(API_ROOT / "private_artifacts")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(DEFAULT_ENV_FILE),
        env_prefix="TRUST_LEDGER_",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: Literal["development", "test", "staging", "production"] = "development"
    api_title: str = "Trust Ledger API"
    api_version: str = "0.1.0"

    database_url: str = DEFAULT_DATABASE_URL
    database_echo: bool = False

    secret_key: str = DEV_SECRET_KEY
    session_ttl_minutes: int = 60 * 24 * 30
    cookie_name: str = "trust_ledger_session"
    cookie_secure: bool = False
    artifact_storage_backend: Literal["local_private", "s3_compatible"] = "local_private"
    artifact_storage_root: str = DEFAULT_ARTIFACT_STORAGE_ROOT
    artifact_s3_bucket_name: str | None = None
    artifact_s3_region: str = "us-east-1"
    artifact_s3_endpoint_url: str | None = None
    artifact_s3_access_key_id: str | None = None
    artifact_s3_secret_access_key: str | None = None
    artifact_s3_use_ssl: bool = True
    artifact_s3_force_path_style: bool = False
    artifact_signed_url_ttl_seconds: int = 300
    artifact_max_upload_size_bytes: int = 10 * 1024 * 1024
    artifact_allowed_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "application/pdf",
            "image/jpeg",
            "image/png",
            "image/webp",
            "text/plain",
        ]
    )

    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )
    public_api_base_url: str = "http://127.0.0.1:8000"
    public_web_base_url: str = "http://127.0.0.1:5173"
    redis_url: str | None = None
    worker_run_mode: Literal["once", "loop"] = "once"
    worker_poll_interval_seconds: int = 15
    worker_locked_poll_interval_seconds: int = 5
    worker_default_limit: int = 100
    worker_stale_follow_up_days: int = 30
    worker_coordination_backend: Literal["auto", "none", "redis"] = "auto"
    worker_lock_key: str = "trustledger:worker:lease"
    worker_lock_ttl_seconds: int = 60
    notification_transport: Literal["disabled", "log"] = "log"
    notification_sender_name: str = "Trust Ledger"
    notification_sender_email: str = "no-reply@trustledger.local"
    notification_batch_limit: int = 100

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("artifact_allowed_content_types", mode="before")
    @classmethod
    def parse_artifact_allowed_content_types(cls, value: object) -> object:
        if isinstance(value, str):
            return [content_type.strip() for content_type in value.split(",") if content_type.strip()]
        return value

    @field_validator("public_api_base_url", "public_web_base_url", mode="before")
    @classmethod
    def normalize_public_base_url(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().rstrip("/")
        return value

    @field_validator("redis_url", mode="before")
    @classmethod
    def normalize_redis_url(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @field_validator(
        "artifact_s3_bucket_name",
        "artifact_s3_endpoint_url",
        "artifact_s3_access_key_id",
        "artifact_s3_secret_access_key",
        mode="before",
    )
    @classmethod
    def normalize_optional_storage_fields(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip()
            return normalized or None
        return value

    @model_validator(mode="after")
    def validate_security_settings(self) -> "Settings":
        if self.app_env in {"staging", "production"}:
            if self.secret_key == DEV_SECRET_KEY or len(self.secret_key) < 32:
                raise ValueError("A long non-default secret key is required outside development.")
            if not self.cookie_secure:
                raise ValueError("cookie_secure must be enabled outside development.")
        if self.worker_coordination_backend == "redis" and not self.redis_url:
            raise ValueError("worker_coordination_backend=redis requires redis_url.")
        if self.artifact_storage_backend == "s3_compatible":
            if not self.artifact_s3_bucket_name:
                raise ValueError(
                    "artifact_s3_bucket_name is required when artifact_storage_backend=s3_compatible."
                )
            if not self.artifact_s3_access_key_id or not self.artifact_s3_secret_access_key:
                raise ValueError(
                    "artifact_s3_access_key_id and artifact_s3_secret_access_key are required "
                    "when artifact_storage_backend=s3_compatible."
                )
        if self.app_env == "production":
            for name, value in (
                ("public_api_base_url", self.public_api_base_url),
                ("public_web_base_url", self.public_web_base_url),
            ):
                parsed = urlparse(value)
                if parsed.scheme != "https":
                    raise ValueError(f"{name} must use https in production.")
        return self

    @property
    def is_production_like(self) -> bool:
        return self.app_env in {"staging", "production"}

    @property
    def resolved_worker_coordination_backend(self) -> Literal["none", "redis"]:
        if self.worker_coordination_backend == "auto":
            return "redis" if self.redis_url else "none"
        return "none" if self.worker_coordination_backend == "none" else "redis"

    @property
    def notifications_enabled(self) -> bool:
        return self.notification_transport != "disabled"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
