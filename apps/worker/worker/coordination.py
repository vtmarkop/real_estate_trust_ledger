from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from io import BufferedReader
from typing import Callable
import socket
from urllib.parse import urlparse

from app.core.config import Settings
from app.core.security import generate_session_token


RELEASE_LOCK_SCRIPT = (
    "if redis.call('GET', KEYS[1]) == ARGV[1] "
    "then return redis.call('DEL', KEYS[1]) else return 0 end"
)


class WorkerCoordinationError(RuntimeError):
    """Raised when runtime coordination fails unexpectedly."""


@dataclass
class WorkerExecutionLease(AbstractContextManager["WorkerExecutionLease"]):
    acquired: bool
    backend: str
    lock_key: str | None = None
    owner_token: str | None = None
    _release_callback: Callable[[], None] | None = None

    def __enter__(self) -> "WorkerExecutionLease":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._release_callback is not None and self.acquired:
            self._release_callback()


class NoopWorkerCoordinator:
    backend_name = "none"

    def execution_lease(self) -> WorkerExecutionLease:
        return WorkerExecutionLease(acquired=True, backend=self.backend_name)


class RedisWorkerCoordinator:
    backend_name = "redis"

    def __init__(
        self,
        *,
        redis_url: str,
        lock_key: str,
        lock_ttl_seconds: int,
        socket_timeout_seconds: float = 2.0,
    ) -> None:
        parsed = urlparse(redis_url)
        if parsed.scheme != "redis":
            raise WorkerCoordinationError("Only redis:// URLs are currently supported for worker coordination.")
        self.redis_url = redis_url
        self.host = parsed.hostname or "127.0.0.1"
        self.port = parsed.port or 6379
        self.password = parsed.password
        self.database_index = int((parsed.path or "/0").lstrip("/") or "0")
        self.lock_key = lock_key
        self.lock_ttl_seconds = lock_ttl_seconds
        self.socket_timeout_seconds = socket_timeout_seconds

    def execution_lease(self) -> WorkerExecutionLease:
        owner_token = generate_session_token()
        acquired = self._try_acquire_lock(owner_token)
        if not acquired:
            return WorkerExecutionLease(
                acquired=False,
                backend=self.backend_name,
                lock_key=self.lock_key,
            )
        return WorkerExecutionLease(
            acquired=True,
            backend=self.backend_name,
            lock_key=self.lock_key,
            owner_token=owner_token,
            _release_callback=lambda: self._release_lock(owner_token),
        )

    def _connect(self):
        try:
            connection = socket.create_connection(
                (self.host, self.port),
                timeout=self.socket_timeout_seconds,
            )
        except OSError as exc:
            raise WorkerCoordinationError(f"Unable to connect to Redis coordination backend: {exc}") from exc
        file_handle = connection.makefile("rb")
        try:
            if self.password:
                self._send_command(connection, "AUTH", self.password)
                self._read_response(file_handle)
            if self.database_index:
                self._send_command(connection, "SELECT", str(self.database_index))
                self._read_response(file_handle)
            return connection, file_handle
        except Exception:
            file_handle.close()
            connection.close()
            raise

    def _send_command(self, connection, *parts: str) -> None:
        encoded = self._encode_command(*parts)
        connection.sendall(encoded)

    def _try_acquire_lock(self, owner_token: str) -> bool:
        connection, file_handle = self._connect()
        try:
            self._send_command(
                connection,
                "SET",
                self.lock_key,
                owner_token,
                "NX",
                "EX",
                str(self.lock_ttl_seconds),
            )
            response = self._read_response(file_handle)
            return response == "OK"
        finally:
            file_handle.close()
            connection.close()

    def _release_lock(self, owner_token: str) -> None:
        connection, file_handle = self._connect()
        try:
            self._send_command(
                connection,
                "EVAL",
                RELEASE_LOCK_SCRIPT,
                "1",
                self.lock_key,
                owner_token,
            )
            self._read_response(file_handle)
        finally:
            file_handle.close()
            connection.close()

    @staticmethod
    def _encode_command(*parts: str) -> bytes:
        chunks = [f"*{len(parts)}\r\n".encode("utf-8")]
        for part in parts:
            encoded_part = part.encode("utf-8")
            chunks.append(f"${len(encoded_part)}\r\n".encode("utf-8"))
            chunks.append(encoded_part)
            chunks.append(b"\r\n")
        return b"".join(chunks)

    @classmethod
    def _read_response(cls, file_handle: BufferedReader):
        prefix = file_handle.read(1)
        if not prefix:
            raise WorkerCoordinationError("Redis coordination connection closed unexpectedly.")
        if prefix == b"+":
            return cls._read_line(file_handle)
        if prefix == b"-":
            raise WorkerCoordinationError(f"Redis returned an error: {cls._read_line(file_handle)}")
        if prefix == b":":
            return int(cls._read_line(file_handle))
        if prefix == b"$":
            length = int(cls._read_line(file_handle))
            if length == -1:
                return None
            data = file_handle.read(length)
            file_handle.read(2)
            return data.decode("utf-8")
        if prefix == b"*":
            length = int(cls._read_line(file_handle))
            if length == -1:
                return None
            return [cls._read_response(file_handle) for _ in range(length)]
        raise WorkerCoordinationError(f"Unsupported Redis response prefix: {prefix!r}")

    @staticmethod
    def _read_line(file_handle: BufferedReader) -> str:
        line = file_handle.readline()
        if not line:
            raise WorkerCoordinationError("Redis coordination connection closed while reading response.")
        return line[:-2].decode("utf-8")


def build_worker_coordinator(settings: Settings):
    if settings.resolved_worker_coordination_backend == "redis":
        if not settings.redis_url:
            raise WorkerCoordinationError("Redis coordination requires redis_url.")
        return RedisWorkerCoordinator(
            redis_url=settings.redis_url,
            lock_key=settings.worker_lock_key,
            lock_ttl_seconds=settings.worker_lock_ttl_seconds,
        )
    return NoopWorkerCoordinator()
