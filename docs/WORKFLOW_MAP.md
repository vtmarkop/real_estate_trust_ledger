# Workflow Map

This document maps the rebuilt Trust Ledger product from backend to frontend so we can trace every important business workflow end to end.

Use this document when you want to answer questions like:

- Which backend route powers this screen?
- Which service owns the business logic for this workflow?
- Which model stores the state?
- Which user role is supposed to act next?
- Where should we make a change without mixing concerns?

## How To Read This Map

Each workflow is described across the same layers:

- `Roles`: who is allowed to act
- `Backend routes`: where the HTTP contract lives
- `Backend services`: where the business logic lives
- `Models`: where state is stored
- `Frontend`: where the workflow appears in the app
- `Typical flow`: the expected real-world sequence

## Frontend Lanes After The Workflow Simplification Pass

The rebuilt web app now separates work by lane so each role does the minimum needed work in one place:

- `Home`: orientation and quick status
- `My Trust`: scores, score history, trust events, consent sharing
- `Listings`: tenant-facing browse/apply flow
- `Rental Records`: property setup, tenancy setup, artifacts, imports, and references
- `Rent & Issues`: payments, deposits, maintenance, and the dispute desk
- `Agency Tools`: publishing, portfolio, screening, team access, and pipeline
- `Review Center`: overview, controls, reviews, disputes, runtime, and audit
- `Account`: session and account safety controls

The shell now also applies an active workspace role:

- `tenant`: tenant trust, listings, tenant records, and tenant-side operations
- `landlord`: landlord trust, property/tenant records, and landlord-side operations
- `agency`: agency tools only, plus account controls
- `reviewer/internal`: review queues and dispute verdict work, plus account controls
- `admin/internal`: platform controls, account role management, audit/runtime/release tooling, plus account controls

The available roles come from explicit account workspace-role entitlements returned by `/auth/me`. The active role decides what workspace is visible; backend routes still enforce tenancy participation, property ownership, agency organization membership, reviewer system role, admin system role, or other internal privileges before allowing real actions. Agency workspace creation is intentionally tied to the `agency` entitlement: an unassigned agent can create the first agency organization from `Home`, while landlord-only accounts stay in owner-managed property setup.

The dense pages are now intentionally split into tabs or lanes:

- `Rental Records`
  - `Tenancy records`
  - `Properties & setup`
  - `Artifacts`
  - `History & references`
- `Rent & Issues`
  - `Payments`
  - `Deposit`
  - `Maintenance`
  - `Dispute desk`
- `Agency Tools`
  - `Overview`
  - `Publishing`
  - `Portfolio`
  - `Screening`
  - `Screening history`
  - `Team access`
  - `Pipeline`
- `Review Center`
  - `Overview`
  - `Controls`
  - `Reviews`
  - `Disputes`
  - `Runtime`
  - `Audit`

This matters because it gives us clearer separation of concerns both in the UI and in future code changes.

Current UX-reset note:

