# Architecture Decisions

## D001: Archive The MVP Instead Of Editing In Place

The previous implementation is preserved under `archive/mesitis-mvp-2026-04-09/`.
Reason: we want a clean rebuild lane and a stable historical reference.

## D002: New Code Lives Under `apps/` And `packages/`

Reason: the boundary between legacy and rebuild must be obvious in both code and docs.

## D003: Evidence-Verified Instead Of Bank-Verified

The platform will support uploaded and reviewed evidence, counterparty confirmation, and automation, without paying for bank APIs in the initial product.

## D004: Monolith First

The rebuild starts as:

- one web app,
- one API,
- one worker.

Reason: faster delivery, lower complexity, easier stabilization.

## D005: Structured Audit Events Replace Free-Form Timelines

Reason: append-only, queryable, and reliable trust history is required for scoring, dispute review, and enterprise auditability.

## D006: Score And Confidence Are Separate

The product will expose:

- trust score,
- verification strength.

Reason: cold-start users should not be punished just for being new.

## D007: Tenant And Landlord Are Business Personas, Not Global Auth Roles

Identity starts with:

- users,
- organizations,
- memberships,
- system roles.

Tenant and landlord behavior will be represented through domain participation such as tenancies, listings, and applications.
Reason: this keeps auth flexible and avoids hard-coding business state into login roles.

## D008: Web Auth Will Prefer Server-Side Sessions

The rebuild will prefer opaque session tokens stored server-side instead of making JWTs the primary browser authentication mechanism.
Reason: session revocation, enterprise auditability, and safer browser behavior are easier to manage this way.

## D009: Agency Trust Checks Require Dual Consent

Agency trust-check access requires:

- active agency membership with trust-check permission,
- a user-issued share token,
- a matching access code.

Reason: B2B trust sharing must be explicit, revocable, and auditable from the first implementation slice.

## D010: Organizations Must Always Retain An Active Owner

Membership changes may update roles or deactivate members, but the platform must prevent a change that would leave an organization without at least one active owner.
Reason: this preserves recoverability and avoids orphaned agency or internal organizations.

## D011: Trust Profiles Start As Explicitly Limited Summaries

The first trust profile surface exposes only currently trustworthy platform facts such as:

- account activity,
- email verification state,
- consent sharing metadata,
- agency trust-check counts.

Reason: the rebuild should not imply richer trust signals before the tenancy, evidence, and scoring domains exist.

## D012: Monetary Rental Fields Use Minor Units

Tenancy financial fields are stored in integer minor units plus currency code, for example:

- `monthly_rent_minor`,
- `deposit_minor`,
- `currency_code`.

Reason: this keeps calculations deterministic and avoids early float precision mistakes in later scoring and reporting logic.

## D013: Tenancy History Writes Append Structured Events For Both Parties

When tenancy lifecycle actions occur, the platform appends structured trust events for both the tenant and landlord subjects.
Reason: the trust ledger must support dual-sided history rather than implying that only one side of a tenancy generated the event.

## D014: Internal Review Starts With Final Reviewer Decisions Only

The first reviewer queue only allows decisions that move a tenancy to:

- `reviewed`,
- `verified`.

Reason: the initial review workflow should stay narrow and auditable before more nuanced dispute or rejection states are added.

## D015: Properties Are Reusable Records, Tenancies Keep Snapshots

The rebuild now stores reusable property records separately while also persisting property label and address fields on each tenancy.
Reason: properties need reusable identities for future listings and applications, while tenancy snapshots preserve the state that was actually agreed at the time.

## D016: Counterparty Confirmation Resolves The Pre-Review Path

When the non-creator participant confirms a tenancy record, the tenancy moves to `counterparty_confirmed` and any pending internal review request is cleared.
Reason: counterparty confirmation is a stronger signal than self-reported history and should prevent unnecessary reviewer queue work.

## D017: Trust Event Reads Start With Subject And Tenancy Scopes

The first trust-event read surfaces are:

- current-user subject history,
- authorized tenancy history views.

Reason: this is enough to support user transparency, reviewer work, and later scoring inputs without prematurely exposing broad event search surfaces.

## D018: Listings Belong To Agencies And Reuse Property Records

Listings are modeled as agency-owned records that reference reusable properties and carry their own rental and eligibility settings.
Reason: agencies need a B2B management surface on top of stable property identities, while each listing remains a separate market-facing offer.

