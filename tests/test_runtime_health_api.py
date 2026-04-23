from __future__ import annotations

from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"

for path in (API_ROOT, DOMAIN_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.api.deps import get_runtime_settings  # noqa: E402
from app.core.config import Settings  # noqa: E402
from app.core.db import create_engine_from_url, get_session  # noqa: E402
from app.main import create_app  # noqa: E402


class RuntimeHealthApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)
        self.tempdir = TemporaryDirectory()
        self.settings = Settings(
            app_env="development",
            database_url="sqlite://",
            artifact_storage_root=self.tempdir.name,
            secret_key="development-secret-key-with-32-characters",
            cookie_secure=False,
            redis_url=None,
            worker_coordination_backend="auto",
        )
        self.clients: list[TestClient] = []
        self.build_app()

    def build_app(self) -> None:
        if hasattr(self, "app"):
            self.app.dependency_overrides.clear()

        app = create_app(settings=self.settings)

        def override_get_session():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_runtime_settings] = lambda: self.settings
        self.app = app

    def tearDown(self) -> None:
        for client in self.clients:
            client.close()
        self.app.dependency_overrides.clear()
        self.tempdir.cleanup()

    def new_client(self, *, base_url: str = "http://testserver") -> TestClient:
        client = TestClient(self.app, base_url=base_url)
        self.clients.append(client)
        return client

    def test_liveness_and_readiness_report_component_state(self) -> None:
        client = self.new_client()

        with self.assertLogs("trustledger.request", level="INFO") as logs:
            live_response = client.get("/health/live")
        self.assertEqual(live_response.status_code, 200, live_response.text)
        self.assertEqual(live_response.json()["status"], "live")
        self.assertIn("X-Request-ID", live_response.headers)
        self.assertEqual(live_response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(live_response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(
            live_response.headers["Referrer-Policy"],
            "strict-origin-when-cross-origin",
        )
        self.assertTrue(any("/health/live" in entry for entry in logs.output))

        ready_response = client.get("/health/ready")
        self.assertEqual(ready_response.status_code, 200, ready_response.text)
        payload = ready_response.json()
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["components"]["database"]["status"], "ok")
        self.assertEqual(payload["components"]["artifact_storage"]["status"], "ok")
        self.assertEqual(payload["components"]["redis"]["status"], "skipped")
        self.assertIn("X-Request-ID", ready_response.headers)
        self.assertEqual(ready_response.headers["X-Content-Type-Options"], "nosniff")

    def test_readiness_returns_503_when_redis_check_fails(self) -> None:
        self.settings = Settings(
            app_env="development",
            database_url="sqlite://",
            artifact_storage_root=self.tempdir.name,
            secret_key="development-secret-key-with-32-characters",
            cookie_secure=False,
            redis_url="redis://127.0.0.1:6379/0",
            worker_coordination_backend="redis",
        )
        client = self.new_client()

        with patch(
            "app.core.health.probe_redis_ready",
            side_effect=RuntimeError("redis unavailable"),
        ):
            ready_response = client.get("/health/ready")

        self.assertEqual(ready_response.status_code, 503, ready_response.text)
        payload = ready_response.json()
        self.assertEqual(payload["status"], "not_ready")
        self.assertEqual(payload["components"]["redis"]["status"], "error")
        self.assertIn("redis unavailable", payload["components"]["redis"]["detail"])

    def test_production_like_runtime_adds_hsts_header(self) -> None:
        self.settings = Settings(
            app_env="staging",
            database_url="postgresql+psycopg://trustledger:secret@db.example:5432/trustledger",
            artifact_storage_root=self.tempdir.name,
            secret_key="staging-secret-key-that-is-safely-over-thirty-two",
            cookie_secure=True,
            public_api_base_url="https://api.example.com",
            public_web_base_url="https://app.example.com",
            redis_url="redis://127.0.0.1:6379/0",
            worker_coordination_backend="redis",
        )
        self.build_app()
        client = self.new_client(base_url="https://testserver")

        with patch(
            "app.core.health.probe_redis_ready",
            return_value={"status": "ok", "detail": "redis ping succeeded"},
        ):
            live_response = client.get("/health/live")

        self.assertEqual(
            live_response.headers["Strict-Transport-Security"],
            "max-age=31536000; includeSubDomains",
        )


if __name__ == "__main__":
    unittest.main()
