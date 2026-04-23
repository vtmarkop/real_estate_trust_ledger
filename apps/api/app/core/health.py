from __future__ import annotations

from pathlib import Path
import socket
from urllib.parse import urlparse

from sqlalchemy import text
from sqlmodel import Session

from app.core.config import Settings


def check_database_ready(*, session: Session) -> dict[str, str]:
    session.exec(text("SELECT 1")).one()
    return {"status": "ok", "detail": "database query succeeded"}


def check_artifact_storage_ready(*, settings: Settings) -> dict[str, str]:
    artifact_root = Path(settings.artifact_storage_root)
    artifact_root.mkdir(parents=True, exist_ok=True)
    if not artifact_root.is_dir():
        raise RuntimeError("artifact storage root is not a directory")
    if not artifact_root.exists():
        raise RuntimeError("artifact storage root does not exist")
    return {"status": "ok", "detail": str(artifact_root)}


def probe_redis_ready(*, redis_url: str, timeout_seconds: float = 1.5) -> dict[str, str]:
    parsed = urlparse(redis_url)
    if parsed.scheme != "redis":
        raise RuntimeError("only redis:// urls are supported for readiness checks")

    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 6379
    password = parsed.password
    database_index = int((parsed.path or "/0").lstrip("/") or "0")

    with socket.create_connection((host, port), timeout=timeout_seconds) as connection:
        file_handle = connection.makefile("rb")
        try:
            if password:
                _send_redis_command(connection, "AUTH", password)
                _expect_redis_ok(file_handle)
            if database_index:
                _send_redis_command(connection, "SELECT", str(database_index))
                _expect_redis_ok(file_handle)
            _send_redis_command(connection, "PING")
            response = _read_redis_response(file_handle)
        finally:
            file_handle.close()

    if response != "PONG":
        raise RuntimeError("redis ping returned an unexpected response")
    return {"status": "ok", "detail": f"redis ping succeeded against {host}:{port}"}


def check_redis_ready(*, settings: Settings) -> dict[str, str]:
    if settings.resolved_worker_coordination_backend != "redis":
        return {"status": "skipped", "detail": "redis coordination is not enabled"}
    if not settings.redis_url:
        raise RuntimeError("redis coordination is enabled without a redis url")
    return probe_redis_ready(redis_url=settings.redis_url)


def build_readiness_payload(*, session: Session, settings: Settings, stage: str) -> dict:
    components: dict[str, dict[str, str]] = {}
    overall_status = "ready"

    for component_name, checker in (
        ("database", lambda: check_database_ready(session=session)),
        ("artifact_storage", lambda: check_artifact_storage_ready(settings=settings)),
        ("redis", lambda: check_redis_ready(settings=settings)),
    ):
        try:
            component_payload = checker()
        except Exception as exc:
            component_payload = {"status": "error", "detail": str(exc)}
        components[component_name] = component_payload
        if component_payload["status"] == "error":
            overall_status = "not_ready"

    return {
        "status": overall_status,
        "service": "api",
        "stage": stage,
        "environment": settings.app_env,
        "components": components,
    }


def _send_redis_command(connection, *parts: str) -> None:
    chunks = [f"*{len(parts)}\r\n".encode("utf-8")]
    for part in parts:
        encoded_part = part.encode("utf-8")
        chunks.append(f"${len(encoded_part)}\r\n".encode("utf-8"))
        chunks.append(encoded_part)
        chunks.append(b"\r\n")
    connection.sendall(b"".join(chunks))


def _expect_redis_ok(file_handle) -> None:
    response = _read_redis_response(file_handle)
    if response != "OK":
        raise RuntimeError(f"unexpected redis response: {response}")


def _read_redis_response(file_handle):
    prefix = file_handle.read(1)
    if not prefix:
        raise RuntimeError("redis connection closed unexpectedly")
    if prefix == b"+":
        return _read_redis_line(file_handle)
    if prefix == b"-":
        raise RuntimeError(_read_redis_line(file_handle))
    if prefix == b":":
        return int(_read_redis_line(file_handle))
    if prefix == b"$":
        length = int(_read_redis_line(file_handle))
        if length == -1:
            return None
        data = file_handle.read(length)
        file_handle.read(2)
        return data.decode("utf-8")
    raise RuntimeError(f"unsupported redis response prefix: {prefix!r}")


def _read_redis_line(file_handle) -> str:
    line = file_handle.readline()
    if not line:
        raise RuntimeError("redis connection closed while reading response")
    return line[:-2].decode("utf-8")
