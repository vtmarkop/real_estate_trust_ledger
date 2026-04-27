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
from app.models import User  # noqa: E402
from trustledger_domain import AccountWorkspaceRole, SystemRole  # noqa: E402


class InternalAuditApiTests(unittest.TestCase):
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
        workspace_roles: tuple[AccountWorkspaceRole, ...] | None = None,
    ) -> User:
        with Session(self.engine) as session:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
                system_role=system_role,
            )
            if workspace_roles is not None:
                user.set_workspace_roles(workspace_roles)
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

    def create_agency(self, client: TestClient, *, name: str = "Acme Realty") -> dict:
        response = client.post(
            "/api/v1/organizations",
            json={
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "organization_type": "agency",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_reviewer_can_read_audit_logs_for_consent_and_trust_check_flows(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )
        self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        subject_client = self.new_client()
        self.login(subject_client, email="tenant@example.com", password="tenant-password-123")
        create_consent = subject_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 14,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_payload = create_consent.json()

        validate_response = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_payload["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(validate_response.status_code, 200, validate_response.text)

        preview_response = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/profile",
            json={
                "share_token": consent_payload["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(preview_response.status_code, 200, preview_response.text)

        create_trust_check = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks",
            json={
                "share_token": consent_payload["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(create_trust_check.status_code, 201, create_trust_check.text)

        revoke_response = subject_client.post(
            f"/api/v1/consents/trust-report/{consent_payload['id']}/revoke"
        )
        self.assertEqual(revoke_response.status_code, 200, revoke_response.text)

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        audit_logs = reviewer_client.get(
            "/api/v1/internal/audit-logs",
            params={"organization_id": agency["id"], "limit": 20},
        )
        self.assertEqual(audit_logs.status_code, 200, audit_logs.text)
        action_types = {entry["action_type"] for entry in audit_logs.json()}
        self.assertIn("trust_report_consent_created", action_types)
        self.assertIn("trust_check_validated", action_types)
        self.assertIn("trust_profile_previewed", action_types)
        self.assertIn("trust_check_created", action_types)
        self.assertIn("trust_report_consent_revoked", action_types)

        consent_logs = reviewer_client.get(
            "/api/v1/internal/audit-logs",
            params={"action_type": "trust_report_consent_created", "limit": 10},
        )
        self.assertEqual(consent_logs.status_code, 200, consent_logs.text)
        self.assertEqual(len(consent_logs.json()), 1)
        self.assertEqual(consent_logs.json()[0]["organization_id"], agency["id"])
        self.assertEqual(consent_logs.json()[0]["subject_user_email"], "tenant@example.com")

    def test_reviewer_can_read_audit_logs_for_automation_operations(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )
        subject = self.seed_user(
            email="subject@example.com",
            full_name="Subject User",
            password="subject-password-123",
        )

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")

        create_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/score-refresh/users/{subject.id}",
            json={"scheduled_for": "2026-04-10T07:00:00Z"},
        )
        self.assertEqual(create_task.status_code, 201, create_task.text)
        task_payload = create_task.json()

        claim_task = reviewer_client.post(
            "/api/v1/internal/automation/tasks/claim",
            json={
                "task_type": "user_score_recalculation",
                "limit": 1,
                "due_before": "2026-04-11T12:00:00Z",
            },
        )
        self.assertEqual(claim_task.status_code, 200, claim_task.text)
        self.assertEqual(len(claim_task.json()), 1)

        execute_task = reviewer_client.post(
            f"/api/v1/internal/automation/tasks/{task_payload['id']}/execute"
        )
        self.assertEqual(execute_task.status_code, 200, execute_task.text)

        stale_follow_up = reviewer_client.post(
            "/api/v1/internal/automation/tasks/follow-ups",
            json={
                "title": "Old follow-up",
                "details": "This one should auto-close.",
                "subject_user_id": str(subject.id),
                "scheduled_for": "2026-03-01T09:00:00Z",
            },
        )
        self.assertEqual(stale_follow_up.status_code, 201, stale_follow_up.text)

        cleanup_follow_up = reviewer_client.post(
            "/api/v1/internal/automation/cleanup/stale-follow-ups",
            json={
                "due_before": "2026-04-11T12:00:00Z",
                "stale_after_days": 14,
            },
        )
        self.assertEqual(cleanup_follow_up.status_code, 200, cleanup_follow_up.text)
        self.assertEqual(cleanup_follow_up.json()["processed_task_count"], 1)

        audit_logs = reviewer_client.get("/api/v1/internal/audit-logs", params={"limit": 20})
        self.assertEqual(audit_logs.status_code, 200, audit_logs.text)
        action_types = [entry["action_type"] for entry in audit_logs.json()]
        self.assertIn("automation_task_claimed", action_types)
        self.assertIn("automation_task_executed", action_types)
        self.assertIn("automation_task_cleaned_up", action_types)

        plain_user = self.seed_user(
            email="plain@example.com",
            full_name="Plain User",
            password="plain-password-123",
        )
        plain_client = self.new_client()
        self.login(plain_client, email=plain_user.email, password="plain-password-123")
        denied = plain_client.get("/api/v1/internal/audit-logs")
        self.assertEqual(denied.status_code, 403, denied.text)

    def test_denied_trust_check_attempt_is_audited(self) -> None:
        self.seed_user(
            email="reviewer@example.com",
            full_name="Reviewer User",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
            workspace_roles=(AccountWorkspaceRole.INTERNAL,),
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )
        self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)

        subject_client = self.new_client()
        self.login(subject_client, email="tenant@example.com", password="tenant-password-123")
        create_consent = subject_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 14,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_payload = create_consent.json()

        denied_validate = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_payload["share_token"],
                "access_code": "9999",
            },
        )
        self.assertEqual(denied_validate.status_code, 401, denied_validate.text)

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        audit_logs = reviewer_client.get(
            "/api/v1/internal/audit-logs",
            params={"action_type": "trust_check_validated", "organization_id": agency["id"]},
        )
        self.assertEqual(audit_logs.status_code, 200, audit_logs.text)
        self.assertEqual(len(audit_logs.json()), 1)
        self.assertEqual(audit_logs.json()[0]["outcome_status"], "denied")
        self.assertEqual(audit_logs.json()[0]["subject_user_email"], "tenant@example.com")


if __name__ == "__main__":
    unittest.main()
