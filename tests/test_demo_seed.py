from __future__ import annotations

from pathlib import Path
import sys
import unittest

from sqlmodel import SQLModel, Session, select


ROOT = Path(__file__).resolve().parents[1]
API_ROOT = ROOT / "apps" / "api"
DOMAIN_ROOT = ROOT / "packages" / "domain"

for path in (API_ROOT, DOMAIN_ROOT):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


from app.core.db import create_engine_from_url  # noqa: E402
from app.devtools.demo_seed import (  # noqa: E402
    DEMO_ACCESS_CODE,
    DEMO_ACCOUNTS,
    DEMO_ADMIN,
    DEMO_AGENCY_OWNER,
    DEMO_LANDLORD,
    DEMO_REVIEWER,
    DEMO_SHARE_TOKEN,
    DEMO_TENANT,
    seed_demo_environment,
)
from app.models import (  # noqa: E402
    AgencyTrustCheck,
    AutomationTask,
    DepositRecord,
    EvidenceDocument,
    HistoryImport,
    Listing,
    ListingApplication,
    MaintenanceTicket,
    Organization,
    PaymentRecord,
    Property,
    StoredArtifact,
    Tenancy,
    TrustEvent,
    TrustReportConsent,
    TrustScoreSnapshot,
    User,
)
from app.core.security import hash_password  # noqa: E402
from trustledger_domain import (  # noqa: E402
    DepositStatus,
    MaintenanceTicketStatus,
    PaymentRecordStatus,
    SystemRole,
)


class DemoSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_demo_seed_is_idempotent_and_creates_live_dataset(self) -> None:
        with Session(self.engine) as session:
            summary = seed_demo_environment(session=session)

        self.assertEqual(summary.accounts, DEMO_ACCOUNTS)
        self.assertEqual(summary.share_token, DEMO_SHARE_TOKEN)
        self.assertEqual(summary.access_code, DEMO_ACCESS_CODE)
        self.assertGreater(summary.tenant_score, 500)
        self.assertGreater(summary.landlord_score, 500)
        self.assertGreater(summary.verification_strength, 0)

        with Session(self.engine) as session:
            self.assertEqual(len(session.exec(select(User)).all()), 5)
            self.assertEqual(len(session.exec(select(Organization)).all()), 2)
            self.assertEqual(len(session.exec(select(Property)).all()), 4)
            self.assertEqual(len(session.exec(select(Tenancy)).all()), 4)
            self.assertEqual(len(session.exec(select(HistoryImport)).all()), 1)
            self.assertEqual(len(session.exec(select(StoredArtifact)).all()), 21)
            self.assertEqual(len(session.exec(select(EvidenceDocument)).all()), 8)
            self.assertEqual(len(session.exec(select(PaymentRecord)).all()), 3)
            self.assertEqual(len(session.exec(select(DepositRecord)).all()), 3)
            self.assertEqual(len(session.exec(select(MaintenanceTicket)).all()), 3)
            self.assertEqual(len(session.exec(select(Listing)).all()), 1)
            self.assertEqual(len(session.exec(select(ListingApplication)).all()), 1)
            self.assertEqual(len(session.exec(select(TrustReportConsent)).all()), 1)
            self.assertEqual(len(session.exec(select(AgencyTrustCheck)).all()), 1)
            self.assertEqual(len(session.exec(select(AutomationTask)).all()), 1)

            payment_statuses = {record.payment_status for record in session.exec(select(PaymentRecord)).all()}
            self.assertEqual(
                payment_statuses,
                {
                    PaymentRecordStatus.CONFIRMED,
                    PaymentRecordStatus.UNDER_REVIEW,
                    PaymentRecordStatus.VERDICT_ISSUED,
                },
            )
            deposit_statuses = {record.deposit_status for record in session.exec(select(DepositRecord)).all()}
            self.assertEqual(
                deposit_statuses,
                {
                    DepositStatus.HELD,
                    DepositStatus.UNDER_REVIEW,
                    DepositStatus.VERDICT_ISSUED,
                },
            )
            maintenance_statuses = {
                record.ticket_status for record in session.exec(select(MaintenanceTicket)).all()
            }
            self.assertEqual(
                maintenance_statuses,
                {
                    MaintenanceTicketStatus.RESOLVED,
                    MaintenanceTicketStatus.UNDER_REVIEW,
                    MaintenanceTicketStatus.VERDICT_ISSUED,
                },
            )
            tagged_assigned_properties = [
                property_record
                for property_record in session.exec(select(Property)).all()
                if property_record.assigned_agency_organization_id is not None
                and property_record.assigned_tenant_user_id is not None
                and property_record.custom_tags_json != "[]"
            ]
            self.assertGreaterEqual(len(tagged_assigned_properties), 3)
            uploaded_evidence = [
                evidence for evidence in session.exec(select(EvidenceDocument)).all()
                if evidence.stored_artifact_id is not None
            ]
            self.assertEqual(len(uploaded_evidence), 8)

    def test_demo_seed_migrates_legacy_local_demo_emails(self) -> None:
        legacy_accounts = (
            (DEMO_ADMIN, SystemRole.ADMIN),
            (DEMO_REVIEWER, SystemRole.REVIEWER),
            (DEMO_AGENCY_OWNER, SystemRole.USER),
            (DEMO_TENANT, SystemRole.USER),
            (DEMO_LANDLORD, SystemRole.USER),
        )

        with Session(self.engine) as session:
            for demo_account, system_role in legacy_accounts:
                session.add(
                    User(
                        email=demo_account.legacy_emails[0],
                        full_name=demo_account.label,
                        password_hash=hash_password(demo_account.password),
                        system_role=system_role,
                        is_active=True,
                        email_verified=True,
                    )
                )
            session.commit()

        with Session(self.engine) as session:
            seed_demo_environment(session=session)

        with Session(self.engine) as session:
            users = session.exec(select(User)).all()
            emails = sorted(user.email for user in users)
            snapshot_count = len(session.exec(select(TrustScoreSnapshot)).all())
            trust_event_count = len(session.exec(select(TrustEvent)).all())
            application = session.exec(select(ListingApplication)).first()
            listing = session.exec(select(Listing)).first()

        self.assertEqual(len(users), 5)
        for demo_account, _system_role in legacy_accounts:
            self.assertIn(demo_account.email, emails)
            self.assertNotIn(demo_account.legacy_emails[0], emails)
        self.assertEqual(snapshot_count, 5)
        self.assertGreater(trust_event_count, 40)
        self.assertIsNotNone(application)
        self.assertIsNotNone(listing)
        self.assertEqual(application.application_status.value, "accepted")
        self.assertEqual(listing.listing_status.value, "open")

        with Session(self.engine) as session:
            seed_demo_environment(session=session)

        with Session(self.engine) as session:
            self.assertEqual(len(session.exec(select(User)).all()), 5)
            self.assertEqual(len(session.exec(select(Organization)).all()), 2)
            self.assertEqual(len(session.exec(select(Property)).all()), 4)
            self.assertEqual(len(session.exec(select(Tenancy)).all()), 4)
            self.assertEqual(len(session.exec(select(HistoryImport)).all()), 1)
            self.assertEqual(len(session.exec(select(StoredArtifact)).all()), 21)
            self.assertEqual(len(session.exec(select(EvidenceDocument)).all()), 8)
            self.assertEqual(len(session.exec(select(PaymentRecord)).all()), 3)
            self.assertEqual(len(session.exec(select(DepositRecord)).all()), 3)
            self.assertEqual(len(session.exec(select(MaintenanceTicket)).all()), 3)
            self.assertEqual(len(session.exec(select(Listing)).all()), 1)
            self.assertEqual(len(session.exec(select(ListingApplication)).all()), 1)
            self.assertEqual(len(session.exec(select(TrustReportConsent)).all()), 1)
            self.assertEqual(len(session.exec(select(AgencyTrustCheck)).all()), 1)
            self.assertEqual(len(session.exec(select(AutomationTask)).all()), 1)


if __name__ == "__main__":
    unittest.main()
