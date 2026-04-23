from __future__ import annotations

from enum import Enum


class TenancyStatus(str, Enum):
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class ListingStatus(str, Enum):
    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"


class ApplicationStatus(str, Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class VerificationStatus(str, Enum):
    SELF_REPORTED = "self_reported"
    COUNTERPARTY_CONFIRMED = "counterparty_confirmed"
    REVIEWED = "reviewed"
    VERIFIED = "verified"

    @property
    def is_reviewer_final(self) -> bool:
        return self in {VerificationStatus.REVIEWED, VerificationStatus.VERIFIED}


class PropertyManagementMode(str, Enum):
    OWNER_MANAGED = "owner_managed"
    AGENCY_MANAGED = "agency_managed"


class EvidenceDocumentType(str, Enum):
    LEASE_AGREEMENT = "lease_agreement"
    RENT_RECEIPT = "rent_receipt"
    UTILITY_SETTLEMENT = "utility_settlement"
    DEPOSIT_RETURN = "deposit_return"
    LANDLORD_REFERENCE = "landlord_reference"
    IDENTITY_DOCUMENT = "identity_document"
    OTHER = "other"


class EvidenceReviewStatus(str, Enum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

    @property
    def is_final(self) -> bool:
        return self in {EvidenceReviewStatus.ACCEPTED, EvidenceReviewStatus.REJECTED}


class HistoryImportStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

    @property
    def is_final(self) -> bool:
        return self in {HistoryImportStatus.ACCEPTED, HistoryImportStatus.REJECTED}


class ReferenceRequestStatus(str, Enum):
    PENDING = "pending"
    FULFILLED = "fulfilled"
    DECLINED = "declined"

    @property
    def is_final(self) -> bool:
        return self in {ReferenceRequestStatus.FULFILLED, ReferenceRequestStatus.DECLINED}


class ScoreCalculationReason(str, Enum):
    SELF_SERVICE_REFRESH = "self_service_refresh"
    TRUST_CHECK_PREVIEW = "trust_check_preview"
    AGENCY_TRUST_CHECK = "agency_trust_check"
    INTERNAL_RECALCULATION = "internal_recalculation"
    SCHEDULED_AUTOMATION_REFRESH = "scheduled_automation_refresh"
    ORGANIZATION_BATCH_REFRESH = "organization_batch_refresh"
    NIGHTLY_BATCH_REFRESH = "nightly_batch_refresh"


class ScoreRecalculationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @property
    def is_final(self) -> bool:
        return self in {
            ScoreRecalculationStatus.COMPLETED,
            ScoreRecalculationStatus.FAILED,
        }


class ScoreRecalculationScope(str, Enum):
    ORGANIZATION_MEMBERS = "organization_members"
    ALL_ACTIVE_USERS = "all_active_users"


class AutomationTaskType(str, Enum):
    CONSENT_EXPIRY_REMINDER = "consent_expiry_reminder"
    INTERNAL_FOLLOW_UP = "internal_follow_up"
    USER_SCORE_RECALCULATION = "user_score_recalculation"
    ORGANIZATION_SCORE_RECALCULATION_BATCH = "organization_score_recalculation_batch"


class AutomationTaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"

    @property
    def is_final(self) -> bool:
        return self in {
            AutomationTaskStatus.COMPLETED,
            AutomationTaskStatus.CANCELED,
            AutomationTaskStatus.FAILED,
        }


class WorkerRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class NotificationChannel(str, Enum):
    EMAIL = "email"


class NotificationDeliveryStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    CANCELED = "canceled"
    FAILED = "failed"

    @property
    def is_final(self) -> bool:
        return self in {
            NotificationDeliveryStatus.SENT,
            NotificationDeliveryStatus.CANCELED,
            NotificationDeliveryStatus.FAILED,
        }


class AuditActionType(str, Enum):
    AUTH_SESSION_CREATED = "auth_session_created"
    AUTH_SESSION_REVOKED = "auth_session_revoked"
    AUTH_LOGIN_DENIED = "auth_login_denied"
    SCORE_RECALCULATION_REQUEST_CLAIMED = "score_recalculation_request_claimed"
    SCORE_RECALCULATION_REQUEST_PROCESSED = "score_recalculation_request_processed"
    TRUST_REPORT_CONSENT_CREATED = "trust_report_consent_created"
    TRUST_REPORT_CONSENT_REVOKED = "trust_report_consent_revoked"
    TRUST_CHECK_VALIDATED = "trust_check_validated"
    TRUST_PROFILE_PREVIEWED = "trust_profile_previewed"
    TRUST_CHECK_CREATED = "trust_check_created"
    AUTOMATION_TASK_CLAIMED = "automation_task_claimed"
    AUTOMATION_TASK_EXECUTED = "automation_task_executed"
    AUTOMATION_TASK_CLEANED_UP = "automation_task_cleaned_up"
    NOTIFICATION_QUEUED = "notification_queued"
    NOTIFICATION_DELIVERED = "notification_delivered"


class AuditOutcomeStatus(str, Enum):
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    DENIED = "denied"
    FAILED = "failed"


class PaymentRecordType(str, Enum):
    RENT = "rent"
    UTILITY_REIMBURSEMENT = "utility_reimbursement"
    MAINTENANCE_REIMBURSEMENT = "maintenance_reimbursement"
    OTHER = "other"


class PaymentRecordStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    DISPUTED = "disputed"
    UNDER_REVIEW = "under_review"
    VERDICT_ISSUED = "verdict_issued"

    @property
    def is_counterparty_final(self) -> bool:
        return self in {PaymentRecordStatus.CONFIRMED, PaymentRecordStatus.REJECTED}


class PaymentProofStatus(str, Enum):
    NONE = "none"
    PROVIDED = "provided"
    COUNTERPARTY_CONFIRMED = "counterparty_confirmed"


class DepositStatus(str, Enum):
    HELD = "held"
    RETURN_SUBMITTED = "return_submitted"
    RETURNED = "returned"
    PARTIALLY_WITHHELD = "partially_withheld"
    DISPUTED = "disputed"
    UNDER_REVIEW = "under_review"
    VERDICT_ISSUED = "verdict_issued"


class MaintenanceTicketPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MaintenanceTicketStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISPUTED = "disputed"
    UNDER_REVIEW = "under_review"
    VERDICT_ISSUED = "verdict_issued"


class DisputeVerdictOutcome(str, Enum):
    FAVORS_TENANT = "favors_tenant"
    FAVORS_LANDLORD = "favors_landlord"
    SHARED_FAULT = "shared_fault"
    INCONCLUSIVE = "inconclusive"


class TrustEventType(str, Enum):
    TENANCY_CREATED = "tenancy:created"
    TENANCY_COUNTERPARTY_CONFIRMED = "tenancy:counterparty_confirmed"
    TENANCY_REVIEW_REQUESTED = "tenancy:review_requested"
    TENANCY_REVIEWED = "tenancy:reviewed"
    EVIDENCE_SUBMITTED = "evidence:submitted"
    EVIDENCE_ACCEPTED = "evidence:accepted"
    EVIDENCE_REJECTED = "evidence:rejected"
    HISTORY_IMPORT_SUBMITTED = "history_import:submitted"
    HISTORY_IMPORT_ACCEPTED = "history_import:accepted"
    HISTORY_IMPORT_REJECTED = "history_import:rejected"
    REFERENCE_REQUEST_CREATED = "reference_request:created"
    REFERENCE_REQUEST_FULFILLED = "reference_request:fulfilled"
    PAYMENT_CREATED = "payment:created"
    PAYMENT_PROOF_SUBMITTED = "payment:proof_submitted"
    PAYMENT_CONFIRMED = "payment:confirmed"
    PAYMENT_REJECTED = "payment:rejected"
    PAYMENT_DISPUTED = "payment:disputed"
    PAYMENT_REVIEW_REQUESTED = "payment:review_requested"
    PAYMENT_VERDICT_ISSUED = "payment:verdict_issued"
    PAYMENT_APPEALED = "payment:appealed"
    DEPOSIT_RECORDED = "deposit:recorded"
    DEPOSIT_SETTLEMENT_SUBMITTED = "deposit:settlement_submitted"
    DEPOSIT_DISPUTED = "deposit:disputed"
    DEPOSIT_REVIEW_REQUESTED = "deposit:review_requested"
    DEPOSIT_VERDICT_ISSUED = "deposit:verdict_issued"
    DEPOSIT_APPEALED = "deposit:appealed"
    MAINTENANCE_REPORTED = "maintenance:reported"
    MAINTENANCE_ACKNOWLEDGED = "maintenance:acknowledged"
    MAINTENANCE_RESOLVED = "maintenance:resolved"
    MAINTENANCE_DISPUTED = "maintenance:disputed"
    MAINTENANCE_REVIEW_REQUESTED = "maintenance:review_requested"
    MAINTENANCE_VERDICT_ISSUED = "maintenance:verdict_issued"
    MAINTENANCE_APPEALED = "maintenance:appealed"
    LISTING_PUBLISHED = "listing:published"
    APPLICATION_SUBMITTED = "application:submitted"
    APPLICATION_STATUS_UPDATED = "application:status_updated"
