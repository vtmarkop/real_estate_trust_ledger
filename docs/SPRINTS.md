# Sprint Tracker

## Program Status

- Completed: Sprint 0 through Sprint 20
- Post-Sprint-17 remediation checkpoint: complete
- Post-Sprint-18 workflow simplification checkpoint: complete
- Post-Sprint-18 workflow diagram checkpoint: complete
- Post-Sprint-20 cross-device continuity checkpoint: complete
- Post-Sprint-20 GitHub bootstrap checkpoint: complete
- Post-Sprint-20 dispute continuity checkpoint: complete
- Post-Sprint-20 archive-alignment UX reset checkpoint: in progress
- Next planned delivery lane: Sprint 21 frontend experience track for motion, accessibility, and release-level frontend refinement
- Sprint 17 outcome: the rebuilt app now has substantially fuller frontend parity for core operator and review actions, clearer dispute handling, visible evidence upload/storage behavior, and better day-to-day agency portfolio management
- Post-Sprint-17 remediation outcome: archive-parity audit completed, operational document uploads now reach payments/deposits/maintenance in the web app, single-session revoke is available, internal automation cleanup actions are surfaced, and regression coverage was expanded around operational artifact links
- Sprint 18 outcome: the rebuilt frontend now supports English and Greek with a persistent language switch, shared translation infrastructure, locale-aware currency formatting, and localized frontend error presentation before the visual redesign arc
- Pre-Sprint-19 documentation checkpoint outcome: the repo now includes a full technical codebase reference, corrected operator-guide wording, aligned runtime status markers, and stronger source-of-truth coverage before the visual/frontend polish track
- Post-Sprint-18 workflow simplification checkpoint outcome: the heaviest frontend workspaces now run in focused lanes, agency and review pages are split by concern, and the repo includes a dedicated workflow map that traces the main business paths from backend logic to frontend usage
- Post-Sprint-18 workflow diagram checkpoint outcome: the repo now includes Mermaid diagrams for the implemented product flows, covering workspace access, property-to-tenancy setup, artifacts/evidence, listings/applications, trust sharing, disputes, review queues, scoring, and demo scenarios
- Sprint 19 outcome: the rebuilt frontend now has a darker cinematic design system, variable-driven density tokens, a real compact workspace mode in the shell, stronger panel/nav hierarchy, and a more production-grade visual foundation for the page-by-page conversion sprint
- Sprint 20 outcome: the rebuilt frontend now applies the cinematic system across the main pages with richer hero summaries, clearer section framing, additional lane separation on trust, marketplace, and security surfaces, a completed localization refactor that fixes the live language switch and materially expands English/Greek coverage on the Sprint 20 pages, and a surgical UI-semantics pass that distinguishes statuses, facts, notes, and timeline activity far more clearly across the heavier operational cards
- Post-Sprint-20 cross-device continuity checkpoint outcome: the repo now includes a durable handoff system with repo-wide agent instructions, a live handoff file, a workflow-gap tracker, and a daily workstation sync guide so work can continue safely across devices and new Codex threads
- Post-Sprint-20 GitHub bootstrap checkpoint outcome: the repo is now prepared for a first private GitHub publish as `real_estate_trust_ledger`, with local-only databases and artifact storage excluded from version control and the full first-push plus home/work sync procedure documented in-project
- Post-Sprint-20 dispute continuity checkpoint outcome: payment, deposit, and maintenance dispute flows now surface explicit appeal and re-review handoffs in both the user dispute desk and `Review Center > Disputes`, and the payment counterparty decision path is blocked once a case has moved into reviewer flow
- Post-Sprint-20 archive-alignment UX reset status: the reset is underway on branch `codex/archive-ux-reset`, with the first slices restoring property targeting, selected-property operational history, and compact payment/issue detail dropdowns in `Rent & Issues` while preserving the rebuilt dispute/reviewer architecture
- Remaining planned launch track: none
- Remaining planned post-pilot experience track: Sprint 21

## Sprint 0: Foundation Reset

### Objective

Create a safe rebuild lane and stop relying on chat history as project memory.

### In Scope

- archive the MVP,
- establish rebuild folder structure,
- define source-of-truth docs,
- add initial verification tests,
- create minimal app placeholders for the rebuild.

### Acceptance Criteria

- legacy MVP is preserved in a dated archive folder,
- all new rebuild work has a clean home under `apps/` and `packages/`,
- architecture, roadmap, and decisions are written in repo docs,
- the workspace layout test passes.

