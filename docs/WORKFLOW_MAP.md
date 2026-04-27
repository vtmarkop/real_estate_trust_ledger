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

- the non-dispute `Rent & Issues` lanes now begin with property targeting, so normal tenant/landlord work can stay inside one selected tenancy context instead of requiring cross-property scrolling
- the selected property also surfaces an operational history timeline built from the existing payment, deposit, and maintenance workflow timestamps
- inside the selected property, `Payments` and `Maintenance` now use compact record dropdowns so only one payment or issue detail/action/history pane is expanded at a time

## Role Model

The rebuilt product works with capability-driven roles instead of only hard-coded app personas.

- `Personal user`
  - Can act as tenant, landlord, or both depending on the tenancy/property relationship
- `Agency member`
  - Can use `Agency Tools`
- `Internal reviewer`
  - Can use `Review Center`
- `Platform admin`
  - Has the broadest internal control surface

Important architectural difference from the archive MVP:

- The old `judge` concept is now implemented as the internal `reviewer/admin` lane.
- This preserves the neutral-verdict business function without exposing a powerful adjudication role as a normal end-user persona.

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
3. Frontend loads `/auth/me`.
4. Navigation is built from capabilities.
5. User can later revoke an older session from `Account`.

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

1. Agency owner opens `Agency Tools`.
2. They switch to `Team access`.
3. They add an agent by email.
4. They can later change role or deactivate access.

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
   - agency user
   - prospective tenant
4. Agency users later search and tag the property in `Portfolio`.

### Example

- A landlord creates `Harbor Flat`, chooses `I manage this property myself`, and keeps the property outside agency management.
- Another landlord creates `Old Town Duplex`, chooses `An agency manages this property`, and assigns a named agent immediately.

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
  - `Create artifact`
  - `Artifact library`
  - `Reference request`
- `OperationsPage.js` for operational proof uploads

### Typical flow

1. User uploads a file as a private artifact.
2. The artifact is attached to an evidence document or operational record.
3. Reviewer later accepts or rejects it.
4. Short-lived access URLs keep the file private.

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
- `AgencyWorkbenchPage.js` in `Screening`

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
- Tenant applicant

### Backend routes

- listing CRUD/status routes
- application creation and status routes

### Backend services

- listing publication
- application status transitions
- application screening signals

### Models

- `Listing`
- `Application`

### Frontend

- `AgencyWorkbenchPage.js`
  - `Publishing`
  - `Pipeline`
- `MarketplacePage.js`

### Typical flow

1. Agency creates a property.
2. Agency publishes a listing with thresholds.
3. Tenant applies from `Listings`.
4. Agency reviews the application in `Pipeline`.
5. Status moves through submitted/review/accepted/rejected/withdrawn.

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
2. User selects the relevant payment from the payment menu or creates a new payment record.
3. Payer attaches proof inside the selected payment detail.
4. Payee confirms or rejects inside the selected payment detail.
5. If rejected, the other party may dispute and send the case into reviewer flow.
6. Once a payment is disputed or re-opened for review, the normal payee decision path is blocked.
7. The selected payment detail shows its local timeline/history.
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
2. User selects the relevant issue from the issue menu or creates a new maintenance ticket.
3. Tenant reports a problem with evidence.
4. Landlord acknowledges and resolves with response evidence inside the selected issue detail.
5. The selected issue detail shows its local timeline/history.
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
- Platform admin

### Backend routes

- internal tenancy review
- internal evidence review
- internal history import review
- internal dispute review

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
- Reviewer/admin for manual score operations
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
2. Internal reviewer can queue a refresh or batch recalculation.
3. Worker/runtime processes queued items.
4. Score history remains visible to the subject user.

## Workflow 15: Automation, Notifications, Worker Runs

### Roles

- Reviewer/admin
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

1. Internal operator claims or executes automation tasks.
2. Notification deliveries are monitored from the same lane.
3. Worker runs are inspected for failures and throughput.

## Workflow 16: Audit And Release Readiness

### Roles

- Reviewer/admin

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

1. Internal operator checks release readiness.
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
   - current scores
   - verification strength
   - score history
   - trust events
   - sharing/access history

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