## D019: Pre-Score Listing Eligibility Uses Verified History Counts

Before the scoring engine exists, listing eligibility is enforced through narrow count-based rules such as:

- minimum counterparty-confirmed tenancies,
- minimum verified tenancies.

Reason: this lets the agency workflow enforce meaningful trust thresholds now without pretending that a full scoring model already exists.

## D020: Listing And Application Lifecycle Actions Write Trust Events

Listing publication and application lifecycle updates append trust events for the relevant user subjects.
Reason: the ledger should reflect market participation history alongside tenancy verification history as the platform expands.

## D021: Evidence Documents Attach To A Tenancy And A Subject User

Each evidence record is anchored to:

- one tenancy,
- one subject user whose trust history the evidence supports,
- one uploader who supplied it.

Reason: this preserves the distinction between who is being evaluated and who provided the proof, which is especially important for landlord references and counterparty-supported history.

## D022: Evidence Review Uses Explicit Accepted Or Rejected Outcomes

Internal reviewer decisions on evidence records currently end in:

- `accepted`,
- `rejected`.

Reason: evidence review needs a clear final outcome for trust strength without prematurely implying that every accepted document has escalated a tenancy to full verification.

## D023: Trust Events Can Reference Evidence Records Directly

Trust events may now carry a direct reference to an `evidence_document`.
Reason: the ledger should stay structured and queryable as evidence-backed history grows, instead of forcing later services to reconstruct context from free-form summaries.

## D024: Cold-Start History Uses Bundles Separate From Live Tenancy Verification

Historical onboarding imports are grouped into dedicated `history_imports` that can collect multiple tenancy records and their supporting evidence.
Reason: cold-start review needs a container for imported history without overloading the main tenancy model with bundle workflow state.

## D025: Only The Subject User Can Submit A History Import For Review

A history import may be created and edited while in draft, but submission for internal review is restricted to the subject user tied to that import.
Reason: cold-start reputation packages should remain under the evaluated user's control even when other participants later contribute evidence or references.

## D026: History Import Acceptance Does Not Automatically Upgrade Tenancy Or Evidence States

Reviewing a history import bundle records that the package was accepted or rejected, but it does not automatically mutate the underlying tenancy verification status or evidence review outcomes.
Reason: the scoring engine will need to weigh bundle-level trust, tenancy-level verification, and evidence-level review separately instead of collapsing them into one state too early.

## D027: Counterparty References Require An Explicit Request Chain

Landlord-style references now start as a `reference_request` created by the subject user and fulfilled by the counterparty.
Reason: this prevents the platform from treating a self-uploaded statement as equivalent to an actually requested counterparty attestation.

## D028: Fulfilled Reference Requests Produce Evidence With Preserved Provenance

When a counterparty fulfills a reference request, the resulting evidence record retains a direct link back to that request.
Reason: reviewer tooling, agency trust views, and later scoring need to distinguish counterparty-supplied references from generic uploaded documents.

## D029: Counterparty Reference Signals Are Counted Separately From Generic Evidence

Trust profiles now separately expose:

- counterparty reference documents,
- accepted counterparty reference documents.

Reason: these signals are stronger than self-supplied evidence and should remain explicit as scoring logic becomes more sophisticated.

## D030: Scores Are Persisted As Snapshots Plus Append-Only History

The rebuild now stores:

- a latest `trust_score_snapshot` per user,
- append-only `trust_score_history` entries when scores actually change.

Reason: product surfaces need a fast current read, while auditability and later automation need a history of meaningful score transitions.

## D031: The First Scoring Service Is Deterministic And Signal-Scoped

The initial scoring service only uses structured signals that already exist in the rebuild, including:

- counterparty-confirmed and verified tenancies,
- accepted evidence,
- accepted counterparty references,
- accepted history imports for verification strength.

Reason: the first scoring slice should be explainable and auditable, even if it remains conservative until richer negative and operational signals are added later.

## D032: Score Trigger Reasons Are Canonical And Shared

Score recalculation reasons are now drawn from a shared set, including:

- `self_service_refresh`,
- `trust_check_preview`,
- `agency_trust_check`,
- `internal_recalculation`.

Reason: score history should remain analyzable and worker-ready instead of accumulating ad hoc free-text trigger labels across routes.

## D033: Score Recalculation Requests Are Persisted Even Before The Worker Exists

