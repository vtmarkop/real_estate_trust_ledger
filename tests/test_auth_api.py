from __future__ import annotations

from pathlib import Path
import sys
import unittest
import uuid

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, select


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
from app.models import AuditLog, AuthSession, User  # noqa: E402
from app.models.common import utcnow  # noqa: E402
from trustledger_domain import AccountWorkspaceRole, SystemRole  # noqa: E402


class AuthApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)

        app = create_app()

        def override_get_session():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        self.app = app
        self.client = TestClient(app)
        self.extra_clients: list[TestClient] = []

    def tearDown(self) -> None:
        self.client.close()
        for client in self.extra_clients:
            client.close()
        self.app.dependency_overrides.clear()

    def new_client(self) -> TestClient:
        client = TestClient(self.app)
        self.extra_clients.append(client)
        return client

    def test_register_login_me_logout_flow(self) -> None:
        register_payload = {
            "email": "agent@example.com",
            "full_name": "Agency Agent",
            "password": "super-secret-123",
        }

        register_response = self.client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(register_response.status_code, 201)
        self.assertEqual(register_response.json()["email"], "agent@example.com")
        self.assertEqual(register_response.json()["workspace_roles"], ["tenant"])

        duplicate_response = self.client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(duplicate_response.status_code, 409)

        login_response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "agent@example.com",
                "password": "super-secret-123",
            },
        )
        self.assertEqual(login_response.status_code, 200)
        self.assertIn("trust_ledger_session", login_response.headers.get("set-cookie", ""))

        me_response = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["full_name"], "Agency Agent")
        self.assertEqual(me_response.json()["workspace_roles"], ["tenant"])

        with Session(self.engine) as session:
            sessions = session.exec(select(AuthSession)).all()
            self.assertEqual(len(sessions), 1)
            self.assertIsNone(sessions[0].revoked_at)

        logout_response = self.client.post("/api/v1/auth/logout")
        self.assertEqual(logout_response.status_code, 204)

        me_after_logout = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_after_logout.status_code, 401)

        with Session(self.engine) as session:
            sessions = session.exec(select(AuthSession)).all()
            self.assertEqual(len(sessions), 1)
            self.assertIsNotNone(sessions[0].revoked_at)

    def test_login_rejects_invalid_credentials(self) -> None:
        with Session(self.engine) as session:
            user = User(
                email="user@example.com",
                full_name="Example User",
                password_hash=hash_password("different-password-123"),
            )
            session.add(user)
            session.commit()

        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "super-secret-123",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_user_can_list_and_revoke_other_sessions(self) -> None:
        register_payload = {
            "email": "agent@example.com",
            "full_name": "Agency Agent",
            "password": "super-secret-123",
        }
        register_response = self.client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(register_response.status_code, 201)

        login_primary = self.client.post(
            "/api/v1/auth/login",
            json={"email": "agent@example.com", "password": "super-secret-123"},
        )
        self.assertEqual(login_primary.status_code, 200)

        second_client = self.new_client()
        login_secondary = second_client.post(
            "/api/v1/auth/login",
            json={"email": "agent@example.com", "password": "super-secret-123"},
        )
        self.assertEqual(login_secondary.status_code, 200)

        list_sessions = self.client.get("/api/v1/auth/sessions")
        self.assertEqual(list_sessions.status_code, 200, list_sessions.text)
        self.assertEqual(len(list_sessions.json()), 2)
        current_sessions = [entry for entry in list_sessions.json() if entry["is_current"]]
        self.assertEqual(len(current_sessions), 1)

        revoke_others = self.client.post("/api/v1/auth/sessions/revoke-others")
        self.assertEqual(revoke_others.status_code, 200, revoke_others.text)
        self.assertEqual(revoke_others.json()["revoked_session_count"], 1)
        revoked_session_id = revoke_others.json()["revoked_session_ids"][0]

        me_primary = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_primary.status_code, 200, me_primary.text)

        me_secondary = second_client.get("/api/v1/auth/me")
        self.assertEqual(me_secondary.status_code, 401, me_secondary.text)

        sessions_after = self.client.get("/api/v1/auth/sessions")
        self.assertEqual(sessions_after.status_code, 200, sessions_after.text)
        revoked_entries = [
            entry for entry in sessions_after.json() if entry["id"] == revoked_session_id
        ]
        self.assertEqual(len(revoked_entries), 1)
        self.assertFalse(revoked_entries[0]["is_active"])

        with Session(self.engine) as session:
            auth_sessions = session.exec(select(AuthSession)).all()
            self.assertEqual(len(auth_sessions), 2)
            self.assertEqual(sum(1 for item in auth_sessions if item.revoked_at is not None), 1)
            audit_logs = session.exec(select(AuditLog)).all()
            self.assertTrue(any(log.action_type.value == "auth_session_created" for log in audit_logs))
            self.assertTrue(any(log.action_type.value == "auth_session_revoked" for log in audit_logs))

        security_events = self.client.get("/api/v1/auth/security-events")
        self.assertEqual(security_events.status_code, 200, security_events.text)
        action_types = [entry["action_type"] for entry in security_events.json()]
        self.assertIn("auth_session_created", action_types)
        self.assertIn("auth_session_revoked", action_types)

    def test_user_can_revoke_current_session_from_session_management(self) -> None:
        register_payload = {
            "email": "owner@example.com",
            "full_name": "Owner User",
            "password": "super-secret-123",
        }
        register_response = self.client.post("/api/v1/auth/register", json=register_payload)
        self.assertEqual(register_response.status_code, 201)

        login_response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "owner@example.com", "password": "super-secret-123"},
        )
        self.assertEqual(login_response.status_code, 200)

        sessions_response = self.client.get("/api/v1/auth/sessions")
        self.assertEqual(sessions_response.status_code, 200, sessions_response.text)
        self.assertEqual(len(sessions_response.json()), 1)
        current_session_id = sessions_response.json()[0]["id"]

        revoke_current = self.client.post(
            f"/api/v1/auth/sessions/{current_session_id}/revoke"
        )
        self.assertEqual(revoke_current.status_code, 200, revoke_current.text)
        self.assertFalse(revoke_current.json()["is_active"])

        me_after_revoke = self.client.get("/api/v1/auth/me")
        self.assertEqual(me_after_revoke.status_code, 401, me_after_revoke.text)

    def test_repeated_invalid_login_attempts_trigger_temporary_lockout(self) -> None:
        with Session(self.engine) as session:
            user = User(
                email="locked@example.com",
                full_name="Locked User",
                password_hash=hash_password("super-secret-123"),
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        for _ in range(4):
            denied = self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": "locked@example.com",
                    "password": "wrong-password-123",
                },
            )
            self.assertEqual(denied.status_code, 401, denied.text)

        locked = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "locked@example.com",
                "password": "wrong-password-123",
            },
        )
        self.assertEqual(locked.status_code, 429, locked.text)

        blocked_valid_login = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "locked@example.com",
                "password": "super-secret-123",
            },
        )
        self.assertEqual(blocked_valid_login.status_code, 429, blocked_valid_login.text)

        with Session(self.engine) as session:
            user = session.get(User, user_id)
            self.assertIsNotNone(user)
            self.assertEqual(user.failed_login_attempt_count, 5)
            self.assertIsNotNone(user.login_locked_until)
            user.login_locked_until = utcnow()
            session.add(user)
            session.commit()

        unlocked_login = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "locked@example.com",
                "password": "super-secret-123",
            },
        )
        self.assertEqual(unlocked_login.status_code, 200, unlocked_login.text)
        self.assertIsNotNone(unlocked_login.json()["last_login_at"])

        with Session(self.engine) as session:
            user = session.get(User, uuid.UUID(str(user_id)))
            self.assertIsNotNone(user)
            self.assertEqual(user.failed_login_attempt_count, 0)
            self.assertIsNone(user.login_locked_until)
            self.assertIsNotNone(user.last_login_at)

        security_events = self.client.get("/api/v1/auth/security-events")
        self.assertEqual(security_events.status_code, 200, security_events.text)
        action_types = [entry["action_type"] for entry in security_events.json()]
        self.assertIn("auth_login_denied", action_types)
        self.assertIn("auth_session_created", action_types)

    def test_admin_can_add_and_remove_independent_workspace_roles(self) -> None:
        with Session(self.engine) as session:
            admin = User(
                email="admin@example.com",
                full_name="Admin User",
                password_hash=hash_password("admin-password-123"),
                system_role=SystemRole.ADMIN,
            )
            admin.set_workspace_roles((AccountWorkspaceRole.INTERNAL,))
            user = User(
                email="role-user@example.com",
                full_name="Role User",
                password_hash=hash_password("user-password-123"),
            )
            user.set_workspace_roles((AccountWorkspaceRole.TENANT,))
            session.add(admin)
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        login_response = self.client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@example.com",
                "password": "admin-password-123",
            },
        )
        self.assertEqual(login_response.status_code, 200, login_response.text)

        users_response = self.client.get("/api/v1/internal/users?query=role-user")
        self.assertEqual(users_response.status_code, 200, users_response.text)
        self.assertEqual(len(users_response.json()), 1)
        self.assertEqual(users_response.json()[0]["workspace_roles"], ["tenant"])

        update_response = self.client.patch(
            f"/api/v1/internal/users/{user_id}/workspace-roles",
            json={"workspace_roles": ["landlord", "agency"]},
        )
        self.assertEqual(update_response.status_code, 200, update_response.text)
        self.assertEqual(update_response.json()["workspace_roles"], ["landlord", "agency"])
        self.assertEqual(update_response.json()["system_role"], "user")

        with Session(self.engine) as session:
            updated_user = session.get(User, user_id)
            self.assertIsNotNone(updated_user)
            self.assertEqual(
                updated_user.workspace_roles,
                [AccountWorkspaceRole.LANDLORD, AccountWorkspaceRole.AGENCY],
            )


if __name__ == "__main__":
    unittest.main()