- users now sign in first, then the shell opens the last valid role for the browser or the first assigned account role; mixed-role users switch roles from the sidebar, not from a pre-login dropdown
- role availability comes from explicit account workspace-role entitlements, and the active role scopes visible menus, direct routes, score dimensions, tenancy records, property setup, and operational records without replacing backend authorization
- the non-dispute `Rent & Issues` lanes now begin with property targeting, so normal tenant/landlord work can stay inside one selected tenancy context instead of requiring cross-property scrolling
- tenancy metadata in `Rental Records` and `Rent & Issues` now identifies the signed-in user's role and the counterparty instead of repeating generic tenant/landlord labels
- the selected property now separates `Daily work` from read-only `History`, so forms/actions and timeline browsing are no longer mixed together
- inside `Daily work`, `Payments` and `Maintenance` first split create-new work from existing saved records, then use compact record dropdowns so only one payment or issue detail/action pane is expanded at a time
- inside `History`, the selected property shows the read-only timeline and saved proof/notes/verdict details for the active operational lane, built from existing payment, deposit, or maintenance workflow timestamps
- agency `Screening` is now action-only, while saved trust checks live in `Screening history`
- score transparency now uses one contribution vocabulary across `My Trust`, agency trust previews, and internal scoring controls instead of hiding the scoring formula in source code or daily action forms
- landlord agency assignment now uses active agency-operator choices instead of manual email guessing, and agency-created properties are saved as agency inventory assigned to the selected organization and signed-in agent so listing publication has a real property to use; that inventory can also be explicitly linked to an existing landlord owner account when the agency is preparing the property for that owner
- self-managed landlord listing publication now lives in `Rental Records > Properties & setup > Publish listing`, while tenant `Listings` stays unified and labels whether a home is listed by an agency or directly by a landlord
- accepted applications now surface an explicit tenancy-creation bridge in the manager's review lane, and button-like actions expose hover/focus help bubbles so novice users can understand what each action will do before clicking
- `Tenancy records` now shows existing role-scoped tenancy cards as well as the create form, so accepted-application bridge output and direct tenancy records are visible before artifact/evidence work
- `Artifacts` now starts with an active tenancy selector and only renders the selected tenancy's upload, library, and reference workspace, avoiding the old all-tenancies-at-once card sprawl
- `docs/WORKFLOW_QA_PLAN.md` is the active execution plan for validating these workflows with real local accounts, mouse/keyboard interaction, dummy data, console checks, and classification in `WORKFLOW_GAPS.md`

## Role Model

The rebuilt product works with explicit account workspace-role entitlements plus record-level permissions instead of only hard-coded app personas.

- `Personal user`
  - Can be entitled for tenant, landlord, or both
  - Still needs the relevant tenancy/property relationship before backend routes allow record access
  - Chooses an active tenant or landlord workspace mode so the UI only shows that persona's records and actions
- `Agency member`
  - Needs the agency workspace entitlement to see agency mode
  - Still needs active agency organization membership before backend agency routes allow work
  - Can create an agency organization from `Home` when the account has the agency entitlement and no agency membership yet
- `Internal reviewer`
  - Needs the internal workspace entitlement plus the reviewer system role to see case-review sections
  - Can issue tenancy, evidence, history-import, payment, deposit, and maintenance review decisions
- `Platform admin`
  - Needs the internal workspace entitlement plus the admin system role to see platform-control sections
  - Can manage account workspace roles, scoring controls, automation, notifications, workers, audit, and release readiness

Important architectural difference from the archive MVP:

- The old `judge` concept is now implemented as the internal reviewer lane only.
- This preserves the neutral-verdict business function without exposing case decisions to the platform-admin role or to a normal end-user persona.
- The active workspace role is a UI scoping choice and entitlement filter, not a record-access grant. Backend access still depends on system roles, organization memberships, and record participation.

## Workflow 1: Authentication And Session Safety

### Roles

- Everyone

### Backend routes

- `/api/v1/auth/register`
- `/api/v1/auth/login`
- `/api/v1/auth/logout`
- `/api/v1/auth/me`
- `/api/v1/auth/sessions`
- `/api/v1/auth/sessions/{session_id}`

### Backend services and support

- session and auth handling live in the auth route layer plus the shared security/config modules

### Models

- `User`
- `AuthSession`

### Frontend

- `AuthPage.js`
- `SecurityPage.js`
- navigation/session capability helpers in `session.js` and `router.js`

### Typical flow

1. User signs in.
2. Backend creates an opaque session.
3. Frontend loads `/auth/me` and `/organizations/mine`.
4. The saved browser workspace role is normalized against `user.workspace_roles`.
5. Navigation is built from the active role plus backend-derived capabilities.
6. User can later switch active role from the shell or revoke an older session from `Account`.
7. A platform admin can add or remove account workspace-role entitlements from `Review Center > Roles`.

### Example

- A landlord signs in from a laptop and a phone.
- In `Account`, they revoke the older phone session without logging out the laptop they are currently using.

## Workflow 2: Organization And Membership Management

### Roles

- Agency owner/admin
- Platform admin for internal organizations

### Backend routes