Internal score recalculation now writes a `trust_score_recalculation_request` record before processing.
Reason: the API path and the future worker path must share the same audit-friendly trigger contract instead of each inventing separate execution flows.

## D034: Batch Score Refresh Uses Explicit Scope Records

Batch recalculation intent is now modeled through `trust_score_recalculation_batches` with scopes such as:

- `organization_members`,
- `all_active_users`.

Reason: organization-level refreshes and future nightly runs need a durable, inspectable planning object before asynchronous worker execution is introduced.

## D035: Operational Payments Are First-Class Records, Not Reconstructed From Generic Evidence

The rebuild now models tenancy-linked `payment_records` with explicit:

- payer,
- payee,
- payment status,
- proof status.

Reason: ongoing rental operations need their own auditable workflow before deposit, maintenance, and dispute logic can be layered on safely.

## D036: Payment Proof And Counterparty Decision Remain Separate States

Payments now track both:

- `payment_status`,
- `proof_status`.

Reason: a payment can be confirmed without uploaded proof, or carry proof that has not yet been counterparty-confirmed; the ledger should preserve that distinction instead of collapsing operational truth into one field.

## D037: Deposit Settlement Uses One Record Per Tenancy

The rebuild now models one `deposit_record` per tenancy rather than letting multiple overlapping settlement threads emerge.
Reason: deposit settlement should have a single auditable source of truth for held amount, proposed return, withholding, and dispute notes.

## D038: Deposit Disputes Preserve Settlement State Instead Of Hiding It

When a tenant disputes a deposit settlement, the record keeps:

- proposed return amount,
- withheld amount,
- settlement notes,
- dispute notes.

Reason: the platform needs a dispute-ready audit trail that preserves both the landlord's stated settlement and the tenant's objection for later review and automation.

## D039: Maintenance Uses Structured Ticket State Instead Of Free-Form Dispute Threads

The rebuild now models maintenance operations as `maintenance_tickets` with explicit:

- reported,
- acknowledged,
- resolved,
- disputed

state transitions.
Reason: operational trust needs a durable service-quality record that can later inform scoring and reviewer queues without reconstructing meaning from comments.

## D040: Tenant Maintenance Disputes Require A Prior Resolution State

The first maintenance dispute flow only allows a dispute after the landlord has recorded a resolution.
Reason: the platform should distinguish unresolved issues from explicitly contested resolutions, which creates a cleaner basis for later score logic and reviewer escalation.

## D041: Listing Gates Now Use Actual Scores Instead Of Transitional History Counts

Agency listings now gate applications using:

- `minimum_tenant_score`,
- `minimum_verification_strength`.

Reason: once the centralized score engine exists, agency screening rules should align with the real scoring surface rather than continuing to depend on temporary pre-score heuristics.

## D042: Applications Capture The Score Snapshot Used At Submission Time

Listing applications now persist:

- applicant tenant score,
- applicant verification strength,
- scoring version,
- score calculation timestamp.

Reason: agency review should be able to inspect the score context that actually gated the application without depending on a later recalculation that may no longer match the submission moment.

## D043: Automation Starts With Durable Task Records Instead Of Cron-Only Behavior

The first automation slice stores reminder and follow-up work in `automation_tasks` with explicit:

- task type,
- status,
- schedule,
- processor,
- result notes.

Reason: future worker execution, internal queue tooling, and auditability should all share the same persisted contract rather than hiding reminder behavior inside ad hoc timers or background callbacks.

## D044: Consent Sharing Owns Its Expiry Reminder Lifecycle

Trust-report consent creation now queues a reminder task, and consent revocation cancels the pending reminder when appropriate.
Reason: reminder correctness should be anchored to the consent lifecycle itself so that future worker automation inherits safe defaults without needing to reconstruct business intent after the fact.

## D045: Scheduled Score Automation Must Reuse The Persisted Scoring Queue

Automation-driven score refreshes now enqueue:

- `trust_score_recalculation_requests`,
- `trust_score_recalculation_batches`

through the same scoring services already used by internal API flows.
Reason: automated and manual recalculation should share one auditable execution path so future workers, dashboards, and failure handling do not diverge.

## D046: Automation Workers Claim Due Tasks Instead Of Reinterpreting The Queue

The automation layer now supports explicit claiming of due pending tasks before execution.
Reason: future workers should consume a stable queue contract with visible ownership and attempt counts instead of each background runner inventing its own selection logic.

