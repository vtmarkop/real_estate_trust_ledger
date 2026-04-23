from __future__ import annotations

from pathlib import Path
import sys
import unittest

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"
WORKER_ROOT = ROOT / "apps" / "worker"

for path in (API_ROOT, DOMAIN_ROOT, WORKER_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.core.db import create_engine_from_url, get_session  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import User  # noqa: E402
from trustledger_domain import SystemRole  # noqa: E402
from worker.runtime import run_worker_cycle  # noqa: E402


class InternalWorkerApiTests(unittest.TestCase):
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

    def test_reviewer_can_list_and_read_worker_runs(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        self.seed_user(
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )

        with Session(self.engine) as session:
            summary = run_worker_cycle(session=session, limit=5)

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        runs_response = reviewer_client.get(
            "/api/v1/internal/workers/runs",
            params={"status_filter": "completed"},
        )
        self.assertEqual(runs_response.status_code, 200, runs_response.text)
        runs_payload = runs_response.json()
        self.assertEqual(len(runs_payload), 1)
        self.assertEqual(runs_payload[0]["id"], str(summary.worker_run_id))
        self.assertEqual(runs_payload[0]["status"], "completed")
        self.assertEqual(runs_payload[0]["requested_limit"], 5)

        run_detail = reviewer_client.get(f"/api/v1/internal/workers/runs/{summary.worker_run_id}")
        self.assertEqual(run_detail.status_code, 200, run_detail.text)
        self.assertEqual(run_detail.json()["id"], str(summary.worker_run_id))
        self.assertEqual(run_detail.json()["worker_user_email"], "worker@trustledger.internal")

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        denied = outsider_client.get("/api/v1/internal/workers/runs")
        self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()