- `/api/v1/organizations`
- `/api/v1/organizations/{organization_id}`
- `/api/v1/organizations/{organization_id}/memberships`

### Backend services and support

- organization role and membership validation

### Models

- `Organization`
- `OrganizationMembership`

### Frontend

- `AgencyWorkbenchPage.js` in `Team access`

### Typical flow

1. If no agency organization exists yet, an agent-entitled account opens `Home` and creates the agency workspace.
2. The organization endpoint creates that account's owner membership.
3. Agency owner opens `Agency Tools`.
4. They switch to `Team access`.
5. They add an agent by email.
6. They can later change role or deactivate access.

Current clarity rule:

- `POST /organizations` for an agency organization now requires the current user to have the `agency` workspace entitlement.
- Landlord-only accounts do not see the agency workspace creation panel and should use owner-managed property setup unless a real agency organization later exists.
- If `Agency Tools` opens before membership exists, it should explain the missing agency organization and point the user back to `Home` or an owner invite.

## Workflow 3: Property Setup And Management Mode

### Roles

- Landlord / property owner
- Agency user with assigned property access

### Backend routes

- `/api/v1/properties`
- `/api/v1/properties/mine`
- `/api/v1/properties/{property_id}`

### Backend services

- property creation, assignment resolution, tag handling, and management mode validation

### Models

- `Property`

### Frontend

- `RecordsPage.js` in `Properties & setup`
- `AgencyWorkbenchPage.js` in `Portfolio`

### Typical flow

1. Landlord creates a property.
2. They choose management mode:
   - `owner_managed`
   - `agency_managed`
3. They can assign:
   - agency organization
   - agency operator from the active owner/admin/agent directory
   - prospective tenant
4. Agency users later search and tag the property in `Portfolio`.
5. Agency users can also create agency inventory directly from `Agency Tools > Publishing`; that inventory is assigned to the agency organization and signed-in agent and can be listed immediately.
6. If the agency-created property belongs to an existing landlord account, the agent can add that landlord's email during creation or later from `Agency Tools > Portfolio`.

### Example

- A landlord creates `Harbor Flat`, chooses `I manage this property myself`, and keeps the property outside agency management.
- Another landlord creates `Old Town Duplex`, chooses `An agency manages this property`, and assigns a named agent immediately.

Current clarity rule:

- If the agency directory is empty, `Rental Records > Properties & setup` keeps `owner_managed` as the available path and explains that agency assignment can happen later.
- The backend still requires a real agency organization for `agency_managed`; the frontend should not imply agency assignment exists before the organization exists.
- Landlord-owned properties can still be created from landlord mode and optionally assigned to an agency. Agency-created properties remain agency inventory for publication, but they can now carry a separate explicit landlord-owner link to an existing account with the landlord workspace role.

## Workflow 4: Tenancy Creation, Counterparty Confirmation, And Review Request

### Roles

- Tenant
- Landlord
- Internal reviewer

### Backend routes

- `/api/v1/tenancies`
- `/api/v1/tenancies/mine`
- `/api/v1/tenancies/{tenancy_id}/confirm`
- `/api/v1/tenancies/{tenancy_id}/request-review`

### Backend services

- tenancy creation and party/property synchronization

### Models

- `Tenancy`
- `TrustEvent`

### Frontend

- `RecordsPage.js` in `Tenancy records`

### Typical flow

1. Tenant or landlord creates a tenancy using counterparty email.
2. Counterparty confirms the relationship.
3. Either side requests review if the tenancy should be formally reviewed/verified.
4. Reviewer sees it later in `Review Center > Reviews`.

UI continuity rule:

- `Tenancy records` must show both the creation form and the existing role-scoped records. Counterparty confirmation and review-request actions belong on the existing tenancy card. Artifact upload, evidence, imports, and references stay in their own lanes.

### Example

- Landlord creates a tenancy for `tenant@demo.trustledger.app`.
- Tenant signs in, confirms it, and the tenancy becomes a stronger trust signal than a self-reported record.

## Workflow 5: Artifact Storage And Evidence Documents