### Deliverables

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/SPRINTS.md`
- `docs/DECISIONS.md`
- initial rebuild placeholders under `apps/` and `packages/`
- `tests/test_repo_layout.py`

## Sprint 1: Identity And Access

### Planned Scope

- users, organizations, memberships,
- sessions, auth flows, RBAC,
- agency access boundaries,
- reviewer/admin role definition,
- consent primitives.

### Planned Exit Criteria

- auth is modeled for the rebuild,
- roles are explicit and enforceable,
- tests cover critical access boundaries.

### Current Progress

Completed in the first Sprint 1 slice:

- secure API settings scaffold with environment validation,
- database engine/session wiring,
- shared access enums in the domain package,
- initial models for users, organizations, memberships, auth sessions, and report consents,
- in-memory tests for config rules, security helpers, role capabilities, and model integration.

Completed in the second Sprint 1 slice:

- Alembic scaffold and first migration baseline for identity and access,
- versioned API routing under `/api/v1`,
- session-based auth dependencies,
- register, login, logout, and current-user endpoints,
- API tests for the full auth session flow,
- verified local migration execution against SQLite.

Completed in the third Sprint 1 slice:

- RBAC dependencies for system-role and organization access checks,
- organization creation endpoint with owner membership bootstrap,
- organization membership listing and member-add flows,
- internal reviewer/admin access surface,
- API tests covering org access, membership management, and protected internal routes.

Completed in the fourth Sprint 1 slice:

- trust report consent issue, list, and revoke endpoints for end users,
- agency-scoped trust-check validate, create, and list endpoints,
- audited `agency_trust_checks` model and follow-up Alembic migration,
- shared consent validation service for trust-check execution,
- API tests covering consent lifecycle, revoked consent behavior, and trust-check permission gates.

Completed in the fifth Sprint 1 slice:

- organization membership role-update and activation/deactivation flows,
- owner-safety guard that prevents an organization from losing its last active owner,
- first consent-aware trust profile summary service and profile-preview endpoint,
- trust-check create responses enriched with a minimal trust profile payload,
- API tests covering membership lifecycle invariants and trust-profile responses.

### Current Deliverables

- `apps/api/.env.example`
- `apps/api/requirements.txt`
- `apps/api/app/core/config.py`
- `apps/api/app/core/db.py`
- `apps/api/app/core/security.py`
- `apps/api/app/models/*.py`
- `packages/domain/trustledger_domain/access.py`
- `tests/test_api_identity_foundations.py`
- `apps/api/alembic.ini`
- `apps/api/alembic/`
- `apps/api/app/api/`
- `apps/api/app/schemas/auth.py`
- `tests/test_auth_api.py`
- `apps/api/app/schemas/organization.py`
- `apps/api/app/schemas/internal.py`
- `apps/api/app/schemas/consent.py`
- `apps/api/app/schemas/trust_check.py`
- `apps/api/app/api/routes/organizations.py`
- `apps/api/app/api/routes/internal.py`
- `apps/api/app/api/routes/consents.py`
- `apps/api/app/api/routes/trust_checks.py`
- `apps/api/app/services/consents.py`
- `apps/api/app/services/trust_profiles.py`
- `tests/test_organization_rbac_api.py`
- `tests/test_consent_trust_checks_api.py`

### Next Slice

Sprint 1 is now functionally complete for the current planned scope.

## Sprint 2: Tenancies And Trust Events

### Planned Scope

- tenancy and lease backbone,
- structured trust events,
- reviewer queue primitives,
- early property-linked trust profile signals,
- foundations for later evidence and scoring work.

### Planned Exit Criteria

- tenancy history is represented in the rebuild domain,
- trust-changing actions append structured events,
- reviewer workflows can process queued tenancy verification,
- agency trust profiles can expose tenancy-derived summary signals.

### Current Progress

Completed in the first Sprint 2 slice:

- shared tenancy, verification, and trust-event enums in the domain package,
- `tenancies` and `trust_events` models with Alembic migration support,
- tenancy create, self list, and review-request endpoints,
- internal reviewer queue list and review-decision endpoints,
- trust-event append helpers and tenancy response builder services,
- trust-profile summary enrichment with tenancy and trust-event counts,
- API tests covering tenancy participation rules, review queue flow, and profile updates.

Completed in the second Sprint 2 slice:

- reusable `properties` model with property create/list endpoints,
- tenancy linkage to reusable properties while preserving tenancy address snapshots,
- counterparty-confirmation flow for tenancy history before reviewer escalation,
- trust-event read surfaces for the current user and tenancy-specific authorized viewers,
- trust-profile enrichment with linked-property and counterparty-confirmation counts,
- API tests covering property reuse, confirmation behavior, and trust-event history reads.

Completed in the third Sprint 2 slice:

- agency-owned `listings` and tenant `listing_applications` models with Alembic migration support,
- listing publish, list, update, and open-listing discovery endpoints,
- application submit, self-list, organization-list, and agency status-update endpoints,
- eligibility rules based on counterparty-confirmed and verified tenancy history as a pre-score hook,
- trust-event writes for listing publication and application lifecycle changes,
- API tests covering agency permissions, eligibility enforcement, and application lifecycle history.

### Current Deliverables

- `packages/domain/trustledger_domain/trust.py`
- `apps/api/app/models/tenancy.py`
- `apps/api/app/models/trust_event.py`
- `apps/api/alembic/versions/20260409_0003_tenancies_and_trust_events.py`
- `apps/api/app/models/property.py`
- `apps/api/alembic/versions/20260409_0004_properties_and_confirmation.py`
- `apps/api/app/models/listing.py`
- `apps/api/app/models/application.py`
- `apps/api/alembic/versions/20260409_0005_listings_and_applications.py`
- `apps/api/app/schemas/property.py`
- `apps/api/app/schemas/tenancy.py`
- `apps/api/app/schemas/listing.py`
- `apps/api/app/schemas/trust_event.py`
- `apps/api/app/api/routes/listings.py`
- `apps/api/app/api/routes/properties.py`
- `apps/api/app/api/routes/tenancies.py`
- `apps/api/app/api/routes/trust_events.py`
- `apps/api/app/api/routes/internal.py`
- `apps/api/app/services/listings.py`
- `apps/api/app/services/properties.py`
- `apps/api/app/services/tenancies.py`
- `apps/api/app/services/trust_events.py`
- `apps/api/app/services/trust_profiles.py`
- `tests/test_tenancy_review_api.py`
- `tests/test_listing_application_api.py`

### Next Slice

Sprint 2 is now functionally complete for the current planned scope.

## Sprint 3: Evidence And Verification Flows

### Planned Scope

- evidence document records,
- tenancy evidence submission,
- landlord reference inputs,
- reviewer verification workflows on uploaded/declared evidence,
- foundations for cold-start onboarding imports.

### Planned Exit Criteria

- evidence can be modeled and attached to a trust history object,
- users can submit verification material without bank APIs,
- reviewer decisions can act on structured evidence records,
- trust profiles can begin reflecting evidence-backed verification strength.

### Current Progress

Completed in the first Sprint 3 slice:

- `evidence_documents` model with structured evidence types and reviewer decision states,
- tenancy-linked evidence submission flow for participants,
- reviewer/admin evidence queue list and decision endpoints,
- trust-event support for evidence submission and accepted/rejected review outcomes,
- trust-profile enrichment with evidence-backed counts for submitted, accepted, and rejected documents,
- API tests covering evidence submission, access control, queue processing, and profile-summary updates,
- verified Alembic migration chain through the evidence workflow schema.

Completed in the second Sprint 3 slice:

- `history_imports` model as a cold-start onboarding bundle owned by a subject user,
- tenancy linkage into draft history imports without disrupting the existing live-tenancy flow,
- self-service history import create/list/submit endpoints,
- reviewer/admin history-import queue list and accept/reject decisions,
- trust-profile enrichment with submitted/accepted/rejected history import counts,
- trust-event support for history import submission and review outcomes,
- API tests covering non-empty bundle rules, subject-only submission, and accepted import visibility in agency trust profiles,
- verified Alembic migration chain through the history import schema.

Completed in the third Sprint 3 slice:

- `reference_requests` model for subject-controlled counterparty reference requests,
- explicit request-and-fulfill flow for landlord references without letting the subject self-fulfill them,
- provenance linkage from fulfilled reference requests into evidence records and trust events,
- trust-profile enrichment with counterparty reference counts and accepted counterparty reference counts,
- API tests covering request ownership, duplicate protection, counterparty-only fulfillment, and agency visibility of accepted counterparty references,
- verified Alembic migration chain through the reference-request schema.

### Current Deliverables

- `apps/api/app/models/evidence.py`
- `apps/api/alembic/versions/20260410_0006_evidence_documents.py`
- `apps/api/app/schemas/evidence.py`
- `apps/api/app/api/routes/tenancies.py`
- `apps/api/app/api/routes/internal.py`
- `apps/api/app/services/evidence.py`
- `apps/api/app/services/trust_events.py`
- `apps/api/app/services/trust_profiles.py`
- `tests/test_evidence_review_api.py`
- `apps/api/app/models/history_import.py`
- `apps/api/alembic/versions/20260410_0007_history_imports.py`
- `apps/api/app/schemas/history_import.py`
- `apps/api/app/api/routes/history_imports.py`
- `apps/api/app/services/history_imports.py`
- `tests/test_history_import_api.py`
- `apps/api/app/models/reference_request.py`
- `apps/api/alembic/versions/20260410_0008_reference_requests.py`
- `apps/api/app/schemas/reference_request.py`
- `apps/api/app/api/routes/reference_requests.py`
- `apps/api/app/services/reference_requests.py`
- `tests/test_reference_request_api.py`

### Next Slice

Sprint 3 is now functionally complete for the current planned scope.

## Sprint 4: Scoring Foundations

### Planned Scope

- central scoring and verification-strength inputs,
- score snapshot model,
- score history records,
- first deterministic recalculation service,
- pre-worker recalculation entry points.

### Planned Exit Criteria

- trust and verification strength can be derived from current structured history,
- scoring logic is centralized instead of living inside route handlers,
- score history is persisted and queryable for later automation.

### Current Progress

Completed in the first Sprint 4 slice:

- `trust_score_snapshots` and `trust_score_history` models with Alembic migration support,
- centralized deterministic scoring service with score versioning and persisted snapshot/history refresh logic,
- current-user score summary and score-history read endpoints,
- trust-profile enrichment with tenant score, landlord score, verification strength, scoring version, and score calculation timestamp,
- API tests covering score persistence, stable history behavior when scores do not change, and score visibility inside agency trust profiles,
- verified Alembic migration chain through the scoring schema.

Completed in the second Sprint 4 slice:

- canonical score calculation reasons shared across public and internal scoring entry points,
- reviewer/admin internal scoring endpoints for user-targeted recalculation and score-history inspection,
- API tests covering internal score recalculation, stable unchanged-history behavior, and permission enforcement.

Completed in the third Sprint 4 slice:

- persisted `trust_score_recalculation_requests` and `trust_score_recalculation_batches` tables with Alembic migration support,
- worker-ready scoring service helpers for queued single-user recalculation, scoped batch creation, and batch status rollup,
- internal scoring endpoints for request creation, request processing, batch creation, and batch inspection,
- API tests covering queued recalculation idempotency and organization-scoped batch completion flow,
- verified Alembic migration chain through the score-recalculation queue schema.

### Current Deliverables

- `apps/api/app/models/trust_score.py`
- `apps/api/alembic/versions/20260410_0009_trust_scores.py`
- `apps/api/app/schemas/score.py`
- `apps/api/app/api/routes/trust_scores.py`
- `apps/api/app/services/scoring.py`
- `apps/api/app/services/trust_profiles.py`
- `tests/test_trust_scores_api.py`
- `apps/api/app/api/routes/internal_scoring.py`
- `tests/test_internal_scoring_api.py`
- `apps/api/app/models/trust_score_recalculation.py`
- `apps/api/alembic/versions/20260411_0010_trust_score_recalculation_queue.py`

### Next Slice

Sprint 4 is now functionally complete for the current planned scope.

## Sprint 5: Operational Trust Flows

### Planned Scope

- payment obligations and settlement tracking,
- deposit lifecycle records,
- maintenance tickets and reviewer-visible dispute state,
- operational trust events that feed later score expansion,
- safe first negative-signal foundations without over-automating blame.

### Planned Exit Criteria

- rental operations can be recorded as first-class domain objects instead of inferred from generic evidence,
- disputes and resolutions remain structured and auditable,
- operational trust signals are ready for later score integration and automation.

### Current Progress

Completed in the first Sprint 5 slice:

- `payment_records` model with explicit payer/payee roles, payment status, proof state, and counterparty action fields,
- tenancy-linked payment create, list, proof-submit, and confirm/reject endpoints,
- trust-event linkage for payment creation, proof submission, confirmation, and rejection,
- API tests covering payer-created proof-backed payments, payee-created pending obligations, rejection, and resubmission flow,
- verified Alembic migration chain through the payment-record schema.

Completed in the second Sprint 5 slice:

- `deposit_records` model with one settlement record per tenancy, held/proposed/withheld amount fields, and dispute-ready notes,
- tenancy-linked deposit create, settlement, and dispute endpoints,
- trust-event linkage for deposit record opening, settlement submission, and dispute lifecycle,
- API tests covering partial withholding, tenant dispute, uniqueness rules, and zero-deposit rejection,
- verified Alembic migration chain through the deposit-record schema.

Completed in the third Sprint 5 slice:

- `maintenance_tickets` model with open/acknowledged/resolved/disputed states and participant action attribution,
- tenancy-linked maintenance report, acknowledge, resolve, and dispute endpoints,
- trust-event linkage for maintenance reporting and dispute-ready operational history,
- API tests covering end-to-end resolution flow, tenant dispute, and permission boundaries,
- verified Alembic migration chain through the maintenance-ticket schema.

### Current Deliverables

- `apps/api/app/models/payment.py`
- `apps/api/alembic/versions/20260411_0011_payment_records.py`
- `apps/api/app/schemas/payment.py`
- `apps/api/app/api/routes/payments.py`
- `apps/api/app/services/payments.py`
- `apps/api/app/services/trust_events.py`
- `tests/test_payments_api.py`
- `apps/api/app/models/deposit.py`
- `apps/api/alembic/versions/20260411_0012_deposit_records.py`
- `apps/api/app/schemas/deposit.py`
- `apps/api/app/api/routes/deposits.py`
- `apps/api/app/services/deposits.py`
- `tests/test_deposits_api.py`
- `apps/api/app/models/maintenance_ticket.py`
- `apps/api/alembic/versions/20260411_0013_maintenance_tickets.py`
- `apps/api/app/schemas/maintenance.py`
- `apps/api/app/api/routes/maintenance.py`
- `apps/api/app/services/maintenance.py`
- `tests/test_maintenance_api.py`

### Next Slice

Sprint 5 is now functionally complete for the current planned scope.

## Sprint 6: Agency Product

### Planned Scope

- score-aware agency screening and listing rules,
- consent-safe trust profile access expansion,
- agency-visible applicant evaluation surfaces,
- tighter alignment between listings and the central score engine.

### Planned Exit Criteria

- agencies can use real trust scores for listing gates and screening,
- agency flows no longer rely on temporary pre-score heuristics,
- applicant evaluation remains consent-aware and auditable.

### Current Progress

Completed in the first Sprint 6 slice:

- score-aware listing threshold fields added to listings and exposed in listing APIs,
- listing application eligibility now uses the central scoring service instead of temporary tenancy-count heuristics,
- API tests updated to validate passing and blocking behavior against actual tenant-score and verification-strength thresholds,
- verified Alembic migration chain through the score-aware listing-threshold schema.

Completed in the second Sprint 6 slice:

- application-time applicant score and verification snapshots stored on `listing_applications`,
- agency screening dashboard endpoint added with listing/application counts and snapshot-based applicant averages,
- agency application responses now expose the captured applicant scoring context instead of forcing recalculation on every list call,
- API tests updated to validate application snapshot persistence and dashboard rollup behavior,
- full regression suite re-verified after the agency dashboard surface was introduced.

### Current Deliverables

- `apps/api/alembic/versions/20260411_0014_listing_score_thresholds.py`
- `apps/api/app/models/listing.py`
- `apps/api/app/schemas/listing.py`
- `apps/api/app/api/routes/listings.py`
- `apps/api/app/services/listings.py`
- `tests/test_listing_application_api.py`
- `apps/api/alembic/versions/20260411_0015_application_score_snapshots.py`

### Next Slice

Sprint 6 is now functionally complete for the current planned scope.

## Sprint 7: Automation Layer

### Planned Scope

- worker-aligned automation records and queues,
- reminders, expirations, and reviewer/admin follow-up tasks,
- scheduled recalculation and cleanup jobs built on the existing persisted request path.

### Planned Exit Criteria

- backgroundable automation work is represented as durable records instead of implicit cron assumptions,
- reminder and expiry workflows can be processed by the future worker without changing API contracts,
- score recalculation automation reuses the persisted request/batch path already in place.

### Current Progress

Completed in the first Sprint 7 slice:

- `automation_tasks` model with worker-aligned task type, status, scheduling, and processing fields,
- automatic consent-expiry reminder creation on trust-report consent issue and cancellation on consent revocation,
- reviewer/admin internal automation endpoints for queue listing, consent-reminder backfill, follow-up task creation, and explicit task processing,
- API tests covering consent-reminder lifecycle, follow-up task processing, and permission boundaries,
- full regression suite and fresh Alembic verification through the automation-task schema.

Completed in the second Sprint 7 slice:

- scheduled automation task types for user score refresh and organization score batch refresh,
- automation-task linkage to the persisted score recalculation request and batch records,
- execution endpoints that enqueue recalculation work through the existing scoring request/batch path instead of bypassing it,
- API tests covering scheduled score-refresh task creation and execution for both user and organization flows,
- full regression suite and fresh Alembic verification through the automation-task scoring-link schema.

Completed in the third Sprint 7 slice:

- due-task claim endpoint for worker-style pickup of pending automation records,
- execution support for consent-expiry reminder tasks so reminders can move through the same task lifecycle as score refresh jobs,
- cleanup endpoints for expired consent reminders and stale internal follow-up tasks that no longer need manual closure,
- API tests covering due-task claim behavior, reminder execution/cleanup, and stale follow-up cleanup,
- full regression suite re-verified after the worker-style queue surfaces were added.

### Current Deliverables

- `apps/api/app/models/automation_task.py`
- `apps/api/alembic/versions/20260411_0016_automation_tasks.py`
- `apps/api/alembic/versions/20260411_0017_automation_task_scoring_links.py`
- `apps/api/app/schemas/automation.py`
- `apps/api/app/api/routes/internal_automation.py`
- `apps/api/app/services/automation.py`
- `apps/api/app/api/routes/consents.py`
- `tests/test_internal_automation_api.py`

### Next Slice

Sprint 7 is now functionally complete for the current planned scope.

Next slice:

- begin Sprint 8 enterprise hardening with durable audit logging for sensitive trust-sharing, agency screening, and internal operations,
- keep the first hardening slice narrow enough to apply consistently across existing API surfaces without destabilizing the core product.

## Sprint 8: Enterprise Hardening

### Planned Scope

- durable auditability for sensitive platform actions,
- privacy-supporting access history for trust-sharing,
- operational hardening surfaces that improve accountability without rewriting core flows.

### Planned Exit Criteria

- sensitive user, agency, and internal actions leave an append-only audit trail,
- relevant access history can be inspected by internal staff and by the affected subject user where appropriate,
- hardening features reuse the existing domain and permission model instead of introducing a parallel subsystem.

### Current Progress

Completed in the first Sprint 8 slice:

- append-only `audit_logs` model and migration for sensitive operational tracing,
- internal audit-log read endpoint with action, actor, and organization filters,
- audit-log writes for trust-report consent lifecycle, agency trust-check access, and internal automation claim/execute/cleanup actions,
- API tests covering internal audit visibility across trust-sharing and automation flows,
- full regression suite and fresh Alembic verification through the audit-log schema.

Completed in the second Sprint 8 slice:

- subject-facing trust-report access-history endpoint backed by the new audit-log stream,
- API coverage proving a user can inspect agency validation, preview, and trust-check access against their own shared profile,
- full regression suite re-verified after adding the privacy-facing access-history surface.

Completed in the third Sprint 8 slice:

- denied trust-check access attempts are now written into the audit-log stream with an explicit denied outcome,
- trust-sharing validation helpers now preserve enough consent context to log failed protected-access attempts without exposing secrets,
- API coverage proving reviewers can inspect denied trust-check access against a subject's shared profile,
- full regression suite re-verified after the denied-access audit path was introduced.

Completed in the fourth Sprint 8 slice:

- trust-report consents now track failed access-code attempts, last access attempt timing, temporary lockout state, and last successful validation time,
- repeated invalid trust-check access attempts now trigger a temporary consent-level lockout instead of allowing unlimited retries,
- subject-facing consent responses now expose the lockout-related state needed for support and transparency,
- API coverage proving repeated invalid attempts trigger lockout and a later successful validation resets the counters,
- full regression suite and fresh Alembic verification through the consent-lockout schema.

Completed in the fifth Sprint 8 slice:

- active-session visibility endpoint for authenticated users on the existing server-side session model,
- targeted session revocation and revoke-other-sessions controls with cookie cleanup when the current session is revoked,
- session creation and revocation audit events aligned with the broader audit-log discipline,
- API coverage proving users can inspect sessions, revoke other sessions, and revoke the current session cleanly,
- full regression suite re-verified after the session-management surface was added.

Completed in the sixth Sprint 8 slice:

- user accounts now track failed login attempts, last login attempt timing, temporary login lockout state, and last successful login time,
- repeated invalid password attempts now trigger a temporary account-level login lockout instead of allowing unlimited retries,
- user responses now expose last successful login time for current-user security visibility,
- API coverage proving repeated invalid logins trigger lockout and a later successful login resets the counters,
- full regression suite and fresh Alembic verification through the user-login-lockout schema.

Completed in the seventh Sprint 8 slice:

- denied-login attempts for known users now write audit events instead of remaining invisible operationally,
- authenticated users can now inspect their own auth security-event stream including session creation, revocation, and denied-login activity,
- API coverage proving current-user security events include denied-login and session lifecycle activity,
- full regression suite re-verified after the user-facing auth security-event surface was added.

### Current Deliverables

- `apps/api/app/models/audit_log.py`
- `apps/api/alembic/versions/20260411_0018_audit_logs.py`
- `apps/api/app/schemas/audit_log.py`
- `apps/api/app/services/audit_logs.py`
- `apps/api/app/api/routes/internal_audit.py`
- `apps/api/app/api/routes/consents.py`
- `apps/api/app/api/routes/trust_checks.py`
- `apps/api/app/api/routes/internal_automation.py`
- `tests/test_internal_audit_api.py`
- `tests/test_consent_trust_checks_api.py`

### Next Slice

Next slice:

Sprint 8 is now functionally complete for the current planned scope.

Next slice:

- begin a worker-runtime slice so the automation and scoring queues can be executed by a concrete worker component instead of only through API-triggered processing,
- keep the first worker slice narrow, synchronous, and testable inside the current monolith workspace.

## Sprint 9: Worker Runtime

### Planned Scope

- give the worker app a concrete execution loop for due automation and scoring work,
- keep worker behavior aligned with the same service-layer contracts already used by the API,
- start with a single synchronous worker cycle before introducing long-running orchestration.

### Planned Exit Criteria

- `apps/worker` is capable of meaningfully processing due queued work,
- worker execution reuses existing queue models and service logic instead of inventing parallel rules,
- worker behavior is covered by targeted tests and the broader regression suite.

### Current Progress

Completed in the first Sprint 9 slice:

- synchronous worker runtime that claims due automation tasks, executes them, and then processes due score recalculation requests,
- dedicated worker user bootstrap for traceable internal execution identity,
- worker CLI entrypoint updated from scaffold-only status to a real one-cycle runner,
- API service helpers expanded to support worker failure handling and due-score request discovery,
- focused worker runtime tests plus full regression-suite verification.

Completed in the second Sprint 9 slice:

- worker runtime now cleans expired consent reminders and stale internal follow-up tasks before claiming executable work,
- worker execution now writes durable audit logs for task claim, task execution, queue cleanup, and score-request processing,
- synchronous worker tests expanded to cover cleanup behavior and audit visibility,
- full regression suite re-verified after aligning worker processing with the platform audit discipline.

Completed in the third Sprint 9 slice:

- score recalculation requests now track processing ownership and attempt counts on the persisted queue records,
- the scoring service now supports explicit claim-and-process flow for due score requests instead of relying on a read-only pending list,
- worker score processing now claims requests first and writes a distinct score-request-claimed audit event before execution,
- internal scoring responses now expose queue-processing metadata needed for support and operations visibility,
- full regression suite and fresh Alembic verification re-run through the score-request processing-tracking schema.

Completed in the fourth Sprint 9 slice:

- worker cycles now persist first-class `worker_runs` records with run status, due-boundary context, queue counts, and last-error details,
- worker runtime now finalizes run records on both successful and failed cycles instead of leaving execution observability only in task rows and audit logs,
- internal reviewer/admin APIs can now list worker runs and inspect a single run directly,
- worker runtime tests now cover both successful run persistence and failed-run recording, with API coverage for internal worker-run visibility,
- full regression suite and fresh Alembic verification re-run through the worker-run schema.

Completed in the fifth Sprint 9 slice:

- internal operations overview endpoint now summarizes review backlog, automation backlog, score-recalculation backlog, and latest worker activity in one response,
- the overview surface reads directly from the current domain queue models instead of introducing a separate reporting store,
- API coverage now proves reviewers can inspect combined operations state while regular users remain blocked,
- full regression suite re-verified after adding the internal operations overview surface.

### Current Deliverables

- `apps/worker/worker/runtime.py`
- `apps/worker/worker/main.py`
- `apps/worker/README.md`
- `tests/test_worker_runtime.py`
- `apps/api/app/services/automation.py`
- `apps/api/app/services/scoring.py`
- `apps/api/alembic/versions/20260411_0021_score_request_processing_tracking.py`
- `apps/api/app/models/trust_score_recalculation.py`
- `apps/api/app/schemas/score.py`
- `apps/api/app/api/routes/internal_scoring.py`
- `tests/test_internal_scoring_api.py`
- `apps/api/alembic/versions/20260411_0022_worker_runs.py`
- `apps/api/app/models/worker_run.py`
- `apps/api/app/schemas/worker_run.py`
- `apps/api/app/services/worker_runs.py`
- `apps/api/app/api/routes/internal_workers.py`
- `tests/test_internal_worker_api.py`
- `apps/api/app/schemas/operations.py`
- `apps/api/app/api/routes/internal_operations.py`
- `tests/test_internal_operations_api.py`

### Next Slice

Next slice:

- begin the first real `apps/web` rebuild slice on top of the now-stabilized API and internal operations surfaces,
- keep that web slice narrow: app shell, auth/session wiring, and route scaffolding before feature-heavy screens.

## Sprint 10: Web App Foundation

### Planned Scope

- establish the real `apps/web` application lane,
- connect the shell to the server-side session model,
- add public, authenticated, and internal route boundaries,
- expose the first user-facing security and internal operations surfaces.

### Planned Exit Criteria

- `apps/web` contains a real frontend scaffold instead of only a placeholder README,
- the web shell can reason about authenticated versus anonymous session state,
- route boundaries align with the backend permission model,
- the first frontend slice is covered by repo-level verification that fits the local toolchain.

### Current Progress

Completed in the first Sprint 10 slice:

- `apps/web` now has a real Vite/React scaffold with package manifest, entry HTML, and source folders,
- session-aware auth wiring now targets `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/me`, and `/api/v1/auth/logout`,
- public, authenticated, and internal route scaffolding now exists with a navigable shell layout,
- user-facing security and internal operations pages are wired to live API surfaces instead of placeholder-only local state,
- web source files were parsed successfully with a real JavaScript module parser using the archived toolchain packages already in the workspace,
- frontend scaffold tests were added and the full regression suite was re-verified after the first web slice landed.

Completed in the second Sprint 10 slice:

- current-user organization discovery now exists at `/api/v1/organizations/mine` so the web app can discover live agency context without hardcoded identifiers,
- the workspace home page now reads live trust-score and organization data instead of acting as a static post-login placeholder,
- a dedicated trust profile page now reads canonical score summary and score history from the rebuilt scoring APIs,
- the agency workbench now reads live screening-dashboard data with selectable agency context and recent application activity,
- Node 24 and npm 11 were installed locally for the rebuild lane, `apps/web` dependencies were installed, and real Vite production-build and dev-server verification replaced parser-only frontend checks,
- targeted web and organization API tests plus the full regression suite were re-verified after the live frontend slice landed.

Completed in the third Sprint 10 slice:

- the agency workbench now loads full live listing and application queues for the selected agency context, not just dashboard rollups,
- agency operators can now move applications through allowed backend status transitions directly from the web app,
- the agency frontend continues to rely only on existing backend contracts for listings, applications, and dashboard data instead of introducing client-only state models,
- targeted web and listing-application tests plus a fresh real Vite production build were re-verified after the operator-flow slice landed.

Completed in the fourth Sprint 10 slice:

- the agency workbench now supports property creation and listing publication directly from the rebuilt web app,
- property and listing forms reuse the existing backend APIs and feed immediately into the same live dashboard, listing, and application views,
- targeted web and listing-application tests plus a fresh real Vite production build were re-verified after the publishing slice landed.

Completed in the fifth Sprint 10 slice:

- a new marketplace route now exposes live open listings and current-user application history,
- authenticated users can now submit listing applications from the rebuilt web app against the existing score-gated backend rules,
- targeted web and listing-application tests plus a fresh real Vite production build were re-verified after the applicant slice landed.

Completed in the sixth Sprint 10 slice:

- authenticated users can now discover active agencies through a new agency-directory API path designed for trust-sharing UX,
- the trust profile page now combines score visibility with consent issuance, consent revocation, and trust-report access-history reads,
- targeted organization, consent, and frontend tests plus a fresh real Vite production build were re-verified after the trust-sharing slice landed.

Completed in the seventh Sprint 10 slice:

- the internal operations page now reads live tenancy, evidence, and history-import review queues in addition to the existing operations overview,
- reviewers can now send queue decisions from the rebuilt web app through the same backend decision endpoints already used in API coverage,
- targeted internal, tenancy, evidence, and frontend tests plus a fresh real frontend build output check were re-verified after the reviewer-workbench slice landed.

Completed in the eighth Sprint 10 slice:

- the agency workbench now supports consent-backed trust-check validation, profile preview, and trust-check creation directly from the web UI,
- recent trust checks are now visible in the same agency surface so operators can see sharing-driven screening activity alongside listings and applications,
- targeted consent, agency, and frontend tests plus a fresh real Vite production build were re-verified after the trust-check execution slice landed.

Completed in the ninth Sprint 10 slice:

- agency operators can now change listing lifecycle state between open, paused, and closed directly from the rebuilt workbench,
- listing lifecycle controls continue to reuse the existing listing patch endpoint instead of introducing any frontend-only workflow rules,
- targeted agency/frontend tests plus a fresh real Vite production build were re-verified after the listing-lifecycle slice landed.

Completed in the tenth Sprint 10 slice:

- the internal operations page now exposes due automation tasks and recent worker runs in addition to review queues and overview metrics,
- internal runtime visibility continues to read only from the existing automation and worker APIs without introducing a separate frontend reporting model,
- targeted internal/frontend tests plus a fresh real Vite production build were re-verified after the runtime-visibility slice landed.

Completed in the eleventh Sprint 10 slice:

- a new records route now exposes current-user tenancy records, inline review requests, counterparty confirmations, and tenancy-level evidence submission,
- the records page also reads tenancy-linked evidence lists so users can inspect the proof already attached to each trust record,
- targeted tenancy, evidence, and frontend tests plus a fresh real Vite production build were re-verified after the personal-records slice landed.

Completed in the twelfth Sprint 10 slice:

- the records workspace now reads live history-import and reference-request data alongside current tenancy records,
- users can now create and submit history-import drafts, request counterparty references from tenancy participants, and fulfill incoming pending reference requests from the web app,
- targeted tenancy, evidence, history-import, reference-request, and frontend tests plus a fresh real Vite production build were re-verified after the cold-start self-service slice landed.

Completed in the thirteenth Sprint 10 slice:

- the internal operations workspace now reads recent audit-log activity from the rebuilt hardening APIs,
- reviewers can now filter the recent audit stream by action type without leaving the main operations control surface,
- targeted internal audit, internal operations, automation, worker, and frontend tests plus a fresh real Vite production build were re-verified after the audit-visibility slice landed.

Completed in the fourteenth Sprint 10 slice:

- the agency workbench now supports inline listing screening-policy edits on top of the existing listing patch endpoint,
- agency operators can now filter the application pipeline by status from the same workbench without introducing any new backend reporting contract,
- targeted organization, listing-application, and frontend tests plus a fresh real Vite production build were re-verified after the screening-controls slice landed.

Completed in the fifteenth Sprint 10 slice:

- the trust profile page now reads and renders the current-user trust-event ledger stream in addition to score summary and score history,
- user-facing trust visibility is now less abstract because score aggregates, sharing controls, and ledger history all coexist in one workspace,
- targeted trust-score, consent, tenancy, and frontend tests plus a fresh real Vite production build were re-verified after the trust-ledger-history slice landed.

Completed in the sixteenth Sprint 10 slice:

- a new operations route now exposes tenancy-linked payments, deposits, and maintenance workflows from the rebuilt web app,
- tenancy participants can now create payment records, submit payment proof, confirm or reject payments, open and settle deposit records, dispute eligible deposit settlements, and run core maintenance actions from one operational workspace,
- targeted payment, deposit, maintenance, and frontend tests plus a fresh real Vite production build were re-verified after the operational-ledger slice landed.

### Current Deliverables

- `apps/web/package.json`
- `apps/web/index.html`
- `apps/web/vite.config.js`
- `apps/web/src/main.js`
- `apps/web/src/lib/api.js`
- `apps/web/src/app/session.js`
- `apps/web/src/app/router.js`
- `apps/web/src/app/AppShell.js`
- `apps/web/src/pages/LandingPage.js`
- `apps/web/src/pages/AuthPage.js`
- `apps/web/src/pages/WorkspaceHomePage.js`
- `apps/web/src/pages/AgencyWorkbenchPage.js`
- `apps/web/src/pages/MarketplacePage.js`
- `apps/web/src/pages/RecordsPage.js`
- `apps/web/src/pages/TrustProfilePage.js`
- `apps/web/src/pages/SecurityPage.js`
- `apps/web/src/pages/InternalOperationsPage.js`
- `apps/web/src/pages/NotFoundPage.js`
- `apps/web/src/styles/index.css`
- `tests/test_web_scaffold.py`

### Next Slice

Next slice:

- begin Sprint 11 with local demo and delivery-experience work,
- reconcile top-level roadmap docs with the already completed Sprint 10 delivery,
- add a real seeded local demo path so the rebuilt app can be run and reviewed without an empty database.

## Sprint 11: Demo And Local Live Path

### Planned Scope

- reconcile the top-level roadmap and README with the already completed Sprint 10 work,
- add an idempotent seeded demo path for the rebuilt app,
- add a concrete local run guide for API, web, worker, and demo accounts,
- make the local demo path truthful to the current architecture without pretending hosted launch work is already done.

### Planned Exit Criteria

- a developer can migrate the database, seed a meaningful dataset, and open the rebuilt app locally,
- the local demo includes real trust, screening, operations, and sharing data,
- the roadmap documents reflect the real completed and remaining sprint arc.

### Current Progress

Completed in the first Sprint 11 slice:

- reconciled `README.md`, `docs/ROADMAP.md`, and `docs/SPRINTS.md` so the sprint arc now reflects the already completed Sprint 10 work and the remaining go-live path,
- added an idempotent demo-seed module and CLI under `apps/api` so the rebuilt app can be explored with meaningful trust, screening, operations, consent, and audit data,
- added a repo-root worker wrapper plus updated worker guidance so the local runtime path is no longer trapped in test-only path assumptions,
- added `docs/LOCAL_RUN.md` and `docs/GO_LIVE.md` so there is now a concrete path from local demo to hosted pilot,
- added path bootstrap in `apps/api/app/__init__.py` so the monorepo domain package resolves during real local API and seed execution, not only inside tests,
- verified the local live path by running Alembic migrations, running the real `dev_seed.py` command, re-running the full regression suite, and producing a fresh real Vite build.

### Current Deliverables

- `apps/api/app/__init__.py`
- `apps/api/app/devtools/demo_seed.py`
- `apps/api/dev_seed.py`
- `apps/worker/run_once.py`
- `apps/worker/README.md`
- `docs/LOCAL_RUN.md`
- `docs/GO_LIVE.md`
- `README.md`
- `docs/ROADMAP.md`
- `docs/SPRINTS.md`
- `docs/DECISIONS.md`
- `tests/test_demo_seed.py`

### Next Slice

Next slice:

- begin Sprint 13 with deployment-runtime foundations,
- keep the next slice focused on staging-oriented runtime shape and worker readiness rather than jumping ahead to hosted-pilot claims.

## Sprint 12: Evidence Artifacts And Storage

### Planned Scope

- replace metadata-only evidence placeholders with real upload/download behavior,
- introduce private object storage access patterns and signed retrieval,
- keep evidence metadata, artifact location, and reviewer workflows aligned.

### Planned Exit Criteria

- evidence records can point to real stored artifacts instead of placeholder filenames only,
- sensitive files are not publicly exposed,
- the web and API layers can safely work with uploaded evidence files.

### Current Progress

Completed in the first Sprint 12 slice:

- added private stored-artifact records plus evidence linkage in the rebuild schema,
- added SQLite-safe migration `20260411_0023` for stored artifacts and evidence attachment,
- added private local artifact storage with content-type and size validation, hashed file metadata, and signed short-lived download URLs,
- added upload and artifact-access endpoints under the evidence API,
- extended tenancy evidence submission and reference-request fulfillment so they can attach pre-uploaded private artifacts,
- extended the records web workspace so users can upload artifact files for evidence and counterparty references, then open uploaded files through signed API URLs,
- added targeted regression coverage for artifact upload, signed download, outsider denial, and uploaded reference fulfillment,
- installed `python-multipart` into the project virtualenv so the secure upload routes can run and be tested,
- verified the sprint by re-running targeted tests, the full regression suite, a real Vite build, a real Alembic upgrade, and the live demo seed command.

### Current Deliverables

- `apps/api/app/models/stored_artifact.py`
- `apps/api/alembic/versions/20260411_0023_stored_artifacts.py`
- `apps/api/app/schemas/artifact.py`
- `apps/api/app/api/routes/evidence.py`
- `apps/api/app/services/artifacts.py`
- `apps/api/app/api/routes/tenancies.py`
- `apps/api/app/api/routes/reference_requests.py`
- `apps/api/app/schemas/evidence.py`
- `apps/api/app/schemas/reference_request.py`
- `apps/api/app/services/evidence.py`
- `apps/api/requirements.txt`
- `apps/api/.env.example`
- `apps/web/src/pages/RecordsPage.js`
- `tests/test_evidence_artifact_api.py`
- `tests/test_web_scaffold.py`

### Next Slice

Next slice:

- begin Sprint 13 with staging-oriented runtime foundations,
- keep the next delivery lane centered on deployment shape, worker/runtime packaging, and production-path environment discipline.

## Sprint 13: Deployment Runtime Foundations

### Planned Scope

- add Redis-backed runtime coordination where it materially helps worker execution,
- tighten worker execution packaging and notification readiness,
- prepare staging-friendly environment handling around API, worker, and web lanes.

### Planned Exit Criteria

- the worker can run in a staging-like runtime shape without ad hoc path tricks,
- environment handling is ready for a non-local deployment target,
- reminder and notification work has a clearer runtime path.

### Current Progress

Completed in the first Sprint 13 slice:

- runtime settings now resolve from `apps/api/.env` through an absolute shared contract instead of depending on the current working directory,
- default SQLite and private-artifact paths now resolve under `apps/api` so repo-root worker runs and API runs point at the same local data and file locations,
- staging-oriented runtime settings now cover public API/web base URLs, optional Redis coordination, worker loop settings, and notification transport configuration,
- `apps/web` now has an explicit `.env.example`, build-time API base URL support, and env-driven dev proxy target support instead of relying on hardcoded runtime assumptions.

Completed in the second Sprint 13 slice:

- added durable `notification_deliveries` records plus worker-run notification counters in the rebuild schema,
- consent-expiry reminder automation now queues a real notification outbox record instead of only leaving a note on the automation task,
- internal reviewer/admin APIs can now inspect notification deliveries through `/api/v1/internal/notifications`,
- internal operations overview now includes notification backlog counts.

Completed in the third Sprint 13 slice:

- the worker now supports an execution lease abstraction with an optional Redis-backed implementation and a safe local no-op fallback,
- repo-root worker commands now support both one-shot and loop modes through `run_once.py`, `run_service.py`, and an argument-aware `worker.main`,
- worker cycles now claim and dispatch queued notification deliveries in addition to automation and score work,
- the internal operations web workspace now surfaces recent notification deliveries and notification-aware worker summaries,
- full regression, real Vite build, real Alembic upgrade, real demo seed, and a real repo-root worker run were all re-verified at the sprint boundary.

### Current Deliverables

- `apps/api/app/core/config.py`
- `apps/api/.env.example`
- `apps/api/app/models/notification_delivery.py`
- `apps/api/app/models/worker_run.py`
- `apps/api/alembic/versions/20260411_0024_notification_deliveries_and_worker_counts.py`
- `apps/api/app/schemas/notification.py`
- `apps/api/app/schemas/operations.py`
- `apps/api/app/schemas/worker_run.py`
- `apps/api/app/services/notifications.py`
- `apps/api/app/services/automation.py`
- `apps/api/app/services/worker_runs.py`
- `apps/api/app/api/routes/internal_notifications.py`
- `apps/api/app/api/routes/internal_automation.py`
- `apps/api/app/api/routes/internal_operations.py`
- `apps/worker/worker/coordination.py`
- `apps/worker/worker/main.py`
- `apps/worker/worker/runtime.py`
- `apps/worker/run_once.py`
- `apps/worker/run_service.py`
- `apps/worker/README.md`
- `apps/web/.env.example`
- `apps/web/vite.config.js`
- `apps/web/src/lib/api.js`
- `apps/web/src/pages/InternalOperationsPage.js`
- `tests/test_api_identity_foundations.py`
- `tests/test_internal_automation_api.py`
- `tests/test_internal_notifications_api.py`
- `tests/test_internal_operations_api.py`
- `tests/test_worker_runtime.py`
- `tests/test_worker_coordination.py`
- `tests/test_web_scaffold.py`

### Next Slice

Next slice:

- begin Sprint 14 with hosted delivery shape around PostgreSQL, backups, readiness checks, and structured operational deployment guidance.

## Sprint 14: Hosted Delivery Lane

### Planned Scope

- prepare a staging deployment shape around PostgreSQL, worker execution, and static web delivery,
- add backup and restore runbooks,
- strengthen readiness, logging, and operational visibility.

### Planned Exit Criteria

- the platform can be deployed into a staging environment with a documented runtime shape,
- restore and recovery expectations are written and tested at a practical level,
- operators have enough observability to support a real pilot environment.

### Current Progress

Completed in the first Sprint 14 slice:

- added structured request logging with response `X-Request-ID` headers on the API,
- added `/health/live` and `/health/ready` with component-level readiness checks for database, artifact storage, and Redis coordination,
- extended the internal operations overview with environment, database backend, worker coordination backend, and notification transport fields,
- added Dockerfiles for API, worker, and web plus a first staging compose stack around PostgreSQL, Redis, and the shared private-artifact volume,
- added staging and PostgreSQL backup/restore runbooks under `docs/`,
- added runtime-health and staging-delivery verification tests,
- re-verified the sprint with compile checks, targeted tests, the full regression suite, a real Vite build, a real Alembic upgrade, the real demo seed command, and a real worker one-shot execution.

### Current Deliverables

- `apps/api/app/core/logging.py`
- `apps/api/app/core/health.py`
- `apps/api/app/main.py`
- `apps/api/app/api/routes/internal_operations.py`
- `apps/api/app/schemas/operations.py`
- `apps/api/requirements.txt`
- `apps/api/Dockerfile`
- `apps/worker/Dockerfile`
- `apps/web/Dockerfile`
- `apps/web/nginx.conf`
- `deploy/staging/.env.example`
- `deploy/staging/docker-compose.yml`
- `docs/STAGING_RUN.md`
- `docs/BACKUP_RESTORE.md`
- `tests/test_runtime_health_api.py`
- `tests/test_staging_delivery_files.py`

### Next Slice

Next slice:

- begin Sprint 15 with pilot go-live hardening,
- keep the next delivery lane focused on UAT, security review, operator readiness, and release-candidate discipline rather than adding broad new product scope.

## Sprint 15: Pilot Go-Live Hardening

### Planned Scope

- complete UAT on the rebuilt product,
- perform security and release-readiness review,
- finalize the monitored release-candidate path for the first hosted pilot.

### Planned Exit Criteria

- a first hosted pilot can be launched with confidence,
- go/no-go checks, operators, and monitoring are in place,
- the roadmap can move from build mode into pilot support mode.

### Current Progress

Completed in the first Sprint 15 slice:

- added a protected internal release-readiness endpoint that combines runtime configuration checks with recent worker and notification health,
- added a release-readiness panel to the internal web workspace so the go/no-go view is visible in the product, not only in docs,
- added baseline API response hardening with request IDs, `nosniff`, `X-Frame-Options`, `Referrer-Policy`, and production-like HSTS support,
- added explicit UAT, security-review, and release-candidate runbooks for the first hosted pilot lane,
- added targeted regression coverage for release readiness, security headers, pilot runbooks, and internal web wiring,
- re-verified the sprint with compile checks, targeted tests, the full regression suite, a real Vite build, a real Alembic upgrade, the real demo seed command, and a real worker one-shot execution.

### Current Deliverables

- `apps/api/app/schemas/release.py`
- `apps/api/app/services/release_readiness.py`
- `apps/api/app/api/routes/internal_release.py`
- `apps/api/app/api/router.py`
- `apps/api/app/main.py`
- `apps/web/src/pages/InternalOperationsPage.js`
- `docs/UAT.md`
- `docs/SECURITY_REVIEW.md`
- `docs/RELEASE_CANDIDATE.md`
- `tests/test_release_readiness_api.py`
- `tests/test_runtime_health_api.py`
- `tests/test_pilot_release_docs.py`
- `tests/test_web_scaffold.py`

### Next Slice

Next slice:

- begin Sprint 16 with post-pilot expansion,
- keep that work additive to the pilot-grade core rather than reopening launch-critical infrastructure or security foundations.

## Sprint 16: Post-Pilot Expansion

### Planned Scope

- improve PWA/mobile experience on top of the stabilized product,
- expand commercial and analytics capabilities,
- revisit optional integrations only after the hosted pilot is stable.

### Planned Exit Criteria

- post-pilot work remains additive and does not destabilize the pilot-grade core,
- expansion priorities are clearly separated from the launch-critical path.

### Current Progress

Completed in the first Sprint 16 slice:

- added an agency commercial-overview API built from existing organization, listing, application, and trust-check data,
- added commercial overview metrics to the agency workbench without introducing a second reporting backend,
- added a PWA-ready web shell with manifest metadata, production service-worker registration, install lifecycle hooks, and a user-facing install panel,
- improved mobile shell behavior with more practical small-screen navigation treatment,
- added targeted regression coverage for the commercial-overview API and the new PWA/mobile web scaffolding,
- re-verified the sprint with compile checks, targeted tests, the full regression suite, a real Vite build, a real Alembic upgrade, the real demo seed command, and a real worker one-shot execution.

### Current Deliverables

- `apps/api/app/services/commercial_overview.py`
- `apps/api/app/schemas/organization.py`
- `apps/api/app/api/routes/organizations.py`
- `apps/web/public/manifest.webmanifest`
- `apps/web/public/icon.svg`
- `apps/web/public/sw.js`
- `apps/web/index.html`
- `apps/web/src/main.js`
- `apps/web/src/app/AppShell.js`
- `apps/web/src/pages/WorkspaceHomePage.js`
- `apps/web/src/pages/AgencyWorkbenchPage.js`
- `apps/web/src/styles/index.css`
- `docs/POST_PILOT.md`
- `tests/test_commercial_overview_api.py`
- `tests/test_web_scaffold.py`

### Next Slice

Sprint 16 closes the planned roadmap. Future work should now be chosen from post-pilot backlog priorities rather than from the original launch-critical sprint arc.

## Sprint 17: Frontend Parity And Information Architecture

### Planned Scope

- audit backend route coverage against the current web surfaces,
- expose the highest-value backend operations that still require manual/API-only usage,
- complete frontend parity for tenancy creation, internal control actions, and remaining organization/admin flows,
- introduce estate portfolio helpers such as custom property tags and fast filtering,
- make evidence upload and object-storage behavior more explicit, while preparing a MinIO/S3-compatible storage lane before visual redesign,
- expand dispute handling into a clearer frontend-operable workflow,
- simplify and regroup navigation around clearer jobs-to-be-done,
- establish the structural foundation for compact views on data-heavy pages.

### Planned Exit Criteria

- the main product operations are no longer split awkwardly between frontend and API-only usage,
- users can visibly create and manage the important trust records from the web app without falling back to raw API calls,
- evidence/document handling is obviously real to operators and users, not hidden behind unclear labels,
- estate users can organize properties quickly enough for day-to-day portfolio work,
- user jobs are easier to find without guessing which page owns them,
- compact-view work can start from a clean information architecture instead of stacking onto the current layout ad hoc.

### Current Progress

Completed in the first Sprint 17 slice:

- added property custom tags on the backend with create/update/list support,
- added email-based counterparty resolution for tenancy creation so the frontend no longer depends on raw UUID entry,
- added a real tenancy-creation flow to the records workspace,
- added a saved-property summary to the records workspace,
- added an estate portfolio section to the agency workspace with tag editing and quick filtering,
- updated the roadmap to make frontend parity, evidence-storage visibility, dispute-surface expansion, and property tagging explicit Sprint 17 goals,
- re-verified the slice with targeted backend tests and frontend tests.

Completed in the second Sprint 17 slice:

- upgraded evidence storage from a local-only assumption to a pluggable backend model that supports both private local storage and S3-compatible object storage such as MinIO,
- kept artifact retrieval API-controlled and signed so the user flow stays the same across storage backends,
- exposed the active artifact storage backend in the internal operations overview so operators can immediately see which runtime mode they are using,
- expanded the internal scoring controls so reviewers can queue, list, and directly trigger score recalculation by user email instead of needing raw internal IDs,
- expanded internal automation controls so reviewers can create follow-up tasks by subject email and act on due tasks from the web workspace,
- expanded organization management so agency team members can be invited by email and managed directly from the web workspace,
- added a clearer dispute desk to the operational workspace so open disputes and dispute-ready records are visible without hunting inside tenancy detail cards,
- re-verified the slice with targeted API tests, frontend tests, a real Vite build, a real Alembic upgrade, and a real demo reseed.

### Current Deliverables

- `apps/api/app/core/config.py`
- `apps/api/app/schemas/artifact.py`
- `apps/api/app/services/artifacts.py`
- `apps/api/app/api/routes/evidence.py`
- `apps/api/app/schemas/property.py`
- `apps/api/app/services/properties.py`
- `apps/api/app/api/routes/properties.py`
- `apps/api/app/schemas/organization.py`
- `apps/api/app/api/routes/organizations.py`
- `apps/api/app/schemas/automation.py`
- `apps/api/app/api/routes/internal_automation.py`
- `apps/api/app/schemas/score.py`
- `apps/api/app/api/routes/internal_scoring.py`
- `apps/api/app/schemas/operations.py`
- `apps/api/app/api/routes/internal_operations.py`
- `apps/api/.env.example`
- `apps/api/requirements.txt`
- `apps/web/src/pages/RecordsPage.js`
- `apps/web/src/pages/OperationsPage.js`
- `apps/web/src/pages/AgencyWorkbenchPage.js`
- `apps/web/src/pages/InternalOperationsPage.js`
- `docs/WORKSPACE_GUIDE.md`
- `docs/LOCAL_RUN.md`
- `tests/test_evidence_artifact_api.py`
- `tests/test_internal_scoring_api.py`
- `tests/test_internal_automation_api.py`
- `tests/test_internal_operations_api.py`
- `tests/test_organization_rbac_api.py`
- `tests/test_web_scaffold.py`

### Next Slice

Sprint 17 is now functionally complete for the current planned scope.

Next slice:

- begin Sprint 18 with bilingual localization before visual redesign,
- translate the rebuilt frontend and add a user-controlled language switch that works across public and authenticated routes,
- keep the next slice additive so the existing stable product flows remain unchanged while the UI becomes more accessible to Greek-speaking users.

## Sprint 18: Bilingual Frontend Localization

### Planned Scope

- add a reusable frontend localization layer instead of page-by-page hard-coded translation fragments,
- support English and Greek across public and authenticated web surfaces,
- add a visible language switch so users can move between English and Greek without losing context,
- localize common frontend error presentation and locale-aware number formatting before visual redesign.

### Planned Exit Criteria

- the rebuilt frontend can render in both English and Greek,
- language choice persists for repeat visits,
- the web app exposes the toggle clearly enough that users do not need a hidden setting,
- the visual redesign can build on top of a stable bilingual text foundation instead of reworking copy later.

### Current Progress

Completed in the first Sprint 18 slice:

- added a reusable frontend language layer with shared translation helpers, persistent language choice, and a globally available language dock,
- switched the rebuilt web app root to wrap the existing session/router tree in the new language provider without disturbing the auth flow,
- localized API-originated frontend error presentation so validation and request failures now pass through the same language layer.

Completed in the second Sprint 18 slice:

- threaded the language-aware element wrapper through the app shell, route gates, and all primary page surfaces so the visible rebuilt frontend can render in English or Greek from the same codebase,
- added locale-aware currency formatting for the major agency, marketplace, and operational ledger surfaces,
- added targeted web tests for translation behavior and updated scaffold tests to pin the new localization sprint into the roadmap docs.

### Current Deliverables

- `apps/web/src/lib/i18n.js`
- `apps/web/src/lib/api.js`
- `apps/web/src/main.js`
- `apps/web/src/app/AppShell.js`
- `apps/web/src/app/router.js`
- `apps/web/src/pages/LandingPage.js`
- `apps/web/src/pages/AuthPage.js`
- `apps/web/src/pages/NotFoundPage.js`
- `apps/web/src/pages/WorkspaceHomePage.js`
- `apps/web/src/pages/TrustProfilePage.js`
- `apps/web/src/pages/MarketplacePage.js`
- `apps/web/src/pages/RecordsPage.js`
- `apps/web/src/pages/OperationsPage.js`
- `apps/web/src/pages/AgencyWorkbenchPage.js`
- `apps/web/src/pages/InternalOperationsPage.js`
- `apps/web/src/pages/SecurityPage.js`
- `apps/web/src/styles/index.css`
- `apps/web/tests/i18n.test.mjs`
- `tests/test_web_scaffold.py`
- `README.md`
- `docs/ROADMAP.md`
- `docs/SPRINTS.md`

### Next Slice

Sprint 18 is now functionally complete for the current planned scope.

Next slice:

- begin Sprint 19 with compact-density foundations,
- introduce the darker, higher-contrast visual system without regressing the now-completed operational parity,
- keep the design changes additive to the stable product flows completed in Sprint 17 and the bilingual foundation completed in Sprint 18.

## Sprint 19: Compact Workspace And Cinematic Visual System

### Planned Scope

- add density tokens and a compact workspace mode,
- redesign the color system toward deeper neutrals, stronger contrast, and confident accent usage,
- upgrade typography, surfaces, hover states, and visual hierarchy,
- define a cinematic visual direction inspired by Netflix's confidence and contrast without copying Netflix literally.

### Planned Exit Criteria

- users can switch or experience a denser operational layout where it helps productivity,
- the product looks more modern and premium while remaining readable and enterprise-safe,
- the design system is explicit enough to be applied consistently across all pages.

## Sprint 20: Page Conversion And Role Workspace Polish

### Planned Scope

- apply the new visual and compact rules to home, trust, records, operations, agency, and internal pages,
- improve scanability for listings, queues, applications, trust events, and operational ledgers,
- tighten action placement and page hierarchy for each role,
- keep the design coherent across tenant, landlord, agency, and reviewer experiences.

### Planned Exit Criteria

- the major workspaces feel visually related and materially improved, not partially redesigned,
- dense workflows become faster to scan and operate,
- the interface feels intentionally designed rather than only functionally assembled.

## Sprint 21: Motion, Accessibility, And Frontend Release Polish

### Planned Scope

- add intentional transitions and motion to page and component state changes,
- verify accessibility for contrast, focus, keyboard use, and responsive breakpoints,
- document the upgraded design system and compact-mode rules,
- finish with a polished frontend release candidate on top of the existing stable backend.

### Planned Exit Criteria

- the upgraded interface is visually stronger without regressing usability or accessibility,
- compact mode and cinematic styling are documented and maintainable,
- the frontend is ready for a controlled visual-release push.
