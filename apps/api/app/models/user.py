import json
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, SQLModel

from app.models.common import TimestampedModel, ensure_utc, utcnow
from trustledger_domain import AccountWorkspaceRole, SystemRole

if TYPE_CHECKING:
    from app.models.agency_trust_check import AgencyTrustCheck
    from app.models.application import ListingApplication
    from app.models.automation_task import AutomationTask
    from app.models.auth_session import AuthSession
    from app.models.consent import TrustReportConsent
    from app.models.deposit import DepositRecord
    from app.models.evidence import EvidenceDocument
    from app.models.history_import import HistoryImport
    from app.models.listing import Listing
    from app.models.maintenance_ticket import MaintenanceTicket
    from app.models.membership import OrganizationMembership
    from app.models.notification_delivery import NotificationDelivery
    from app.models.payment import PaymentRecord
    from app.models.property import Property
    from app.models.reference_request import ReferenceRequest
    from app.models.tenancy import Tenancy
    from app.models.trust_score_recalculation import (
        TrustScoreRecalculationBatch,
        TrustScoreRecalculationRequest,
    )
    from app.models.trust_score import TrustScoreHistory, TrustScoreSnapshot
    from app.models.trust_event import TrustEvent
    from app.models.worker_run import WorkerRun


DEFAULT_WORKSPACE_ROLES = (AccountWorkspaceRole.TENANT,)


def normalize_workspace_roles(
    roles: list[str | AccountWorkspaceRole] | tuple[str | AccountWorkspaceRole, ...] | None,
) -> list[AccountWorkspaceRole]:
    normalized_roles: list[AccountWorkspaceRole] = []
    for role in roles or DEFAULT_WORKSPACE_ROLES:
        try:
            normalized_role = role if isinstance(role, AccountWorkspaceRole) else AccountWorkspaceRole(str(role))
        except ValueError:
            continue
        if normalized_role not in normalized_roles:
            normalized_roles.append(normalized_role)

    return normalized_roles or [AccountWorkspaceRole.TENANT]