### Roles

- Tenant
- Landlord
- Reviewer

### Backend routes

- `/api/v1/evidence/artifacts`
- `/api/v1/evidence/artifacts/{artifact_id}/access`
- evidence-document creation/review routes

### Backend services

- artifact storage
- signed artifact access
- evidence review handling

### Models

- `StoredArtifact`
- `EvidenceDocument`

### Frontend

- `RecordsPage.js` in `Artifacts`
  - `Choose one tenancy for artifacts`
  - `Active artifact tenancy`
  - `Create artifact`
  - `Artifact library`
  - `Reference request`
- `OperationsPage.js` for operational proof uploads

### Typical flow

1. User uploads a file as a private artifact.
2. The artifact is attached to an evidence document or operational record.
3. Reviewer later accepts or rejects it.
4. Short-lived access URLs keep the file private.

UI continuity rule:

- `Artifacts` should not act as a tenancy overview. Users choose one tenancy first, then work with that tenancy's artifact upload, library, and reference actions. Current tenancy facts and confirmation/review actions stay in `Tenancy records`.

### Example

- Tenant uploads a rent proof PDF.
- Landlord uploads a repair invoice image.
- Reviewer opens each artifact from the review queue without exposing a public file URL.

## Workflow 6: Historical Imports And Cold-Start Onboarding

### Roles

- Tenant
- Landlord
- Reviewer

### Backend routes

- history import creation and review endpoints under the trust/evidence review surface

### Backend services

- historical import packaging
- evidence association
- reviewer decision flow

### Models

- `HistoryImport`
- linked `Tenancy` and `EvidenceDocument` records

### Frontend

- `RecordsPage.js` in `History & references`
- `Review Center > Reviews`

### Typical flow

1. User creates a historical import bundle.
2. They attach prior tenancy and payment evidence.
3. Reviewer accepts or rejects the import.
4. Accepted imports strengthen early trust without bank APIs.

## Workflow 7: Reference Requests

### Roles

- Tenant
- Landlord
- Previous counterparty

### Backend routes

- reference request create/respond routes

### Backend services

- request generation
- response capture
- provenance into trust/evidence state

### Models

- `ReferenceRequest`

### Frontend

- `RecordsPage.js` in `History & references`
- tenancy-level `Artifacts` references tab

### Typical flow

1. User sends a reference request.
2. Counterparty answers.
3. The response becomes part of the trust record.

## Workflow 8: Consent Sharing And Agency Trust Checks

### Roles

- Subject user
- Agency member

### Backend routes

- `/api/v1/consents/trust-report`
- `/api/v1/consents/trust-report/access-history`
- `/api/v1/organizations/{organization_id}/trust-checks/validate`
- `/api/v1/organizations/{organization_id}/trust-checks/profile`
- `/api/v1/organizations/{organization_id}/trust-checks`

### Backend services

- consent validation
- trust profile composition
- trust check recording

### Models

- `TrustReportConsent`
- `AgencyTrustCheck`
- `TrustScore`
- `TrustScoreHistory`

### Frontend

- `TrustProfilePage.js`
- `AgencyWorkbenchPage.js` in `Screening` for actions and `Screening history` for saved trust-check records

### Typical flow

1. Subject user creates a share token and access code.
2. Agency user enters both in `Agency Tools > Screening`.
3. Agency can validate, preview, or save a trust check.
4. Subject user sees access history in `My Trust`.

### Example

- A tenant shares a report with a letting agency.
- The agent previews the score before deciding whether to save a formal trust check into agency history.

## Workflow 9: Listing Publication And Application Pipeline

### Roles

- Agency owner/admin/agent
- Landlord for owner-managed direct listings
- Tenant applicant

### Backend routes

- `/api/v1/organizations/{organization_id}/listings`
- `/api/v1/organizations/{organization_id}/applications`
- `/api/v1/organizations/{organization_id}/applications/{application_id}/tenancy`
- `/api/v1/landlord/listings`
- `/api/v1/landlord/applications`
- `/api/v1/landlord/applications/{application_id}/tenancy`
- `/api/v1/listings/open`
- `/api/v1/listings/{listing_id}/applications`
- `/api/v1/applications/mine`

