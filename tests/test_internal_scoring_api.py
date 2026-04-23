from __future__ import annotations

from pathlib import Path
import sys
import unittest

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
from app.models import (  # noqa: E402
    TrustScoreHistory,
    TrustScoreRecalculationBatch,
    TrustScoreRecalculationRequest,
    User,
)
from trustledger_domain import SystemRole  # noqa: E402


class InternalScoringApiTests(unittest.TestCase):
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

    def build_verified_tenancy(
        self,
        *,
        tenant: User,
        landlord: User,
        reviewer_email: str,
        reviewer_password: str,
    ) -> None:
        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        reviewer_client = self.new_client()
        self.login(reviewer_client, email=reviewer_email, password=reviewer_password)

        create_tenancy = tenant_client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Scoring Flat",
                "address_line1": "18 Score Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 90000,
                "deposit_minor": 180000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(create_tenancy.status_code, 201, create_tenancy.text)
        tenancy_id = create_tenancy.json()["id"]

        confirm = landlord_client.post(f"/api/v1/tenancies/{tenancy_id}/confirm")
        self.assertEqual(confirm.status_code, 200, confirm.text)

        request_review = tenant_client.post(f"/api/v1/tenancies/{tenancy_id}/request-review")
        self.assertEqual(request_review.status_code, 200, request_review.text)

        verify = reviewer_client.post(
            f"/api/v1/internal/review-queue/tenancies/{tenancy_id}/decision",
            json={
                "verification_status": "verified",
                "review_notes": "Verified for internal scoring route tests.",
            },
        )
        self.assertEqual(verify.status_code, 200, verify.text)

    def test_reviewer_can_recalculate_user_scores_and_read_history(self) -> None:
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
        )
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

        self.build_verified_tenancy(
            tenant=tenant,
            landlord=landlord,
            reviewer_email="reviewer@example.com",
            reviewer_password="reviewer-password-123",
        )

        reviewer_client = self.new_client()
        self.login(reviewer_client, email="reviewer@example.com", password="reviewer-password-123")
        recalc = reviewer_client.post(f"/api/v1/internal/scoring/users/{tenant.id}/recalculate")
        self.assertEqual(recalc.status_code, 200, recalc.text)
        self.assertEqual(recalc.json()["tenant_score"], 575)
        self.assertEqual(recalc.json()["landlord_score"], 500)
        self.assertEqual(recalc.json()["verification_strength"], 18)
        self.assertEqual(recalc.json()["inputs"]["tenant_verified_tenancies"], 1)

        second_recalc = reviewer_client.post(f"/api/v1/internal/scoring/users/{tenant.id}/recalculate")
        self.assertEqual(second_recalc.status_code, 200, second_recalc.text)
        self.assertEqual(second_recalc.json()["tenant_score"], 575)

        history = reviewer_client.get(f"/api/v1/internal/scoring/users/{tenant.id}/history")
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(len(history.json()), 1)
        self.assertEqual(history.json()[0]["calculation_reason"], "internal_recalculation")

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        denied = outsider_client.post(f"/api/v1/internal/scoring/users/{tenant.id}/recalculate")
        self.assertEqual(denied.status_code, 403)

    def test_reviewer_can_queue_and_process_single_score_recalculation_request(self) -> None:
        tenant = self.seed_user(
            email="queued-tenant@example.com",
            full_name="Queued Tenant",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="queued-landlord@example.com",
            full_name="Queued Landlord",
            password="landlord-password-123",
        )
        reviewer = self.seed_user(
            email="queued-reviewer@example.com",
            full_name="Queued Reviewer",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )

        self.build_verified_tenancy(
            tenant=tenant,
            landlord=landlord,
            reviewer_email="queued-reviewer@example.com",
            reviewer_password="reviewer-password-123",
        )

        reviewer_client = self.new_client()
        self.login(
            reviewer_client,
            email="queued-reviewer@example.com",
            password="reviewer-password-123",
        )

        create_request = reviewer_client.post(
            f"/api/v1/internal/scoring/users/{tenant.id}/requests"
        )
        self.assertEqual(create_request.status_code, 201, create_request.text)
        request_payload = create_request.json()
        self.assertEqual(request_payload["status"], "pending")
        self.assertEqual(request_payload["calculation_reason"], "internal_recalculation")
        self.assertEqual(request_payload["attempt_count"], 0)
        self.assertIsNone(request_payload["processed_by_user_id"])
        self.assertIsNone(request_payload["result_tenant_score"])

        get_request = reviewer_client.get(
            f"/api/v1/internal/scoring/requests/{request_payload['id']}"
        )
        self.assertEqual(get_request.status_code, 200, get_request.text)
        self.assertEqual(get_request.json()["status"], "pending")

        process_request = reviewer_client.post(
            f"/api/v1/internal/scoring/requests/{request_payload['id']}/process"
        )
        self.assertEqual(process_request.status_code, 200, process_request.text)
        processed_payload = process_request.json()
        self.assertEqual(processed_payload["status"], "completed")
        self.assertEqual(processed_payload["attempt_count"], 1)
        self.assertEqual(processed_payload["processed_by_user_id"], str(reviewer.id))
        self.assertEqual(processed_payload["result_tenant_score"], 575)
        self.assertEqual(processed_payload["result_landlord_score"], 500)
        self.assertEqual(processed_payload["result_verification_strength"], 18)
        self.assertEqual(processed_payload["result_scoring_version"], "v1")

        process_again = reviewer_client.post(
            f"/api/v1/internal/scoring/requests/{request_payload['id']}/process"
        )
        self.assertEqual(process_again.status_code, 200, process_again.text)
        self.assertEqual(process_again.json()["status"], "completed")

        history = reviewer_client.get(f"/api/v1/internal/scoring/users/{tenant.id}/history")
        self.assertEqual(history.status_code, 200, history.text)
        self.assertEqual(len(history.json()), 1)
        self.assertEqual(history.json()[0]["calculation_reason"], "internal_recalculation")

        with Session(self.engine) as session:
            requests = session.exec(select(TrustScoreRecalculationRequest)).all()
            history_entries = session.exec(select(TrustScoreHistory)).all()
            self.assertEqual(len(requests), 1)
            self.assertEqual(requests[0].status.value, "completed")
            self.assertEqual(requests[0].attempt_count, 1)
            self.assertEqual(requests[0].processed_by_user_id, reviewer.id)
            self.assertEqual(len(history_entries), 1)

    def test_reviewer_can_queue_and_list_score_requests_by_email(self) -> None:
        tenant = self.seed_user(
            email="email-score-tenant@example.com",
            full_name="Email Score Tenant",
            password="tenant-password-123",
        )
        self.seed_user(
            email="email-score-reviewer@example.com",
            full_name="Email Score Reviewer",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )

        reviewer_client = self.new_client()
        self.login(
            reviewer_client,
            email="email-score-reviewer@example.com",
            password="reviewer-password-123",
        )

        create_request = reviewer_client.post(
            "/api/v1/internal/scoring/requests",
            json={"user_email": "email-score-tenant@example.com"},
        )
        self.assertEqual(create_request.status_code, 201, create_request.text)
        self.assertEqual(create_request.json()["user_id"], str(tenant.id))
        self.assertEqual(create_request.json()["status"], "pending")

        request_list = reviewer_client.get(
            "/api/v1/internal/scoring/requests",
            params={"status_filter": "pending", "limit": 10},
        )
        self.assertEqual(request_list.status_code, 200, request_list.text)
        self.assertEqual(len(request_list.json()), 1)
        self.assertEqual(request_list.json()[0]["id"], create_request.json()["id"])

    def test_reviewer_can_create_and_finish_organization_score_recalculation_batch(self) -> None:
        self.seed_user(
            email="batch-reviewer@example.com",
            full_name="Batch Reviewer",
            password="reviewer-password-123",
            system_role=SystemRole.REVIEWER,
        )
        owner = self.seed_user(
            email="agency-owner@example.com",
            full_name="Agency Owner",
            password="owner-password-123",
        )
        member = self.seed_user(
            email="agency-member@example.com",
            full_name="Agency Member",
            password="member-password-123",
        )

        owner_client = self.new_client()
        self.login(owner_client, email=owner.email, password="owner-password-123")
        agency = self.create_agency(owner_client, name="Batch Realty")

        add_member = owner_client.post(
            f"/api/v1/organizations/{agency['id']}/memberships",
            json={
                "user_id": str(member.id),
                "role": "member",
            },
        )
        self.assertEqual(add_member.status_code, 201, add_member.text)

        reviewer_client = self.new_client()
        self.login(
            reviewer_client,
            email="batch-reviewer@example.com",
            password="reviewer-password-123",
        )

        create_batch = reviewer_client.post(
            "/api/v1/internal/scoring/batches",
            json={
                "scope_type": "organization_members",
                "organization_id": agency["id"],
            },
        )
        self.assertEqual(create_batch.status_code, 201, create_batch.text)
        batch_payload = create_batch.json()
        self.assertEqual(batch_payload["status"], "pending")
        self.assertEqual(batch_payload["calculation_reason"], "organization_batch_refresh")
        self.assertEqual(batch_payload["requested_user_count"], 2)
        self.assertEqual(batch_payload["pending_request_count"], 2)
        self.assertEqual(batch_payload["completed_request_count"], 0)
        self.assertEqual(len(batch_payload["request_ids"]), 2)

        get_batch = reviewer_client.get(f"/api/v1/internal/scoring/batches/{batch_payload['id']}")
        self.assertEqual(get_batch.status_code, 200, get_batch.text)
        self.assertEqual(get_batch.json()["pending_request_count"], 2)

        first_request_id = batch_payload["request_ids"][0]
        process_first = reviewer_client.post(
            f"/api/v1/internal/scoring/requests/{first_request_id}/process"
        )
        self.assertEqual(process_first.status_code, 200, process_first.text)
        self.assertEqual(process_first.json()["status"], "completed")

        first_batch_refresh = reviewer_client.get(
            f"/api/v1/internal/scoring/batches/{batch_payload['id']}"
        )
        self.assertEqual(first_batch_refresh.status_code, 200, first_batch_refresh.text)
        self.assertEqual(first_batch_refresh.json()["status"], "pending")
        self.assertEqual(first_batch_refresh.json()["pending_request_count"], 1)
        self.assertEqual(first_batch_refresh.json()["completed_request_count"], 1)

        second_request_id = batch_payload["request_ids"][1]
        process_second = reviewer_client.post(
            f"/api/v1/internal/scoring/requests/{second_request_id}/process"
        )
        self.assertEqual(process_second.status_code, 200, process_second.text)
        self.assertEqual(process_second.json()["status"], "completed")

        completed_batch = reviewer_client.get(
            f"/api/v1/internal/scoring/batches/{batch_payload['id']}"
        )
        self.assertEqual(completed_batch.status_code, 200, completed_batch.text)
        self.assertEqual(completed_batch.json()["status"], "completed")
        self.assertEqual(completed_batch.json()["pending_request_count"], 0)
        self.assertEqual(completed_batch.json()["completed_request_count"], 2)

        with Session(self.engine) as session:
            batches = session.exec(select(TrustScoreRecalculationBatch)).all()
            requests = session.exec(
                select(TrustScoreRecalculationRequest).order_by(
                    TrustScoreRecalculationRequest.created_at.asc()
                )
            ).all()
            self.assertEqual(len(batches), 1)
            self.assertEqual(batches[0].status.value, "completed")
            self.assertEqual(len(requests), 2)
            self.assertTrue(all(request.status.value == "completed" for request in requests))


if __name__ == "__main__":
    unittest.main()