## D047: Expired Or Stale Automation Work Is Closed Explicitly

Expired consent reminders and stale follow-up tasks now have explicit cleanup paths that mark them closed on the same durable records.
Reason: enterprise operations need a queue that stays trustworthy over time instead of accumulating obsolete pending work that no longer reflects real action required.

## D048: Sensitive Platform Actions Write Append-Only Audit Logs

The rebuild now records audit logs for high-sensitivity actions such as:

- trust-report consent lifecycle changes,
- agency trust-check access,
- internal automation queue actions.

Reason: enterprise-grade traceability should be built into the platform behavior itself instead of left to ad hoc infrastructure logs that are harder to query in business context.

## D049: Shared-Profile Subjects Can Inspect Their Own Access History

Users can now read an access-history view for agency actions taken against their shared trust report.
Reason: privacy, consent transparency, and future compliance workflows are stronger when subjects can see who validated or viewed their shared profile without relying on staff to answer that question manually.

## D050: Denied Protected-Access Attempts Are Audit Events Too

The audit layer now records denied trust-check access attempts alongside successful ones.
Reason: enterprise security review depends on seeing failed attempts against protected trust-sharing flows, not just the accesses that succeeded.

## D051: Trust-Report Consents Apply Temporary Lockouts After Repeated Invalid Access Codes

Trust-report consent access now tracks failed attempts and applies a short temporary lockout after repeated invalid access-code submissions.
Reason: shared-profile access should resist brute-force guessing attempts without requiring a separate external rate-limiting system this early in the rebuild.

## D052: Users Can Inspect And Revoke Their Active Sessions

The rebuild now exposes active-session visibility plus single-session and revoke-other-session controls on top of the existing server-side session model.
Reason: enterprise security posture improves when users can directly contain account exposure without needing staff intervention for basic session hygiene.

## D053: User Login Applies Temporary Lockout After Repeated Invalid Password Attempts

User authentication now tracks repeated failed password attempts and applies a short temporary account-level lockout before login can succeed again.
Reason: the primary sign-in path should resist brute-force password guessing with the same seriousness applied to shared trust-report access.

## D054: Users Can Inspect Their Own Auth Security Events

Authenticated users can now read a security-event view of their own login and session-related audit activity.
Reason: security transparency should not be limited to internal staff when the events directly affect the account owner.

## D055: The First Worker Runtime Reuses Existing Queue Services

The first concrete worker cycle processes due automation tasks and due score recalculation requests through the same service-layer functions already used by the API.
Reason: the worker should be an execution surface for existing domain rules, not a second implementation of queue behavior.

## D056: Worker Execution Uses A Dedicated Internal User Identity

The worker runtime bootstraps a dedicated internal user identity for queue processing.
Reason: background execution should still be attributable in domain records and future audit trails instead of acting as an anonymous side effect.

## D057: Worker Cleanup Runs Before Executable Task Claiming

The worker cycle now closes expired consent reminders and stale follow-up tasks before it claims executable automation work.
Reason: obsolete queue items should be canceled through explicit cleanup paths instead of being half-processed as if they were still actionable.

## D058: Worker Queue Processing Emits The Same Audit Signals As Internal Operations

Worker claim, execution, cleanup, and score-request processing now append durable audit logs.
Reason: background processing must remain just as traceable as equivalent internal API actions if the platform is going to support enterprise review and incident analysis.

## D059: Score Recalculation Requests Now Behave Like A Durable Claimed Queue

Score recalculation requests now track:

- `processed_by_user_id`,
- `attempt_count`,
- explicit claim-before-process flow.

Reason: queue ownership and retry visibility should be first-class on scoring work before the runtime grows into a longer-lived worker process.

## D060: Every Worker Cycle Leaves A First-Class Run Record

Worker execution now persists a `worker_run` record with:

- run status,
- requested limit,
- due-boundary context,
- queue-processing counts,
- last error details when the cycle fails.

Reason: operational review should not depend on reconstructing worker behavior from scattered task rows and audit events alone.

## D061: Internal Operations Overview Reads Directly From Domain Queues

The first operations-overview surface summarizes:

- pending review queues,
- pending and due automation tasks,
- pending and due score requests,
- latest worker run state

directly from the live domain tables.
Reason: the platform needs one truthful internal view of operational state, but it is still early enough that a separate reporting subsystem would add complexity without improving trustworthiness.

