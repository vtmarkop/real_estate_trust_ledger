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


from app.core.db import create_engine_from_url, get_session  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import NotificationDelivery, User  # noqa: E402
from app.models.common import utcnow  # noqa: E402
from trustledger_domain import (  # noqa: E402
    NotificationChannel,
    NotificationDeliveryStatus,
    SystemRole,
)


class InternalNotificationsApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)

        app = create_app()

        def override_get_session():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        self.app = app
        self.clients: list[TestClient] = []

    def tearDown(self) -> None:
        for client in self.clients:
            client.close()
        self.app.dependency_overrides.clear()

    def new_client(self) -> TestClient:
        client = TestClient(self.app)
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

    def test_reviewer_can_list_due_notifications(self) -> None:
        reviewer = self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        subject = self.seed_user(
            email="subject@example.com",
            full_name="Subject User",
            password="subject-password-123",
        )

        with Session(self.engine) as session:
            session.add(
                NotificationDelivery(
                    channel=NotificationChannel.EMAIL,
                    status=NotificationDeliveryStatus.PENDING,
                    template_key="consent_expiry_reminder",
                    recipient_user_id=subject.id,
                    requested_by_user_id=reviewer.id,
                    recipient_address="subject@example.com",
                    subject_line="Reminder",
                    body_text="Reminder body",
                    scheduled_for=utcnow(),
                )
            )
            session.commit()

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        response = reviewer_client.get("/api/v1/internal/notifications", params={"due_only": "true"})
        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["recipient_user_email"], "subject@example.com")
        self.assertEqual(payload[0]["status"], "pending")

    def test_plain_user_is_denied_internal_notifications(self) -> None:
        self.seed_user(
            email="plain@example.com",
            full_name="Plain User",
            password="plain-password-123",
        )

        plain_client = self.new_client()
        self.login(plain_client, email="plain@example.com", password="plain-password-123")

        denied = plain_client.get("/api/v1/internal/notifications")
        self.assertEqual(denied.status_code, 403, denied.text)


if __name__ == "__main__":
    unittest.main()