class User(TimestampedModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False, max_length=320)
    full_name: str = Field(nullable=False, max_length=255)
    password_hash: str = Field(nullable=False, max_length=255)
    system_role: SystemRole = Field(default=SystemRole.USER, nullable=False, max_length=50)
    workspace_roles_json: str = Field(default='["tenant"]', nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    email_verified: bool = Field(default=False, nullable=False)
    failed_login_attempt_count: int = Field(default=0, nullable=False, ge=0)
    last_login_attempt_at: datetime | None = Field(default=None, nullable=True)
    login_locked_until: datetime | None = Field(default=None, nullable=True)
    last_login_at: datetime | None = Field(default=None, nullable=True)

    memberships: List["OrganizationMembership"] = Relationship(back_populates="user")
    sessions: List["AuthSession"] = Relationship(back_populates="user")
    consents_granted: List["TrustReportConsent"] = Relationship(
        back_populates="granted_by_user",
        sa_relationship_kwargs={"foreign_keys": "TrustReportConsent.granted_by_user_id"},
    )
    consents_as_subject: List["TrustReportConsent"] = Relationship(
        back_populates="subject_user",
        sa_relationship_kwargs={"foreign_keys": "TrustReportConsent.subject_user_id"},
    )
    automation_tasks_as_subject: List["AutomationTask"] = Relationship(
        back_populates="subject_user",
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.subject_user_id"},
    )
    requested_automation_tasks: List["AutomationTask"] = Relationship(
        back_populates="requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.requested_by_user_id"},
    )
    processed_automation_tasks: List["AutomationTask"] = Relationship(
        back_populates="processed_by_user",
        sa_relationship_kwargs={"foreign_keys": "AutomationTask.processed_by_user_id"},
    )
    notification_deliveries_as_recipient: List["NotificationDelivery"] = Relationship(
        back_populates="recipient_user",
        sa_relationship_kwargs={"foreign_keys": "NotificationDelivery.recipient_user_id"},
    )
    requested_notification_deliveries: List["NotificationDelivery"] = Relationship(
        back_populates="requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "NotificationDelivery.requested_by_user_id"},
    )
    processed_notification_deliveries: List["NotificationDelivery"] = Relationship(
        back_populates="processed_by_user",
        sa_relationship_kwargs={"foreign_keys": "NotificationDelivery.processed_by_user_id"},
    )
    requested_trust_checks: List["AgencyTrustCheck"] = Relationship(
        back_populates="requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "AgencyTrustCheck.requested_by_user_id"},
    )
    subject_trust_checks: List["AgencyTrustCheck"] = Relationship(
        back_populates="subject_user",
        sa_relationship_kwargs={"foreign_keys": "AgencyTrustCheck.subject_user_id"},
    )
    tenancies_as_tenant: List["Tenancy"] = Relationship(
        back_populates="tenant_user",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.tenant_user_id"},
    )
    tenancies_as_landlord: List["Tenancy"] = Relationship(
        back_populates="landlord_user",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.landlord_user_id"},
    )
    tenancies_created: List["Tenancy"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.created_by_user_id"},
    )
    tenancies_reviewed: List["Tenancy"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.reviewed_by_user_id"},
    )
    tenancies_counterparty_confirmed: List["Tenancy"] = Relationship(
        back_populates="counterparty_confirmed_by_user",
        sa_relationship_kwargs={"foreign_keys": "Tenancy.counterparty_confirmed_by_user_id"},
    )
    evidence_documents_as_subject: List["EvidenceDocument"] = Relationship(
        back_populates="subject_user",
        sa_relationship_kwargs={"foreign_keys": "EvidenceDocument.subject_user_id"},
    )
    evidence_documents_uploaded: List["EvidenceDocument"] = Relationship(
        back_populates="uploaded_by_user",
        sa_relationship_kwargs={"foreign_keys": "EvidenceDocument.uploaded_by_user_id"},
    )
    evidence_documents_reviewed: List["EvidenceDocument"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "EvidenceDocument.reviewed_by_user_id"},
    )
    history_imports_as_subject: List["HistoryImport"] = Relationship(
        back_populates="subject_user",
        sa_relationship_kwargs={"foreign_keys": "HistoryImport.subject_user_id"},
    )
    history_imports_created: List["HistoryImport"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "HistoryImport.created_by_user_id"},
    )
    history_imports_reviewed: List["HistoryImport"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "HistoryImport.reviewed_by_user_id"},
    )
    reference_requests_as_subject: List["ReferenceRequest"] = Relationship(
        back_populates="subject_user",
        sa_relationship_kwargs={"foreign_keys": "ReferenceRequest.subject_user_id"},
    )
    reference_requests_created: List["ReferenceRequest"] = Relationship(
        back_populates="requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "ReferenceRequest.requested_by_user_id"},
    )
    reference_requests_to_fulfill: List["ReferenceRequest"] = Relationship(
        back_populates="requested_from_user",
        sa_relationship_kwargs={"foreign_keys": "ReferenceRequest.requested_from_user_id"},
    )
    listings_created: List["Listing"] = Relationship(back_populates="created_by_user")
    applications_as_applicant: List["ListingApplication"] = Relationship(
        back_populates="applicant_user",
        sa_relationship_kwargs={"foreign_keys": "ListingApplication.applicant_user_id"},
    )
    applications_submitted: List["ListingApplication"] = Relationship(
        back_populates="submitted_by_user",
        sa_relationship_kwargs={"foreign_keys": "ListingApplication.submitted_by_user_id"},
    )
    applications_decided: List["ListingApplication"] = Relationship(
        back_populates="decided_by_user",
        sa_relationship_kwargs={"foreign_keys": "ListingApplication.decided_by_user_id"},
    )
    payments_as_payer: List["PaymentRecord"] = Relationship(
        back_populates="payer_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.payer_user_id"},
    )
    payments_as_payee: List["PaymentRecord"] = Relationship(
        back_populates="payee_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.payee_user_id"},
    )
    payments_created: List["PaymentRecord"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.created_by_user_id"},
    )
    payments_counterparty_actioned: List["PaymentRecord"] = Relationship(
        back_populates="counterparty_action_by_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.counterparty_action_by_user_id"},
    )
    payments_disputed: List["PaymentRecord"] = Relationship(
        back_populates="disputed_by_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.disputed_by_user_id"},
    )
    payments_review_requested: List["PaymentRecord"] = Relationship(
        back_populates="review_requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.review_requested_by_user_id"},
    )
    payments_reviewed: List["PaymentRecord"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.reviewed_by_user_id"},
    )
    payments_appealed: List["PaymentRecord"] = Relationship(
        back_populates="appeal_requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "PaymentRecord.appeal_requested_by_user_id"},
    )
    deposit_records_created: List["DepositRecord"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.created_by_user_id"},
    )
    deposit_records_counterparty_actioned: List["DepositRecord"] = Relationship(
        back_populates="counterparty_action_by_user",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.counterparty_action_by_user_id"},
    )
    deposit_records_disputed: List["DepositRecord"] = Relationship(
        back_populates="disputed_by_user",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.disputed_by_user_id"},
    )
    deposit_records_review_requested: List["DepositRecord"] = Relationship(
        back_populates="review_requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.review_requested_by_user_id"},
    )
    deposit_records_reviewed: List["DepositRecord"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.reviewed_by_user_id"},
    )
    deposit_records_appealed: List["DepositRecord"] = Relationship(
        back_populates="appeal_requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "DepositRecord.appeal_requested_by_user_id"},
    )
    maintenance_tickets_created: List["MaintenanceTicket"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.created_by_user_id"},
    )
    maintenance_tickets_acknowledged: List["MaintenanceTicket"] = Relationship(
        back_populates="acknowledged_by_user",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.acknowledged_by_user_id"},
    )
    maintenance_tickets_resolved: List["MaintenanceTicket"] = Relationship(
        back_populates="resolved_by_user",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.resolved_by_user_id"},
    )
    maintenance_tickets_disputed: List["MaintenanceTicket"] = Relationship(
        back_populates="disputed_by_user",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.disputed_by_user_id"},
    )
    maintenance_tickets_review_requested: List["MaintenanceTicket"] = Relationship(
        back_populates="review_requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.review_requested_by_user_id"},
    )
    maintenance_tickets_reviewed: List["MaintenanceTicket"] = Relationship(
        back_populates="reviewed_by_user",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.reviewed_by_user_id"},
    )
    maintenance_tickets_appealed: List["MaintenanceTicket"] = Relationship(
        back_populates="appeal_requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "MaintenanceTicket.appeal_requested_by_user_id"},
    )
    properties_created: List["Property"] = Relationship(
        back_populates="created_by_user",
        sa_relationship_kwargs={"foreign_keys": "Property.created_by_user_id"},
    )
    properties_as_assigned_agent: List["Property"] = Relationship(
        back_populates="assigned_agency_user",
        sa_relationship_kwargs={"foreign_keys": "Property.assigned_agency_user_id"},
    )
    properties_as_assigned_tenant: List["Property"] = Relationship(
        back_populates="assigned_tenant_user",
        sa_relationship_kwargs={"foreign_keys": "Property.assigned_tenant_user_id"},
    )
    trust_score_snapshots: List["TrustScoreSnapshot"] = Relationship(back_populates="user")
    trust_score_history_entries: List["TrustScoreHistory"] = Relationship(back_populates="user")
    trust_score_recalculation_requests: List["TrustScoreRecalculationRequest"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationRequest.user_id"},
    )
    requested_trust_score_recalculation_requests: List["TrustScoreRecalculationRequest"] = Relationship(
        back_populates="requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationRequest.requested_by_user_id"},
    )
    processed_trust_score_recalculation_requests: List["TrustScoreRecalculationRequest"] = Relationship(
        back_populates="processed_by_user",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationRequest.processed_by_user_id"},
    )
    requested_trust_score_recalculation_batches: List["TrustScoreRecalculationBatch"] = Relationship(
        back_populates="requested_by_user",
        sa_relationship_kwargs={"foreign_keys": "TrustScoreRecalculationBatch.requested_by_user_id"},
    )
    worker_runs: List["WorkerRun"] = Relationship(back_populates="worker_user")
    trust_events_as_subject: List["TrustEvent"] = Relationship(
        back_populates="subject_user",
        sa_relationship_kwargs={"foreign_keys": "TrustEvent.subject_user_id"},
    )
    trust_events_as_actor: List["TrustEvent"] = Relationship(
        back_populates="actor_user",
        sa_relationship_kwargs={"foreign_keys": "TrustEvent.actor_user_id"},
    )

    @property
    def workspace_roles(self) -> list[AccountWorkspaceRole]:
        try:
            parsed_roles = json.loads(self.workspace_roles_json or "[]")
        except json.JSONDecodeError:
            parsed_roles = []
        return normalize_workspace_roles(parsed_roles)

    def set_workspace_roles(
        self,
        roles: list[str | AccountWorkspaceRole] | tuple[str | AccountWorkspaceRole, ...],
    ) -> None:
        normalized_roles = normalize_workspace_roles(roles)
        self.workspace_roles_json = json.dumps([role.value for role in normalized_roles])

    def is_login_locked(self, *, now: datetime | None = None) -> bool:
        if self.login_locked_until is None:
            return False
        current = ensure_utc(now or utcnow())
        return current < ensure_utc(self.login_locked_until)
