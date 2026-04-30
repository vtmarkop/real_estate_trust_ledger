from __future__ import annotations

from pathlib import Path
import uuid
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
from app.models import Property, User  # noqa: E402
from trustledger_domain import AccountWorkspaceRole  # noqa: E402


class PropertyAssignmentApiTests(unittest.TestCase):
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
        workspace_roles: tuple[AccountWorkspaceRole, ...] | None = None,
    ) -> User:
        with Session(self.engine) as session:
            user = User(
                email=email,
                full_name=full_name,
                password_hash=hash_password(password),
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

    def create_agency(self, *, owner_email: str, owner_password: str) -> dict:
        client = self.new_client()
        self.login(client, email=owner_email, password=owner_password)
        response = client.post(
            "/api/v1/organizations",
            json={
                "name": "Blue Key Realty",
                "slug": "blue-key-realty",
                "organization_type": "agency",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_landlord_can_assign_property_to_agency_agent_and_tenant(self) -> None:
        landlord = self.seed_user(
            email="landlord@example.com",
            full_name="Landlord User",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        agent = self.seed_user(
            email="agent@example.com",
            full_name="Agency Agent",
            password="agent-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )
        tenant = self.seed_user(
            email="tenant@example.com",
            full_name="Tenant User",
            password="tenant-password-123",
        )

        agency_payload = self.create_agency(
            owner_email=agent.email,
            owner_password="agent-password-123",
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        create_property = landlord_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Harbor Flat",
                "address_line1": "12 Port View",
                "city": "Athens",
                "country_code": "GR",
                "custom_tags": ["waterfront"],
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        property_payload = create_property.json()
        self.assertEqual(property_payload["management_mode"], "owner_managed")

        update_property = landlord_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={
                "management_mode": "agency_managed",
                "assigned_agency_organization_id": agency_payload["id"],
                "assigned_agency_user_email": agent.email,
                "assigned_tenant_email": tenant.email,
                "custom_tags": ["waterfront", "priority"],
            },
        )
        self.assertEqual(update_property.status_code, 200, update_property.text)
        updated_payload = update_property.json()
        self.assertEqual(updated_payload["management_mode"], "agency_managed")
        self.assertEqual(updated_payload["assigned_agency_organization_name"], "Blue Key Realty")
        self.assertEqual(updated_payload["assigned_agency_user_full_name"], "Agency Agent")
        self.assertEqual(updated_payload["assigned_tenant_user_full_name"], "Tenant User")

        agent_client = self.new_client()
        self.login(agent_client, email=agent.email, password="agent-password-123")
        agent_properties = agent_client.get("/api/v1/properties/mine")
        self.assertEqual(agent_properties.status_code, 200, agent_properties.text)
        self.assertEqual(len(agent_properties.json()), 1)
        self.assertEqual(agent_properties.json()[0]["id"], property_payload["id"])

        tenant_client = self.new_client()
        self.login(tenant_client, email=tenant.email, password="tenant-password-123")
        tenant_properties = tenant_client.get("/api/v1/properties/mine")
        self.assertEqual(tenant_properties.status_code, 200, tenant_properties.text)
        self.assertEqual(len(tenant_properties.json()), 1)
        self.assertEqual(tenant_properties.json()[0]["assigned_tenant_user_email"], tenant.email)

    def test_agency_can_create_assigned_inventory_visible_in_agency_workspace(self) -> None:
        agent = self.seed_user(
            email="agent-inventory@example.com",
            full_name="Inventory Agent",
            password="agent-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )

        agency_payload = self.create_agency(
            owner_email=agent.email,
            owner_password="agent-password-123",
        )

        agent_client = self.new_client()
        self.login(agent_client, email=agent.email, password="agent-password-123")
        create_property = agent_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Agency Inventory Flat",
                "address_line1": "15 Operator Street",
                "city": "Athens",
                "country_code": "GR",
                "management_mode": "agency_managed",
                "assigned_agency_organization_id": agency_payload["id"],
                "assigned_agency_user_email": agent.email,
                "custom_tags": ["listing-ready"],
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        property_payload = create_property.json()
        self.assertEqual(property_payload["management_mode"], "agency_managed")
        self.assertEqual(property_payload["assigned_agency_organization_name"], "Blue Key Realty")
        self.assertEqual(property_payload["assigned_agency_user_full_name"], "Inventory Agent")

        my_properties = agent_client.get("/api/v1/properties/mine")
        self.assertEqual(my_properties.status_code, 200, my_properties.text)
        self.assertEqual(len(my_properties.json()), 1)
        self.assertEqual(my_properties.json()[0]["id"], property_payload["id"])

        save_tags = agent_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={"custom_tags": ["listing-ready", "agency-inventory"]},
        )
        self.assertEqual(save_tags.status_code, 200, save_tags.text)
        self.assertEqual(save_tags.json()["custom_tags"], ["listing-ready", "agency-inventory"])

        denied_core_edit = agent_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={"property_label": "Renamed By Agency"},
        )
        self.assertEqual(denied_core_edit.status_code, 403, denied_core_edit.text)

    def test_agency_can_assign_created_inventory_to_existing_landlord(self) -> None:
        agent = self.seed_user(
            email="agent-owner-link@example.com",
            full_name="Owner Link Agent",
            password="agent-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )
        landlord = self.seed_user(
            email="assigned-landlord@example.com",
            full_name="Assigned Landlord",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        tenant = self.seed_user(
            email="tenant-owner-link@example.com",
            full_name="Owner Link Tenant",
            password="tenant-password-123",
        )

        agency_payload = self.create_agency(
            owner_email=agent.email,
            owner_password="agent-password-123",
        )

        agent_client = self.new_client()
        self.login(agent_client, email=agent.email, password="agent-password-123")
        create_property = agent_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Landlord Assigned Inventory",
                "address_line1": "18 Owner Street",
                "city": "Athens",
                "country_code": "GR",
                "management_mode": "agency_managed",
                "assigned_agency_organization_id": agency_payload["id"],
                "assigned_agency_user_email": agent.email,
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        property_payload = create_property.json()
        self.assertIsNone(property_payload["owner_landlord_user_email"])

        assign_landlord = agent_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={"owner_landlord_email": landlord.email},
        )
        self.assertEqual(assign_landlord.status_code, 200, assign_landlord.text)
        assigned_payload = assign_landlord.json()
        self.assertEqual(assigned_payload["owner_landlord_user_id"], str(landlord.id))
        self.assertEqual(assigned_payload["owner_landlord_user_full_name"], "Assigned Landlord")
        self.assertEqual(assigned_payload["owner_landlord_user_email"], landlord.email)

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        landlord_properties = landlord_client.get("/api/v1/properties/mine")
        self.assertEqual(landlord_properties.status_code, 200, landlord_properties.text)
        self.assertEqual(len(landlord_properties.json()), 1)
        self.assertEqual(landlord_properties.json()[0]["id"], property_payload["id"])

        renamed = landlord_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={"property_label": "Landlord Accepted Inventory"},
        )
        self.assertEqual(renamed.status_code, 200, renamed.text)
        self.assertEqual(renamed.json()["property_label"], "Landlord Accepted Inventory")

        tenancy = landlord_client.post(
            "/api/v1/tenancies",
            json={
                "property_id": property_payload["id"],
                "lease_start_date": "2026-05-01",
                "lease_end_date": "2027-04-30",
                "monthly_rent_minor": 90000,
                "deposit_minor": 180000,
                "currency_code": "EUR",
                "tenant_user_id": str(tenant.id),
                "landlord_user_id": str(landlord.id),
            },
        )
        self.assertEqual(tenancy.status_code, 201, tenancy.text)
        self.assertEqual(tenancy.json()["property_label"], "Landlord Accepted Inventory")

    def test_property_owner_assignment_requires_landlord_role(self) -> None:
        agent = self.seed_user(
            email="agent-owner-reject@example.com",
            full_name="Owner Reject Agent",
            password="agent-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )
        tenant = self.seed_user(
            email="not-a-landlord@example.com",
            full_name="Not A Landlord",
            password="tenant-password-123",
        )

        agency_payload = self.create_agency(
            owner_email=agent.email,
            owner_password="agent-password-123",
        )

        agent_client = self.new_client()
        self.login(agent_client, email=agent.email, password="agent-password-123")
        create_property = agent_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Reject Owner Inventory",
                "address_line1": "19 Owner Street",
                "city": "Athens",
                "country_code": "GR",
                "management_mode": "agency_managed",
                "assigned_agency_organization_id": agency_payload["id"],
                "assigned_agency_user_email": agent.email,
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)

        assign_landlord = agent_client.patch(
            f"/api/v1/properties/{create_property.json()['id']}",
            json={"owner_landlord_email": tenant.email},
        )
        self.assertEqual(assign_landlord.status_code, 409, assign_landlord.text)
        self.assertEqual(
            assign_landlord.json()["detail"],
            "The selected property owner does not have the landlord role.",
        )

    def test_assigned_agency_operator_can_update_tags_but_not_core_property_fields(self) -> None:
        landlord = self.seed_user(
            email="landlord2@example.com",
            full_name="Landlord Two",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        agent = self.seed_user(
            email="agent2@example.com",
            full_name="Agency Agent Two",
            password="agent-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )

        agency_payload = self.create_agency(
            owner_email=agent.email,
            owner_password="agent-password-123",
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        create_property = landlord_client.post(
            "/api/v1/properties",
            json={
                "property_label": "City Loft",
                "address_line1": "33 Center Street",
                "city": "Athens",
                "country_code": "GR",
                "custom_tags": [],
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        property_payload = create_property.json()

        assign_property = landlord_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={
                "assigned_agency_organization_id": agency_payload["id"],
                "assigned_agency_user_email": agent.email,
            },
        )
        self.assertEqual(assign_property.status_code, 200, assign_property.text)

        agent_client = self.new_client()
        self.login(agent_client, email=agent.email, password="agent-password-123")
        save_tags = agent_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={"custom_tags": ["student", "hot lead"]},
        )
        self.assertEqual(save_tags.status_code, 200, save_tags.text)
        self.assertEqual(save_tags.json()["custom_tags"], ["student", "hot lead"])

        denied_core_edit = agent_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={"property_label": "Agent Renamed Loft"},
        )
        self.assertEqual(denied_core_edit.status_code, 403, denied_core_edit.text)

        with Session(self.engine) as session:
            property_record = session.get(Property, uuid.UUID(property_payload["id"]))
            self.assertIsNotNone(property_record)
            self.assertEqual(property_record.property_label, "City Loft")

    def test_landlord_can_keep_property_owner_managed_without_agency_assignment(self) -> None:
        landlord = self.seed_user(
            email="landlord3@example.com",
            full_name="Landlord Three",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        tenant = self.seed_user(
            email="tenant3@example.com",
            full_name="Tenant Three",
            password="tenant-password-123",
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        create_property = landlord_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Owner Managed House",
                "address_line1": "7 Garden Lane",
                "city": "Athens",
                "country_code": "GR",
                "management_mode": "owner_managed",
                "assigned_tenant_email": tenant.email,
                "custom_tags": ["direct-owner"],
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        payload = create_property.json()
        self.assertEqual(payload["management_mode"], "owner_managed")
        self.assertIsNone(payload["assigned_agency_organization_id"])
        self.assertIsNone(payload["assigned_agency_user_id"])
        self.assertEqual(payload["assigned_tenant_user_email"], tenant.email)

    def test_switching_back_to_owner_managed_clears_agency_assignment(self) -> None:
        landlord = self.seed_user(
            email="landlord4@example.com",
            full_name="Landlord Four",
            password="landlord-password-123",
            workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        )
        agent = self.seed_user(
            email="agent4@example.com",
            full_name="Agent Four",
            password="agent-password-123",
            workspace_roles=(AccountWorkspaceRole.AGENCY,),
        )

        agency_payload = self.create_agency(
            owner_email=agent.email,
            owner_password="agent-password-123",
        )

        landlord_client = self.new_client()
        self.login(landlord_client, email=landlord.email, password="landlord-password-123")
        create_property = landlord_client.post(
            "/api/v1/properties",
            json={
                "property_label": "Convertible Home",
                "address_line1": "99 Seaside Road",
                "city": "Athens",
                "country_code": "GR",
                "management_mode": "agency_managed",
                "assigned_agency_organization_id": agency_payload["id"],
                "assigned_agency_user_email": agent.email,
            },
        )
        self.assertEqual(create_property.status_code, 201, create_property.text)
        property_payload = create_property.json()
        self.assertEqual(property_payload["management_mode"], "agency_managed")

        owner_managed = landlord_client.patch(
            f"/api/v1/properties/{property_payload['id']}",
            json={
                "management_mode": "owner_managed",
            },
        )
        self.assertEqual(owner_managed.status_code, 200, owner_managed.text)
        updated_payload = owner_managed.json()
        self.assertEqual(updated_payload["management_mode"], "owner_managed")
        self.assertIsNone(updated_payload["assigned_agency_organization_id"])
        self.assertIsNone(updated_payload["assigned_agency_user_id"])


if __name__ == "__main__":
    unittest.main()
