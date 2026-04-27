# Codebase Reference

This document is the code-level map of the rebuilt Trust Ledger platform.

Use it when you want to answer questions like:

- "Where does this workflow live?"
- "Which model owns this data?"
- "Which schema does this endpoint return?"
- "Which service computes this behavior?"
- "Which page uses this API?"
- "What should I read before changing a specific feature?"

This is intentionally more technical than [WORKSPACE_GUIDE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKSPACE_GUIDE.md). The workspace guide explains how to operate the product. This document explains how the product is built.

## Recommended Reading Order

If you are new to the rebuild, this order is the fastest path to understanding it:

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ROADMAP.md`
4. `docs/SPRINTS.md`
5. `docs/WORKSPACE_GUIDE.md`
6. `docs/PARITY_AUDIT.md`
7. This file

Example:

- If you want to change dispute handling, read the domain enums, the maintenance/payment/deposit models, the service response builders, the route files, and then the `OperationsPage` and `InternalOperationsPage`.
- If you want to change trust scoring, read `packages/domain/trustledger_domain/trust.py`, `apps/api/app/models/trust_score.py`, `apps/api/app/models/trust_score_recalculation.py`, `apps/api/app/services/scoring.py`, `apps/api/app/api/routes/trust_scores.py`, and `apps/api/app/api/routes/internal_scoring.py`.

## Repository Map

The rebuild is organized into four main layers:

- `apps/api/`
  - FastAPI application, database models, schemas, services, route handlers, seed helpers, and migrations.
- `apps/web/`
  - React application with routing, session state, localization, and workflow pages.
- `apps/worker/`
  - Worker runtime for automation tasks, notifications, and score recalculation processing.
- `packages/domain/`
  - Shared enum vocabulary for roles, statuses, verification, scoring, disputes, automation, and audit concepts.

Supporting directories:

- `docs/`
  - Source-of-truth docs, operator guides, runbooks, and sprint memory.
- `tests/`
  - Python regression suite for backend, docs/layout, runtime health, and seeded workflows.
- `archive/mesitis-mvp-2026-04-09/`
  - Preserved legacy app for comparison and migration reference only.

## Runtime Architecture

At runtime the system has three primary lanes:

- API lane
  - Serves `/api/v1/...`
  - Owns auth, RBAC, data writes, scoring calls, signed artifact access, and internal operations.
- Web lane
  - Calls the API over JSON
  - Organizes the product into role-based workspaces and task-oriented pages
  - Supports English and Greek
- Worker lane
  - Claims due work
  - Processes automation tasks, notifications, and score recalculation requests
  - Records worker runs for operational visibility

Example:

- A tenant uploads evidence from the web page.
- The web page calls the evidence route.
- The API stores a `StoredArtifact`, creates or updates an `EvidenceDocument`, and returns response metadata.
- A reviewer later inspects it from the internal workspace.
- If the evidence affects verification or a dispute, the scoring service can later recalculate the user scores.

## Shared Domain Vocabulary

The `packages/domain/trustledger_domain` package exists so the backend uses a stable, centralized language for statuses and roles.

### `access.py`

- `SystemRole`
  - Global platform roles such as end user, reviewer, or admin.
- `AccountWorkspaceRole`
  - Explicit account entitlements for tenant, landlord, agent/agency, and admin/internal workspace visibility.
- `OrganizationType`
  - Distinguishes agency organizations from internal/platform organizations.
- `OrganizationMembershipRole`
  - Distinguishes organization owner, manager, operator, and other org-level responsibilities.
- `ConsentScope`
  - Defines what a trust-report consent allows an external organization to view.

Why this matters:

- route guards use these enums,
- organization access decisions use these enums,
- frontend capabilities and workspace role menus are derived from these enums.

### `trust.py`

This file is the core business vocabulary of the system.

- `TenancyStatus`
  - Draft, active, ended, cancelled, and similar lifecycle states for tenancy records.
- `ListingStatus`
  - Open, paused, archived, and similar listing availability states.
- `ApplicationStatus`
  - Submitted, under review, accepted, rejected, withdrawn.
- `VerificationStatus`
  - Self-reported, counterparty-confirmed, reviewed, verified, rejected.
- `EvidenceDocumentType`
  - Lease, receipt, utility proof, deposit proof, reference, and similar evidence categories.
- `EvidenceReviewStatus`
  - Pending, accepted, rejected, and similar review decisions.
- `HistoryImportStatus`
  - Draft, submitted, accepted, rejected.
- `ReferenceRequestStatus`
  - Requested, fulfilled, cancelled, and similar states.
- `ScoreCalculationReason`
  - Why a score was recalculated.
- `ScoreRecalculationStatus`
  - Pending, processing, completed, failed.
- `ScoreRecalculationScope`
  - Single-user vs broader organization/batch scope.
- `AutomationTaskType`
  - Follow-ups, reminders, score refreshes, and similar task categories.
- `AutomationTaskStatus`
  - Pending, claimed, processing, completed, failed, cancelled.
- `WorkerRunStatus`
  - Running, completed, failed.
- `NotificationChannel`
  - Current notification transport category.
- `NotificationDeliveryStatus`
  - Pending, processing, sent, failed, cancelled.
- `AuditActionType`
  - Security, consent, trust-check, automation, and other auditable actions.
- `AuditOutcomeStatus`
  - Success, denied, failed.
- `PaymentRecordType`
  - Rent, utility, deposit-related payment, and similar payment meanings.
- `PaymentRecordStatus`
  - Pending, accepted, rejected, disputed, verdict-issued, appealed, and related states.
- `PaymentProofStatus`
  - Missing, submitted, accepted, rejected.
- `DepositStatus`
  - Held, proposed, disputed, verdict-issued, returned, and related stages.
- `MaintenanceTicketPriority`
  - Low, medium, high, urgent.
- `MaintenanceTicketStatus`
  - Reported, acknowledged, resolved, disputed, verdict-issued, appealed, etc.
- `DisputeVerdictOutcome`
  - Tenant-favored, landlord-favored, mixed, no-fault, or equivalent outcome values.
- `TrustEventType`
  - The ledger-style event vocabulary that powers the trust history.

Example:

- A maintenance ticket can move from `reported` to `acknowledged` to `resolved`.
- If challenged, it can move to a disputed/review state.
- A reviewer can issue a `DisputeVerdictOutcome`.
- The trust-event stream and score inputs both rely on those statuses remaining consistent.

## Backend Core

### `apps/api/app/main.py`

Main responsibility:

- creates the FastAPI app,
- configures logging,
- adds CORS,
- attaches request logging/security middleware,
- mounts the versioned API router,
- exposes health and readiness endpoints.

Important definitions:

- `CURRENT_STAGE`
  - Human-readable checkpoint marker for the current rebuild state.
- `create_app(settings=None)`
  - App factory for tests and runtime.

Operational behavior:

- every request receives an `X-Request-ID`,
- structured request logs are emitted,
- production-like environments add HSTS,
- readiness probes aggregate database, artifact storage, and Redis/coordination checks.

### `apps/api/app/api/router.py`

Main responsibility:

- collects every route module under `/api/v1`.

This is the fastest place to inspect the full HTTP surface:

- auth
- consents
- deposits
- evidence
- history imports
- listings/applications
- maintenance
- organizations
- payments
- properties
- reference requests
- tenancies
- internal review/audit/automation/disputes/notifications/operations/release/scoring/workers
- trust checks
- trust scores
- trust events

### `apps/api/app/api/deps.py`

Main responsibility:

- shared dependency injection for settings, sessions, users, and role checks.

Key definitions:

- `get_runtime_settings`
  - Returns the active `Settings`.
- `get_current_session`
  - Resolves the current auth session from cookies/session token.
- `get_current_user`
  - Resolves the active signed-in user.
- `require_system_roles`
  - Enforces reviewer/admin-style platform access.
- `has_workspace_role`
  - Checks whether a signed-in account has a specific account workspace entitlement.
- `require_workspace_role_for_user`
  - Rejects tenant, landlord, or agency workflows when the account lacks the matching workspace entitlement.
- `require_tenancy_workspace_access`
  - Combines tenant/landlord workspace entitlement checks with tenancy participation checks.
- `OrganizationAccessContext`
  - Structured org-access result used by org-scoped routes.
- `get_organization_access_context`
  - Resolves the signed-in user’s relationship to an organization.
- `require_membership_manager`
  - Enforces org-owner/manager controls.
- `require_agency_operator_access`
  - Enforces agency workspace access by requiring both the agency account entitlement and agency organization membership.

Example:

- `InternalOperationsPage` is only useful if the signed-in user is a reviewer or admin.
- The route guard uses `require_system_roles`.
- The frontend router also hides those tabs unless the account has the internal workspace entitlement.

### `apps/api/app/core/config.py`

Main responsibility:

- central runtime settings model and environment parsing.

Important areas:

- environment mode
- API/public URLs
- database URL
- artifact storage backend and root
- S3-compatible configuration
- cookie security
- Redis and worker coordination
- notification transport
- CORS origins

Why it matters:

- this is where "local vs staging vs production-like" behavior is decided,
- Alembic and runtime health rely on it,
- worker and API share this contract.

### `apps/api/app/core/db.py`

Main responsibility:

- engine/session creation for SQLModel/SQLAlchemy.

Key definitions:

- `create_engine_from_url`
  - Normalizes engine creation across SQLite and PostgreSQL.
- `get_session`
  - Standard request-scoped session dependency.

### `apps/api/app/core/health.py`

Main responsibility:

- readiness and liveness probing.

The readiness payload explains whether:

- the database is reachable,
- artifact storage is writable/reachable,
- Redis coordination is available or intentionally skipped.

### `apps/api/app/core/logging.py`

Main responsibility:

- structured runtime logging.

Important definitions:

- `configure_logging`
  - Configures the logger once.
- `emit_structured_log`
  - Writes consistent event records such as request completion and request failure.

### `apps/api/app/core/security.py`

Main responsibility:

- password hashing,
- opaque session token handling,
- secure comparisons and hashes for share tokens/access codes.

This is used by:

- auth login/register,
- trust-report share-token/access-code validation,
- session revocation,
- secure token storage.

## ORM Models

The backend uses SQLModel models under `apps/api/app/models`.

### `common.py`

- `utcnow()`
  - Returns a timezone-safe current timestamp.
- `ensure_utc(value)`
  - Normalizes datetimes into UTC.
- `TimestampedModel`
  - Shared `created_at` and `updated_at` fields for almost every table.

### `user.py`

- `User`
  - The platform identity record.
  - Key identity fields:
    - `email`
    - `full_name`
    - `password_hash`
    - `system_role`
    - `workspace_roles_json`
    - `is_active`
    - `email_verified`
  - Workspace role helpers:
    - `workspace_roles`
    - `set_workspace_roles(...)`
    - `normalize_workspace_roles(...)`
  - Key security fields:
    - `failed_login_attempt_count`
    - `last_login_attempt_at`
    - `login_locked_until`
    - `last_login_at`
  - Key relationships:
    - org memberships
    - sessions
    - tenancies as tenant/landlord/creator/reviewer
    - evidence uploads/reviews
    - payments, deposits, maintenance actions
    - properties created or assigned
    - trust score snapshots/history
    - worker runs
    - trust events as subject or actor

Example:

- One user can be both a personal workspace user and an agency member.
- Tenant, landlord, agency, and admin/internal workspace visibility comes from explicit account entitlements.
- Agency tools can be visible because the account has the agency entitlement, but backend agency work still requires organization membership.

### `organization.py`

- `Organization`
  - Agency or internal workspace record.
  - Key fields:
    - `name`
    - `slug`
    - `organization_type`
    - `is_active`
  - Key relationships:
    - memberships
    - listings
    - trust-report consents
    - assigned properties
    - trust checks
    - automation tasks
    - notifications
    - score recalculation batches

### `membership.py`

- `OrganizationMembership`
  - Join model between `User` and `Organization`.
  - Key fields:
    - `user_id`
    - `organization_id`
    - `role`
    - `is_active`

### `auth_session.py`

- `AuthSession`
  - Server-side session record.
  - Key fields:
    - `user_id`
    - `token_hash`
    - `expires_at`
    - `revoked_at`
    - `last_seen_at`
    - `ip_address`
    - `user_agent`

### `consent.py`

- `TrustReportConsent`
  - Permission grant allowing an external organization to view a subject’s trust profile.
  - Key fields:
    - `subject_user_id`
    - `granted_by_user_id`
    - `grantee_organization_id`
    - `scope`
    - `share_token_hash`
    - `access_code_hash`
    - `expires_at`
    - `revoked_at`
    - brute-force protection fields such as failed attempts and lockout timestamps

### `property.py`

- `Property`
  - Reusable real-estate record.
  - Key fields:
    - `property_label`
    - `address_line1`
    - `city`
    - `country_code`
    - `custom_tags_json`
    - `created_by_user_id`
    - `assigned_agency_organization_id`
    - `assigned_agency_user_id`
    - `assigned_tenant_user_id`
    - `is_active`
  - Key relationships:
    - listings
    - tenancies

Example:

- A landlord can create a property first.
- The property can later be assigned to an agency organization and an agency operator.
- The property can also carry a prospective tenant assignment before the tenancy is formally created.

### `tenancy.py`

- `Tenancy`
  - Core rental relationship record.
  - Key fields:
    - address/property identity
    - `tenancy_status`
    - `verification_status`
    - lease dates
    - monthly rent
    - deposit
    - `history_import_id`
    - `property_id`
    - `tenant_user_id`
    - `landlord_user_id`
    - counterparty confirmation timestamps
    - internal review timestamps and notes
  - Key relationships:
    - property
    - evidence
    - payments
    - deposits
    - maintenance tickets
    - references
    - trust events

### `stored_artifact.py`

- `StoredArtifact`
  - Private file storage record.
  - Key fields:
    - `created_by_user_id`
    - `tenancy_id`
    - `artifact_purpose`
    - `storage_backend`
    - `storage_key`
    - `original_file_name`
    - `content_type`
    - `size_bytes`
    - `sha256_hex`
    - `last_accessed_at`

### `evidence.py`

- `EvidenceDocument`
  - Evidence item attached to a tenancy and subject user.
  - Key fields:
    - `tenancy_id`
    - `subject_user_id`
    - `uploaded_by_user_id`
    - `stored_artifact_id`
    - `reference_request_id`
    - `document_type`
    - `review_status`
    - `artifact_name`
    - `summary`
    - `issuer_name`
    - `document_date`
    - `amount_minor`
    - `currency_code`
    - review metadata

### `history_import.py`

- `HistoryImport`
  - Cold-start evidence bundle for prior rental history.
  - Key fields:
    - `subject_user_id`
    - `created_by_user_id`
    - `title`
    - `summary`
    - `status`
    - submitted/reviewed timestamps and notes

### `reference_request.py`

- `ReferenceRequest`
  - Structured request for a previous landlord or related counterparty reference.
  - Key fields:
    - `tenancy_id`
    - `subject_user_id`
    - `requested_by_user_id`
    - `requested_from_user_id`
    - `status`
    - `message`
    - `fulfilled_at`

### `payment.py`

- `PaymentRecord`
  - Payment workflow record for rent/utilities/other tenancy-linked payments.
  - Key fields:
    - `tenancy_id`
    - `payer_user_id`
    - `payee_user_id`
    - `payment_type`
    - `payment_status`
    - `proof_status`
    - amount/currency/date fields
    - proof artifact and counterparty artifact fields
    - dispute, verdict, and appeal fields

### `deposit.py`

- `DepositRecord`
  - Deposit settlement/dispute record for a tenancy.
  - Key fields:
    - `tenancy_id`
    - deposit amounts and currency
    - move-out and due dates
    - settlement artifact fields
    - dispute, verdict, and appeal fields

### `maintenance_ticket.py`

- `MaintenanceTicket`
  - Maintenance issue workflow with evidence, landlord response, reviewer verdict, and appeal.
  - Key fields:
    - `tenancy_id`
    - creator/acknowledger/resolver/reviewer actors
    - `title`
    - `description`
    - `priority`
    - `ticket_status`
    - reported/resolution artifact fields
    - dispute, verdict, and appeal fields

### `listing.py`

- `Listing`
  - Agency-controlled property listing.
  - Key fields:
    - `organization_id`
    - `property_id`
    - `listing_status`
    - `title`
    - `description`
    - monthly rent and deposit
    - minimum trust-score and verification thresholds

### `application.py`

- `ListingApplication`
  - Tenant application for a listing.
  - Key fields:
    - `listing_id`
    - `applicant_user_id`
    - `submitted_by_user_id`
    - `application_status`
    - applicant score snapshot fields
    - `eligibility_met`
    - `eligibility_notes`
    - `applicant_note`
    - `status_notes`
    - decision actor/timestamp

### `agency_trust_check.py`

- `AgencyTrustCheck`
  - Audited organization-level access event against a consented trust report.
  - Key fields:
    - `organization_id`
    - `consent_id`
    - `requested_by_user_id`
    - `subject_user_id`
    - `scope`

### `trust_event.py`

- `TrustEvent`
  - Append-only trust-ledger event record.
  - Key fields:
    - subject/actor user IDs
    - pointers to the related tenancy/history import/reference/evidence/payment/deposit/maintenance/listing
    - `event_type`
    - `verification_status`
    - `summary`
    - `details`

This is the app’s closest equivalent to the trust ledger itself.

### `trust_score.py`

- `TrustScoreSnapshot`
  - Latest current score state for a user.
- `TrustScoreHistory`
  - Historical score entries over time.

Shared fields:

- `tenant_score`
- `landlord_score`
- `verification_strength`
- `scoring_version`
- `calculated_at`

### `trust_score_recalculation.py`

- `TrustScoreRecalculationBatch`
  - Batch recalculation request, often org-scoped.
- `TrustScoreRecalculationRequest`
  - Individual user recalculation request, possibly linked to a batch.

These records power:

- manual internal score refresh,
- scheduled refresh,
- worker processing,
- auditability of scoring operations.

### `automation_task.py`

- `AutomationTask`
  - General-purpose due-task queue record.
  - Supports reminders, follow-ups, and score-refresh orchestration.

### `notification_delivery.py`

- `NotificationDelivery`
  - Durable notification outbox record.
  - Stores schedule, status, attempt count, template, recipient, and processing metadata.

### `audit_log.py`

- `AuditLog`
  - Append-only audit record for security-sensitive or operationally sensitive actions.
  - Key fields:
    - actor
    - organization
    - subject user
    - `action_type`
    - `outcome_status`
    - `target_type`
    - `target_id`
    - `details`

### `worker_run.py`

- `WorkerRun`
  - Summary record of one worker cycle.
  - Tracks counts for:
    - claimed/completed/failed automation tasks
    - claimed/sent/failed notifications
    - processed/failed score requests
    - cleanup actions
    - overall status and errors

## API Schemas

The schema package describes the request and response contracts returned to the frontend and tests.

### Auth and security

#### `auth.py`

- `RegisterRequest`
  - Email, full name, password.
- `LoginRequest`
  - Email and password.
- `UserResponse`
  - Current user profile returned after auth/session reads, including `workspace_roles`.
- `AuthSessionResponse`
  - Session metadata for account security pages.
- `AuthSessionBulkRevokeResponse`
  - Returned when revoking all sessions except the current one.

#### `internal.py`

- `InternalUserResponse`
  - Admin-facing user summary for account role management.
- `WorkspaceRolesUpdateRequest`
  - Replaces the editable account workspace-role entitlement set.

### Organizations and agency work

#### `organization.py`

- `OrganizationCreateRequest`
  - Create agency or internal organization.
- `OrganizationResponse`
  - Org summary with current user membership role.
- `CommercialOverviewResponse`
  - Agency-facing performance/dashboard summary.
- `MembershipCreateRequest`
  - Add a user to an organization by ID or email with a role.
- `MembershipUpdateRequest`
  - Change role or active status.
- `MembershipResponse`
  - Membership detail returned to the web app.

#### `property.py`

- `PropertyCreateRequest`
  - Property label, address, country, and custom tags.
- `PropertyUpdateRequest`
  - Property edit plus assignment fields:
    - agency organization
    - agency user
    - tenant user
    - clear-assignment toggles
    - activation flag
- `PropertyResponse`
  - Full property record including assigned agency/user/tenant display information.

#### `listing.py`

- `ListingCreateRequest`
  - Property, price, deposit, and trust thresholds.
- `ListingUpdateRequest`
  - Status and threshold edits.
- `ListingResponse`
  - Listing details plus organization and property context.
- `ApplicationCreateRequest`
  - Applicant note.
- `ApplicationUpdateRequest`
  - Decision/status updates.
- `ListingApplicationResponse`
  - Application plus applicant score snapshot and decision info.
- `AgencyScreeningDashboardResponse`
  - Aggregated listing/application metrics for agency tools.

### Tenancy records and evidence

#### `tenancy.py`

- `TenancyCreateRequest`
  - Flexible create shape allowing:
    - existing property link
    - raw property address fields
    - tenant by ID or email
    - landlord by ID or email
    - rent/deposit/lease dates
- `TenancyReviewDecisionRequest`
  - Reviewer verification outcome for a tenancy record.
- `TenancyResponse`
  - Full tenancy state with participant display names and review metadata.

#### `artifact.py`

- `StoredArtifactResponse`
  - Metadata for a private uploaded file.
- `StoredArtifactAccessResponse`
  - Signed access response containing a short-lived download URL and expiry timestamp.

#### `evidence.py`

- `EvidenceCreateRequest`
  - User subject, document type, summary, artifact ID, issuer/date/amount/reference metadata.
- `EvidenceReviewDecisionRequest`
  - Reviewer accept/reject style decision.
- `EvidenceResponse`
  - Full evidence state plus artifact metadata and reviewer fields.

#### `history_import.py`

- `HistoryImportCreateRequest`
  - Title and summary.
- `HistoryImportReviewDecisionRequest`
  - Internal decision and notes.
- `HistoryImportResponse`
  - History-import summary plus counts of linked tenancies and evidence.

#### `reference_request.py`

- `ReferenceRequestCreateRequest`
  - Subject, requested-from user, message.
- `ReferenceRequestFulfillmentRequest`
  - Artifact metadata and evidence summary for the fulfilled reference.
- `ReferenceRequestResponse`
  - Reference request plus fulfillment evidence linkage.

### Operational workflows

#### `payment.py`

- `PaymentCreateRequest`
  - Initial payment intent or record.
- `PaymentProofSubmitRequest`
  - Adds or refreshes proof.
- `PaymentDecisionRequest`
  - Counterparty decision and optional counter-evidence.
- `PaymentDisputeRequest`
  - Starts dispute review.
- `PaymentAppealRequest`
  - Reopens a verdict for appeal.
- `PaymentVerdictRequest`
  - Internal verdict including score deltas.
- `PaymentResponse`
  - Full workflow state with all actors, artifacts, verdict fields, and timestamps.

#### `deposit.py`

- `DepositCreateRequest`
  - Initial deposit record.
- `DepositSettlementRequest`
  - Settlement proposal with artifacts and notes.
- `DepositDisputeRequest`
  - Dispute initiation.
- `DepositAppealRequest`
  - Appeal initiation.
- `DepositVerdictRequest`
  - Internal reviewer verdict.
- `DepositResponse`
  - Full deposit workflow state.

#### `maintenance.py`

- `MaintenanceTicketCreateRequest`
  - Issue report and initial evidence.
- `MaintenanceTicketAcknowledgeRequest`
  - Landlord acknowledgement notes.
- `MaintenanceTicketResolveRequest`
  - Resolution summary and optional evidence.
- `MaintenanceTicketDisputeRequest`
  - Dispute initiation.
- `MaintenanceTicketAppealRequest`
  - Appeal initiation.
- `MaintenanceTicketVerdictRequest`
  - Internal reviewer verdict.
- `MaintenanceTicketResponse`
  - Full maintenance workflow state.

### Trust, scoring, audit, and runtime

#### `consent.py`

- `TrustReportConsentCreateRequest`
  - Organization, access code, and expiry.
- `TrustReportConsentResponse`
  - Persistent consent metadata.
- `TrustReportConsentCreateResponse`
  - Adds the generated share token.

#### `trust_check.py`

- `TrustCheckAccessRequest`
  - Share token + access code.
- `TrustCheckValidationResponse`
  - Lightweight confirmation that the consent is valid.
- `TrustProfileSummaryResponse`
  - Summary profile shared with an agency after consent validation.
- `AgencyTrustCheckResponse`
  - Trust-check record summary.
- `AgencyTrustCheckResultResponse`
  - Trust-check record plus the shared profile payload.

#### `trust_event.py`

- `TrustEventResponse`
  - Ledger event payload with cross-linked context such as listing, payment, evidence, or property label.

#### `score.py`

- `TrustScoreInputsResponse`
  - Input counts used to compute trust scores.
- `TrustScoreSummaryResponse`
  - Current scores plus inputs.
- `TrustScoreHistoryResponse`
  - Historical score rows.
- `TrustScoreRecalculationRequestResponse`
  - Single queued recalculation job.
- `TrustScoreRecalculationBatchCreateRequest`
  - Batch create request.
- `TrustScoreRecalculationDirectCreateRequest`
  - Direct single-user recalculation request.
- `TrustScoreRecalculationBatchResponse`
  - Batch status and aggregated counts.

#### `automation.py`

- `AutomationTaskResponse`
  - Queue task metadata.
- `AutomationFollowUpCreateRequest`
  - Manual follow-up task creation.
- `AutomationTaskProcessRequest`
  - Manual task status updates.
- `ScheduledScoreRefreshTaskCreateRequest`
  - Schedule a score-refresh automation task.
- `AutomationTaskClaimRequest`
  - Claim due tasks.
- `AutomationCleanupRequest`
  - Cleanup criteria for stale or expired tasks.
- `AutomationCleanupResponse`
  - Cleanup result payload.

#### `notification.py`

- `NotificationDeliveryResponse`
  - Notification outbox detail with recipient and attempt metadata.

#### `audit_log.py`

- `AuditLogResponse`
  - Actor, subject, organization, action, outcome, target, details, timestamp.

#### `operations.py`

- `InternalOperationsOverviewResponse`
  - High-level operations dashboard for reviewers/admins.

#### `release.py`

- `ReleaseReadinessCheckResponse`
  - One readiness check result.
- `ReleaseReadinessResponse`
  - Full release readiness snapshot.

#### `internal.py`

- `InternalAccessResponse`
  - Current user’s internal/reviewer access status.

#### `worker_run.py`

- `WorkerRunResponse`
  - Full worker-cycle summary.

## Service Layer

The service layer is where pure response-building, storage behavior, queue logic, and orchestration rules live.

### `artifacts.py`

Purpose:

- validate uploads,
- route storage to local-private or S3-compatible backends,
- generate signed access,
- reopen artifacts safely.

Functions:

- `sanitize_filename`
  - Normalizes user-supplied file names.
- `ensure_upload_allowed`
  - Enforces size/content-type policy.
- `get_artifact_storage_root`
  - Resolves the local artifact root.
- `create_s3_client`
  - Builds an S3-compatible client when that backend is enabled.
- `read_upload_bytes`
  - Reads and size-checks the upload body.
- `build_storage_key`
  - Creates a stable private storage key.
- `store_local_artifact_payload`
  - Writes bytes to local private storage.
- `store_s3_artifact_payload`
  - Writes bytes to S3-compatible storage.
- `store_uploaded_artifact`
  - Main orchestration entry point for artifact storage.
- `build_stored_artifact_response`
  - Serializes stored-artifact metadata.
- `build_download_signature`
  - Creates a signed access token for a time-limited download.
- `validate_download_signature`
  - Validates the signed download token.
- `build_stored_artifact_access_response`
  - Returns a time-limited access payload.
- `resolve_artifact_path`
  - Resolves a local artifact path.
- `build_storage_redirect_url`
  - Builds the eventual download URL for the client.
- `resolve_attachable_tenancy_artifact`
  - Verifies that an artifact belongs to the relevant tenancy before attaching it.

Example:

- A tenant uploads a PDF receipt.
- `store_uploaded_artifact` writes it and records metadata.
- Later `build_stored_artifact_access_response` creates a short-lived link.

### `audit_logs.py`

- `build_audit_log_response`
  - Serializes audit logs.
- `append_audit_log`
  - Creates a new audit record.

### `automation.py`

Purpose:

- own the durable automation-task queue.

Important functions:

- `build_automation_task_response`
- `get_due_boundary`
- `calculate_consent_expiry_reminder_schedule`
- `get_automation_task_by_dedupe_key`
- `ensure_consent_expiry_reminder`
- `cancel_consent_expiry_reminder`
- `create_internal_follow_up_task`
- `create_user_score_refresh_task`
- `create_organization_score_batch_refresh_task`
- `claim_due_automation_tasks`
- `transition_automation_task`
- `fail_automation_task`
- `resolve_automation_task_requester`
- `execute_automation_task`
- `cleanup_expired_consent_reminder_tasks`
- `cleanup_stale_follow_up_tasks`

### `commercial_overview.py`

- `build_commercial_overview`
  - Computes agency-facing business metrics for the agency workspace.

### `consents.py`

- `ValidatedTrustConsent`
  - Lightweight validated-consent result object.
- `find_trust_report_consent_by_share_token`
  - Securely resolves a consent from a share token.
- `validate_trust_report_consent`
  - Full validation with expiry, lockout, org, and access-code checks.

### `deposits.py`

- `build_deposit_response`
  - Serializes a deposit record into the response shape used by the frontend and dispute queue.

### `evidence.py`

- `format_evidence_document_type_label`
  - Human-readable document label helper.
- `build_evidence_response`
  - Serializes evidence records including reviewer and artifact context.

### `history_imports.py`

- `build_history_import_response`
  - Serializes history-import bundles.

### `listings.py`

- `build_listing_response`
- `build_application_response`
- `evaluate_listing_eligibility`
  - Applies score/verification thresholds.
- `ensure_listing_is_open`
- `ensure_application_status_transition`
- `build_agency_screening_dashboard_response`

### `maintenance.py`

- `build_maintenance_ticket_response`
  - Serializes a maintenance ticket with artifact and dispute metadata.

### `notifications.py`

- `build_notification_delivery_response`
- `get_due_boundary`
- `get_notification_by_dedupe_key`
- `build_consent_expiry_notification_body`
- `queue_consent_expiry_reminder_notification`
- `claim_due_notification_deliveries`
- `dispatch_notification_delivery`
- `fail_notification_delivery`

### `payments.py`

- `build_payment_response`
  - Serializes a payment record including artifacts, actors, and verdict/appeal state.

### `properties.py`

- `normalize_property_tags`
- `serialize_property_tags`
- `parse_property_tags`
- `build_property_response`

These helpers keep property tags consistent across DB storage, API responses, and the frontend.

### `reference_requests.py`

- `build_reference_request_response`
  - Serializes a reference request and any fulfilled evidence linkage.

### `release_readiness.py`

- `ReleaseCheck`
  - Internal structured check object.
- `build_release_readiness`
  - Aggregates the entire release-readiness result.
- `_count_scalar`
- `_check_environment`
- `_check_secret_key`
- `_check_secure_cookie`
- `_check_public_urls`
- `_check_database_backend`
- `_check_worker_coordination`
- `_check_notification_transport`
- `_check_latest_worker_run`
- `_check_failed_worker_runs`
- `_check_failed_notifications`

### `scoring.py`

Purpose:

- compute tenant score,
- compute landlord score,
- compute verification strength,
- persist snapshots/history,
- orchestrate recalculation queue/batch processing.

Classes:

- `TrustScoreInputs`
- `TrustScoreComputation`
- `TrustScoreRecalculationBatchCounts`

Functions:

- `clamp`
- `calculate_user_trust_scores`
- `persist_user_trust_score_computation`
- `refresh_user_trust_score`
- `create_user_score_recalculation_request`
- `resolve_batch_calculation_reason`
- `resolve_batch_target_users`
- `create_score_recalculation_batch`
- `build_score_recalculation_batch_counts`
- `sync_score_recalculation_batch_status`
- `begin_score_recalculation_request_processing`
- `process_score_recalculation_request`
- `list_due_score_recalculation_requests`
- `claim_due_score_recalculation_requests`
- `build_trust_score_summary_response`
- `build_trust_score_history_response`
- `build_score_recalculation_request_response`
- `build_score_recalculation_batch_response`

Example:

- A payment verdict issues a `tenant_score_delta` and `landlord_score_delta`.
- The dispute queue action triggers a refresh.
- `calculate_user_trust_scores` recomputes the user scores from all accepted/verified evidence and current adjudication adjustments.

### `tenancies.py`

- `build_tenancy_response`
  - Serializes a tenancy with participants, property context, and review fields.

### `trust_events.py`

- `append_tenancy_events`
  - Appends ledger events related to a tenancy workflow.
- `append_user_event`
  - Appends broader user-level events.
- `build_trust_event_response`
  - Serializes trust events for the timeline UI.

### `trust_profiles.py`

- `build_trust_profile_summary`
  - Aggregates the data shared to agencies during a trust check.

### `worker_runs.py`

- `create_worker_run`
- `finalize_worker_run`
- `build_worker_run_response`

## Route Modules And HTTP Surface

All routes are mounted under `/api/v1`.

### `auth.py` with prefix `/auth`

Purpose:

- account registration, login, logout, current-user profile, session management, and auth/security audit visibility.

Helper functions:

- `build_auth_session_response`
- `append_auth_login_denied_audit`

Endpoints:

- `POST /auth/register` -> `register_user`
- `POST /auth/login` -> `login_user`
- `POST /auth/logout` -> `logout_user`
- `GET /auth/me` -> `get_current_user_profile`
- `GET /auth/security-events` -> `list_auth_security_events`
- `GET /auth/sessions` -> `list_auth_sessions`
- `POST /auth/sessions/revoke-others` -> `revoke_other_auth_sessions`
- `POST /auth/sessions/{session_id}/revoke` -> `revoke_auth_session`

### `organizations.py` with prefix `/organizations`

Purpose:

- organizations, memberships, agency directory, and commercial overview.

Helpers:

- `normalize_slug`
- `build_organization_response`
- `build_membership_response`
- `assert_owner_safety`
- `resolve_membership_target_user`

Endpoints:

- `POST /organizations`
- `GET /organizations/mine`
- `GET /organizations/directory/agencies`
- `GET /organizations/{organization_id}`
- `GET /organizations/{organization_id}/commercial-overview`
- `GET /organizations/{organization_id}/memberships`
- `POST /organizations/{organization_id}/memberships`
- `PATCH /organizations/{organization_id}/memberships/{membership_id}`

### `properties.py` with prefix `/properties`

Purpose:

- property creation, assignment, tagging, and personal/agency property listing.

Helpers:

- `resolve_target_user`
- `resolve_agency_assignment`
- `resolve_tenant_assignment`

Endpoints:

- `POST /properties`
- `PATCH /properties/{property_id}`
- `GET /properties/mine`

### `tenancies.py` with prefix `/tenancies`

Purpose:

- tenancy creation, evidence submission, review request, and counterparty confirmation.

Helpers:

- `resolve_tenancy_user`
- `ensure_tenancy_participants`
- `resolve_property_for_tenancy`
- `ensure_tenancy_access`
- `ensure_tenancy_subject`
- `resolve_history_import_for_tenancy`

Endpoints:

- `POST /tenancies`
- `POST /tenancies/{tenancy_id}/evidence`
- `GET /tenancies/{tenancy_id}/evidence`
- `GET /tenancies/mine`
- `POST /tenancies/{tenancy_id}/request-review`
- `POST /tenancies/{tenancy_id}/confirm`

### `evidence.py` with prefix `/evidence`

Purpose:

- private artifact upload and short-lived artifact access.

Endpoints:

- `POST /evidence/tenancies/{tenancy_id}/artifacts`
- `POST /evidence/{evidence_id}/artifact-access`
- `POST /evidence/artifacts/{artifact_id}/access`
- `GET /evidence/artifacts/download`

### `history_imports.py` with prefix `/history-imports`

- `POST /history-imports`
- `GET /history-imports/mine`
- `POST /history-imports/{history_import_id}/submit`

### `reference_requests.py` with prefix `/reference-requests`

- `POST /reference-requests/tenancies/{tenancy_id}`
- `GET /reference-requests/mine`
- `POST /reference-requests/{reference_request_id}/fulfill`

### `payments.py` with prefix `/payments`

Purpose:

- payment creation, proof submission, counterparty decision, dispute, and appeal.

Helpers:

- `get_tenancy_or_404`
- `get_payment_or_404`
- `ensure_tenancy_access`
- `append_payment_party_events`
- `ensure_payment_users`
- `resolve_tenancy_artifact`

Endpoints:

- `POST /payments/tenancies/{tenancy_id}`
- `GET /payments/tenancies/{tenancy_id}`
- `POST /payments/{payment_id}/proof`
- `POST /payments/{payment_id}/decision`
- `POST /payments/{payment_id}/dispute`
- `POST /payments/{payment_id}/appeal`

### `deposits.py` with prefix `/deposits`

Purpose:

- deposit creation, settlement, dispute, and appeal.

Helpers:

- `get_tenancy_or_404`
- `get_deposit_record_or_404`
- `get_deposit_record_for_tenancy`
- `ensure_tenancy_access`
- `append_deposit_party_events`
- `refresh_tenancy_scores`
- `resolve_tenancy_artifact`

Endpoints:

- `POST /deposits/tenancies/{tenancy_id}`
- `GET /deposits/tenancies/{tenancy_id}`
- `POST /deposits/{deposit_id}/settlement`
- `POST /deposits/{deposit_id}/dispute`
- `POST /deposits/{deposit_id}/appeal`

### `maintenance.py` with prefix `/maintenance-tickets`

Purpose:

- maintenance issue reporting, acknowledgement, resolution, dispute, and appeal.

Helpers:

- `get_tenancy_or_404`
- `get_maintenance_ticket_or_404`
- `ensure_tenancy_access`
- `append_maintenance_party_events`
- `resolve_tenancy_artifact`

Endpoints:

- `POST /maintenance-tickets/tenancies/{tenancy_id}`
- `GET /maintenance-tickets/tenancies/{tenancy_id}`
- `POST /maintenance-tickets/{ticket_id}/acknowledge`
- `POST /maintenance-tickets/{ticket_id}/resolve`
- `POST /maintenance-tickets/{ticket_id}/dispute`
- `POST /maintenance-tickets/{ticket_id}/appeal`

### `listings.py`

Purpose:

- agency listings, public listing browse, and applications.

Helpers:

- `get_listing_for_organization`

Endpoints:

- `POST /organizations/{organization_id}/listings`
- `GET /organizations/{organization_id}/listings`
- `PATCH /organizations/{organization_id}/listings/{listing_id}`
- `GET /listings/open`
- `POST /listings/{listing_id}/applications`
- `GET /applications/mine`
- `GET /organizations/{organization_id}/applications`
- `GET /organizations/{organization_id}/screening-dashboard`
- `PATCH /organizations/{organization_id}/applications/{application_id}`

### `consents.py` with prefix `/consents/trust-report`

- `POST /consents/trust-report`
- `GET /consents/trust-report`
- `GET /consents/trust-report/access-history`
- `POST /consents/trust-report/{consent_id}/revoke`

### `trust_checks.py` with prefix `/organizations/{organization_id}/trust-checks`

Purpose:

- validate consent, preview a trust profile, create an auditable trust check, and list prior checks.

Helpers:

- `build_trust_check_response`
- `validate_trust_report_consent_with_audit`

Endpoints:

- `POST /organizations/{organization_id}/trust-checks/validate`
- `POST /organizations/{organization_id}/trust-checks/profile`
- `POST /organizations/{organization_id}/trust-checks`
- `GET /organizations/{organization_id}/trust-checks`

### `trust_scores.py` with prefix `/trust-scores`

- `GET /trust-scores/mine`
- `GET /trust-scores/mine/history`

### `trust_events.py` with prefix `/trust-events`

- `GET /trust-events/mine`
- `GET /trust-events/tenancies/{tenancy_id}`

### `internal.py` with prefix `/internal`

Purpose:

- internal access status, account role management, and reviewer queues for tenancies, evidence, and history imports.

Endpoints:

- `GET /internal/access`
- `GET /internal/users`
- `PATCH /internal/users/{user_id}/workspace-roles`
- `GET /internal/review-queue/tenancies`
- `GET /internal/review-queue/evidence`
- `GET /internal/review-queue/history-imports`
- `POST /internal/review-queue/tenancies/{tenancy_id}/decision`
- `POST /internal/review-queue/evidence/{evidence_document_id}/decision`
- `POST /internal/review-queue/history-imports/{history_import_id}/decision`

### `internal_disputes.py` with prefix `/internal/disputes`

Purpose:

- reviewer/admin verdict handling for payment, deposit, and maintenance disputes.

Endpoints:

- `GET /internal/disputes/maintenance`
- `POST /internal/disputes/maintenance/{ticket_id}/verdict`
- `GET /internal/disputes/payments`
- `GET /internal/disputes/deposits`
- `POST /internal/disputes/deposits/{deposit_id}/verdict`
- `POST /internal/disputes/payments/{payment_id}/verdict`

### `internal_scoring.py` with prefix `/internal/scoring`

Purpose:

- manual recalculation, request/batch management, and score history inspection.

Endpoints:

- `POST /internal/scoring/requests`
- `GET /internal/scoring/requests`
- `GET /internal/scoring/batches`
- `POST /internal/scoring/users/{user_id}/requests`
- `GET /internal/scoring/requests/{request_id}`
- `POST /internal/scoring/requests/{request_id}/process`
- `POST /internal/scoring/batches`
- `GET /internal/scoring/batches/{batch_id}`
- `POST /internal/scoring/recalculate`
- `POST /internal/scoring/users/{user_id}/recalculate`
- `GET /internal/scoring/users/{user_id}/history`

### `internal_automation.py` with prefix `/internal/automation`

Purpose:

- manual automation control, claiming, follow-up creation, cleanup, and score-refresh task orchestration.

Endpoints:

- `GET /internal/automation/tasks`
- `GET /internal/automation/tasks/{task_id}`
- `POST /internal/automation/tasks/claim`
- `POST /internal/automation/tasks/follow-ups`
- `POST /internal/automation/cleanup/expired-consent-reminders`
- `POST /internal/automation/cleanup/stale-follow-ups`
- `POST /internal/automation/tasks/score-refresh/users/{user_id}`
- `POST /internal/automation/tasks/score-refresh/organizations/{organization_id}`
- `POST /internal/automation/consents/{consent_id}/ensure-expiry-reminder`
- `POST /internal/automation/tasks/{task_id}/execute`
- `POST /internal/automation/tasks/{task_id}/process`

### `internal_notifications.py` with prefix `/internal/notifications`

- `GET /internal/notifications`
- `GET /internal/notifications/{notification_delivery_id}`

### `internal_workers.py` with prefix `/internal/workers`

- `GET /internal/workers/runs`
- `GET /internal/workers/runs/{worker_run_id}`

### `internal_operations.py` with prefix `/internal/operations`

- `GET /internal/operations/overview`

### `internal_release.py` with prefix `/internal/release-readiness`

- `GET /internal/release-readiness`

### `internal_audit.py` with prefix `/internal/audit-logs`

- `GET /internal/audit-logs`

## Worker Runtime

The worker lives under `apps/worker`.

### `worker/coordination.py`

Purpose:

- prevent multiple workers from taking the same due work incorrectly.

Definitions:

- `WorkerCoordinationError`
  - Raised when coordination/lease logic fails.
- `WorkerExecutionLease`
  - Represents an execution lease.
- `NoopWorkerCoordinator`
  - Local/dev fallback coordination strategy.
- `RedisWorkerCoordinator`
  - Redis-backed coordination strategy.
- `build_worker_coordinator`
  - Chooses the coordination backend from settings.

### `worker/runtime.py`

Purpose:

- execute one full worker cycle against the API data model.

Definitions:

- `WorkerRunSummary`
  - Aggregated results from one worker cycle.
- `get_or_create_worker_user`
  - Ensures a worker identity exists.
- `run_worker_cycle`
  - Claims due automation tasks, notifications, and score recalculations, then records the outcome.

### `worker/main.py`

Purpose:

- CLI/service wrapper around the runtime cycle.

Definitions:

- `WorkerServiceIterationResult`
  - One loop iteration result.
- `run_worker_service_once`
  - Runs one iteration.
- `run_worker_service`
  - Runs continuously.
- `build_arg_parser`
  - CLI argument parser.
- `main`
  - Entrypoint.

### Runtime examples

- Local smoke run:
  - use `apps/worker/run_once.py`
- Continuous service run:
  - use `apps/worker/run_service.py`

## Frontend Application

The frontend lives under `apps/web/src`.

### App shell and routing

#### `app/AppShell.js`

Purpose:

- top-level signed-in shell and role-aware navigation.

Definitions:

- `formatRoleLabel`
  - Human-readable role text.
- `buildNavigation(session)`
  - Builds the visible menu from current capabilities plus the active workspace role.
- `NavigationLink`
  - Shell link component.
- `AppShell`
  - Main authenticated layout.

Important behavior:

- tabs are capability-driven and active-role-scoped,
- agency/internal tabs only appear when the session permits them,
- tenant and landlord modes show different personal navigation,
- the sidebar role switch changes the active workspace role and returns the user to `Home`,
- role visibility is not only cosmetic because router guards reinforce it.

#### `app/router.js`

Purpose:

- route map and route guards.

Definitions:

- `LoadingScreen`
- `RequireAuth`
- `RequireInternalAccess`
- `RequireAgencyAccess`
- `RequirePersonalWorkspace`
- `RedirectAuthenticatedHome`
- `createAppRouter`

#### `app/session.js`

Purpose:

- load `/auth/me`,
- derive frontend capabilities from explicit user workspace-role entitlements + organizations,
- normalize and persist the active workspace role,
- expose session state/actions to the app.

Definitions:

- `buildCapabilities(user, organizations, activeWorkspaceRole)`
- `getAvailableWorkspaceRoles(user, organizations)`
- `normalizeWorkspaceRole(role, user, organizations)`
- `getWorkspaceRoleLabel(role)`
- `getWorkspaceRoleCopy(role)`
- `isPersonalWorkspaceRole(role)`
- `SessionProvider`
- `useSession`

### Shared libraries

#### `lib/api.js`

Purpose:

- lightweight fetch wrapper and normalized API error formatting.

Definitions:

- `ApiError`
- `getRuntimeEnv`
- `formatApiErrorMessage`

Important detail:

- FastAPI validation error arrays are converted into readable strings instead of being rendered as raw objects.

#### `lib/i18n.js`

Purpose:

- English/Greek translation layer for the rebuilt frontend.

Definitions:

- `normalizeLanguage`
- `detectDefaultLanguage`
- `getDictionary`
- `translateCore`
- `translateText`
- `translateProps`
- `translateNode`
- `e`
- `getLanguageLocale`
- `LanguageDock`
- `LanguageProvider`
- `useLanguage`

### Pages

#### `pages/LandingPage.js`

- `PersonaCard`
- `LandingPage`

Purpose:

- public landing surface explaining personas and entry points.

#### `pages/AuthPage.js`

- `buildInitialState`
- `AuthPage`

Purpose:

- login, registration, and initial workspace role selection.

#### `pages/WorkspaceHomePage.js`

- `formatLabel`
- `SummaryCard`
- `buildAgencySlug`
- `MenuGuideCard`
- `OrganizationCard`
- `isStandaloneDisplayMode`
- `WorkspaceHomePage`

Purpose:

- signed-in home page,
- quick orientation,
- org summaries,
- installable/PWA cues,
- "where do I go next?" guidance.

#### `pages/TrustProfilePage.js`

- `formatLabel`
- `MetricCard`
- `buildInitialConsentForm`
- `updateNamedField`
- `TrustProfilePage`

Purpose:

- scores,
- score history,
- trust events,
- trust-report consent create/revoke,
- access-history visibility.

#### `pages/MarketplacePage.js`

- `formatMinorAmount`
- `MarketplacePage`

Purpose:

- browse open listings,
- submit applications,
- inspect own applications.

#### `pages/RecordsPage.js`

- `buildEvidenceForm`
- `buildHistoryImportForm`
- `buildTenancyForm`
- `buildPropertyCreateForm`
- `buildPropertyEditForm`
- `buildReferenceRequestForm`
- `buildTenancyPartyContext`
- `buildReferenceFulfillmentForm`
- `updateEntityForm`
- `updateSimpleForm`
- `parseMinorAmount`
- `parseTagText`
- `formatTagText`
- `RecordsPage`

Purpose:

- property setup,
- tenancy creation by email or ID,
- property assignment,
- evidence upload,
- history imports,
- reference requests,
- role/counterparty clarity on tenancy cards,
- active tenant/landlord role filtering,
- property tagging.

This is one of the most important pages because it covers the "build the trust record" lane.

#### `pages/OperationsPage.js`

- `formatMinorAmount`
- `parseMinorAmount`
- `updateEntityForm`
- `buildPaymentForm`
- `buildPaymentProofForm`
- `buildPaymentDecisionForm`
- `buildPaymentDisputeForm`
- `buildAppealForm`
- `buildDepositSettlementForm`
- `buildDepositDisputeForm`
- `buildMaintenanceForm`
- `buildSimpleNotesForm`
- `buildTenancyPartyContext`
- `formatArtifactMeta`
- `OperationsPage`

Purpose:

- day-to-day tenancy operations:
  - payments
  - deposits
  - maintenance
  - disputes
  - appeals
- selected-property role/counterparty context
- active tenant/landlord role filtering

This page is the closest equivalent to the practical "active tenancy operations desk."

#### `pages/AgencyWorkbenchPage.js`

- `MetricCard`
- `buildEmptyState`
- `formatMinorAmount`
- `parseMinorAmount`
- `formatPercent`
- `formatHours`
- `parseTagText`
- `formatTagText`
- `buildApplicationActions`
- `buildListingActions`
- `buildInitialPropertyForm`
- `buildInitialListingForm`
- `buildListingEditForm`
- `buildInitialTrustCheckForm`
- `buildInitialMembershipForm`
- `buildMembershipEditForm`
- `updateNamedField`
- `updateEntityForm`
- `AgencyWorkbenchPage`

Purpose:

- agency dashboard,
- commercial overview,
- properties and custom tags,
- listings and thresholds,
- applications and decisions,
- trust checks,
- team-access management.

#### `pages/InternalOperationsPage.js`

- `OverviewCard`
- `buildDecisionKey`
- `updateNote`
- `updateNamedField`
- `updateEntityForm`
- `buildDisputeVerdictForm`
- `canExecuteAutomationTask`
- `InternalOperationsPage`

Purpose:

- reviewer/admin workspace:
  - tenancy/evidence/history review
  - dispute verdicts
  - scoring control
  - automation queue control
  - account workspace-role management
  - worker/notification visibility
  - audit visibility
  - release readiness

This page replaces the legacy "judge" concept with a centralized internal review center.

#### `pages/SecurityPage.js`

- `DataPanel`
- `SecurityPage`

Purpose:

- session visibility,
- revoke current/other sessions,
- auth-related self-service security operations.

#### `pages/NotFoundPage.js`

- `NotFoundPage`

Purpose:

- fallback route.

### Frontend bootstrap

#### `main.js`

Definitions:

- `registerInstallLifecycle`
- `registerServiceWorker`

Purpose:

- bootstraps the React app,
- wraps it with the language provider,
- registers install/service worker behavior for the PWA-ready shell.

## Demo Data And Seeded Workflow Scenarios

The demo seed is designed to make real workflows visible immediately.

Primary entrypoint:

- `apps/api/app/devtools/demo_seed.py`

Minimal account-only reset entrypoint:

- `apps/api/dev_reset_minimal_users.py`

It creates:

- platform users,
- agency/internal organizations,
- memberships,
- properties and assignments,
- tenancies in multiple states,
- evidence and artifact records,
- listings and applications,
- payment/deposit/maintenance examples,
- dispute queues and verdict-ready states,
- trust checks and shareable flows.

The minimal reset script is destructive for local data. It wipes model tables and local private artifacts, then creates only the four requested users with explicit account workspace-role entitlements and no properties, tenancies, organizations, trust events, or operational records.

Key seeded scenarios:

- `Harbor Flat`
  - healthy active tenancy
  - confirmed payment
  - held deposit
  - resolved maintenance
  - uploaded evidence
  - reference fulfilled
- `Old Town Duplex`
  - ended tenancy
  - verdict-issued payment/deposit/maintenance disputes
  - ideal for appeal testing
- `Hillside Studio`
  - ended tenancy
  - pending payment/deposit/maintenance disputes
  - ideal for internal review queue testing
- `Agency Showcase Loft`
  - agency-facing property/listing/application/tag flow

## Core Workflow Examples

### 1. Landlord property setup

Flow:

1. landlord signs in
2. opens `Rental Records`
3. creates a property
4. optionally assigns:
   - agency organization
   - agency user
   - prospective tenant
5. later creates the tenancy using emails or IDs

Backend pieces involved:

- `Property`
- `Tenancy`
- `properties.py` routes/services
- `tenancies.py` routes/services
- `RecordsPage`

### 2. Evidence-backed tenancy onboarding

Flow:

1. user creates or imports a tenancy
2. uploads supporting documents
3. requests internal review or waits for counterparty confirmation
4. reviewer accepts/rejects evidence or the tenancy itself
5. trust events and verification state update

### 3. Payment dispute and appeal

Flow:

1. payment created
2. proof uploaded
3. counterparty decides
4. if challenged, a dispute is opened
5. internal reviewer issues verdict
6. either party can appeal
7. score recomputation incorporates or removes the adjudication adjustment depending on current state

### 4. Maintenance issue with evidence on both sides

Flow:

1. tenant reports issue with evidence
2. landlord acknowledges/resolves with notes and optional evidence
3. if disagreement remains, dispute is opened
4. internal reviewer issues verdict
5. appeal can reopen the matter

### 5. Deposit return dispute

Flow:

1. deposit record exists for tenancy
2. landlord proposes return/withholding with evidence
3. tenant disputes
4. internal reviewer issues verdict with score deltas if appropriate
5. either side can appeal

### 6. Agency trust screening

Flow:

1. subject user grants trust-report consent
2. agency validates consent with share token + access code
3. agency previews profile
4. agency creates audited trust check
5. trust-check access becomes visible in subject access history

## What Was Corrected In This Documentation Checkpoint

This pass intentionally did not add a new product feature sprint. It cleaned and documented the current state so Sprint 19 starts from a clearer base.

Corrections made in this checkpoint:

- aligned the codebase docs around a new technical reference,
- corrected the workspace-guide language-switch text,
- aligned the API stage marker with the current checkpoint instead of leaving it on an older post-Sprint-17 marker,
- added documentation/test hooks so the new reference becomes part of the maintained source-of-truth set.

## Safe Places To Start The Next Sprint

If the next sprint is visual/design-heavy, these are the safest entry points:

- `apps/web/src/styles/index.css`
- `apps/web/src/app/AppShell.js`
- `apps/web/src/pages/WorkspaceHomePage.js`
- `apps/web/src/pages/AgencyWorkbenchPage.js`
- `apps/web/src/pages/OperationsPage.js`
- `apps/web/src/pages/InternalOperationsPage.js`

If the next sprint is workflow-polish-heavy, start here:

- `apps/web/src/pages/RecordsPage.js`
- `apps/web/src/pages/OperationsPage.js`
- `apps/api/app/api/routes/payments.py`
- `apps/api/app/api/routes/deposits.py`
- `apps/api/app/api/routes/maintenance.py`
- `apps/api/app/api/routes/internal_disputes.py`

If the next sprint is platform/runtime-heavy, start here:

- `apps/api/app/core/config.py`
- `apps/api/app/core/health.py`
- `apps/api/app/services/automation.py`
- `apps/api/app/services/notifications.py`
- `apps/api/app/services/scoring.py`
- `apps/worker/worker/runtime.py`

## Final Orientation Advice

When something feels hard to find, ask three questions:

1. Is this a business concept, a transport shape, or a UI shape?
2. If it is a business concept, which enum or model owns its vocabulary?
3. If it is a UI action, which page calls which route, and which service builds the response?

That mental model usually gets you to the right file quickly:

- vocabulary -> `packages/domain`
- persisted state -> `apps/api/app/models`
- request/response shape -> `apps/api/app/schemas`
- business assembly -> `apps/api/app/services`
- HTTP behavior -> `apps/api/app/api/routes`
- user interaction -> `apps/web/src/pages`
- background execution -> `apps/worker`
