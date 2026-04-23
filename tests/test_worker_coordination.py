from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from sqlmodel import SQLModel, Session, select


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"
WORKER_ROOT = ROOT / "apps" / "worker"

for path in (API_ROOT, DOMAIN_ROOT, WORKER_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.core.config import Settings  # noqa: E402
from app.core.db import create_engine_from_url  # noqa: E402
from app.models import WorkerRun  # noqa: E402
from worker.coordination import (  # noqa: E402
    RedisWorkerCoordinator,
    build_worker_coordinator,
)
from worker.main import run_worker_service_once  # noqa: E402


class FakeRedisSocket:
    def __init__(self, response_bytes: bytes) -> None:
        self._response = BytesIO(response_bytes)
        self.sent_payload = b""

    def sendall(self, payload: bytes) -> None:
        self.sent_payload += payload

    def makefile(self, mode: str):
        return self._response

    def close(self) -> None:
        return None


class DecliningCoordinator:
    def execution_lease(self):
        from worker.coordination import WorkerExecutionLease

        return WorkerExecutionLease(acquired=False, backend="test")


class WorkerCoordinationTests(unittest.TestCase):
    def test_build_worker_coordinator_defaults_to_noop_without_redis(self) -> None:
        settings = Settings(worker_coordination_backend="auto", redis_url=None)
        coordinator = build_worker_coordinator(settings)
        lease = coordinator.execution_lease()
        self.assertTrue(lease.acquired)
        self.assertEqual(lease.backend, "none")

    def test_redis_worker_coordinator_acquires_and_releases_lock(self) -> None:
        acquire_socket = FakeRedisSocket(b"+OK\r\n")
        release_socket = FakeRedisSocket(b":1\r\n")

        with patch(
            "worker.coordination.socket.create_connection",
            side_effect=[acquire_socket, release_socket],
        ):
            coordinator = RedisWorkerCoordinator(
                redis_url="redis://127.0.0.1:6379/0",
                lock_key="trustledger:test:lock",
                lock_ttl_seconds=30,
            )
            with coordinator.execution_lease() as lease:
                self.assertTrue(lease.acquired)
                self.assertEqual(lease.backend, "redis")
            self.assertIn(b"SET", acquire_socket.sent_payload)
            self.assertIn(b"EVAL", release_socket.sent_payload)

    def test_redis_worker_coordinator_skips_when_lock_is_unavailable(self) -> None:
        contended_socket = FakeRedisSocket(b"$-1\r\n")

        with patch(
            "worker.coordination.socket.create_connection",
            return_value=contended_socket,
        ):
            coordinator = RedisWorkerCoordinator(
                redis_url="redis://127.0.0.1:6379/0",
                lock_key="trustledger:test:lock",
                lock_ttl_seconds=30,
            )
            with coordinator.execution_lease() as lease:
                self.assertFalse(lease.acquired)
                self.assertEqual(lease.lock_key, "trustledger:test:lock")

    def test_worker_service_once_skips_without_creating_worker_run_when_lease_is_unavailable(self) -> None:
        engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(engine)

        result = run_worker_service_once(
            settings=Settings(database_url="sqlite://"),
            coordinator=DecliningCoordinator(),
            session_factory=lambda: Session(engine),
        )
        self.assertFalse(result.executed)
        self.assertEqual(result.coordination_backend, "test")

        with Session(engine) as session:
            worker_runs = session.exec(select(WorkerRun)).all()
            self.assertEqual(worker_runs, [])


if __name__ == "__main__":
    unittest.main()