## D062: The First Frontend Slice Starts With Session Truth, Not Feature Depth

The first real `apps/web` slice focuses on:

- session restoration,
- login and registration wiring,
- route boundaries,
- shell navigation

before deeper feature pages.
Reason: the frontend should inherit the backend security and permission model first, so later product screens do not have to be rebuilt around auth edge cases.

## D063: Early Frontend Operational Views Must Read Live APIs

The first internal operations and account-security screens in the web app are wired directly to existing APIs rather than mocked or precomputed frontend data.
Reason: even placeholder-grade UI should prove the rebuilt backend surfaces are consumable by the real client before more elaborate feature work begins.

## D064: Organization Discovery Is A First-Class User API, Not A Frontend Guess

Authenticated users can now list their own active organization memberships through `/api/v1/organizations/mine`.
Reason: agency and internal frontend surfaces need a truthful way to establish current organizational context without hardcoded IDs, hidden bootstrap state, or brittle client-side reconstruction.

## D065: The First Feature-Grade Frontend Screens Must Show Canonical Score And Dashboard Reads

The first non-scaffold frontend pages now read directly from:

- `/api/v1/trust-scores/mine`,
- `/api/v1/trust-scores/mine/history`,
- `/api/v1/organizations/mine`,
- `/api/v1/organizations/{organization_id}/screening-dashboard`.

Reason: the web app should demonstrate real product truth early, using the same scoring and agency data contracts that later operator workflows will depend on.

## D066: Agency Frontend Actions Must Reuse Existing Backend Transition Rules

The agency workbench now reads and mutates application state through the existing listings and applications APIs, including backend-enforced status transitions.
Reason: operator-facing UI should not invent its own workflow rules; it should remain a thin, truthful client over the same transition discipline already validated in the API test suite.

## D067: Publishing Inventory Belongs In The Same Agency Workbench As Screening

The agency workbench now supports:

- property creation,
- listing publication,
- applicant screening

within one continuous operator surface.
Reason: the real agency workflow is operationally connected, and splitting publishing from screening too early would add navigation complexity without improving trust or safety.

## D068: Applicant Marketplace Must Reuse The Existing Score-Gated Listing APIs

The new marketplace surface reads from `/listings/open`, `/applications/mine`, and the existing listing-application create endpoint.
Reason: the applicant-facing UI should prove that the rebuilt listing and application contracts work end to end for both sides of the platform before any separate client-specific abstractions are introduced.

## D069: Trust Sharing Needs Discoverable Agencies, Not Hidden Organization IDs

Authenticated users can now discover active agencies through `/api/v1/organizations/directory/agencies`, and the trust page uses that directory for consent issuance.
Reason: consent UX should be explicit and safe; asking users to know or paste opaque organization identifiers would make the sharing model brittle and error-prone.

## D070: Reviewer Frontend Actions Must Reuse The Existing Queue And Decision APIs

The internal web workspace now reads:

- `/internal/operations/overview`,
- `/internal/review-queue/tenancies`,
- `/internal/review-queue/evidence`,
- `/internal/review-queue/history-imports`

and posts decisions back through the existing review endpoints.
Reason: reviewer UI should stay thin and truthful, so operational and verification rules continue to live in the backend services and tests rather than drifting into client-only workflow logic.

## D071: Agency Trust Checks Belong Inside The Same Operator Surface As Listings And Applications

The agency workbench now supports:

- trust-check validation,
- profile preview,
- trust-check creation,
- trust-check history visibility

alongside listing publication and applicant review.
Reason: agencies experience consent-driven screening as part of one operating context, so the frontend should reflect that integrated workflow instead of scattering core screening actions across unrelated screens.

## D072: Listing Lifecycle Controls Must Stay Backend-Driven

The web app now changes listing status through the existing listing update endpoint instead of implementing separate frontend-only status logic.
Reason: listing availability directly affects applicant experience and agency metrics, so lifecycle transitions should continue to be enforced in one backend path that remains testable and auditable.

## D073: Internal Runtime Visibility Reuses Existing Automation And Worker APIs

The internal web workspace now reads:

- `/internal/automation/tasks`,
- `/internal/workers/runs`

alongside the existing operations overview and review queues.
Reason: operational truth should come from the same backend queue and worker contracts already used by the platform, not from a separate frontend-only reporting layer.

## D074: Personal Records UI Starts With Existing Tenancy And Evidence Contracts

