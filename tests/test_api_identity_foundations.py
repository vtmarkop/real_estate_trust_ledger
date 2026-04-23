from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import sys
import tempfile
import unittest

from pydantic import ValidationError
from sqlmodel import SQLModel, Session, select


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"

for path in (API_ROOT, DOMAIN_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.core.config import DEV_SECRET_KEY, Settings  # noqa: E402
from app.core.db import create_engine_from_url  # noqa: E402
from app.core.security import generate_session_token, hash_password, hash_token, verify_password  # noqa: E402
from app.models import AuthSession, Organization, OrganizationMembership, TrustReportConsent, User  # noqa: E402
from app.models.common import utcnow  # noqa: E402
from trustledger_domain import ConsentScope, OrganizationMembershipRole, OrganizationType, SystemRole  # noqa: E402


class ApiIdentityFoundationTests(unittest.TestCase):
    def test_settings_parse_origins_and_enforce_production_security(self) -> None:
        settings = Settings(allowed_origins="http://localhost:3000,http://localhost:5173")
        self.assertEqual(
            settings.allowed_origins,
            ["http://localhost:3000", "http://localhost:5173"],
        )
        self.assertTrue(str(settings.model_config.get("env_file")).endswith("apps\\api\\.env"))
        self.assertIn("trust_ledger.db", settings.database_url)
        self.assertTrue(settings.artifact_storage_root.endswith("private_artifacts"))
        self.assertEqual(settings.resolved_worker_coordination_backend, "none")

        redis_settings = Settings(
            redis_url="redis://127.0.0.1:6379/0",
            worker_coordination_backend="auto",
        )
        self.assertEqual(redis_settings.resolved_worker_coordination_backend, "redis")

        with self.assertRaises(ValidationError):
            Settings(
                app_env="production",
                secret_key=DEV_SECRET_KEY,
                cookie_secure=True,
            )

        with self.assertRaises(ValidationError):
            Settings(
                app_env="production",
                secret_key="x" * 64,
                cookie_secure=False,
            )

        with self.assertRaises(ValidationError):
            Settings(
                worker_coordination_backend="redis",
                redis_url=None,
            )

        with self.assertRaises(ValidationError):
            Settings(
                app_env="production",
                secret_key="x" * 64,
                cookie_secure=True,
                public_api_base_url="http://api.example.com",
            )

    def test_settings_parse_list_fields_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "TRUST_LEDGER_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173",
                        (
                            "TRUST_LEDGER_ARTIFACT_ALLOWED_CONTENT_TYPES="
                            "application/pdf,image/jpeg,image/png"
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            settings = Settings(_env_file=env_path)

        self.assertEqual(
            settings.allowed_origins,
            ["http://localhost:3000", "http://localhost:5173"],
        )
        self.assertEqual(
            settings.artifact_allowed_content_types,
            ["application/pdf", "image/jpeg", "image/png"],
        )

    def test_password_and_session_token_helpers(self) -> None:
        password_hash = hash_password("correct horse battery staple")
        self.assertTrue(verify_password("correct horse battery staple", password_hash))
        self.assertFalse(verify_password("wrong password", password_hash))

        session_token = generate_session_token()
        self.assertGreaterEqual(len(session_token), 20)
        self.assertEqual(hash_token(session_token), hash_token(session_token))

    def test_membership_role_capabilities(self) -> None:
        owner_role = OrganizationMembershipRole.OWNER
        agent_role = OrganizationMembershipRole.AGENT
        reviewer_role = OrganizationMembershipRole.REVIEWER

        self.assertTrue(owner_role.can_manage_members)
        self.assertTrue(owner_role.can_run_trust_checks)
        self.assertTrue(agent_role.can_run_trust_checks)
        self.assertFalse(agent_role.can_manage_members)
        self.assertTrue(reviewer_role.can_review_verifications)
        self.assertFalse(reviewer_role.can_run_trust_checks)

    def test_identity_models_work_together_in_memory(self) -> None:
        engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(engine)

        now = utcnow()

        with Session(engine) as session:
            user = User(
                email="owner@agency.test",
                full_name="Agency Owner",
                password_hash=hash_password("super-secret"),
                system_role=SystemRole.ADMIN,
            )
            organization = Organization(
                name="Acme Realty",
                slug="acme-realty",
                organization_type=OrganizationType.AGENCY,
            )
            session.add(user)
            session.add(organization)
            session.commit()
            session.refresh(user)
            session.refresh(organization)

            membership = OrganizationMembership(
                user_id=user.id,
                organization_id=organization.id,
                role=OrganizationMembershipRole.OWNER,
            )
            auth_session = AuthSession(
                user_id=user.id,
                token_hash=hash_token(generate_session_token()),
                expires_at=now + timedelta(days=30),
            )
            consent = TrustReportConsent(
                subject_user_id=user.id,
                granted_by_user_id=user.id,
                grantee_organization_id=organization.id,
                scope=ConsentScope.TRUST_REPORT_READ,
                share_token_hash=hash_token(generate_session_token()),
                access_code_hash=hash_password("123456"),
                expires_at=now + timedelta(days=7),
            )

            session.add(membership)
            session.add(auth_session)
            session.add(consent)
            session.commit()

            memberships = session.exec(select(OrganizationMembership)).all()
            sessions = session.exec(select(AuthSession)).all()
            consents = session.exec(select(TrustReportConsent)).all()

        self.assertEqual(len(memberships), 1)
        self.assertTrue(memberships[0].can_manage_members)
        self.assertEqual(len(sessions), 1)
        self.assertTrue(sessions[0].is_active(now=now))
        self.assertEqual(len(consents), 1)
        self.assertTrue(consents[0].is_active(now=now))


if __name__ == "__main__":
    unittest.main()
