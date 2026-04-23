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
from app.core.security import hash_password  # noqa: E402
from app.main import create_app  # noqa: E402
from app.models import User  # noqa: E402
from trustledger_domain import SystemRole  # noqa: E402


class EvidenceArtifactApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine_from_url("sqlite://")
        SQLModel.metadata.create_all(self.engine)
        self.tempdir = TemporaryDirectory()
        self.settings = Settings(
            app_env="development",
            database_url="sqlite://",
            artifact_storage_root=self.tempdir.name,
            artifact_signed_url_ttl_seconds=900,
            secret_key="development-secret-key-with-32-characters",
            cookie_secure=False,
        )

        app = create_app()

        def override_get_session():
            with Session(self.engine) as session:
                yield session

        app.dependency_overrides[get_session] = override_get_session
        app.dependency_overrides[get_runtime_settings] = lambda: self.settings
        self.app = app
        self.clients: list[TestClient] = []

    def tearDown(self) -> None:
        for client in self.clients:
            client.close()
        self.app.dependency_overrides.clear()
        self.tempdir.cleanup()

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

    def create_tenancy(self, client: TestClient, *, tenant_id: str, landlord_id: str) -> str:
        response = client.post(
            "/api/v1/tenancies",
            json={
                "property_label": "Artifact Flat",
                "address_line1": "12 Market Street",
                "city": "Athens",
                "country_code": "GR",
                "lease_start_date": "2026-01-01",
                "lease_end_date": "2026-12-31",
                "monthly_rent_minor": 95000,
                "deposit_minor": 190000,
                "currency_code": "EUR",
                "tenant_user_id": tenant_id,
                "landlord_user_id": landlord_id,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["id"]

    def test_participant_can_upload_private_artifact_and_download_via_signed_url(self) -> None:
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

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        tenancy_id = self.create_tenancy(
            tenant_client,
            tenant_id=str(tenant.id),
            landlord_id=str(landlord.id),
        )

        upload = tenant_client.post(
            f"/api/v1/evidence/tenancies/{tenancy_id}/artifacts",
            files={"artifact": ("receipt-april-2026.pdf", b"pdf-demo-artifact", "application/pdf")},
        )
        self.assertEqual(upload.status_code, 201, upload.text)
        stored_artifact = upload.json()
        self.assertEqual(stored_artifact["original_file_name"], "receipt-april-2026.pdf")
        self.assertEqual(stored_artifact["storage_backend"], "local_private")
        self.assertEqual(stored_artifact["content_type"], "application/pdf")
        self.assertEqual(stored_artifact["size_bytes"], len(b"pdf-demo-artifact"))

        submit_evidence = tenant_client.post(
            f"/api/v1/tenancies/{tenancy_id}/evidence",
            json={
                "subject_user_id": str(tenant.id),
                "document_type": "rent_receipt",
                "artifact_name": "ignored-client-name.pdf",
                "stored_artifact_id": stored_artifact["id"],
                "summary": "Uploaded April rent proof.",
                "document_date": "2026-04-05",
                "amount_minor": 95000,
                "currency_code": "EUR",
            },
        )
        self.assertEqual(submit_evidence.status_code, 201, submit_evidence.text)
        evidence = submit_evidence.json()
        self.assertTrue(evidence["has_uploaded_artifact"])
        self.assertEqual(evidence["stored_artifact_id"], stored_artifact["id"])
        self.assertEqual(evidence["artifact_name"], "receipt-april-2026.pdf")
        self.assertEqual(evidence["artifact_content_type"], "application/pdf")
        self.assertEqual(evidence["artifact_size_bytes"], len(b"pdf-demo-artifact"))

        artifact_access = tenant_client.post(
            f"/api/v1/evidence/{evidence['id']}/artifact-access"
        )
        self.assertEqual(artifact_access.status_code, 200, artifact_access.text)
        access_payload = artifact_access.json()
        self.assertEqual(access_payload["storage_backend"], "local_private")
        self.assertIn("/api/v1/evidence/artifacts/download", access_payload["download_url"])

        download = tenant_client.get(access_payload["download_url"])
        self.assertEqual(download.status_code, 200, download.text)
        self.assertEqual(download.content, b"pdf-demo-artifact")
        self.assertIn("application/pdf", download.headers.get("content-type", ""))

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        landlord_access = landlord_client.post(
            f"/api/v1/evidence/{evidence['id']}/artifact-access"
        )
        self.assertEqual(landlord_access.status_code, 200, landlord_access.text)

    def test_reference_fulfillment_can_attach_uploaded_artifact(self) -> None:
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

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        tenancy_id = self.create_tenancy(
            tenant_client,
            tenant_id=str(tenant.id),
            landlord_id=str(landlord.id),
        )

        create_request = tenant_client.post(
            f"/api/v1/reference-requests/tenancies/{tenancy_id}",
            json={
                "subject_user_id": str(tenant.id),
                "requested_from_user_id": str(landlord.id),
                "message": "Please confirm the payment history.",
            },
        )
        self.assertEqual(create_request.status_code, 201, create_request.text)
        reference_request = create_request.json()

        landlord_client = self.new_client()
        self.login(landlord_client, email="landlord@example.com", password="landlord-password-123")
        upload = landlord_client.post(
            f"/api/v1/evidence/tenancies/{tenancy_id}/artifacts",
            files={"artifact": ("reference-letter.pdf", b"reference-artifact", "application/pdf")},
        )
        self.assertEqual(upload.status_code, 201, upload.text)

        fulfill = landlord_client.post(
            f"/api/v1/reference-requests/{reference_request['id']}/fulfill",
            json={
                "artifact_name": "ignored-reference-name.pdf",
                "stored_artifact_id": upload.json()["id"],
                "summary": "Landlord reference attached with uploaded artifact.",
            },
        )
        self.assertEqual(fulfill.status_code, 200, fulfill.text)

        evidence_list = tenant_client.get(f"/api/v1/tenancies/{tenancy_id}/evidence")
        self.assertEqual(evidence_list.status_code, 200, evidence_list.text)
        reference_evidence = evidence_list.json()[0]
        self.assertEqual(reference_evidence["document_type"], "landlord_reference")
        self.assertTrue(reference_evidence["has_uploaded_artifact"])
        self.assertEqual(reference_evidence["artifact_name"], "reference-letter.pdf")

    def test_outsider_cannot_upload_or_access_private_artifact(self) -> None:
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
            email="outsider@example.com",
            full_name="Outside User",
            password="outsider-password-123",
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="tenant@example.com", password="tenant-password-123")
        tenancy_id = self.create_tenancy(
            tenant_client,
            tenant_id=str(tenant.id),
            landlord_id=str(landlord.id),
        )

        upload = tenant_client.post(
            f"/api/v1/evidence/tenancies/{tenancy_id}/artifacts",
            files={"artifact": ("receipt.pdf", b"private", "application/pdf")},
        )
        self.assertEqual(upload.status_code, 201, upload.text)

        evidence = tenant_client.post(
            f"/api/v1/tenancies/{tenancy_id}/evidence",
            json={
                "subject_user_id": str(tenant.id),
                "document_type": "rent_receipt",
                "artifact_name": "receipt.pdf",
                "stored_artifact_id": upload.json()["id"],
                "summary": "Private evidence.",
            },
        )
        self.assertEqual(evidence.status_code, 201, evidence.text)

        outsider_client = self.new_client()
        self.login(outsider_client, email="outsider@example.com", password="outsider-password-123")
        denied_upload = outsider_client.post(
            f"/api/v1/evidence/tenancies/{tenancy_id}/artifacts",
            files={"artifact": ("note.txt", b"blocked", "text/plain")},
        )
        self.assertEqual(denied_upload.status_code, 403)

        denied_access = outsider_client.post(
            f"/api/v1/evidence/{evidence.json()['id']}/artifact-access"
        )
        self.assertEqual(denied_access.status_code, 403)

    def test_s3_compatible_artifact_backend_returns_signed_redirect_download(self) -> None:
        class FakeS3Client:
            def __init__(self):
                self.put_calls = []

            def put_object(self, **kwargs):
                self.put_calls.append(kwargs)

            def generate_presigned_url(self, operation_name, Params, ExpiresIn):
                return (
                    "https://artifacts.example/download?"
                    + "bucket="
                    + Params["Bucket"]
                    + "&key="
                    + Params["Key"]
                )

        fake_s3_client = FakeS3Client()
        self.settings = Settings(
            app_env="development",
            database_url="sqlite://",
            artifact_storage_backend="s3_compatible",
            artifact_s3_bucket_name="trust-ledger-artifacts",
            artifact_s3_region="us-east-1",
            artifact_s3_endpoint_url="http://minio.local:9000",
            artifact_s3_access_key_id="minio",
            artifact_s3_secret_access_key="minio-secret",
            artifact_s3_use_ssl=False,
            secret_key="development-secret-key-with-32-characters",
            cookie_secure=False,
        )
        self.app.dependency_overrides[get_runtime_settings] = lambda: self.settings

        tenant = self.seed_user(
            email="s3-tenant@example.com",
            full_name="S3 Tenant",
            password="tenant-password-123",
        )
        landlord = self.seed_user(
            email="s3-landlord@example.com",
            full_name="S3 Landlord",
            password="landlord-password-123",
        )

        tenant_client = self.new_client()
        self.login(tenant_client, email="s3-tenant@example.com", password="tenant-password-123")
        tenancy_id = self.create_tenancy(
            tenant_client,
            tenant_id=str(tenant.id),
            landlord_id=str(landlord.id),
        )

        with patch("app.services.artifacts.create_s3_client", return_value=fake_s3_client):
            upload = tenant_client.post(
                f"/api/v1/evidence/tenancies/{tenancy_id}/artifacts",
                files={"artifact": ("receipt.pdf", b"s3-private-artifact", "application/pdf")},
            )
            self.assertEqual(upload.status_code, 201, upload.text)
            self.assertEqual(upload.json()["storage_backend"], "s3_compatible")
            self.assertEqual(len(fake_s3_client.put_calls), 1)

            submit_evidence = tenant_client.post(
                f"/api/v1/tenancies/{tenancy_id}/evidence",
                json={
                    "subject_user_id": str(tenant.id),
                    "document_type": "rent_receipt",
                    "artifact_name": "ignored-client-name.pdf",
                    "stored_artifact_id": upload.json()["id"],
                    "summary": "Uploaded April rent proof.",
                },
            )
            self.assertEqual(submit_evidence.status_code, 201, submit_evidence.text)

            artifact_access = tenant_client.post(
                f"/api/v1/evidence/{submit_evidence.json()['id']}/artifact-access"
            )
            self.assertEqual(artifact_access.status_code, 200, artifact_access.text)
            self.assertEqual(artifact_access.json()["storage_backend"], "s3_compatible")

            download = tenant_client.get(
                artifact_access.json()["download_url"],
                follow_redirects=False,
            )
            self.assertEqual(download.status_code, 307, download.text)
            self.assertIn("https://artifacts.example/download?", download.headers["location"])


if __name__ == "__main__":
    unittest.main()