### Backend services

- listing publication
- application status transitions
- application screening signals
- accepted-application tenancy creation

### Models

- `Listing`
- `ListingApplication`
- `Tenancy`

### Frontend

- `AgencyWorkbenchPage.js`
  - `Publishing`
  - `Pipeline`
- `RecordsPage.js`
  - `Properties & setup`
  - `Publish listing`
- `MarketplacePage.js`

### Typical flow

1. Agency path:
   - agency creates agency inventory
   - property is saved against the agency organization
   - agency publishes a listing with thresholds
   - tenant applies from `Listings`
   - agency reviews the application in `Agency Tools > Pipeline`
   - after acceptance, agency creates the tenancy from the accepted application
2. Owner-managed landlord path:
   - landlord creates or keeps a property as `owner_managed`
   - landlord opens `Rental Records > Properties & setup > Publish listing`
   - landlord publishes the listing directly with rent, deposit, score, and verification thresholds
   - tenant applies from the same `Listings` page
   - landlord reviews the application from the same `Publish listing` lane
   - after acceptance, landlord creates the tenancy from the accepted application
3. Status moves through submitted/review/accepted/rejected/withdrawn according to the same application transition rules.
4. Acceptance is only the decision. Tenancy creation is a separate explicit action that links `tenancy_id`, closes the listing, assigns the tenant to the property, copies the listing terms into the tenancy, and writes tenancy-created trust events.
5. The created tenancy must then be visible to both parties from `Rental Records > Tenancy records`; it should not require users to discover it inside `Artifacts`.

Current guard:

- `POST /organizations/{organization_id}/listings` requires the selected property to be assigned to the same agency organization. This prevents a loose owner-managed property from becoming an agency listing by accident.
- A landlord-owner link does not replace the agency assignment guard. It only lets the linked landlord see and reuse the agency-created property in landlord mode.
- `POST /landlord/listings` requires the signed-in landlord to own the property and the property to be `owner_managed`. It does not accept agency-managed inventory.
- Tenant discovery is unified through `Listings`, but listing responses expose `listing_source` and `manager_name` so the UI can distinguish `Listed by agency` from `Listed by landlord`.
- A mixed tenant/landlord account cannot apply to its own landlord-managed listing from tenant mode.
- Agency application-to-tenancy creation requires the property to have an existing linked landlord owner; owner-managed landlord listings use the signed-in landlord owner directly.
- `ListingApplication.tenancy_id` records whether an accepted application has already produced a tenancy.

## Workflow 10: Payment Ledger, Dispute, Verdict, Appeal

### Roles

- Tenant / payer
- Landlord / payee
- Reviewer

### Backend routes

- payment create/list/update endpoints
- payment proof/counterparty/dispute/verdict/appeal routes

### Backend services

- payment lifecycle
- artifact validation for payment proof
- dispute verdict handling

### Models

- `Payment`
- related `StoredArtifact`
- related `TrustEvent`

### Frontend

- `OperationsPage.js`
  - `Payments`
  - `Dispute desk`
- `InternalOperationsPage.js` in `Disputes`

### Typical flow

1. User selects the relevant property from the `Rent & Issues` property menu.
2. User keeps `Daily work` active, then chooses either `Create new` for a blank payment form or `Existing records` for the payment menu.
3. Payer attaches proof inside the selected payment detail.
4. Payee confirms or rejects inside the selected payment detail.
5. If rejected, the other party may dispute and send the case into reviewer flow.
6. Once a payment is disputed or re-opened for review, the normal payee decision path is blocked.
7. User switches to `History` when they want proof files, old notes, prior decisions, or the read-only payment/deposit/maintenance timeline for the selected property.
8. Reviewer issues verdict if needed.
9. Either side may appeal, which returns the case to `UNDER_REVIEW` for a fresh verdict.
10. Score impact is recalculated through the central scoring service.

