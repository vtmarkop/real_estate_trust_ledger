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
from app.models import AgencyTrustCheck, TrustReportConsent, User  # noqa: E402
from app.models.common import utcnow  # noqa: E402
from trustledger_domain import OrganizationMembershipRole, SystemRole  # noqa: E402


class ConsentTrustChecksApiTests(unittest.TestCase):
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

    def add_membership(
        self,
        client: TestClient,
        *,
        organization_id: str,
        user_id: str,
        role: OrganizationMembershipRole,
    ) -> None:
        response = client.post(
            f"/api/v1/organizations/{organization_id}/memberships",
            json={"user_id": user_id, "role": role.value},
        )
        self.assertEqual(response.status_code, 201, response.text)

    def test_user_can_issue_consent_and_agency_can_run_trust_check(self) -> None:
        subject = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
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
        consent_body = create_consent.json()
        self.assertEqual(consent_body["subject_user_id"], str(subject.id))
        self.assertTrue(consent_body["is_active"])
        self.assertTrue(consent_body["share_token"])

        listed_consents = subject_client.get("/api/v1/consents/trust-report")
        self.assertEqual(listed_consents.status_code, 200)
        self.assertEqual(len(listed_consents.json()), 1)

        validate_response = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(validate_response.status_code, 200, validate_response.text)
        self.assertEqual(validate_response.json()["subject_full_name"], "Tenant Subject")

        profile_preview = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/profile",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(profile_preview.status_code, 200, profile_preview.text)
        self.assertEqual(profile_preview.json()["profile_stage"], "reference_flow_foundation")
        self.assertEqual(profile_preview.json()["reported_tenancies"], 0)
        self.assertEqual(profile_preview.json()["verified_tenancies"], 0)
        self.assertEqual(profile_preview.json()["submitted_evidence_documents"], 0)
        self.assertEqual(profile_preview.json()["accepted_evidence_documents"], 0)
        self.assertEqual(profile_preview.json()["rejected_evidence_documents"], 0)
        self.assertEqual(profile_preview.json()["submitted_history_imports"], 0)
        self.assertEqual(profile_preview.json()["accepted_history_imports"], 0)
        self.assertEqual(profile_preview.json()["rejected_history_imports"], 0)
        self.assertEqual(profile_preview.json()["counterparty_reference_documents"], 0)
        self.assertEqual(profile_preview.json()["accepted_counterparty_reference_documents"], 0)
        self.assertEqual(profile_preview.json()["tenant_score"], 500)
        self.assertEqual(profile_preview.json()["landlord_score"], 500)
        self.assertEqual(profile_preview.json()["verification_strength"], 0)
        self.assertEqual(profile_preview.json()["scoring_version"], "v1")
        self.assertIsNotNone(profile_preview.json()["score_calculated_at"])
        self.assertEqual(profile_preview.json()["active_share_consents"], 1)
        self.assertEqual(profile_preview.json()["organization_trust_checks"], 0)

        create_trust_check = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(create_trust_check.status_code, 201, create_trust_check.text)
        self.assertEqual(create_trust_check.json()["subject_user_id"], str(subject.id))
        self.assertEqual(
            create_trust_check.json()["profile"]["profile_stage"],
            "reference_flow_foundation",
        )
        self.assertEqual(create_trust_check.json()["profile"]["tenant_score"], 500)
        self.assertEqual(create_trust_check.json()["profile"]["landlord_score"], 500)
        self.assertEqual(create_trust_check.json()["profile"]["verification_strength"], 0)
        self.assertEqual(create_trust_check.json()["profile"]["organization_trust_checks"], 1)
        self.assertEqual(create_trust_check.json()["profile"]["total_agency_trust_checks"], 1)

        list_trust_checks = owner_client.get(
            f"/api/v1/organizations/{agency['id']}/trust-checks"
        )
        self.assertEqual(list_trust_checks.status_code, 200)
        self.assertEqual(len(list_trust_checks.json()), 1)

        with Session(self.engine) as session:
            trust_checks = session.exec(select(AgencyTrustCheck)).all()
            self.assertEqual(len(trust_checks), 1)
            self.assertEqual(trust_checks[0].subject_user_id, subject.id)

    def test_revoked_consent_cannot_be_used_for_trust_check(self) -> None:
        self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
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
                "expires_in_days": 7,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_body = create_consent.json()

        revoke_response = subject_client.post(
            f"/api/v1/consents/trust-report/{consent_body['id']}/revoke"
        )
        self.assertEqual(revoke_response.status_code, 200, revoke_response.text)
        self.assertFalse(revoke_response.json()["is_active"])
        self.assertIsNotNone(revoke_response.json()["revoked_at"])

        validate_response = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(validate_response.status_code, 409)

    def test_member_without_trust_check_permission_is_denied(self) -> None:
        member = self.seed_user(
            email="member@agency.example",
            full_name="Agency Member",
            password="member-password-123",
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
        )
        self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)
        self.add_membership(
            owner_client,
            organization_id=agency["id"],
            user_id=str(member.id),
            role=OrganizationMembershipRole.MEMBER,
        )

        subject_client = self.new_client()
        self.login(subject_client, email="tenant@example.com", password="tenant-password-123")
        create_consent = subject_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 7,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_body = create_consent.json()

        member_client = self.new_client()
        self.login(member_client, email="member@agency.example", password="member-password-123")
        validate_response = member_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(validate_response.status_code, 403)

    def test_deactivated_agent_loses_trust_check_access(self) -> None:
        agent = self.seed_user(
            email="agent@agency.example",
            full_name="Agency Agent",
            password="agent-password-123",
        )
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
        )
        self.seed_user(
            email="tenant@example.com",
            full_name="Tenant Subject",
            password="tenant-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email="owner@agency.example", password="owner-password-123")
        agency = self.create_agency(owner_client)
        add_agent = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/memberships",
            json={"user_id": str(agent.id), "role": "agent"},
        )
        self.assertEqual(add_agent.status_code, 201, add_agent.text)
        membership_id = add_agent.json()["id"]

        subject_client = self.new_client()
        self.login(subject_client, email="tenant@example.com", password="tenant-password-123")
        create_consent = subject_client.post(
            "/api/v1/consents/trust-report",
            json={
                "grantee_organization_id": agency["id"],
                "access_code": "4829",
                "expires_in_days": 7,
            },
        )
        self.assertEqual(create_consent.status_code, 201, create_consent.text)
        consent_body = create_consent.json()

        agent_client = self.new_client()
        self.login(agent_client, email="agent@agency.example", password="agent-password-123")
        allowed_before_deactivation = agent_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(allowed_before_deactivation.status_code, 200, allowed_before_deactivation.text)

        deactivate_agent = owner_client.patch(
            f"/api/v1/organizations/{agency['id']}/memberships/{membership_id}",
            json={"is_active": False},
        )
        self.assertEqual(deactivate_agent.status_code, 200, deactivate_agent.text)
        self.assertFalse(deactivate_agent.json()["is_active"])

        denied_after_deactivation = agent_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(denied_after_deactivation.status_code, 403)

    def test_subject_can_read_trust_report_access_history(self) -> None:
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
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
        consent_body = create_consent.json()

        validate_response = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(validate_response.status_code, 200, validate_response.text)

        profile_preview = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/profile",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(profile_preview.status_code, 200, profile_preview.text)

        create_trust_check = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(create_trust_check.status_code, 201, create_trust_check.text)

        access_history = subject_client.get(
            "/api/v1/consents/trust-report/access-history",
            params={"organization_id": agency["id"], "limit": 10},
        )
        self.assertEqual(access_history.status_code, 200, access_history.text)
        action_types = {entry["action_type"] for entry in access_history.json()}
        self.assertEqual(
            action_types,
            {
                "trust_check_validated",
                "trust_profile_previewed",
                "trust_check_created",
            },
        )
        self.assertTrue(all(entry["organization_id"] == agency["id"] for entry in access_history.json()))
        self.assertTrue(all(entry["subject_user_email"] == "tenant@example.com" for entry in access_history.json()))

    def test_repeated_invalid_access_code_attempts_trigger_temporary_lockout(self) -> None:
        self.seed_user(
            email="owner@agency.example",
            full_name="Agency Owner",
            password="owner-password-123",
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
        consent_body = create_consent.json()

        for _ in range(4):
            denied = owner_client.post(
                f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
                json={
                    "share_token": consent_body["share_token"],
                    "access_code": "9999",
                },
            )
            self.assertEqual(denied.status_code, 401, denied.text)

        locked = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "9999",
            },
        )
        self.assertEqual(locked.status_code, 429, locked.text)

        consents_after_lock = subject_client.get("/api/v1/consents/trust-report")
        self.assertEqual(consents_after_lock.status_code, 200, consents_after_lock.text)
        self.assertEqual(consents_after_lock.json()[0]["failed_access_attempt_count"], 5)
        self.assertIsNotNone(consents_after_lock.json()[0]["access_locked_until"])

        blocked_valid_attempt = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(blocked_valid_attempt.status_code, 429, blocked_valid_attempt.text)

        with Session(self.engine) as session:
            consent = session.get(TrustReportConsent, uuid.UUID(consent_body["id"]))
            self.assertIsNotNone(consent)
            consent.access_locked_until = utcnow()
            session.add(consent)
            session.commit()

        unlocked_valid_attempt = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/trust-checks/validate",
            json={
                "share_token": consent_body["share_token"],
                "access_code": "4829",
            },
        )
        self.assertEqual(unlocked_valid_attempt.status_code, 200, unlocked_valid_attempt.text)

        consents_after_success = subject_client.get("/api/v1/consents/trust-report")
        self.assertEqual(consents_after_success.status_code, 200, consents_after_success.text)
        self.assertEqual(consents_after_success.json()[0]["failed_access_attempt_count"], 0)
        self.assertIsNone(consents_after_success.json()[0]["access_locked_until"])
        self.assertIsNotNone(consents_after_success.json()[0]["last_validated_at"])


if __name__ == "__main__":
    unittest.main()