The new records page reads:

- `/tenancies/mine`,
- tenancy review-request and counterparty-confirm endpoints,
- tenancy evidence list and create endpoints.

Reason: early self-service trust management is most valuable when it sits directly on the existing tenancy and evidence model, instead of inventing a separate onboarding-only abstraction in the frontend.

## D075: Cold-Start Import And Counterparty Reference UX Stays Inside The Records Workspace

The records page now also reads and mutates:

- `/history-imports/mine`,
- `/history-imports`,
- `/history-imports/{history_import_id}/submit`,
- `/reference-requests/mine`,
- `/reference-requests/tenancies/{tenancy_id}`,
- `/reference-requests/{reference_request_id}/fulfill`.

Reason: imported history, attached evidence, and counterparty references are all parts of one user-managed trust record, so keeping them together is more truthful than splitting cold-start trust inputs into disconnected frontend areas.

## D076: Internal Audit Visibility Lives Inside The Existing Operations Workspace

The internal operations page now also reads:

- `/internal/audit-logs?limit=20`,
- optional `action_type` filtering on the same endpoint.

Reason: reviewer and admin operators already triage queues, automation, and worker activity from one operational surface, so recent audit visibility belongs in that same control room instead of forcing a separate navigation path for sensitive-event review.

## D077: Agency Screening Controls Reuse The Existing Listing Patch Contract

The agency workbench now uses the existing listing update endpoint to edit:

- listing description,
- minimum tenant score,
- minimum verification strength,
- lifecycle status.

Reason: screening policy should stay attached to the canonical listing record and its existing backend validations, instead of splitting lifecycle actions and screening-threshold edits across separate client-side models.

## D078: The Trust Workspace Should Show Ledger History, Not Only Score Aggregates

The trust profile page now reads `/trust-events/mine` alongside score summary and score history.
Reason: users should be able to see the event stream that feeds the trust ledger, not just the aggregated scores and sharing controls built on top of it.

## D079: Operational Ledger UX Reuses Existing Payment, Deposit, And Maintenance APIs

The web workspace now exposes one operations lane backed by:

- `/payments/tenancies/{tenancy_id}`,
- `/deposits/tenancies/{tenancy_id}`,
- `/maintenance-tickets/tenancies/{tenancy_id}`,
- the existing payment, deposit, and maintenance mutation endpoints for participant actions.

Reason: daily rental operations are a core source of trust signals, and they should stay grounded in the same backend workflows that already produce audited trust events instead of being simulated in frontend-only state.

## D080: Local Product Review Must Use A Real Demo Dataset, Not Empty State

The rebuild now includes an idempotent seeded demo path with:

- stable demo users,
- live tenancies,
- evidence,
- scores,
- operational records,
- consent-sharing data,
- agency screening data.

Reason: the team needs a fast and repeatable way to inspect the rebuilt product in a meaningful state before hosted deployment work is complete.

## D081: Evidence Files Use Private Storage With Signed Short-Lived Retrieval

Evidence artifacts now live in private storage and are opened through short-lived signed download URLs created by the authenticated API.

Reason: uploaded proof files are sensitive by nature, so the first artifact-storage slice must keep them private by default instead of exposing them as public static files.

## D082: API And Worker Share One Runtime Environment Contract

The API and worker now resolve runtime settings from the `apps/api/.env` contract instead of assuming the current working directory.

Reason: local demo runs, repo-root worker commands, and future hosted process layouts should all point at the same database, artifact, notification, and coordination settings.

## D083: Notifications Use A Durable Outbox Before External Providers

Reminder and notification work now lands in a first-class `notification_deliveries` outbox that the worker can claim and dispatch.

Reason: the runtime should stay truthful and testable before the platform is coupled to a paid email provider or a hosted notification service.

## D084: The First Hosted Delivery Lane Uses One Practical Staging Shape

The first hosted-delivery lane now assumes:

- one API container,
- one worker container,
- one static web container,
- PostgreSQL,
- Redis,
- a shared private-artifact volume.

Reason: the rebuild needs a staging path that is realistic enough to rehearse deployment and operations, while still staying simple enough for a small team to understand and run.

## D085: Runtime Readiness Must Check Real Dependencies, Not Just Process Uptime

The API now exposes:

- `/health/live`,
- `/health/ready`

and readiness checks the current database, artifact storage, and Redis coordination dependency state.

