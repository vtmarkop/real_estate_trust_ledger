from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import date, timedelta
import hashlib
from pathlib import Path

from sqlmodel import Session, select

from app.core.config import get_settings
from app.core.security import hash_password, hash_token
from app.models import (
    AgencyTrustCheck,
    AuditLog,
    AutomationTask,
    DepositRecord,
    EvidenceDocument,
    HistoryImport,
    Listing,
    ListingApplication,
    MaintenanceTicket,
    Organization,
    OrganizationMembership,
    PaymentRecord,
    Property,
    StoredArtifact,
    ReferenceRequest,
    Tenancy,
    TrustEvent,
    TrustReportConsent,
    TrustScoreSnapshot,
    User,
)
from app.models.common import utcnow
from app.services.audit_logs import append_audit_log
from app.services.artifacts import LOCAL_STORAGE_BACKEND, get_artifact_storage_root, sanitize_filename
from app.services.properties import serialize_property_tags
from app.services.scoring import refresh_user_trust_score
from trustledger_domain import (
    AccountWorkspaceRole,
    ApplicationStatus,
    AuditActionType,
    AuditOutcomeStatus,
    AutomationTaskStatus,
    AutomationTaskType,
    ConsentScope,
    DepositStatus,
    DisputeVerdictOutcome,
    EvidenceDocumentType,
    EvidenceReviewStatus,
    HistoryImportStatus,
    ListingStatus,
    MaintenanceTicketPriority,
    MaintenanceTicketStatus,
    OrganizationMembershipRole,
    OrganizationType,
    PaymentProofStatus,
    PaymentRecordStatus,
    PaymentRecordType,
    PropertyManagementMode,
    ReferenceRequestStatus,
    ScoreCalculationReason,
    SystemRole,
    TenancyStatus,
    TrustEventType,
    VerificationStatus,
)


@dataclass(frozen=True)
class DemoAccount:
    label: str
    email: str
    password: str
    legacy_emails: tuple[str, ...] = ()


@dataclass(frozen=True)
class DemoSeedSummary:
    accounts: tuple[DemoAccount, ...]
    share_token: str
    access_code: str
    tenant_score: int
    landlord_score: int
    verification_strength: int


DEMO_ADMIN = DemoAccount(
    "Platform Admin",
    "admin@demo.trustledger.app",
    "DemoAdmin123!",
    legacy_emails=("admin@demo.trustledger.local",),
)
DEMO_REVIEWER = DemoAccount(
    "Internal Reviewer",
    "reviewer@demo.trustledger.app",
    "DemoReviewer123!",
    legacy_emails=("reviewer@demo.trustledger.local",),
)
DEMO_AGENCY_OWNER = DemoAccount(
    "Agency Owner",
    "owner@demo-agency.app",
    "DemoAgency123!",
    legacy_emails=("owner@demo-agency.local",),
)
DEMO_TENANT = DemoAccount(
    "Tenant",
    "tenant@demo.trustledger.app",
    "DemoTenant123!",
    legacy_emails=("tenant@demo.trustledger.local",),
)
DEMO_LANDLORD = DemoAccount(
    "Landlord",
    "landlord@demo.trustledger.app",
    "DemoLandlord123!",
    legacy_emails=("landlord@demo.trustledger.local",),
)

DEMO_ACCOUNTS = (
    DEMO_ADMIN,
    DEMO_REVIEWER,
    DEMO_AGENCY_OWNER,
    DEMO_TENANT,
    DEMO_LANDLORD,
)

DEMO_SHARE_TOKEN = "demo-tenant-share-token"
DEMO_ACCESS_CODE = "4829"
DEMO_PDF_PAYLOAD = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]/Contents 4 0 R>>endobj\n"
    b"4 0 obj<</Length 58>>stream\n"
    b"BT /F1 12 Tf 36 96 Td (Trust Ledger demo artifact) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"xref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n"
    b"0000000110 00000 n \n0000000193 00000 n \n0000000301 00000 n \n"
    b"trailer<</Root 1 0 R/Size 6>>\nstartxref\n371\n%%EOF\n"
)
DEMO_PNG_PAYLOAD = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
)


def nullable_match(field, value):
    return field.is_(None) if value is None else field == value


def resolve_demo_artifact_payload(*, original_file_name: str) -> tuple[bytes, str]:
    suffix = Path(original_file_name).suffix.lower()
    if suffix == ".png":
        return DEMO_PNG_PAYLOAD, "image/png"
    if suffix == ".txt":
        payload = (
            "Trust Ledger demo artifact\n"
            f"Source: {original_file_name}\n"
            "This is seeded placeholder content for workflow testing.\n"
        ).encode("utf-8")
        return payload, "text/plain"
    return DEMO_PDF_PAYLOAD, "application/pdf"


def get_or_create_stored_artifact(
    *,
    session: Session,
    tenancy: Tenancy,
    created_by_user: User,
    artifact_purpose: str,
    original_file_name: str,
) -> StoredArtifact:
    sanitized_file_name = sanitize_filename(original_file_name)
    payload, content_type = resolve_demo_artifact_payload(original_file_name=sanitized_file_name)
    storage_key = f"seeded/{artifact_purpose}/{tenancy.id}/{sanitized_file_name}"
    sha256_hex = hashlib.sha256(payload).hexdigest()

    stored_artifact = session.exec(
        select(StoredArtifact).where(
            StoredArtifact.tenancy_id == tenancy.id,
            StoredArtifact.artifact_purpose == artifact_purpose,
            StoredArtifact.original_file_name == sanitized_file_name,
        )
    ).first()
    if stored_artifact is None:
        stored_artifact = StoredArtifact(
            created_by_user_id=created_by_user.id,
            tenancy_id=tenancy.id,
            artifact_purpose=artifact_purpose,
            storage_backend=LOCAL_STORAGE_BACKEND,
            storage_key=storage_key,
            original_file_name=sanitized_file_name,
            content_type=content_type,
            size_bytes=len(payload),
            sha256_hex=sha256_hex,
        )
    else:
        stored_artifact.created_by_user_id = created_by_user.id
        stored_artifact.storage_backend = LOCAL_STORAGE_BACKEND
        stored_artifact.storage_key = storage_key
        stored_artifact.content_type = content_type
        stored_artifact.size_bytes = len(payload)
        stored_artifact.sha256_hex = sha256_hex
        stored_artifact.updated_at = utcnow()

    session.add(stored_artifact)
    session.flush()

    storage_root = get_artifact_storage_root(settings=get_settings())
    artifact_path = storage_root / storage_key
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    if not artifact_path.exists() or artifact_path.read_bytes() != payload:
        artifact_path.write_bytes(payload)

    return stored_artifact


def get_or_create_user(
    *,
    session: Session,
    email: str,
    full_name: str,
    password: str,
    system_role: SystemRole = SystemRole.USER,
    workspace_roles: tuple[AccountWorkspaceRole, ...] | None = None,
    legacy_emails: tuple[str, ...] = (),
) -> User:
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None and legacy_emails:
        for legacy_email in legacy_emails:
            user = session.exec(select(User).where(User.email == legacy_email)).first()
            if user is not None:
                user.email = email
                break
    password_hash = hash_password(password)
    current_time = utcnow()

    if user is None:
        user = User(
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            system_role=system_role,
            is_active=True,
            email_verified=True,
        )
    else:
        user.full_name = full_name
        user.password_hash = password_hash
        user.system_role = system_role
        user.is_active = True
        user.email_verified = True
        user.failed_login_attempt_count = 0
        user.login_locked_until = None
        user.updated_at = current_time
    if workspace_roles is None:
        if system_role in {SystemRole.ADMIN, SystemRole.REVIEWER}:
            workspace_roles = (AccountWorkspaceRole.INTERNAL,)
        else:
            workspace_roles = (AccountWorkspaceRole.TENANT,)
    user.set_workspace_roles(workspace_roles)

    session.add(user)
    session.flush()
    return user


def get_or_create_organization(
    *,
    session: Session,
    name: str,
    slug: str,
    organization_type: OrganizationType,
) -> Organization:
    organization = session.exec(select(Organization).where(Organization.slug == slug)).first()
    if organization is None:
        organization = Organization(
            name=name,
            slug=slug,
            organization_type=organization_type,
            is_active=True,
        )
    else:
        organization.name = name
        organization.organization_type = organization_type
        organization.is_active = True
        organization.updated_at = utcnow()

    session.add(organization)
    session.flush()
    return organization


def ensure_membership(
    *,
    session: Session,
    user: User,
    organization: Organization,
    role: OrganizationMembershipRole,
) -> OrganizationMembership:
    membership = session.exec(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == organization.id,
        )
    ).first()
    if membership is None:
        membership = OrganizationMembership(
            user_id=user.id,
            organization_id=organization.id,
            role=role,
            is_active=True,
        )
    else:
        membership.role = role
        membership.is_active = True
        membership.updated_at = utcnow()

    session.add(membership)
    session.flush()
    return membership


def get_or_create_property(
    *,
    session: Session,
    created_by_user: User,
    property_label: str,
    address_line1: str,
    city: str,
    country_code: str,
) -> Property:
    property_record = session.exec(
        select(Property).where(
            Property.created_by_user_id == created_by_user.id,
            Property.property_label == property_label,
            Property.address_line1 == address_line1,
        )
    ).first()
    if property_record is None:
        property_record = Property(
            property_label=property_label,
            address_line1=address_line1,
            city=city,
            country_code=country_code,
            created_by_user_id=created_by_user.id,
            is_active=True,
        )
    else:
        property_record.property_label = property_label
        property_record.address_line1 = address_line1
        property_record.city = city
        property_record.country_code = country_code
        property_record.is_active = True
        property_record.updated_at = utcnow()

    session.add(property_record)
    session.flush()
    return property_record


def get_or_create_history_import(
    *,
    session: Session,
    subject_user: User,
    created_by_user: User,
    title: str,
    summary: str,
    status: HistoryImportStatus,
    submitted_at,
    reviewed_at,
    reviewed_by_user: User | None,
    review_notes: str | None,
) -> HistoryImport:
    history_import = session.exec(
        select(HistoryImport).where(
            HistoryImport.subject_user_id == subject_user.id,
            HistoryImport.title == title,
        )
    ).first()
    if history_import is None:
        history_import = HistoryImport(
            subject_user_id=subject_user.id,
            created_by_user_id=created_by_user.id,
            title=title,
            summary=summary,
            status=status,
            submitted_at=submitted_at,
            reviewed_at=reviewed_at,
            reviewed_by_user_id=reviewed_by_user.id if reviewed_by_user else None,
            review_notes=review_notes,
        )
    else:
        history_import.created_by_user_id = created_by_user.id
        history_import.summary = summary
        history_import.status = status
        history_import.submitted_at = submitted_at
        history_import.reviewed_at = reviewed_at
        history_import.reviewed_by_user_id = reviewed_by_user.id if reviewed_by_user else None
        history_import.review_notes = review_notes
        history_import.updated_at = utcnow()

    session.add(history_import)
    session.flush()
    return history_import