## Workflow 11: Deposit Settlement, Dispute, Verdict, Appeal

### Roles

- Tenant
- Landlord
- Reviewer

### Backend routes

- deposit create/list/settle/dispute/verdict/appeal endpoints

### Backend services

- deposit settlement validation
- dispute handling
- score impact integration

### Models

- `Deposit`

### Frontend

- `OperationsPage.js`
  - `Deposit`
  - `Dispute desk`
- `InternalOperationsPage.js` in `Disputes`

### Typical flow

1. User selects the relevant property from the `Rent & Issues` property menu.
2. Landlord proposes settlement.
3. Tenant disputes if necessary.
4. Reviewer issues verdict.
5. Either side may appeal, which returns the case to `UNDER_REVIEW`.
6. The previous verdict is no longer final until a fresh verdict is issued.

## Workflow 12: Maintenance Ticket, Response, Dispute, Verdict, Appeal

### Roles

- Tenant
- Landlord
- Reviewer

### Backend routes

- maintenance ticket create/acknowledge/resolve/dispute/verdict/appeal endpoints

### Backend services

- ticket lifecycle
- evidence linking
- dispute handling

### Models

- `MaintenanceTicket`

### Frontend

- `OperationsPage.js`
  - `Maintenance`
  - `Dispute desk`
- `InternalOperationsPage.js` in `Disputes`

### Typical flow

1. User selects the relevant property from the `Rent & Issues` property menu.
2. User keeps `Daily work` active, then chooses either `Report new` for a blank issue form or `Existing issues` for the issue menu.
3. Tenant reports a problem with evidence.
4. Landlord acknowledges and resolves with response evidence inside the selected issue detail.
5. User switches to `History` when they want issue evidence, resolution notes, prior decisions, or the read-only payment/deposit/maintenance timeline for the selected property.
6. If disputed, reviewer decides.
7. Either party can appeal, which returns the case to `UNDER_REVIEW`.
8. The reopened case stays in reviewer flow until a fresh verdict is issued.

### Example

- Tenant uploads leak photos.
- Landlord uploads contractor invoice and resolution note.
- Reviewer rules whether the response was adequate and updates score impact accordingly.

## Workflow 13: Internal Review Queues

### Roles

- Reviewer

### Backend routes

- internal tenancy review, reviewer-only
- internal evidence review, reviewer-only
- internal history import review, reviewer-only
- internal dispute review, reviewer-only

### Backend services

- reviewer decision processing
- trust-event creation

### Models

- `Tenancy`
- `EvidenceDocument`
- `HistoryImport`
- dispute-bearing records

### Frontend

- `InternalOperationsPage.js` in `Reviews` and `Disputes`

### Typical flow

1. Reviewer opens `Review Center`.
2. They move to `Reviews` for tenancy/evidence/history decisions.
3. They move to `Disputes` for first verdicts and appealed re-review work.
4. Decisions feed the trust ledger and scoring system.

## Workflow 14: Trust Scores And Score Runtime

### Roles

- Everyone for personal score viewing
- Platform admin for manual score operations
- Worker runtime for background processing

### Backend routes

- `/api/v1/trust-scores/mine`
- `/api/v1/trust-scores/mine/history`
- internal scoring queue and batch routes

### Backend services

- central scoring service
- recalculation queue
- batch scheduling

### Models

- `TrustScore`
- `TrustScoreHistory`
- `TrustScoreRecalculationRequest`
- `TrustScoreRecalculationBatch`

### Frontend

- `TrustProfilePage.js`
- `InternalOperationsPage.js` in `Controls`

### Typical flow

1. Score is viewed from `My Trust`.
2. The personal UI labels tenant-side score as the user's renter dimension and landlord-side score as the user's own landlord/property-owner dimension.
3. The Overview lane shows base score, role-specific contribution rows, verification-strength contribution rows, and adjudication adjustments.
4. Platform admin can queue a refresh or batch recalculation.
5. Worker/runtime processes queued items.
6. Score history remains visible to the subject user with tenant-side and landlord-side labels.

### Score contribution transparency

