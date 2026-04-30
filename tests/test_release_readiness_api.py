from __future__ import annotations

from pathlib import Path
import sys
import unittest

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
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import NotificationDelivery, User, WorkerRun  # noqa: E402
from trustledger_domain import (  # noqa: E402
    NotificationChannel,
    NotificationDeliveryStatus,
    SystemRole,
    WorkerRunStatus,
)


class ReleaseReadinessApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)
        self.settings = Settings(
            app_env="development",
            database_url="sqlite://",
            secret_key="development-secret-key-with-32-characters",
            cookie_secure=False,
            public_api_base_url="http://127.0.0.1:8000",
            public_web_base_url="http://127.0.0.1:5173",
            worker_coordination_backend="auto",
            notification_transport="log",
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

    def new_client(self, *, base_url: str = "http://testserver") -> TestClient:
        client = TestClient(self.app, base_url=base_url)
        self.clients.append(client)
        return client

    def seed_user(
        self,
        *,
        email: str,
        full_name: str,
        password: str,
        system_role: SystemRole = SystemRole.USER,
    ) -> User:
        with Session(self.engine) as session:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                system_role=system_role,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def login(self, client: TestClient, *, email: str, password: str) -> None:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_development_runtime_shows_blocking_release_issues(self) -> None:
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.ADMIN,
        )
        with Session(self.engine) as session:
            session.add(
                NotificationDelivery(
                    channel=NotificationChannel.EMAIL,
                    status=NotificationDeliveryStatus.FAILED,
                    template_key="consent_expiry_reminder",
                    recipient_user_id=reviewer.id,
                    requested_by_user_id=reviewer.id,
                    recipient_address="reviewer@example.com",
                    subject_line="Test notification",
                    body_text="Failed delivery",
                )
            )
            session.commit()

        client = self.new_client()
        self.login(client, email="reviewer@example.com", password="reviewer-password-123")

        response = client.get("/api/v1/internal/release-readiness")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertNotIn("Strict-Transport-Security", response.headers)

        payload = response.json()
        self.assertEqual(payload["status"], "needs_attention")
        self.assertGreaterEqual(payload["blocking_issue_count"], 5)
        checks = {check["key"]: check for check in payload["checks"]}
        self.assertEqual(checks["environment"]["status"], "fail")
        self.assertEqual(checks["secure_cookie"]["status"], "fail")
        self.assertEqual(checks["public_urls"]["status"], "fail")
        self.assertEqual(checks["database_backend"]["status"], "fail")
        self.assertEqual(checks["worker_coordination"]["status"], "fail")
        self.assertEqual(checks["notification_transport"]["status"], "warning")
        self.assertEqual(checks["failed_notifications"]["status"], "warning")

    def test_staging_runtime_can_report_ready_status(self) -> None:
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.ADMIN,
        )
        self.settings = Settings(
            app_env="staging",
            database_url="postgresql+psycopg://trustledger:secret@db.example:5432/trustledger",
            secret_key="staging-secret-key-that-is-safely-over-thirty-two",
            cookie_secure=True,
            public_api_base_url="https://api.example.com",
            public_web_base_url="https://app.example.com",
            redis_url="redis://127.0.0.1:6379/0",
            worker_coordination_backend="redis",
            notification_transport="log",
        )
        self.build_app()

        with Session(self.engine) as session:
            session.add(
                WorkerRun(
                    worker_user_id=reviewer.id,
                    status=WorkerRunStatus.COMPLETED,
                    requested_limit=50,
                )
            )
            session.commit()

        client = self.new_client(base_url="https://testserver")
        self.login(client, email="reviewer@example.com", password="reviewer-password-123")

        response = client.get("/api/v1/internal/release-readiness")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(
            response.headers["Strict-Transport-Security"],
            "max-age=31536000; includeSubDomains",
        )

        payload = response.json()
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["blocking_issue_count"], 0)
        self.assertEqual(payload["environment"], "staging")
        checks = {check["key"]: check for check in payload["checks"]}
        self.assertEqual(checks["environment"]["status"], "pass")
        self.assertEqual(checks["secure_cookie"]["status"], "pass")
        self.assertEqual(checks["public_urls"]["status"], "pass")
        self.assertEqual(checks["database_backend"]["status"], "pass")
        self.assertEqual(checks["worker_coordination"]["status"], "pass")
        self.assertEqual(checks["latest_worker_run"]["status"], "pass")
        self.assertEqual(checks["notification_transport"]["status"], "warning")


if __name__ == "__main__":
    unittest.main()