def get_or_create_tenancy(
    *,
    session: Session,
    property_label: str,
    address_line1: str,
    city: str,
    country_code: str,
    tenancy_status: TenancyStatus,
    verification_status: VerificationStatus,
    lease_start_date: date,
    lease_end_date: date | None,
    monthly_rent_minor: int,
    deposit_minor: int,
    currency_code: str,
    tenant_user: User,
    landlord_user: User,
    created_by_user: User,
    history_import: HistoryImport | None = None,
    property_record: Property | None = None,
    counterparty_confirmed_by_user: User | None = None,
    counterparty_confirmed_at=None,
    review_requested_at=None,
    reviewed_by_user: User | None = None,
    reviewed_at=None,
    review_notes: str | None = None,
) -> Tenancy:
    tenancy = session.exec(
        select(Tenancy).where(
            Tenancy.tenant_user_id == tenant_user.id,
            Tenancy.landlord_user_id == landlord_user.id,
            Tenancy.lease_start_date == lease_start_date,
            Tenancy.property_label == property_label,
        )
    ).first()
    if tenancy is None:
        tenancy = Tenancy(
            property_label=property_label,
            address_line1=address_line1,
            city=city,
            country_code=country_code,
            tenancy_status=tenancy_status,
            verification_status=verification_status,
            lease_start_date=lease_start_date,
            lease_end_date=lease_end_date,
            monthly_rent_minor=monthly_rent_minor,
            deposit_minor=deposit_minor,
            currency_code=currency_code,
            history_import_id=history_import.id if history_import else None,
            property_id=property_record.id if property_record else None,
            tenant_user_id=tenant_user.id,
            landlord_user_id=landlord_user.id,
            created_by_user_id=created_by_user.id,
            counterparty_confirmed_at=counterparty_confirmed_at,
            counterparty_confirmed_by_user_id=(
                counterparty_confirmed_by_user.id if counterparty_confirmed_by_user else None
            ),
            review_requested_at=review_requested_at,
            reviewed_at=reviewed_at,
            reviewed_by_user_id=reviewed_by_user.id if reviewed_by_user else None,
            review_notes=review_notes,
        )
    else:
        tenancy.address_line1 = address_line1
        tenancy.city = city
        tenancy.country_code = country_code
        tenancy.tenancy_status = tenancy_status
        tenancy.verification_status = verification_status
        tenancy.lease_end_date = lease_end_date
        tenancy.monthly_rent_minor = monthly_rent_minor
        tenancy.deposit_minor = deposit_minor
        tenancy.currency_code = currency_code
        tenancy.history_import_id = history_import.id if history_import else None
        tenancy.property_id = property_record.id if property_record else None
        tenancy.created_by_user_id = created_by_user.id
        tenancy.counterparty_confirmed_at = counterparty_confirmed_at
        tenancy.counterparty_confirmed_by_user_id = (
            counterparty_confirmed_by_user.id if counterparty_confirmed_by_user else None
        )
        tenancy.review_requested_at = review_requested_at
        tenancy.reviewed_at = reviewed_at
        tenancy.reviewed_by_user_id = reviewed_by_user.id if reviewed_by_user else None
        tenancy.review_notes = review_notes
        tenancy.updated_at = utcnow()

    session.add(tenancy)
    session.flush()
    return tenancy


def get_or_create_evidence_document(
    *,
    session: Session,
    tenancy: Tenancy,
    subject_user: User,
    uploaded_by_user: User,
    document_type: EvidenceDocumentType,
    artifact_name: str,
    summary: str,
    review_status: EvidenceReviewStatus,
    review_requested_at,
    stored_artifact: StoredArtifact | None = None,
    reviewed_by_user: User | None = None,
    reviewed_at=None,
    review_notes: str | None = None,
    issuer_name: str | None = None,
    document_date: date | None = None,
    amount_minor: int | None = None,
    currency_code: str | None = None,
    external_reference: str | None = None,
    reference_request: ReferenceRequest | None = None,
) -> EvidenceDocument:
    evidence_document = session.exec(
        select(EvidenceDocument).where(
            EvidenceDocument.tenancy_id == tenancy.id,
            EvidenceDocument.subject_user_id == subject_user.id,
            EvidenceDocument.document_type == document_type,
            EvidenceDocument.artifact_name == artifact_name,
        )
    ).first()
    if evidence_document is None:
        evidence_document = EvidenceDocument(
            tenancy_id=tenancy.id,
            subject_user_id=subject_user.id,
            uploaded_by_user_id=uploaded_by_user.id,
            stored_artifact_id=stored_artifact.id if stored_artifact else None,
            reference_request_id=reference_request.id if reference_request else None,
            document_type=document_type,
            review_status=review_status,
            artifact_name=artifact_name,
            summary=summary,
            issuer_name=issuer_name,
            document_date=document_date,
            amount_minor=amount_minor,
            currency_code=currency_code,
            external_reference=external_reference,
            review_requested_at=review_requested_at,
            reviewed_at=reviewed_at,
            reviewed_by_user_id=reviewed_by_user.id if reviewed_by_user else None,
            review_notes=review_notes,
        )
    else:
        evidence_document.uploaded_by_user_id = uploaded_by_user.id
        evidence_document.stored_artifact_id = stored_artifact.id if stored_artifact else None
        evidence_document.reference_request_id = reference_request.id if reference_request else None
        evidence_document.review_status = review_status
        evidence_document.summary = summary
        evidence_document.issuer_name = issuer_name
        evidence_document.document_date = document_date
        evidence_document.amount_minor = amount_minor
        evidence_document.currency_code = currency_code
        evidence_document.external_reference = external_reference
        evidence_document.review_requested_at = review_requested_at
        evidence_document.reviewed_at = reviewed_at
        evidence_document.reviewed_by_user_id = reviewed_by_user.id if reviewed_by_user else None
        evidence_document.review_notes = review_notes
        evidence_document.updated_at = utcnow()

    session.add(evidence_document)
    session.flush()
    return evidence_document


def get_or_create_reference_request(
    *,
    session: Session,
    tenancy: Tenancy,
    subject_user: User,
    requested_by_user: User,
    requested_from_user: User,
    message: str,
    status: ReferenceRequestStatus,
    fulfilled_at=None,
) -> ReferenceRequest:
    reference_request = session.exec(
        select(ReferenceRequest).where(
            ReferenceRequest.tenancy_id == tenancy.id,
            ReferenceRequest.subject_user_id == subject_user.id,
            ReferenceRequest.requested_from_user_id == requested_from_user.id,
        )
    ).first()
    if reference_request is None:
        reference_request = ReferenceRequest(
            tenancy_id=tenancy.id,
            subject_user_id=subject_user.id,
            requested_by_user_id=requested_by_user.id,
            requested_from_user_id=requested_from_user.id,
            status=status,
            message=message,
            fulfilled_at=fulfilled_at,
        )
    else:
        reference_request.requested_by_user_id = requested_by_user.id
        reference_request.status = status
        reference_request.message = message
        reference_request.fulfilled_at = fulfilled_at
        reference_request.updated_at = utcnow()

    session.add(reference_request)
    session.flush()
    return reference_request


def get_or_create_payment_record(
    *,
    session: Session,
    tenancy: Tenancy,
    payer_user: User,
    payee_user: User,
    created_by_user: User,
    payment_type: PaymentRecordType,
    payment_status: PaymentRecordStatus,
    proof_status: PaymentProofStatus,
    amount_minor: int,
    currency_code: str,
    due_date: date,
    period_start_date: date | None,
    period_end_date: date | None,
    paid_at,
    proof_stored_artifact: StoredArtifact | None = None,
    counterparty_stored_artifact: StoredArtifact | None = None,
    proof_artifact_name: str | None,
    proof_summary: str | None,
    external_reference: str | None,
    counterparty_notes: str | None,
    counterparty_action_by_user: User | None,
    counterparty_action_at,
    disputed_by_user: User | None = None,
    review_requested_by_user: User | None = None,
    reviewed_by_user: User | None = None,
    appeal_requested_by_user: User | None = None,
    dispute_notes: str | None = None,
    disputed_at=None,
    review_requested_at=None,
    verdict_outcome: DisputeVerdictOutcome | None = None,
    verdict_summary: str | None = None,
    verdict_tenant_score_delta: int = 0,
    verdict_landlord_score_delta: int = 0,
    reviewed_at=None,
    appeal_notes: str | None = None,
    appeal_requested_at=None,
) -> PaymentRecord:
    payment_record = session.exec(
        select(PaymentRecord).where(
            PaymentRecord.tenancy_id == tenancy.id,
            PaymentRecord.payment_type == payment_type,
            PaymentRecord.due_date == due_date,
        )
    ).first()
    if payment_record is None:
        payment_record = PaymentRecord(
            tenancy_id=tenancy.id,
            payer_user_id=payer_user.id,
            payee_user_id=payee_user.id,
            created_by_user_id=created_by_user.id,
            counterparty_action_by_user_id=counterparty_action_by_user.id if counterparty_action_by_user else None,
            disputed_by_user_id=disputed_by_user.id if disputed_by_user else None,
            review_requested_by_user_id=review_requested_by_user.id if review_requested_by_user else None,
            reviewed_by_user_id=reviewed_by_user.id if reviewed_by_user else None,
            appeal_requested_by_user_id=appeal_requested_by_user.id if appeal_requested_by_user else None,
            payment_type=payment_type,
            payment_status=payment_status,
            proof_status=proof_status,
            amount_minor=amount_minor,
            currency_code=currency_code,
            due_date=due_date,
            period_start_date=period_start_date,
            period_end_date=period_end_date,
            paid_at=paid_at,
            proof_stored_artifact_id=proof_stored_artifact.id if proof_stored_artifact else None,
            counterparty_stored_artifact_id=(
                counterparty_stored_artifact.id if counterparty_stored_artifact else None
            ),
            proof_artifact_name=proof_artifact_name,
            proof_summary=proof_summary,
            external_reference=external_reference,
            counterparty_notes=counterparty_notes,
            counterparty_action_at=counterparty_action_at,
            dispute_notes=dispute_notes,
            disputed_at=disputed_at,
            review_requested_at=review_requested_at,
            verdict_outcome=verdict_outcome,
            verdict_summary=verdict_summary,
            verdict_tenant_score_delta=verdict_tenant_score_delta,
            verdict_landlord_score_delta=verdict_landlord_score_delta,
            reviewed_at=reviewed_at,
            appeal_notes=appeal_notes,
            appeal_requested_at=appeal_requested_at,
        )
    else:
        payment_record.payer_user_id = payer_user.id
        payment_record.payee_user_id = payee_user.id
        payment_record.created_by_user_id = created_by_user.id
        payment_record.counterparty_action_by_user_id = (
            counterparty_action_by_user.id if counterparty_action_by_user else None
        )
        payment_record.disputed_by_user_id = disputed_by_user.id if disputed_by_user else None
        payment_record.review_requested_by_user_id = (
            review_requested_by_user.id if review_requested_by_user else None
        )
        payment_record.reviewed_by_user_id = reviewed_by_user.id if reviewed_by_user else None
        payment_record.appeal_requested_by_user_id = (
            appeal_requested_by_user.id if appeal_requested_by_user else None
        )
        payment_record.payment_status = payment_status
        payment_record.proof_status = proof_status
        payment_record.amount_minor = amount_minor
        payment_record.currency_code = currency_code
        payment_record.period_start_date = period_start_date
        payment_record.period_end_date = period_end_date
        payment_record.paid_at = paid_at
        payment_record.proof_stored_artifact_id = (
            proof_stored_artifact.id if proof_stored_artifact else None
        )
        payment_record.counterparty_stored_artifact_id = (
            counterparty_stored_artifact.id if counterparty_stored_artifact else None
        )
        payment_record.proof_artifact_name = proof_artifact_name
        payment_record.proof_summary = proof_summary
        payment_record.external_reference = external_reference
        payment_record.counterparty_notes = counterparty_notes
        payment_record.counterparty_action_at = counterparty_action_at
        payment_record.dispute_notes = dispute_notes
        payment_record.disputed_at = disputed_at
        payment_record.review_requested_at = review_requested_at
        payment_record.verdict_outcome = verdict_outcome
        payment_record.verdict_summary = verdict_summary
        payment_record.verdict_tenant_score_delta = verdict_tenant_score_delta
        payment_record.verdict_landlord_score_delta = verdict_landlord_score_delta
        payment_record.reviewed_at = reviewed_at
        payment_record.appeal_notes = appeal_notes
        payment_record.appeal_requested_at = appeal_requested_at
        payment_record.updated_at = utcnow()

    session.add(payment_record)
    session.flush()
    return payment_record