- `My Trust` shows the neutral base score, fixed tenant/landlord contribution rows, verification-strength contribution rows, and reviewer-entered adjudication deltas for the active role.
- Agency trust previews explain aggregate tenant-side score drivers and verification strength without exposing role-irrelevant private workflow history.
- Internal scoring controls use the same contribution vocabulary so support can explain the same numbers users see.
- This explanation belongs in trust, preview, and scoring-control surfaces, not inside daily payment/deposit/maintenance action forms.

## Workflow 15: Automation, Notifications, Worker Runs

### Roles

- Platform admin
- Worker process

### Backend routes

- internal automation routes
- internal notifications routes
- internal worker routes

### Backend services

- automation queue
- notification outbox
- worker run tracking

### Models

- `AutomationTask`
- `NotificationDelivery`
- `WorkerRun`

### Frontend

- `InternalOperationsPage.js` in `Runtime`

### Typical flow

1. Platform admin claims or executes automation tasks.
2. Notification deliveries are monitored from the same lane.
3. Worker runs are inspected for failures and throughput.

## Workflow 16: Audit And Release Readiness

### Roles

- Platform admin

### Backend routes

- internal audit routes
- internal release readiness route

### Backend services

- audit logging
- release readiness evaluation

### Models

- `AuditLog`

### Frontend

- `InternalOperationsPage.js`
  - `Overview` for release readiness
  - `Audit` for audit events

### Typical flow

1. Platform admin checks release readiness.
2. They inspect audit history when tracing actions or failures.

## Workflow 17: Personal Trust Visibility

### Roles

- Tenant
- Landlord

### Backend routes

- `/api/v1/trust-scores/mine`
- `/api/v1/trust-scores/mine/history`
- `/api/v1/trust-events/mine`
- consent history routes

### Backend services

- trust profile aggregation

### Models

- score, history, events, consents

### Frontend

- `TrustProfilePage.js`

### Typical flow

1. User opens `My Trust`.
2. They see:
   - current tenant-side and landlord-side scores
   - verification strength
   - score history
   - trust events
   - sharing/access history
3. If the account has no landlord-side inputs yet, the UI explains that the landlord-side score is inactive/neutral and is not a score for the user's current landlord.
4. The Overview lane shows the point-by-point contribution explanation so users can see how the base score, accepted evidence, references, verified tenancies, history imports, and reviewer verdict deltas affect the visible score.

## Workflow 18: Demo Data Scenarios

The demo seed supports real workflow exploration instead of empty placeholder records.

- `Harbor Flat`
  - healthy active tenancy
  - normal operational usage
- `Old Town Duplex`
  - verdict-issued dispute examples
- `Hillside Studio`
  - pending reviewer work
- `Agency Showcase Loft`
  - agency publishing/screening example

Use these when testing workflow behavior end to end.

## Fast Tracing Examples

### Example A: “Where does a payment dispute live?”

- Frontend:
  - `OperationsPage.js` in `Payments` and `Dispute desk`
  - `InternalOperationsPage.js` in `Disputes`
- Backend:
  - payment routes
  - payment service
  - payment model
  - scoring service for verdict impact

### Example B: “Where do I change property assignment rules?”

- Frontend:
  - `RecordsPage.js` in `Properties & setup`
  - `AgencyWorkbenchPage.js` in `Portfolio`
- Backend:
  - property routes
  - property service
  - property model

### Example C: “Where does evidence review happen?”

- Frontend:
  - `RecordsPage.js` for creation
  - `InternalOperationsPage.js` in `Reviews` for review decisions
- Backend:
  - artifact/evidence routes
  - artifact service
  - evidence document model

## Practical Maintenance Rule

When changing the product, try to make the change in the narrowest layer that owns the concern:

- UI grouping or wording issue:
  - frontend page/component
- validation or transition rule:
  - backend service or route contract
- stored truth or relationship:
  - model plus migration
- cross-workflow business effect:
  - service layer plus tests

That rule helps us keep the product simple instead of letting screens, services, and models bleed into each other.