Reason: a pilot operator needs to know more than whether the API process is running; they need to know whether the service can actually do useful work.

## D086: Request IDs And Structured Request Logs Are Part Of The Runtime Contract

The API now emits a response `X-Request-ID` header and structured request logs for both successful and failed requests.

Reason: once the platform enters hosted rehearsal and pilot support, support and incident review need stable request correlation without depending on ad hoc local debugging.

## D087: Pilot Cutover Readiness Must Be A Live Computed Surface

The platform now exposes release readiness through a protected internal endpoint and internal workspace panel that combine:

- runtime environment and public URL checks,
- session and coordination safety checks,
- recent worker and notification health signals.

Reason: a pilot go/no-go decision should come from live platform state, not only from a static checklist in a document.

## D088: API Responses Ship A Baseline Security Header Set

The API now returns:

- `X-Content-Type-Options: nosniff`,
- `X-Frame-Options: DENY`,
- `Referrer-Policy: strict-origin-when-cross-origin`,
- `Strict-Transport-Security` in production-like runtime modes.

Reason: once the platform is being rehearsed for hosted pilot traffic, basic browser-facing hardening should be on by default instead of waiting for later infrastructure work.

## D089: Post-Pilot Mobile Reach Starts With A PWA Shell, Not A Separate Native Rewrite

The first post-pilot mobile expansion now uses:

- manifest metadata,
- service-worker registration,
- install lifecycle hooks,
- mobile-friendly shell layout changes.

Reason: the platform can improve repeat mobile usage quickly and safely on top of the existing web app without fragmenting the product into multiple unstable clients too early.

## D090: Agency Commercial Analytics Must Reuse Live Operational Data

The first commercial-overview surface derives its metrics from the existing organization, listing, application, and trust-check records instead of introducing a separate reporting store.

Reason: early post-pilot business visibility should stay explainable and low-risk, using the same canonical data the pilot-grade product already trusts.

## D091: Cinematic Visual Direction Must Stay Product-Led, Not Clone-Led

The next frontend experience track may borrow from Netflix-like confidence in contrast, density, motion, and cinematic presentation, but it should not become a literal Netflix clone.

Reason: the product needs a stronger and more modern visual identity, but usability, accessibility, and Trust Ledger's own brand clarity matter more than imitation.

## D092: Tenancy Creation May Resolve Counterparties By Email

Tenancy creation may now resolve tenant or landlord participants by email in addition to explicit user IDs.

Reason: the web app needs a practical way to create tenancy records without exposing raw internal identifiers to normal users.

## D093: Property Tags Are Lightweight User-Owned Portfolio Metadata

Property records may now carry custom user-managed tags for organization and filtering.

Reason: estate and agency operators need a fast way to group and find properties without over-engineering a heavier portfolio taxonomy too early.

## D094: Evidence Storage Must Stay API-Controlled While Allowing Backend Swaps

Stored evidence artifacts now keep one API-controlled access pattern while the storage backend may be either:

- local private file storage,
- S3-compatible object storage such as MinIO.

Reason: users and reviewers should experience one secure download flow, while operations retain the freedom to move from local storage to object storage without rewriting the evidence product flow.

## D095: Operator-Critical Targeting Should Accept Email, Not Only Internal IDs

Selected internal and organization-management actions may now resolve users by email in addition to raw internal IDs.

Examples:

- tenancy creation,
- organization membership adds,
- internal follow-up creation,
- direct internal score-refresh requests.

Reason: the frontend should expose the real workflows without forcing human operators to discover or paste opaque identifiers.

## D096: Dispute Workflows Need A First-Class Workspace Surface Before Visual Redesign

The operations workspace now includes a dedicated dispute desk that highlights:

- open disputes,
- items that can be disputed right now,
- the next action a tenant or landlord can take.

Reason: dispute capability existed in the backend and tenancy detail flows, but it was too easy to miss. Clarifying the workflow mattered more than styling it.

## D097: Login Role Selection Is Workspace Scoping, Not Authorization

The web app now lets a signed-in user choose an active workspace role:

- tenant,
- landlord,
- agency,
- reviewer.

The selected role controls which menus, routes, and role-relevant frontend records are shown. It does not grant permissions by itself.

Reason: this gives users strong separation of concerns without violating D007. Tenant and landlord remain business personas derived from domain participation, while agency and reviewer access still come from organization membership and system role checks enforced by the backend.