def get_or_create_deposit_record(
    *,
    session: Session,
    tenancy: Tenancy,
    created_by_user: User,
    held_amount_minor: int,
    proposed_return_minor: int,
    withheld_amount_minor: int,
    currency_code: str,
    deposit_status: DepositStatus,
    move_out_date: date | None = None,
    return_due_date: date | None = None,
    returned_at=None,
    settlement_stored_artifact: StoredArtifact | None = None,
    settlement_artifact_name: str | None = None,
    settlement_summary: str | None = None,
    settlement_notes: str | None = None,
    dispute_notes: str | None = None,
    counterparty_action_by_user: User | None = None,
    counterparty_action_at=None,
    disputed_by_user: User | None = None,
    review_requested_by_user: User | None = None,
    reviewed_by_user: User | None = None,
    appeal_requested_by_user: User | None = None,
    disputed_at=None,
    review_requested_at=None,
    verdict_outcome: DisputeVerdictOutcome | None = None,
    verdict_summary: str | None = None,
    verdict_tenant_score_delta: int = 0,
    verdict_landlord_score_delta: int = 0,
    reviewed_at=None,
    appeal_notes: str | None = None,
    appeal_requested_at=None,
) -> DepositRecord:
    deposit_record = session.exec(
        select(DepositRecord).where(DepositRecord.tenancy_id == tenancy.id)
    ).first()
    if deposit_record is None:
        deposit_record = DepositRecord(
            tenancy_id=tenancy.id,
            created_by_user_id=created_by_user.id,
            counterparty_action_by_user_id=counterparty_action_by_user.id if counterparty_action_by_user else None,
            disputed_by_user_id=disputed_by_user.id if disputed_by_user else None,
            review_requested_by_user_id=review_requested_by_user.id if review_requested_by_user else None,
            reviewed_by_user_id=reviewed_by_user.id if reviewed_by_user else None,
            appeal_requested_by_user_id=appeal_requested_by_user.id if appeal_requested_by_user else None,
            held_amount_minor=held_amount_minor,
            proposed_return_minor=proposed_return_minor,
            withheld_amount_minor=withheld_amount_minor,
            currency_code=currency_code,
            deposit_status=deposit_status,
            move_out_date=move_out_date,
            return_due_date=return_due_date,
            returned_at=returned_at,
            settlement_stored_artifact_id=(
                settlement_stored_artifact.id if settlement_stored_artifact else None
            ),
            settlement_artifact_name=settlement_artifact_name,
            settlement_summary=settlement_summary,
            settlement_notes=settlement_notes,
            dispute_notes=dispute_notes,
            counterparty_action_at=counterparty_action_at,
            disputed_at=disputed_at,
            review_requested_at=review_requested_at,
            verdict_outcome=verdict_outcome,
            verdict_summary=verdict_summary,
            verdict_tenant_score_delta=verdict_tenant_score_delta,
            verdict_landlord_score_delta=verdict_landlord_score_delta,
            reviewed_at=reviewed_at,
            appeal_notes=appeal_notes,
            appeal_requested_at=appeal_requested_at,
        )
    else:
        deposit_record.created_by_user_id = created_by_user.id
        deposit_record.counterparty_action_by_user_id = (
            counterparty_action_by_user.id if counterparty_action_by_user else None
        )
        deposit_record.disputed_by_user_id = disputed_by_user.id if disputed_by_user else None
        deposit_record.review_requested_by_user_id = (
            review_requested_by_user.id if review_requested_by_user else None
        )
        deposit_record.reviewed_by_user_id = reviewed_by_user.id if reviewed_by_user else None
        deposit_record.appeal_requested_by_user_id = (
            appeal_requested_by_user.id if appeal_requested_by_user else None
        )
        deposit_record.held_amount_minor = held_amount_minor
        deposit_record.proposed_return_minor = proposed_return_minor
        deposit_record.withheld_amount_minor = withheld_amount_minor
        deposit_record.currency_code = currency_code
        deposit_record.deposit_status = deposit_status
        deposit_record.move_out_date = move_out_date
        deposit_record.return_due_date = return_due_date
        deposit_record.returned_at = returned_at
        deposit_record.settlement_stored_artifact_id = (
            settlement_stored_artifact.id if settlement_stored_artifact else None
        )
        deposit_record.settlement_artifact_name = settlement_artifact_name
        deposit_record.settlement_summary = settlement_summary
        deposit_record.settlement_notes = settlement_notes
        deposit_record.dispute_notes = dispute_notes
        deposit_record.counterparty_action_at = counterparty_action_at
        deposit_record.disputed_at = disputed_at
        deposit_record.review_requested_at = review_requested_at
        deposit_record.verdict_outcome = verdict_outcome
        deposit_record.verdict_summary = verdict_summary
        deposit_record.verdict_tenant_score_delta = verdict_tenant_score_delta
        deposit_record.verdict_landlord_score_delta = verdict_landlord_score_delta
        deposit_record.reviewed_at = reviewed_at
        deposit_record.appeal_notes = appeal_notes
        deposit_record.appeal_requested_at = appeal_requested_at
        deposit_record.updated_at = utcnow()

    session.add(deposit_record)
    session.flush()
    return deposit_record


def get_or_create_maintenance_ticket(
    *,
    session: Session,
    tenancy: Tenancy,
    created_by_user: User,
    acknowledged_by_user: User | None,
    resolved_by_user: User | None,
    disputed_by_user: User | None,
    title: str,
    description: str,
    priority: MaintenanceTicketPriority,
    ticket_status: MaintenanceTicketStatus,
    reported_stored_artifact: StoredArtifact | None = None,
    reported_artifact_name: str | None = None,
    landlord_response_notes: str | None = None,
    acknowledged_at=None,
    resolution_summary: str | None = None,
    resolution_stored_artifact: StoredArtifact | None = None,
    resolution_artifact_name: str | None = None,
    resolved_at=None,
    dispute_notes: str | None = None,
    disputed_at=None,
    review_requested_by_user: User | None = None,
    reviewed_by_user: User | None = None,
    appeal_requested_by_user: User | None = None,
    review_requested_at=None,
    verdict_outcome: DisputeVerdictOutcome | None = None,
    verdict_summary: str | None = None,
    verdict_tenant_score_delta: int = 0,
    verdict_landlord_score_delta: int = 0,
    reviewed_at=None,
    appeal_notes: str | None = None,
    appeal_requested_at=None,
) -> MaintenanceTicket:
    maintenance_ticket = session.exec(
        select(MaintenanceTicket).where(
            MaintenanceTicket.tenancy_id == tenancy.id,
            MaintenanceTicket.title == title,
        )
    ).first()
    if maintenance_ticket is None:
        maintenance_ticket = MaintenanceTicket(
            tenancy_id=tenancy.id,
            created_by_user_id=created_by_user.id,
            acknowledged_by_user_id=acknowledged_by_user.id if acknowledged_by_user else None,
            resolved_by_user_id=resolved_by_user.id if resolved_by_user else None,
            disputed_by_user_id=disputed_by_user.id if disputed_by_user else None,
            review_requested_by_user_id=review_requested_by_user.id if review_requested_by_user else None,
            reviewed_by_user_id=reviewed_by_user.id if reviewed_by_user else None,
            appeal_requested_by_user_id=appeal_requested_by_user.id if appeal_requested_by_user else None,
            title=title,
            description=description,
            priority=priority,
            ticket_status=ticket_status,
            reported_stored_artifact_id=(
                reported_stored_artifact.id if reported_stored_artifact else None
            ),
            reported_artifact_name=reported_artifact_name,
            landlord_response_notes=landlord_response_notes,
            acknowledged_at=acknowledged_at,
            resolution_summary=resolution_summary,
            resolution_stored_artifact_id=(
                resolution_stored_artifact.id if resolution_stored_artifact else None
            ),
            resolution_artifact_name=resolution_artifact_name,
            resolved_at=resolved_at,
            dispute_notes=dispute_notes,
            disputed_at=disputed_at,
            review_requested_at=review_requested_at,
            verdict_outcome=verdict_outcome,
            verdict_summary=verdict_summary,
            verdict_tenant_score_delta=verdict_tenant_score_delta,
            verdict_landlord_score_delta=verdict_landlord_score_delta,
            reviewed_at=reviewed_at,
            appeal_notes=appeal_notes,
            appeal_requested_at=appeal_requested_at,
        )
    else:
        maintenance_ticket.created_by_user_id = created_by_user.id
        maintenance_ticket.acknowledged_by_user_id = acknowledged_by_user.id if acknowledged_by_user else None
        maintenance_ticket.resolved_by_user_id = resolved_by_user.id if resolved_by_user else None
        maintenance_ticket.disputed_by_user_id = disputed_by_user.id if disputed_by_user else None
        maintenance_ticket.review_requested_by_user_id = (
            review_requested_by_user.id if review_requested_by_user else None
        )
        maintenance_ticket.reviewed_by_user_id = reviewed_by_user.id if reviewed_by_user else None
        maintenance_ticket.appeal_requested_by_user_id = (
            appeal_requested_by_user.id if appeal_requested_by_user else None
        )
        maintenance_ticket.description = description
        maintenance_ticket.priority = priority
        maintenance_ticket.ticket_status = ticket_status
        maintenance_ticket.reported_stored_artifact_id = (
            reported_stored_artifact.id if reported_stored_artifact else None
        )
        maintenance_ticket.reported_artifact_name = reported_artifact_name
        maintenance_ticket.landlord_response_notes = landlord_response_notes
        maintenance_ticket.acknowledged_at = acknowledged_at
        maintenance_ticket.resolution_summary = resolution_summary
        maintenance_ticket.resolution_stored_artifact_id = (
            resolution_stored_artifact.id if resolution_stored_artifact else None
        )
        maintenance_ticket.resolution_artifact_name = resolution_artifact_name
        maintenance_ticket.resolved_at = resolved_at
        maintenance_ticket.dispute_notes = dispute_notes
        maintenance_ticket.disputed_at = disputed_at
        maintenance_ticket.review_requested_at = review_requested_at
        maintenance_ticket.verdict_outcome = verdict_outcome
        maintenance_ticket.verdict_summary = verdict_summary
        maintenance_ticket.verdict_tenant_score_delta = verdict_tenant_score_delta
        maintenance_ticket.verdict_landlord_score_delta = verdict_landlord_score_delta
        maintenance_ticket.reviewed_at = reviewed_at
        maintenance_ticket.appeal_notes = appeal_notes
        maintenance_ticket.appeal_requested_at = appeal_requested_at
        maintenance_ticket.updated_at = utcnow()

    session.add(maintenance_ticket)
    session.flush()
    return maintenance_ticket


def get_or_create_listing(
    *,
    session: Session,
    organization: Organization,
    property_record: Property,
    created_by_user: User,
    title: str,
    description: str,
    listing_status: ListingStatus,
    monthly_rent_minor: int,
    deposit_minor: int,
    currency_code: str,
    minimum_tenant_score: int,
    minimum_verification_strength: int,
) -> Listing:
    listing = session.exec(
        select(Listing).where(
            Listing.organization_id == organization.id,
            Listing.property_id == property_record.id,
            Listing.title == title,
        )
    ).first()
    if listing is None:
        listing = Listing(
            organization_id=organization.id,
            property_id=property_record.id,
            created_by_user_id=created_by_user.id,
            listing_status=listing_status,
            title=title,
            description=description,
            monthly_rent_minor=monthly_rent_minor,
            deposit_minor=deposit_minor,
            currency_code=currency_code,
            minimum_tenant_score=minimum_tenant_score,
            minimum_verification_strength=minimum_verification_strength,
        )
    else:
        listing.created_by_user_id = created_by_user.id
        listing.listing_status = listing_status
        listing.description = description
        listing.monthly_rent_minor = monthly_rent_minor
        listing.deposit_minor = deposit_minor
        listing.currency_code = currency_code
        listing.minimum_tenant_score = minimum_tenant_score
        listing.minimum_verification_strength = minimum_verification_strength
        listing.updated_at = utcnow()

    session.add(listing)
    session.flush()
    return listing


def get_or_create_listing_application(
    *,
    session: Session,
    listing: Listing,
    applicant_user: User,
    submitted_by_user: User,
    application_status: ApplicationStatus,
    applicant_tenant_score: int,
    applicant_verification_strength: int,
    applicant_score_version: str,
    applicant_score_calculated_at,
    eligibility_notes: str | None,
    applicant_note: str | None,
    status_notes: str | None,
    decided_by_user: User | None,
    decided_at,
) -> ListingApplication:
    application = session.exec(
        select(ListingApplication).where(
            ListingApplication.listing_id == listing.id,
            ListingApplication.applicant_user_id == applicant_user.id,
        )
    ).first()
    if application is None:
        application = ListingApplication(
            listing_id=listing.id,
            applicant_user_id=applicant_user.id,
            submitted_by_user_id=submitted_by_user.id,
            application_status=application_status,
            applicant_tenant_score=applicant_tenant_score,
            applicant_verification_strength=applicant_verification_strength,
            applicant_score_version=applicant_score_version,
            applicant_score_calculated_at=applicant_score_calculated_at,
            eligibility_met=True,
            eligibility_notes=eligibility_notes,
            applicant_note=applicant_note,
            status_notes=status_notes,
            decided_by_user_id=decided_by_user.id if decided_by_user else None,
            decided_at=decided_at,
        )
    else:
        application.submitted_by_user_id = submitted_by_user.id
        application.application_status = application_status
        application.applicant_tenant_score = applicant_tenant_score
        application.applicant_verification_strength = applicant_verification_strength
        application.applicant_score_version = applicant_score_version
        application.applicant_score_calculated_at = applicant_score_calculated_at
        application.eligibility_met = True
        application.eligibility_notes = eligibility_notes
        application.applicant_note = applicant_note
        application.status_notes = status_notes
        application.decided_by_user_id = decided_by_user.id if decided_by_user else None
        application.decided_at = decided_at
        application.updated_at = utcnow()

    session.add(application)
    session.flush()
    return application


def get_or_create_consent(
    *,
    session: Session,
    subject_user: User,
    granted_by_user: User,
    grantee_organization: Organization,
    expires_at,
    last_validated_at=None,
) -> TrustReportConsent:
    share_token_hash = hash_token(DEMO_SHARE_TOKEN)
    consent = session.exec(
        select(TrustReportConsent).where(
            TrustReportConsent.share_token_hash == share_token_hash
        )
    ).first()
    access_code_hash = hash_password(DEMO_ACCESS_CODE)

    if consent is None:
        consent = TrustReportConsent(
            subject_user_id=subject_user.id,
            granted_by_user_id=granted_by_user.id,
            grantee_organization_id=grantee_organization.id,
            scope=ConsentScope.TRUST_REPORT_READ,
            share_token_hash=share_token_hash,
            access_code_hash=access_code_hash,
            failed_access_attempt_count=0,
            last_access_attempt_at=last_validated_at,
            access_locked_until=None,
            last_validated_at=last_validated_at,
            expires_at=expires_at,
            revoked_at=None,
        )
    else:
        consent.subject_user_id = subject_user.id
        consent.granted_by_user_id = granted_by_user.id
        consent.grantee_organization_id = grantee_organization.id
        consent.scope = ConsentScope.TRUST_REPORT_READ
        consent.access_code_hash = access_code_hash
        consent.failed_access_attempt_count = 0
        consent.last_access_attempt_at = last_validated_at
        consent.access_locked_until = None
        consent.last_validated_at = last_validated_at
        consent.expires_at = expires_at
        consent.revoked_at = None
        consent.updated_at = utcnow()

    session.add(consent)
    session.flush()
    return consent


def get_or_create_trust_check(
    *,
    session: Session,
    organization: Organization,
    consent: TrustReportConsent,
    requested_by_user: User,
    subject_user: User,
) -> AgencyTrustCheck:
    trust_check = session.exec(
        select(AgencyTrustCheck).where(
            AgencyTrustCheck.organization_id == organization.id,
            AgencyTrustCheck.consent_id == consent.id,
            AgencyTrustCheck.requested_by_user_id == requested_by_user.id,
            AgencyTrustCheck.subject_user_id == subject_user.id,
        )
    ).first()
    if trust_check is None:
        trust_check = AgencyTrustCheck(
            organization_id=organization.id,
            consent_id=consent.id,
            requested_by_user_id=requested_by_user.id,
            subject_user_id=subject_user.id,
            scope=ConsentScope.TRUST_REPORT_READ,
        )
    else:
        trust_check.scope = ConsentScope.TRUST_REPORT_READ
        trust_check.updated_at = utcnow()

    session.add(trust_check)
    session.flush()
    return trust_check


def ensure_trust_event(
    *,
    session: Session,
    subject_user_id,
    actor_user_id,
    event_type: TrustEventType,
    verification_status: VerificationStatus,
    summary: str,
    details: str | None = None,
    tenancy_id=None,
    history_import_id=None,
    reference_request_id=None,
    evidence_document_id=None,
    payment_record_id=None,
    deposit_record_id=None,
    maintenance_ticket_id=None,
    listing_id=None,
) -> TrustEvent:
    trust_event = session.exec(
        select(TrustEvent).where(
            TrustEvent.subject_user_id == subject_user_id,
            nullable_match(TrustEvent.actor_user_id, actor_user_id),
            TrustEvent.event_type == event_type,
            TrustEvent.summary == summary,
            nullable_match(TrustEvent.tenancy_id, tenancy_id),
            nullable_match(TrustEvent.history_import_id, history_import_id),
            nullable_match(TrustEvent.reference_request_id, reference_request_id),
            nullable_match(TrustEvent.evidence_document_id, evidence_document_id),
            nullable_match(TrustEvent.payment_record_id, payment_record_id),
            nullable_match(TrustEvent.deposit_record_id, deposit_record_id),
            nullable_match(TrustEvent.maintenance_ticket_id, maintenance_ticket_id),
            nullable_match(TrustEvent.listing_id, listing_id),
        )
    ).first()
    if trust_event is None:
        trust_event = TrustEvent(
            subject_user_id=subject_user_id,
            actor_user_id=actor_user_id,
            tenancy_id=tenancy_id,
            history_import_id=history_import_id,
            reference_request_id=reference_request_id,
            evidence_document_id=evidence_document_id,
            payment_record_id=payment_record_id,
            deposit_record_id=deposit_record_id,
            maintenance_ticket_id=maintenance_ticket_id,
            listing_id=listing_id,
            event_type=event_type,
            verification_status=verification_status,
            summary=summary,
            details=details,
        )
    else:
        trust_event.verification_status = verification_status
        trust_event.details = details
        trust_event.updated_at = utcnow()

    session.add(trust_event)
    session.flush()
    return trust_event


def ensure_audit_log(
    *,
    session: Session,
    action_type: AuditActionType,
    outcome_status: AuditOutcomeStatus,
    actor_user_id=None,
    organization_id=None,
    subject_user_id=None,
    target_type: str | None = None,
    target_id=None,
    details: str | None = None,
) -> AuditLog:
    target_id_str = str(target_id) if target_id is not None else None
    audit_log = session.exec(
        select(AuditLog).where(
            AuditLog.action_type == action_type,
            AuditLog.outcome_status == outcome_status,
            nullable_match(AuditLog.actor_user_id, actor_user_id),
            nullable_match(AuditLog.organization_id, organization_id),
            nullable_match(AuditLog.subject_user_id, subject_user_id),
            nullable_match(AuditLog.target_type, target_type),
            nullable_match(AuditLog.target_id, target_id_str),
        )
    ).first()
    if audit_log is None:
        audit_log = append_audit_log(
            session=session,
            action_type=action_type,
            outcome_status=outcome_status,
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            subject_user_id=subject_user_id,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
    else:
        audit_log.details = details
        audit_log.updated_at = utcnow()
        session.add(audit_log)
        session.flush()
    return audit_log


def get_or_create_automation_task(
    *,
    session: Session,
    task_type: AutomationTaskType,
    status: AutomationTaskStatus,
    title: str,
    details: str | None,
    result_notes: str | None,
    subject_user: User | None,
    organization: Organization | None,
    requested_by_user: User | None,
    consent: TrustReportConsent | None,
    dedupe_key: str,
    scheduled_for,
) -> AutomationTask:
    automation_task = session.exec(
        select(AutomationTask).where(AutomationTask.dedupe_key == dedupe_key)
    ).first()
    if automation_task is None:
        automation_task = AutomationTask(
            task_type=task_type,
            status=status,
            title=title,
            details=details,
            result_notes=result_notes,
            subject_user_id=subject_user.id if subject_user else None,
            organization_id=organization.id if organization else None,
            consent_id=consent.id if consent else None,
            requested_by_user_id=requested_by_user.id if requested_by_user else None,
            dedupe_key=dedupe_key,
            scheduled_for=scheduled_for,
        )
    else:
        automation_task.task_type = task_type
        automation_task.status = status
        automation_task.title = title
        automation_task.details = details
        automation_task.result_notes = result_notes
        automation_task.subject_user_id = subject_user.id if subject_user else None
        automation_task.organization_id = organization.id if organization else None
        automation_task.consent_id = consent.id if consent else None
        automation_task.requested_by_user_id = requested_by_user.id if requested_by_user else None
        automation_task.processed_by_user_id = None
        automation_task.started_at = None
        automation_task.completed_at = None
        automation_task.last_error = None
        automation_task.attempt_count = 0
        automation_task.scheduled_for = scheduled_for
        automation_task.updated_at = utcnow()

    session.add(automation_task)
    session.flush()
    return automation_task


def seed_demo_environment(*, session: Session) -> DemoSeedSummary:
    current_time = utcnow()

    admin_user = get_or_create_user(
        session=session,
        email=DEMO_ADMIN.email,
        full_name=DEMO_ADMIN.label,
        password=DEMO_ADMIN.password,
        system_role=SystemRole.ADMIN,
        legacy_emails=DEMO_ADMIN.legacy_emails,
    )
    reviewer_user = get_or_create_user(
        session=session,
        email=DEMO_REVIEWER.email,
        full_name=DEMO_REVIEWER.label,
        password=DEMO_REVIEWER.password,
        system_role=SystemRole.REVIEWER,
        legacy_emails=DEMO_REVIEWER.legacy_emails,
    )
    agency_owner_user = get_or_create_user(
        session=session,
        email=DEMO_AGENCY_OWNER.email,
        full_name=DEMO_AGENCY_OWNER.label,
        password=DEMO_AGENCY_OWNER.password,
        workspace_roles=(AccountWorkspaceRole.AGENCY,),
        legacy_emails=DEMO_AGENCY_OWNER.legacy_emails,
    )
    tenant_user = get_or_create_user(
        session=session,
        email=DEMO_TENANT.email,
        full_name=DEMO_TENANT.label,
        password=DEMO_TENANT.password,
        legacy_emails=DEMO_TENANT.legacy_emails,
    )
    landlord_user = get_or_create_user(
        session=session,
        email=DEMO_LANDLORD.email,
        full_name=DEMO_LANDLORD.label,
        password=DEMO_LANDLORD.password,
        workspace_roles=(AccountWorkspaceRole.LANDLORD,),
        legacy_emails=DEMO_LANDLORD.legacy_emails,
    )

    internal_org = get_or_create_organization(
        session=session,
        name="Trust Ledger Internal Ops",
        slug="trust-ledger-internal-ops",
        organization_type=OrganizationType.INTERNAL,
    )
    agency_org = get_or_create_organization(
        session=session,
        name="Demo Agency Partners",
        slug="demo-agency-partners",
        organization_type=OrganizationType.AGENCY,
    )

    ensure_membership(
        session=session,
        user=admin_user,
        organization=internal_org,
        role=OrganizationMembershipRole.OWNER,
    )
    ensure_membership(
        session=session,
        user=reviewer_user,
        organization=internal_org,
        role=OrganizationMembershipRole.REVIEWER,
    )
    ensure_membership(
        session=session,
        user=agency_owner_user,
        organization=agency_org,
        role=OrganizationMembershipRole.OWNER,
    )
    ensure_membership(
        session=session,
        user=agency_owner_user,
        organization=internal_org,
        role=OrganizationMembershipRole.MEMBER,
    )

    active_property = get_or_create_property(
        session=session,
        created_by_user=landlord_user,
        property_label="Harbor Flat",
        address_line1="14 Seaside Avenue",
        city="Athens",
        country_code="GR",
    )
    agency_property = get_or_create_property(
        session=session,
        created_by_user=agency_owner_user,
        property_label="Agency Showcase Loft",
        address_line1="28 Market Lane",
        city="Athens",
        country_code="GR",
    )
    review_property = get_or_create_property(
        session=session,
        created_by_user=landlord_user,
        property_label="Old Town Duplex",
        address_line1="61 Archive Walk",
        city="Athens",
        country_code="GR",
    )
    queue_property = get_or_create_property(
        session=session,
        created_by_user=landlord_user,
        property_label="Hillside Studio",
        address_line1="5 Queue Terrace",
        city="Athens",
        country_code="GR",
    )

    for property_record, tags in (
        (active_property, ["managed", "priority", "waterfront"]),
        (agency_property, ["showcase", "listing"]),
        (review_property, ["completed-case", "deposit-review"]),
        (queue_property, ["review-queue", "maintenance"]),
    ):
        property_record.custom_tags_json = serialize_property_tags(tags)
        property_record.updated_at = current_time

    for property_record in (active_property, review_property, queue_property):
        property_record.management_mode = PropertyManagementMode.AGENCY_MANAGED.value
        property_record.assigned_agency_organization_id = agency_org.id
        property_record.assigned_agency_user_id = agency_owner_user.id
        property_record.assigned_tenant_user_id = tenant_user.id
        session.add(property_record)
    agency_property.management_mode = PropertyManagementMode.OWNER_MANAGED.value
    session.add(agency_property)
    session.flush()

    history_import = get_or_create_history_import(
        session=session,
        subject_user=tenant_user,
        created_by_user=tenant_user,
        title="Imported Rental History 2024",
        summary="Cold-start rental history bundle imported for the demo tenant.",
        status=HistoryImportStatus.ACCEPTED,
        submitted_at=current_time - timedelta(days=195),
        reviewed_at=current_time - timedelta(days=190),
        reviewed_by_user=reviewer_user,
        review_notes="Accepted historical package for the demo tenant.",
    )

    imported_tenancy = get_or_create_tenancy(
        session=session,
        property_label="Archive Flat",
        address_line1="8 Archive Street",
        city="Athens",
        country_code="GR",
        tenancy_status=TenancyStatus.ENDED,
        verification_status=VerificationStatus.REVIEWED,
        lease_start_date=date(2024, 1, 1),
        lease_end_date=date(2024, 12, 31),
        monthly_rent_minor=82000,
        deposit_minor=164000,
        currency_code="EUR",
        tenant_user=tenant_user,
        landlord_user=landlord_user,
        created_by_user=tenant_user,
        history_import=history_import,
        reviewed_by_user=reviewer_user,
        review_requested_at=current_time - timedelta(days=193),
        reviewed_at=current_time - timedelta(days=190),
        review_notes="Reviewed historical tenancy for cold-start trust data.",
    )

    current_tenancy = get_or_create_tenancy(
        session=session,
        property_label=active_property.property_label,
        address_line1=active_property.address_line1,
        city=active_property.city,
        country_code=active_property.country_code,
        tenancy_status=TenancyStatus.ACTIVE,
        verification_status=VerificationStatus.VERIFIED,
        lease_start_date=date(2026, 1, 1),
        lease_end_date=date(2026, 12, 31),
        monthly_rent_minor=95000,
        deposit_minor=190000,
        currency_code="EUR",
        tenant_user=tenant_user,
        landlord_user=landlord_user,
        created_by_user=tenant_user,
        property_record=active_property,
        counterparty_confirmed_by_user=landlord_user,
        counterparty_confirmed_at=current_time - timedelta(days=95),
        review_requested_at=current_time - timedelta(days=94),
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=92),
        review_notes="Verified current tenancy for the live demo.",
    )
    review_tenancy = get_or_create_tenancy(
        session=session,
        property_label=review_property.property_label,
        address_line1=review_property.address_line1,
        city=review_property.city,
        country_code=review_property.country_code,
        tenancy_status=TenancyStatus.ENDED,
        verification_status=VerificationStatus.VERIFIED,
        lease_start_date=date(2025, 1, 1),
        lease_end_date=date(2025, 12, 31),
        monthly_rent_minor=91000,
        deposit_minor=182000,
        currency_code="EUR",
        tenant_user=tenant_user,
        landlord_user=landlord_user,
        created_by_user=landlord_user,
        property_record=review_property,
        counterparty_confirmed_by_user=tenant_user,
        counterparty_confirmed_at=current_time - timedelta(days=140),
        review_requested_at=current_time - timedelta(days=138),
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=136),
        review_notes="Reviewed ended tenancy kept to demonstrate verdict and appeal workflows.",
    )
    queue_tenancy = get_or_create_tenancy(
        session=session,
        property_label=queue_property.property_label,
        address_line1=queue_property.address_line1,
        city=queue_property.city,
        country_code=queue_property.country_code,
        tenancy_status=TenancyStatus.ENDED,
        verification_status=VerificationStatus.VERIFIED,
        lease_start_date=date(2025, 6, 1),
        lease_end_date=date(2026, 2, 28),
        monthly_rent_minor=88000,
        deposit_minor=176000,
        currency_code="EUR",
        tenant_user=tenant_user,
        landlord_user=landlord_user,
        created_by_user=tenant_user,
        property_record=queue_property,
        counterparty_confirmed_by_user=landlord_user,
        counterparty_confirmed_at=current_time - timedelta(days=70),
        review_requested_at=current_time - timedelta(days=69),
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=66),
        review_notes="Reviewed ended tenancy kept to populate the live dispute queues.",
    )

    imported_lease_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=imported_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="evidence_document",
        original_file_name="archive-lease.pdf",
    )
    current_rent_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="evidence_document",
        original_file_name="march-2026-rent-receipt.pdf",
    )
    utility_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="evidence_document",
        original_file_name="utility-closeout-q1-2026.pdf",
    )
    pending_landlord_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="evidence_document",
        original_file_name="repair-invoice-pending.pdf",
    )
    reference_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="evidence_document",
        original_file_name="landlord-reference.pdf",
    )
    current_identity_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="evidence_document",
        original_file_name="tenant-identity-check.pdf",
    )
    review_deposit_evidence_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=review_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="evidence_document",
        original_file_name="deposit-deductions-package.pdf",
    )
    queue_rent_evidence_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="evidence_document",
        original_file_name="queue-rent-proof.pdf",
    )
    current_payment_proof_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="payment_proof",
        original_file_name="april-rent-transfer.pdf",
    )
    current_maintenance_report_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="maintenance_report",
        original_file_name="kitchen-leak-photo.png",
    )
    current_maintenance_resolution_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=current_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="maintenance_resolution",
        original_file_name="repair-complete-photo.png",
    )
    review_payment_proof_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=review_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="payment_proof",
        original_file_name="november-rent-proof.pdf",
    )
    review_payment_counterparty_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=review_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="payment_counterparty",
        original_file_name="november-rent-rejection.pdf",
    )
    review_deposit_settlement_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=review_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="deposit_settlement",
        original_file_name="review-deposit-settlement.pdf",
    )
    review_maintenance_report_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=review_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="maintenance_report",
        original_file_name="boiler-damage-photo.png",
    )
    review_maintenance_resolution_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=review_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="maintenance_resolution",
        original_file_name="boiler-repair-report.pdf",
    )
    queue_payment_proof_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="payment_proof",
        original_file_name="march-rent-proof.pdf",
    )
    queue_payment_counterparty_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="payment_counterparty",
        original_file_name="march-rent-rejection.pdf",
    )
    queue_deposit_settlement_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="deposit_settlement",
        original_file_name="queue-move-out-settlement.pdf",
    )
    queue_maintenance_report_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=tenant_user,
        artifact_purpose="maintenance_report",
        original_file_name="mold-report-photo.png",
    )
    queue_maintenance_resolution_artifact = get_or_create_stored_artifact(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=landlord_user,
        artifact_purpose="maintenance_resolution",
        original_file_name="mold-remediation-report.pdf",
    )

    imported_lease_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=imported_tenancy,
        subject_user=tenant_user,
        uploaded_by_user=tenant_user,
        document_type=EvidenceDocumentType.LEASE_AGREEMENT,
        artifact_name="archive-lease.pdf",
        summary="Historical lease agreement used to support the accepted import bundle.",
        review_status=EvidenceReviewStatus.ACCEPTED,
        review_requested_at=current_time - timedelta(days=194),
        stored_artifact=imported_lease_artifact,
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=190),
        review_notes="Accepted lease agreement for the imported history bundle.",
        issuer_name="Archive Flat Holdings",
        document_date=date(2024, 1, 1),
    )
    current_rent_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=current_tenancy,
        subject_user=tenant_user,
        uploaded_by_user=tenant_user,
        document_type=EvidenceDocumentType.RENT_RECEIPT,
        artifact_name="march-2026-rent-receipt.pdf",
        summary="Accepted rent receipt for the current verified tenancy.",
        review_status=EvidenceReviewStatus.ACCEPTED,
        review_requested_at=current_time - timedelta(days=40),
        stored_artifact=current_rent_artifact,
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=38),
        review_notes="Accepted recurring rent proof for the tenant.",
        issuer_name="Demo Landlord Holdings",
        document_date=date(2026, 3, 5),
        amount_minor=95000,
        currency_code="EUR",
        external_reference="RENT-2026-03",
    )
    utility_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=current_tenancy,
        subject_user=tenant_user,
        uploaded_by_user=tenant_user,
        document_type=EvidenceDocumentType.UTILITY_SETTLEMENT,
        artifact_name="utility-closeout-q1-2026.pdf",
        summary="Accepted utility settlement to strengthen the tenant trust file.",
        review_status=EvidenceReviewStatus.ACCEPTED,
        review_requested_at=current_time - timedelta(days=25),
        stored_artifact=utility_artifact,
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=23),
        review_notes="Accepted utility settlement evidence.",
        issuer_name="Athens Utility Co.",
        document_date=date(2026, 3, 20),
        amount_minor=14600,
        currency_code="EUR",
        external_reference="UTIL-2026-Q1",
    )
    pending_landlord_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=current_tenancy,
        subject_user=landlord_user,
        uploaded_by_user=landlord_user,
        document_type=EvidenceDocumentType.OTHER,
        artifact_name="repair-invoice-pending.pdf",
        summary="Pending repair invoice kept in the queue for reviewer demo visibility.",
        review_status=EvidenceReviewStatus.SUBMITTED,
        review_requested_at=current_time - timedelta(hours=8),
        stored_artifact=pending_landlord_artifact,
        review_notes="Awaiting reviewer decision.",
        issuer_name="Plumbing Works Ltd.",
        document_date=date(2026, 4, 10),
        amount_minor=32000,
        currency_code="EUR",
        external_reference="PLUMB-4401",
    )

    reference_request = get_or_create_reference_request(
        session=session,
        tenancy=current_tenancy,
        subject_user=tenant_user,
        requested_by_user=tenant_user,
        requested_from_user=landlord_user,
        message="Please confirm that rent and maintenance communication have been reliable.",
        status=ReferenceRequestStatus.FULFILLED,
        fulfilled_at=current_time - timedelta(days=18),
    )
    reference_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=current_tenancy,
        subject_user=tenant_user,
        uploaded_by_user=landlord_user,
        document_type=EvidenceDocumentType.LANDLORD_REFERENCE,
        artifact_name="landlord-reference.pdf",
        summary="Counterparty reference confirming strong payment behavior and communication.",
        review_status=EvidenceReviewStatus.ACCEPTED,
        review_requested_at=current_time - timedelta(days=18),
        stored_artifact=reference_artifact,
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=16),
        review_notes="Accepted counterparty reference.",
        issuer_name="Demo Landlord Holdings",
        document_date=date(2026, 3, 24),
        reference_request=reference_request,
    )
    current_identity_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=current_tenancy,
        subject_user=tenant_user,
        uploaded_by_user=tenant_user,
        document_type=EvidenceDocumentType.IDENTITY_DOCUMENT,
        artifact_name="tenant-identity-check.pdf",
        summary="Identity document retained to support the verified trust profile.",
        review_status=EvidenceReviewStatus.ACCEPTED,
        review_requested_at=current_time - timedelta(days=60),
        stored_artifact=current_identity_artifact,
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=58),
        review_notes="Identity evidence accepted for the demo user.",
        issuer_name="Greek Citizen Registry",
        document_date=date(2025, 12, 15),
    )
    review_deposit_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=review_tenancy,
        subject_user=tenant_user,
        uploaded_by_user=landlord_user,
        document_type=EvidenceDocumentType.DEPOSIT_RETURN,
        artifact_name="deposit-deductions-package.pdf",
        summary="Deposit deduction package retained for the verdict-ready deposit dispute.",
        review_status=EvidenceReviewStatus.ACCEPTED,
        review_requested_at=current_time - timedelta(days=120),
        stored_artifact=review_deposit_evidence_artifact,
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=118),
        review_notes="Accepted deduction package before dispute escalation.",
        issuer_name="Demo Landlord Holdings",
        document_date=date(2025, 12, 20),
        amount_minor=62000,
        currency_code="EUR",
        external_reference="DEP-2025-EXIT",
    )
    queue_rent_evidence = get_or_create_evidence_document(
        session=session,
        tenancy=queue_tenancy,
        subject_user=tenant_user,
        uploaded_by_user=tenant_user,
        document_type=EvidenceDocumentType.RENT_RECEIPT,
        artifact_name="queue-rent-proof.pdf",
        summary="Rent proof used in the payment dispute that is still waiting for reviewer action.",
        review_status=EvidenceReviewStatus.ACCEPTED,
        review_requested_at=current_time - timedelta(days=31),
        stored_artifact=queue_rent_evidence_artifact,
        reviewed_by_user=reviewer_user,
        reviewed_at=current_time - timedelta(days=29),
        review_notes="Accepted payment evidence prior to dispute escalation.",
        issuer_name="Queue Terrace Landlord",
        document_date=date(2026, 3, 4),
        amount_minor=88000,
        currency_code="EUR",
        external_reference="QUEUE-2026-03",
    )

    payment_record = get_or_create_payment_record(
        session=session,
        tenancy=current_tenancy,
        payer_user=tenant_user,
        payee_user=landlord_user,
        created_by_user=tenant_user,
        payment_type=PaymentRecordType.RENT,
        payment_status=PaymentRecordStatus.CONFIRMED,
        proof_status=PaymentProofStatus.COUNTERPARTY_CONFIRMED,
        amount_minor=95000,
        currency_code="EUR",
        due_date=date(2026, 4, 5),
        period_start_date=date(2026, 4, 1),
        period_end_date=date(2026, 4, 30),
        paid_at=current_time - timedelta(days=6),
        proof_stored_artifact=current_payment_proof_artifact,
        proof_artifact_name="april-rent-transfer.pdf",
        proof_summary="Bank transfer screenshot for April 2026 rent.",
        external_reference="APR-2026-RENT",
        counterparty_notes="Confirmed against the landlord ledger.",
        counterparty_action_by_user=landlord_user,
        counterparty_action_at=current_time - timedelta(days=5),
    )
    payment_verdict_record = get_or_create_payment_record(
        session=session,
        tenancy=review_tenancy,
        payer_user=tenant_user,
        payee_user=landlord_user,
        created_by_user=tenant_user,
        payment_type=PaymentRecordType.RENT,
        payment_status=PaymentRecordStatus.VERDICT_ISSUED,
        proof_status=PaymentProofStatus.PROVIDED,
        amount_minor=91000,
        currency_code="EUR",
        due_date=date(2025, 11, 5),
        period_start_date=date(2025, 11, 1),
        period_end_date=date(2025, 11, 30),
        paid_at=current_time - timedelta(days=125),
        proof_stored_artifact=review_payment_proof_artifact,
        counterparty_stored_artifact=review_payment_counterparty_artifact,
        proof_artifact_name="november-rent-proof.pdf",
        proof_summary="The tenant claims rent was paid with the correct reference.",
        external_reference="NOV-2025-RENT",
        counterparty_notes="Landlord could not reconcile the payment reference at first review.",
        counterparty_action_by_user=landlord_user,
        counterparty_action_at=current_time - timedelta(days=123),
        disputed_by_user=tenant_user,
        review_requested_by_user=tenant_user,
        reviewed_by_user=reviewer_user,
        dispute_notes="Tenant disputes the rejection and points to the supplied transfer record.",
        disputed_at=current_time - timedelta(days=122),
        review_requested_at=current_time - timedelta(days=122),
        verdict_outcome=DisputeVerdictOutcome.FAVORS_LANDLORD,
        verdict_summary="Reviewer kept the rejection because the submitted proof does not match the payee ledger exactly.",
        verdict_tenant_score_delta=-30,
        verdict_landlord_score_delta=12,
        reviewed_at=current_time - timedelta(days=119),
    )
    payment_queue_record = get_or_create_payment_record(
        session=session,
        tenancy=queue_tenancy,
        payer_user=tenant_user,
        payee_user=landlord_user,
        created_by_user=tenant_user,
        payment_type=PaymentRecordType.RENT,
        payment_status=PaymentRecordStatus.UNDER_REVIEW,
        proof_status=PaymentProofStatus.PROVIDED,
        amount_minor=88000,
        currency_code="EUR",
        due_date=date(2026, 3, 5),
        period_start_date=date(2026, 3, 1),
        period_end_date=date(2026, 3, 31),
        paid_at=current_time - timedelta(days=34),
        proof_stored_artifact=queue_payment_proof_artifact,
        counterparty_stored_artifact=queue_payment_counterparty_artifact,
        proof_artifact_name="march-rent-proof.pdf",
        proof_summary="Tenant uploaded transfer proof and bank note for the March payment.",
        external_reference="MAR-2026-QUEUE",
        counterparty_notes="Landlord flagged a mismatch between the stated payer name and transfer details.",
        counterparty_action_by_user=landlord_user,
        counterparty_action_at=current_time - timedelta(days=33),
        disputed_by_user=tenant_user,
        review_requested_by_user=tenant_user,
        dispute_notes="Tenant disputes the rejection and asks for reviewer confirmation.",
        disputed_at=current_time - timedelta(days=32),
        review_requested_at=current_time - timedelta(days=32),
    )

    deposit_record = get_or_create_deposit_record(
        session=session,
        tenancy=current_tenancy,
        created_by_user=landlord_user,
        held_amount_minor=190000,
        proposed_return_minor=0,
        withheld_amount_minor=0,
        currency_code="EUR",
        deposit_status=DepositStatus.HELD,
    )
    deposit_verdict_record = get_or_create_deposit_record(
        session=session,
        tenancy=review_tenancy,
        created_by_user=landlord_user,
        held_amount_minor=182000,
        proposed_return_minor=120000,
        withheld_amount_minor=62000,
        currency_code="EUR",
        deposit_status=DepositStatus.VERDICT_ISSUED,
        move_out_date=date(2025, 12, 31),
        return_due_date=date(2026, 1, 20),
        returned_at=current_time - timedelta(days=121),
        settlement_stored_artifact=review_deposit_settlement_artifact,
        settlement_artifact_name="review-deposit-settlement.pdf",
        settlement_summary="Landlord submitted a deduction package for repainting and carpet replacement.",
        settlement_notes="Tenant disputed most of the withholding after move-out.",
        dispute_notes="Tenant disputes the size of the deductions and says the wear was normal.",
        counterparty_action_by_user=landlord_user,
        counterparty_action_at=current_time - timedelta(days=124),
        disputed_by_user=tenant_user,
        review_requested_by_user=tenant_user,
        reviewed_by_user=reviewer_user,
        disputed_at=current_time - timedelta(days=123),
        review_requested_at=current_time - timedelta(days=123),
        verdict_outcome=DisputeVerdictOutcome.FAVORS_LANDLORD,
        verdict_summary="Reviewer accepted most deductions after reviewing the check-out evidence bundle.",
        verdict_tenant_score_delta=-18,
        verdict_landlord_score_delta=8,
        reviewed_at=current_time - timedelta(days=119),
    )
    deposit_queue_record = get_or_create_deposit_record(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=landlord_user,
        held_amount_minor=176000,
        proposed_return_minor=92000,
        withheld_amount_minor=84000,
        currency_code="EUR",
        deposit_status=DepositStatus.UNDER_REVIEW,
        move_out_date=date(2026, 2, 28),
        return_due_date=date(2026, 3, 20),
        returned_at=current_time - timedelta(days=27),
        settlement_stored_artifact=queue_deposit_settlement_artifact,
        settlement_artifact_name="queue-move-out-settlement.pdf",
        settlement_summary="Move-out settlement proposes major cleaning and mold remediation deductions.",
        settlement_notes="Tenant says the property defects predated move-out.",
        dispute_notes="Tenant disputes the settlement and requests reviewer involvement.",
        counterparty_action_by_user=landlord_user,
        counterparty_action_at=current_time - timedelta(days=30),
        disputed_by_user=tenant_user,
        review_requested_by_user=tenant_user,
        disputed_at=current_time - timedelta(days=29),
        review_requested_at=current_time - timedelta(days=29),
    )

    maintenance_ticket = get_or_create_maintenance_ticket(
        session=session,
        tenancy=current_tenancy,
        created_by_user=tenant_user,
        acknowledged_by_user=landlord_user,
        resolved_by_user=landlord_user,
        disputed_by_user=None,
        title="Kitchen leak repaired",
        description="Minor leak under the kitchen sink reported and resolved within the week.",
        priority=MaintenanceTicketPriority.NORMAL,
        ticket_status=MaintenanceTicketStatus.RESOLVED,
        reported_stored_artifact=current_maintenance_report_artifact,
        reported_artifact_name="kitchen-leak-photo.png",
        landlord_response_notes="Plumber appointment booked for the next business day.",
        acknowledged_at=current_time - timedelta(days=12),
        resolution_summary="Pipe joint replaced and cabinet dried.",
        resolution_stored_artifact=current_maintenance_resolution_artifact,
        resolution_artifact_name="repair-complete-photo.png",
        resolved_at=current_time - timedelta(days=9),
    )
    maintenance_verdict_ticket = get_or_create_maintenance_ticket(
        session=session,
        tenancy=review_tenancy,
        created_by_user=tenant_user,
        acknowledged_by_user=landlord_user,
        resolved_by_user=landlord_user,
        disputed_by_user=tenant_user,
        review_requested_by_user=tenant_user,
        reviewed_by_user=reviewer_user,
        title="Boiler outage dispute",
        description="Tenant reported a boiler outage and later disputed the landlord's response timeline.",
        priority=MaintenanceTicketPriority.HIGH,
        ticket_status=MaintenanceTicketStatus.VERDICT_ISSUED,
        reported_stored_artifact=review_maintenance_report_artifact,
        reported_artifact_name="boiler-damage-photo.png",
        landlord_response_notes="Emergency contractor was called, but the tenant says the response was too slow.",
        acknowledged_at=current_time - timedelta(days=132),
        resolution_summary="Boiler replacement completed after contractor attendance.",
        resolution_stored_artifact=review_maintenance_resolution_artifact,
        resolution_artifact_name="boiler-repair-report.pdf",
        resolved_at=current_time - timedelta(days=129),
        dispute_notes="Tenant argues that the heating outage lasted longer than reasonably acceptable.",
        disputed_at=current_time - timedelta(days=128),
        review_requested_at=current_time - timedelta(days=128),
        verdict_outcome=DisputeVerdictOutcome.SHARED_FAULT,
        verdict_summary="Reviewer found delayed access and delayed contractor scheduling contributed to the outage duration.",
        verdict_tenant_score_delta=-6,
        verdict_landlord_score_delta=-10,
        reviewed_at=current_time - timedelta(days=124),
    )
    maintenance_queue_ticket = get_or_create_maintenance_ticket(
        session=session,
        tenancy=queue_tenancy,
        created_by_user=tenant_user,
        acknowledged_by_user=landlord_user,
        resolved_by_user=landlord_user,
        disputed_by_user=tenant_user,
        review_requested_by_user=tenant_user,
        title="Bedroom mold remediation dispute",
        description="Tenant disputes whether the mold remediation response was fast enough and complete enough.",
        priority=MaintenanceTicketPriority.HIGH,
        ticket_status=MaintenanceTicketStatus.UNDER_REVIEW,
        reported_stored_artifact=queue_maintenance_report_artifact,
        reported_artifact_name="mold-report-photo.png",
        landlord_response_notes="Landlord arranged remediation but the tenant says follow-up drying was incomplete.",
        acknowledged_at=current_time - timedelta(days=24),
        resolution_summary="Vendor performed initial remediation and surface treatment.",
        resolution_stored_artifact=queue_maintenance_resolution_artifact,
        resolution_artifact_name="mold-remediation-report.pdf",
        resolved_at=current_time - timedelta(days=21),
        dispute_notes="Tenant requests reviewer intervention on remediation quality and speed.",
        disputed_at=current_time - timedelta(days=20),
        review_requested_at=current_time - timedelta(days=20),
    )

    def ensure_party_event(
        *,
        tenancy: Tenancy,
        actor_user: User,
        event_type: TrustEventType,
        summary: str,
        details: str | None = None,
        verification_status: VerificationStatus | None = None,
        payment_record: PaymentRecord | None = None,
        deposit_record: DepositRecord | None = None,
        maintenance_record: MaintenanceTicket | None = None,
    ) -> None:
        for subject_user in (tenant_user, landlord_user):
            ensure_trust_event(
                session=session,
                subject_user_id=subject_user.id,
                actor_user_id=actor_user.id,
                event_type=event_type,
                verification_status=(
                    verification_status
                    if verification_status is not None
                    else (
                        VerificationStatus.SELF_REPORTED
                        if subject_user.id == actor_user.id
                        else VerificationStatus.COUNTERPARTY_CONFIRMED
                    )
                ),
                summary=summary,
                tenancy_id=tenancy.id,
                payment_record_id=payment_record.id if payment_record else None,
                deposit_record_id=deposit_record.id if deposit_record else None,
                maintenance_ticket_id=maintenance_record.id if maintenance_record else None,
                details=details,
            )

    for subject_user in (tenant_user, landlord_user):
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=tenant_user.id,
            event_type=TrustEventType.TENANCY_CREATED,
            verification_status=VerificationStatus.SELF_REPORTED,
            summary="Current tenancy created in the trust ledger.",
            tenancy_id=current_tenancy.id,
            details="The live tenancy was created by the tenant for the demo workspace.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=landlord_user.id,
            event_type=TrustEventType.TENANCY_COUNTERPARTY_CONFIRMED,
            verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
            summary="Current tenancy was counterparty confirmed.",
            tenancy_id=current_tenancy.id,
            details="The landlord confirmed the tenancy details before reviewer verification.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=tenant_user.id,
            event_type=TrustEventType.TENANCY_REVIEW_REQUESTED,
            verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
            summary="Current tenancy was submitted for reviewer verification.",
            tenancy_id=current_tenancy.id,
            details="The tenancy moved into the reviewer queue for final verification.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=reviewer_user.id,
            event_type=TrustEventType.TENANCY_REVIEWED,
            verification_status=VerificationStatus.VERIFIED,
            summary="Current tenancy was verified by internal review.",
            tenancy_id=current_tenancy.id,
            details="Internal reviewer marked the active tenancy as verified.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=tenant_user.id,
            event_type=TrustEventType.PAYMENT_CREATED,
            verification_status=VerificationStatus.SELF_REPORTED,
            summary="April 2026 rent payment was recorded.",
            tenancy_id=current_tenancy.id,
            payment_record_id=payment_record.id,
            details="The tenant recorded the April rent obligation and payment.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=tenant_user.id,
            event_type=TrustEventType.PAYMENT_PROOF_SUBMITTED,
            verification_status=VerificationStatus.SELF_REPORTED,
            summary="Proof was submitted for the April 2026 rent payment.",
            tenancy_id=current_tenancy.id,
            payment_record_id=payment_record.id,
            details="Payment proof was attached before landlord confirmation.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=landlord_user.id,
            event_type=TrustEventType.PAYMENT_CONFIRMED,
            verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
            summary="April 2026 rent payment was confirmed by the counterparty.",
            tenancy_id=current_tenancy.id,
            payment_record_id=payment_record.id,
            details="The landlord confirmed receipt of the April rent payment.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=landlord_user.id,
            event_type=TrustEventType.DEPOSIT_RECORDED,
            verification_status=VerificationStatus.SELF_REPORTED,
            summary="The live tenancy deposit is being held on record.",
            tenancy_id=current_tenancy.id,
            deposit_record_id=deposit_record.id,
            details="The deposit remains held for the active tenancy.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=tenant_user.id,
            event_type=TrustEventType.MAINTENANCE_REPORTED,
            verification_status=VerificationStatus.SELF_REPORTED,
            summary="A maintenance issue was reported on the active tenancy.",
            tenancy_id=current_tenancy.id,
            maintenance_ticket_id=maintenance_ticket.id,
            details="The tenant opened a maintenance issue for a kitchen leak.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=landlord_user.id,
            event_type=TrustEventType.MAINTENANCE_ACKNOWLEDGED,
            verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
            summary="The maintenance issue was acknowledged by the landlord.",
            tenancy_id=current_tenancy.id,
            maintenance_ticket_id=maintenance_ticket.id,
            details="The landlord acknowledged the maintenance issue and scheduled a plumber.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=landlord_user.id,
            event_type=TrustEventType.MAINTENANCE_RESOLVED,
            verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
            summary="The maintenance issue was resolved.",
            tenancy_id=current_tenancy.id,
            maintenance_ticket_id=maintenance_ticket.id,
            details="The issue was resolved with a documented repair outcome.",
        )

    for tenancy, created_by_user, confirm_actor, review_summary in (
        (
            review_tenancy,
            landlord_user,
            tenant_user,
            "Ended tenancy kept to demonstrate verdict and appeal workflows.",
        ),
        (
            queue_tenancy,
            tenant_user,
            landlord_user,
            "Ended tenancy kept to populate the live dispute queues.",
        ),
    ):
        for subject_user in (tenant_user, landlord_user):
            ensure_trust_event(
                session=session,
                subject_user_id=subject_user.id,
                actor_user_id=created_by_user.id,
                event_type=TrustEventType.TENANCY_CREATED,
                verification_status=VerificationStatus.SELF_REPORTED,
                summary=f"{tenancy.property_label} tenancy was added to the ledger.",
                tenancy_id=tenancy.id,
                details=f"{tenancy.property_label} was seeded for dispute workflow coverage.",
            )
            ensure_trust_event(
                session=session,
                subject_user_id=subject_user.id,
                actor_user_id=confirm_actor.id,
                event_type=TrustEventType.TENANCY_COUNTERPARTY_CONFIRMED,
                verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
                summary=f"{tenancy.property_label} tenancy was counterparty confirmed.",
                tenancy_id=tenancy.id,
                details="Both tenancy parties confirmed the tenancy before internal review.",
            )
            ensure_trust_event(
                session=session,
                subject_user_id=subject_user.id,
                actor_user_id=created_by_user.id,
                event_type=TrustEventType.TENANCY_REVIEW_REQUESTED,
                verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
                summary=f"{tenancy.property_label} tenancy was submitted for verification.",
                tenancy_id=tenancy.id,
                details="The tenancy moved into internal review.",
            )
            ensure_trust_event(
                session=session,
                subject_user_id=subject_user.id,
                actor_user_id=reviewer_user.id,
                event_type=TrustEventType.TENANCY_REVIEWED,
                verification_status=VerificationStatus.VERIFIED,
                summary=f"{tenancy.property_label} tenancy was reviewed.",
                tenancy_id=tenancy.id,
                details=review_summary,
            )

    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_CREATED,
        summary="A disputed rent payment was recorded for Old Town Duplex.",
        details="The tenant created the November 2025 rent record.",
        payment_record=payment_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_PROOF_SUBMITTED,
        summary="Proof was submitted for the disputed Old Town Duplex rent payment.",
        details=payment_verdict_record.proof_summary,
        payment_record=payment_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.PAYMENT_REJECTED,
        summary="The Old Town Duplex rent payment was rejected by the landlord.",
        details=payment_verdict_record.counterparty_notes,
        payment_record=payment_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_DISPUTED,
        summary="The Old Town Duplex rent payment was disputed.",
        details=payment_verdict_record.dispute_notes,
        payment_record=payment_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_REVIEW_REQUESTED,
        summary="The Old Town Duplex rent payment was escalated to review.",
        details=payment_verdict_record.dispute_notes,
        payment_record=payment_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=reviewer_user,
        event_type=TrustEventType.PAYMENT_VERDICT_ISSUED,
        summary="A reviewer issued a verdict on the Old Town Duplex rent payment.",
        details=payment_verdict_record.verdict_summary,
        verification_status=VerificationStatus.REVIEWED,
        payment_record=payment_verdict_record,
    )

    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_CREATED,
        summary="A queue rent payment was recorded for Hillside Studio.",
        details="The tenant created the March 2026 rent record.",
        payment_record=payment_queue_record,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_PROOF_SUBMITTED,
        summary="Proof was submitted for the Hillside Studio rent payment.",
        details=payment_queue_record.proof_summary,
        payment_record=payment_queue_record,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.PAYMENT_REJECTED,
        summary="The Hillside Studio rent payment was rejected by the landlord.",
        details=payment_queue_record.counterparty_notes,
        payment_record=payment_queue_record,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_DISPUTED,
        summary="The Hillside Studio rent payment was disputed.",
        details=payment_queue_record.dispute_notes,
        payment_record=payment_queue_record,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.PAYMENT_REVIEW_REQUESTED,
        summary="The Hillside Studio rent payment was sent to review.",
        details=payment_queue_record.dispute_notes,
        payment_record=payment_queue_record,
    )

    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.DEPOSIT_RECORDED,
        summary="The Old Town Duplex deposit was recorded.",
        details="The move-out deposit was retained for the ended tenancy.",
        deposit_record=deposit_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.DEPOSIT_SETTLEMENT_SUBMITTED,
        summary="A deposit settlement was submitted for Old Town Duplex.",
        details=deposit_verdict_record.settlement_summary,
        deposit_record=deposit_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.DEPOSIT_DISPUTED,
        summary="The Old Town Duplex deposit settlement was disputed.",
        details=deposit_verdict_record.dispute_notes,
        deposit_record=deposit_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.DEPOSIT_REVIEW_REQUESTED,
        summary="The Old Town Duplex deposit dispute was escalated to review.",
        details=deposit_verdict_record.dispute_notes,
        deposit_record=deposit_verdict_record,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=reviewer_user,
        event_type=TrustEventType.DEPOSIT_VERDICT_ISSUED,
        summary="A reviewer issued a verdict on the Old Town Duplex deposit.",
        details=deposit_verdict_record.verdict_summary,
        verification_status=VerificationStatus.REVIEWED,
        deposit_record=deposit_verdict_record,
    )

    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.DEPOSIT_RECORDED,
        summary="The Hillside Studio deposit was recorded.",
        details="The move-out deposit remains on file during review.",
        deposit_record=deposit_queue_record,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.DEPOSIT_SETTLEMENT_SUBMITTED,
        summary="A deposit settlement was submitted for Hillside Studio.",
        details=deposit_queue_record.settlement_summary,
        deposit_record=deposit_queue_record,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.DEPOSIT_DISPUTED,
        summary="The Hillside Studio deposit settlement was disputed.",
        details=deposit_queue_record.dispute_notes,
        deposit_record=deposit_queue_record,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.DEPOSIT_REVIEW_REQUESTED,
        summary="The Hillside Studio deposit dispute was escalated to review.",
        details=deposit_queue_record.dispute_notes,
        deposit_record=deposit_queue_record,
    )

    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.MAINTENANCE_REPORTED,
        summary="The Old Town Duplex boiler outage was reported.",
        details=maintenance_verdict_ticket.description,
        maintenance_record=maintenance_verdict_ticket,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.MAINTENANCE_ACKNOWLEDGED,
        summary="The Old Town Duplex boiler outage was acknowledged.",
        details=maintenance_verdict_ticket.landlord_response_notes,
        maintenance_record=maintenance_verdict_ticket,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.MAINTENANCE_RESOLVED,
        summary="The Old Town Duplex boiler outage was marked resolved.",
        details=maintenance_verdict_ticket.resolution_summary,
        maintenance_record=maintenance_verdict_ticket,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.MAINTENANCE_DISPUTED,
        summary="The Old Town Duplex maintenance outcome was disputed.",
        details=maintenance_verdict_ticket.dispute_notes,
        maintenance_record=maintenance_verdict_ticket,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.MAINTENANCE_REVIEW_REQUESTED,
        summary="The Old Town Duplex maintenance dispute was sent to review.",
        details=maintenance_verdict_ticket.dispute_notes,
        maintenance_record=maintenance_verdict_ticket,
    )
    ensure_party_event(
        tenancy=review_tenancy,
        actor_user=reviewer_user,
        event_type=TrustEventType.MAINTENANCE_VERDICT_ISSUED,
        summary="A reviewer issued a verdict on the Old Town Duplex maintenance dispute.",
        details=maintenance_verdict_ticket.verdict_summary,
        verification_status=VerificationStatus.REVIEWED,
        maintenance_record=maintenance_verdict_ticket,
    )

    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.MAINTENANCE_REPORTED,
        summary="The Hillside Studio mold issue was reported.",
        details=maintenance_queue_ticket.description,
        maintenance_record=maintenance_queue_ticket,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.MAINTENANCE_ACKNOWLEDGED,
        summary="The Hillside Studio mold issue was acknowledged.",
        details=maintenance_queue_ticket.landlord_response_notes,
        maintenance_record=maintenance_queue_ticket,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=landlord_user,
        event_type=TrustEventType.MAINTENANCE_RESOLVED,
        summary="The Hillside Studio mold issue was marked resolved.",
        details=maintenance_queue_ticket.resolution_summary,
        maintenance_record=maintenance_queue_ticket,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.MAINTENANCE_DISPUTED,
        summary="The Hillside Studio maintenance outcome was disputed.",
        details=maintenance_queue_ticket.dispute_notes,
        maintenance_record=maintenance_queue_ticket,
    )
    ensure_party_event(
        tenancy=queue_tenancy,
        actor_user=tenant_user,
        event_type=TrustEventType.MAINTENANCE_REVIEW_REQUESTED,
        summary="The Hillside Studio maintenance dispute was sent to review.",
        details=maintenance_queue_ticket.dispute_notes,
        maintenance_record=maintenance_queue_ticket,
    )

    for subject_user in (tenant_user, landlord_user):
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=tenant_user.id,
            event_type=TrustEventType.TENANCY_CREATED,
            verification_status=VerificationStatus.SELF_REPORTED,
            summary="Imported tenancy history was added to the ledger.",
            tenancy_id=imported_tenancy.id,
            history_import_id=history_import.id,
            details="The tenant attached a previous tenancy to the historical import bundle.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=tenant_user.id,
            event_type=TrustEventType.TENANCY_REVIEW_REQUESTED,
            verification_status=VerificationStatus.SELF_REPORTED,
            summary="Imported tenancy history was submitted for review.",
            tenancy_id=imported_tenancy.id,
            history_import_id=history_import.id,
            details="Historical tenancy data was bundled into the import for review.",
        )
        ensure_trust_event(
            session=session,
            subject_user_id=subject_user.id,
            actor_user_id=reviewer_user.id,
            event_type=TrustEventType.TENANCY_REVIEWED,
            verification_status=VerificationStatus.REVIEWED,
            summary="Imported tenancy history was reviewed by internal ops.",
            tenancy_id=imported_tenancy.id,
            history_import_id=history_import.id,
            details="The reviewer accepted the historical tenancy as a reviewed signal.",
        )

    ensure_trust_event(
        session=session,
        subject_user_id=tenant_user.id,
        actor_user_id=tenant_user.id,
        event_type=TrustEventType.HISTORY_IMPORT_SUBMITTED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary="A cold-start history import was submitted.",
        history_import_id=history_import.id,
        details="The tenant submitted an imported tenancy bundle for review.",
    )
    ensure_trust_event(
        session=session,
        subject_user_id=tenant_user.id,
        actor_user_id=reviewer_user.id,
        event_type=TrustEventType.HISTORY_IMPORT_ACCEPTED,
        verification_status=VerificationStatus.REVIEWED,
        summary="The cold-start history import was accepted.",
        history_import_id=history_import.id,
        details="The historical import bundle was accepted by internal review.",
    )

    for evidence_document, summary_suffix, actor, verification_status in (
        (
            imported_lease_evidence,
            "Historical lease evidence was submitted.",
            tenant_user,
            VerificationStatus.SELF_REPORTED,
        ),
        (
            current_rent_evidence,
            "Current rent evidence was submitted.",
            tenant_user,
            VerificationStatus.SELF_REPORTED,
        ),
        (
            utility_evidence,
            "Utility settlement evidence was submitted.",
            tenant_user,
            VerificationStatus.SELF_REPORTED,
        ),
        (
            pending_landlord_evidence,
            "Landlord repair invoice evidence was submitted.",
            landlord_user,
            VerificationStatus.SELF_REPORTED,
        ),
        (
            current_identity_evidence,
            "Identity evidence was submitted for the live trust profile.",
            tenant_user,
            VerificationStatus.SELF_REPORTED,
        ),
        (
            reference_evidence,
            "Counterparty reference evidence was submitted.",
            landlord_user,
            VerificationStatus.COUNTERPARTY_CONFIRMED,
        ),
        (
            review_deposit_evidence,
            "Deposit deduction evidence was submitted for the reviewed move-out case.",
            landlord_user,
            VerificationStatus.COUNTERPARTY_CONFIRMED,
        ),
        (
            queue_rent_evidence,
            "Queue rent evidence was submitted for the pending payment review.",
            tenant_user,
            VerificationStatus.SELF_REPORTED,
        ),
    ):
        ensure_trust_event(
            session=session,
            subject_user_id=evidence_document.subject_user_id,
            actor_user_id=actor.id,
            event_type=TrustEventType.EVIDENCE_SUBMITTED,
            verification_status=verification_status,
            summary=summary_suffix,
            tenancy_id=evidence_document.tenancy_id,
            evidence_document_id=evidence_document.id,
            details=evidence_document.summary,
        )

    for evidence_document, summary_suffix in (
        (imported_lease_evidence, "Historical lease evidence was accepted."),
        (current_rent_evidence, "Current rent evidence was accepted."),
        (utility_evidence, "Utility settlement evidence was accepted."),
        (current_identity_evidence, "Identity evidence was accepted."),
        (reference_evidence, "Counterparty reference evidence was accepted."),
        (review_deposit_evidence, "Deposit deduction evidence was accepted."),
        (queue_rent_evidence, "Queue rent evidence was accepted."),
    ):
        ensure_trust_event(
            session=session,
            subject_user_id=evidence_document.subject_user_id,
            actor_user_id=reviewer_user.id,
            event_type=TrustEventType.EVIDENCE_ACCEPTED,
            verification_status=VerificationStatus.REVIEWED,
            summary=summary_suffix,
            tenancy_id=evidence_document.tenancy_id,
            evidence_document_id=evidence_document.id,
            details=evidence_document.review_notes,
        )

    ensure_trust_event(
        session=session,
        subject_user_id=tenant_user.id,
        actor_user_id=tenant_user.id,
        event_type=TrustEventType.REFERENCE_REQUEST_CREATED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary="A landlord reference request was sent.",
        tenancy_id=current_tenancy.id,
        reference_request_id=reference_request.id,
        details="The tenant requested a landlord reference for the current tenancy.",
    )
    ensure_trust_event(
        session=session,
        subject_user_id=tenant_user.id,
        actor_user_id=landlord_user.id,
        event_type=TrustEventType.REFERENCE_REQUEST_FULFILLED,
        verification_status=VerificationStatus.COUNTERPARTY_CONFIRMED,
        summary="The landlord reference request was fulfilled.",
        tenancy_id=current_tenancy.id,
        reference_request_id=reference_request.id,
        evidence_document_id=reference_evidence.id,
        details="The landlord supplied a counterparty reference that was later accepted.",
    )

    tenant_computation = refresh_user_trust_score(
        session=session,
        user=tenant_user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
    )
    landlord_computation = refresh_user_trust_score(
        session=session,
        user=landlord_user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
    )
    refresh_user_trust_score(
        session=session,
        user=agency_owner_user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
    )
    refresh_user_trust_score(
        session=session,
        user=reviewer_user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
    )
    refresh_user_trust_score(
        session=session,
        user=admin_user,
        calculation_reason=ScoreCalculationReason.INTERNAL_RECALCULATION,
    )

    listing = get_or_create_listing(
        session=session,
        organization=agency_org,
        property_record=agency_property,
        created_by_user=agency_owner_user,
        title="Agency Showcase Loft",
        description="A live demo listing that the agency can manage from the rebuilt workbench.",
        listing_status=ListingStatus.OPEN,
        monthly_rent_minor=110000,
        deposit_minor=220000,
        currency_code="EUR",
        minimum_tenant_score=620,
        minimum_verification_strength=60,
    )
    application = get_or_create_listing_application(
        session=session,
        listing=listing,
        applicant_user=tenant_user,
        submitted_by_user=tenant_user,
        application_status=ApplicationStatus.ACCEPTED,
        applicant_tenant_score=tenant_computation.tenant_score,
        applicant_verification_strength=tenant_computation.verification_strength,
        applicant_score_version=tenant_computation.scoring_version,
        applicant_score_calculated_at=tenant_computation.calculated_at,
        eligibility_notes="Seeded demo applicant meets the listing thresholds.",
        applicant_note="Reliable payment history and accepted references already on file.",
        status_notes="Accepted as part of the demo screening flow.",
        decided_by_user=agency_owner_user,
        decided_at=current_time - timedelta(days=2),
    )

    ensure_trust_event(
        session=session,
        subject_user_id=agency_owner_user.id,
        actor_user_id=agency_owner_user.id,
        event_type=TrustEventType.LISTING_PUBLISHED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary="A live agency listing was published.",
        listing_id=listing.id,
        details="The agency published a showcase listing for the rebuilt frontend demo.",
    )
    ensure_trust_event(
        session=session,
        subject_user_id=tenant_user.id,
        actor_user_id=tenant_user.id,
        event_type=TrustEventType.APPLICATION_SUBMITTED,
        verification_status=VerificationStatus.SELF_REPORTED,
        summary="A listing application was submitted.",
        listing_id=listing.id,
        details="The demo tenant applied to the agency showcase listing.",
    )
    ensure_trust_event(
        session=session,
        subject_user_id=tenant_user.id,
        actor_user_id=agency_owner_user.id,
        event_type=TrustEventType.APPLICATION_STATUS_UPDATED,
        verification_status=VerificationStatus.REVIEWED,
        summary="The listing application status was updated to accepted.",
        listing_id=listing.id,
        details="The demo agency accepted the application after screening.",
    )

    consent = get_or_create_consent(
        session=session,
        subject_user=tenant_user,
        granted_by_user=tenant_user,
        grantee_organization=agency_org,
        expires_at=current_time + timedelta(days=30),
        last_validated_at=current_time - timedelta(days=1),
    )
    trust_check = get_or_create_trust_check(
        session=session,
        organization=agency_org,
        consent=consent,
        requested_by_user=agency_owner_user,
        subject_user=tenant_user,
    )

    ensure_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_REPORT_CONSENT_CREATED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=tenant_user.id,
        organization_id=agency_org.id,
        subject_user_id=tenant_user.id,
        target_type="trust_report_consent",
        target_id=consent.id,
        details="Seeded demo trust-report consent for the agency sharing flow.",
    )
    ensure_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_CHECK_VALIDATED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=agency_owner_user.id,
        organization_id=agency_org.id,
        subject_user_id=tenant_user.id,
        target_type="trust_report_consent",
        target_id=consent.id,
        details="Seeded demo validation of the tenant trust-report consent.",
    )
    ensure_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_PROFILE_PREVIEWED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=agency_owner_user.id,
        organization_id=agency_org.id,
        subject_user_id=tenant_user.id,
        target_type="trust_report_consent",
        target_id=consent.id,
        details="Seeded demo preview of the tenant trust profile.",
    )
    ensure_audit_log(
        session=session,
        action_type=AuditActionType.TRUST_CHECK_CREATED,
        outcome_status=AuditOutcomeStatus.SUCCEEDED,
        actor_user_id=agency_owner_user.id,
        organization_id=agency_org.id,
        subject_user_id=tenant_user.id,
        target_type="agency_trust_check",
        target_id=trust_check.id,
        details="Seeded demo trust check created from the active consent.",
    )

    get_or_create_automation_task(
        session=session,
        task_type=AutomationTaskType.INTERNAL_FOLLOW_UP,
        status=AutomationTaskStatus.PENDING,
        title="Review pending landlord repair invoice",
        details="Demo follow-up task tied to the landlord evidence queue item.",
        result_notes=None,
        subject_user=landlord_user,
        organization=internal_org,
        requested_by_user=reviewer_user,
        consent=None,
        dedupe_key="demo:follow-up:landlord-repair-invoice",
        scheduled_for=current_time - timedelta(hours=2),
    )

    session.commit()

    tenant_snapshot = session.exec(
        select(TrustScoreSnapshot).where(TrustScoreSnapshot.user_id == tenant_user.id)
    ).first()
    landlord_snapshot = session.exec(
        select(TrustScoreSnapshot).where(TrustScoreSnapshot.user_id == landlord_user.id)
    ).first()

    return DemoSeedSummary(
        accounts=DEMO_ACCOUNTS,
        share_token=DEMO_SHARE_TOKEN,
        access_code=DEMO_ACCESS_CODE,
        tenant_score=tenant_snapshot.tenant_score if tenant_snapshot else tenant_computation.tenant_score,
        landlord_score=landlord_snapshot.landlord_score
        if landlord_snapshot
        else landlord_computation.landlord_score,
        verification_strength=tenant_snapshot.verification_strength
        if tenant_snapshot
        else tenant_computation.verification_strength,
    )
