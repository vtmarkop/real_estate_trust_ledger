# Workflow Diagrams

This document turns the implemented Trust Ledger workflows into visual diagrams.

It is intentionally based on the real rebuild, not on the original concept alone.

That means these diagrams reflect:

- the current backend routes,
- the current service boundaries,
- the current frontend workspaces and lanes,
- the current neutral-reviewer model instead of the old public `judge` role.

Use this together with:

- `docs/WORKFLOW_MAP.md` for the written flow map
- `docs/CODEBASE_REFERENCE.md` for the code-level reference
- `docs/WORKSPACE_GUIDE.md` for the operator/user guide

## Diagram 1: Workspace And Role View

This diagram shows how the main roles enter the product and which frontend workspace they primarily use.

```mermaid
flowchart TD
    A["User signs in"] --> B{"Account workspace-role entitlements"}
    B --> K{"Active workspace role"}
    K -->|"tenant"| C["Tenant Home"]
    K -->|"tenant"| D["Tenant Trust"]
    K -->|"tenant"| E["Tenant Rental Records"]
    K -->|"tenant"| F["Tenant Rent & Issues"]
    K -->|"tenant"| G["Listings"]
    K -->|"landlord"| L["Landlord Home"]
    K -->|"landlord"| M["Landlord Trust"]
    K -->|"landlord"| N["Landlord Rental Records"]
    K -->|"landlord"| O["Landlord Rent & Issues"]
    K -->|"agency"| I["Agency Tools"]
    K -->|"internal/admin"| J["Review Center"]
    K --> H["Account"]
```

### What this reflects

- Account role visibility is explicit: tenant, landlord, agency, and internal/admin roles come from `User.workspace_roles`.
- Login is email/password only; the active role is resolved after authentication and can be changed from the sidebar.
- Personal users only see tenant or landlord modes when those entitlements are assigned.
- Agency mode can be assigned independently, but backend agency work still requires active agency organization membership.
- Internal/admin mode is separate from agency access and is synced with backend platform-admin protection.
- A user can still have multiple legitimate workspace roles, but the active role controls which workspace is visible at one time.

## Diagram 2: Property Setup To Tenancy Activation

This is the real onboarding chain for the landlord/tenant/property relationship.

```mermaid
flowchart TD
    A["Landlord opens Rental Records > Properties & setup"] --> B["Create property"]
    B --> C{"Management mode"}
    C -->|"owner_managed"| D["Landlord keeps direct operational control"]
    C -->|"agency_managed"| E["Assign agency organization"]
    E --> F["Optional: assign agency user"]
    D --> G["Optional: assign prospective tenant"]
    F --> G
    G --> H["Property is saved"]
    H --> I["Tenant or landlord creates tenancy"]
    I --> J["Counterparty confirms tenancy"]
    J --> K["Optional: request review"]
    K --> L["Review Center > Reviews"]
```

### Frontend lanes

- `Rental Records > Properties & setup`
- `Rental Records > Tenancy records`
- `Review Center > Reviews`

UX clarity note: tenancy cards now show the signed-in user's role and the relevant tenant/landlord counterparty instead of a generic `Parties` label.

### Backend surface

- properties routes
- tenancies routes
- internal review queue routes

## Diagram 3: Artifact And Evidence Lifecycle

This diagram shows the evidence-backed architecture without bank APIs.

```mermaid
flowchart TD
    A["User opens Rental Records > Artifacts"] --> B["Create artifact"]
    B --> C["Upload private file"]
    C --> D["StoredArtifact created"]
    D --> E["Attach artifact to evidence document or operational record"]
    E --> F{"What kind of proof is it?"}
    F -->|"tenancy evidence"| G["Tenancy evidence review queue"]
    F -->|"reference support"| H["Reference workflow"]
    F -->|"payment / deposit / maintenance proof"| I["Operational record view"]
    G --> J["Reviewer accepts or rejects evidence"]
    I --> K["Counterparty sees proof in Rent & Issues"]
    K --> L{"Dispute raised?"}
    L -->|"no"| M["Operational record continues normally"]
    L -->|"yes"| N["Review Center > Disputes"]
```

### Key architectural point

The storage layer is private and signed-access based. Files are not meant to become public URLs.

## Diagram 4: Listing, Application, And Agency Screening

This is the implemented agency pipeline from property publication to applicant handling.

```mermaid
flowchart TD
    A["Agency Tools > Publishing"] --> B["Create or reuse property"]
    B --> C["Publish listing with rent, deposit, score thresholds"]
    C --> D["Listing becomes visible in Listings"]
    D --> E["Tenant browses open listings"]
    E --> F["Tenant applies"]
    F --> G["Agency Tools > Pipeline"]
    G --> H["Agency reviews application status"]
    G --> I["Agency runs trust check from Screening"]
    I --> J["Consent token + access code validated"]
    J --> K["Trust profile preview or saved trust check"]
    H --> L{"Decision"}
    L -->|"under review"| M["Stay in pipeline"]
    L -->|"accepted"| N["Applicant advances"]
    L -->|"rejected"| O["Applicant closed out"]
```

### Frontend lanes

- `Agency Tools > Publishing`
- `Agency Tools > Screening`
- `Agency Tools > Pipeline`
- `Listings`

## Diagram 5: Payment Workflow With Dispute And Appeal

This diagram reflects the actual payment lifecycle in the rebuilt app.

```mermaid
sequenceDiagram
    participant Tenant
    participant Frontend as "Rent & Issues > Payments"
    participant API as "payments routes"
    participant Service as "payments service"
    participant Reviewer as "Review Center > Disputes"
    participant Scoring as "scoring service"

    Tenant->>Frontend: Select property, then create or choose a payment
    Frontend->>API: POST /payments/tenancies/{tenancy_id}
    API->>Service: validate tenancy and participants
    Service-->>API: payment created
    API-->>Frontend: PaymentResponse

    Tenant->>Frontend: Submit proof artifact
    Frontend->>API: POST /payments/{payment_id}/proof
    API->>Service: attach proof and update state
    Service-->>API: proof recorded
    API-->>Frontend: updated payment

    Frontend->>API: POST /payments/{payment_id}/decision
    API->>Service: counterparty decision
    Service-->>API: decision saved

    alt disputed
        Frontend->>API: POST /payments/{payment_id}/dispute
        API->>Service: mark disputed
        Reviewer->>API: POST /internal/disputes/payments/{payment_id}/verdict
        API->>Scoring: include verdict deltas in refresh path
        Scoring-->>API: score impact persisted
        API-->>Reviewer: verdict issued
        Frontend->>API: POST /payments/{payment_id}/appeal
        API->>Service: reopen dispute
        API->>Scoring: remove old verdict effect until resolved again
    else agreed
        Service-->>API: payment completes without dispute
    end
```

Continuity note: once a payment is disputed or appealed, the next action belongs to `Review Center > Disputes` until a reviewer issues the next verdict. The normal counterparty decision path is no longer the active handoff.

UX-reset note: the personal `Payments` lane now keeps the selected property active, separates `Create new` from `Existing records`, exposes one selected payment detail/action pane from a compact payment dropdown under existing records, and keeps proof files, old notes, prior decisions, and the read-only timeline in the selected property's separate `History` view.

### Why this matters

This is one of the clearest examples of “real workflow” in the rebuild:

- proof,
- counterparty response,
- dispute,
- reviewer verdict,
- appeal,
- score effect.

## Diagram 6: Maintenance Ticket Workflow With Dispute And Appeal

```mermaid
sequenceDiagram
    participant Tenant
    participant Landlord
    participant Frontend as "Rent & Issues > Maintenance"
    participant API as "maintenance routes"
    participant Service as "maintenance service"
    participant Reviewer as "Review Center > Disputes"

    Tenant->>Frontend: Select property, then report or choose an issue
    Frontend->>API: POST /maintenance-tickets/tenancies/{tenancy_id}
    API->>Service: create ticket
    Service-->>API: ticket created

    Landlord->>Frontend: Acknowledge issue
    Frontend->>API: POST /maintenance-tickets/{ticket_id}/acknowledge
    API->>Service: record acknowledgement

    Landlord->>Frontend: Resolve issue with summary and evidence
    Frontend->>API: POST /maintenance-tickets/{ticket_id}/resolve
    API->>Service: record resolution

    alt tenant disputes resolution
        Frontend->>API: POST /maintenance-tickets/{ticket_id}/dispute
        API->>Service: mark disputed
        Reviewer->>API: POST /internal/disputes/maintenance/{ticket_id}/verdict
        API->>Service: persist verdict
        Frontend->>API: POST /maintenance-tickets/{ticket_id}/appeal
        API->>Service: reopen case
    else resolved cleanly
        Service-->>API: ticket remains resolved
    end
```

Continuity note: an appeal returns the ticket to `Review Center > Disputes`, and the earlier verdict is no longer final until a fresh verdict is issued.

UX-reset note: the personal `Maintenance` lane now keeps the selected property active, separates `Report new` from `Existing issues`, exposes one selected issue detail/action pane from a compact issue dropdown under existing issues, and keeps issue evidence, resolution notes, prior decisions, and the read-only timeline in the selected property's separate `History` view.

## Diagram 7: Deposit Settlement Workflow With Dispute And Appeal

```mermaid
sequenceDiagram
    participant Landlord
    participant Tenant
    participant Frontend as "Rent & Issues > Deposit"
    participant API as "deposits routes"
    participant Service as "deposits service"
    participant Reviewer as "Review Center > Disputes"

    Frontend->>API: POST /deposits/tenancies/{tenancy_id}
    API->>Service: create deposit record
    Service-->>API: deposit created

    Landlord->>Frontend: Submit settlement proposal
    Frontend->>API: POST /deposits/{deposit_id}/settlement
    API->>Service: validate amounts and notes
    Service-->>API: settlement recorded

    alt tenant disputes settlement
        Tenant->>Frontend: Raise dispute
        Frontend->>API: POST /deposits/{deposit_id}/dispute
        API->>Service: mark disputed
        Reviewer->>API: POST /internal/disputes/deposits/{deposit_id}/verdict
        API->>Service: persist verdict and downstream score effects
        Tenant->>Frontend: Appeal
        Frontend->>API: POST /deposits/{deposit_id}/appeal
        API->>Service: reopen case
    else no dispute
        Service-->>API: settlement stands
    end
```

Continuity note: an appeal returns the deposit case to `Review Center > Disputes`, and the earlier verdict is no longer final until a fresh verdict is issued.

## Diagram 8: Review Center Internal Flow

This is the reason the `Review Center` was split into lanes.

```mermaid
flowchart TD
    A["Reviewer opens Review Center"] --> B{"Choose lane"}
    B --> C["Overview"]
    B --> D["Controls"]
    B --> E["Reviews"]
    B --> F["Disputes"]
    B --> G["Runtime"]
    B --> H["Audit"]

    C --> C1["Release readiness"]
    C --> C2["Queue metrics"]
    C --> C3["Latest worker run"]

    D --> D1["Queue score refresh"]
    D --> D2["Run immediate recalculation"]
    D --> D3["Create score batch"]
    D --> D4["Create manual follow-up"]

    E --> E1["Tenancy review decisions"]
    E --> E2["Evidence review decisions"]
    E --> E3["History import decisions"]

    F --> F1["Deposit verdicts"]
    F --> F2["Maintenance verdicts"]
    F --> F3["Payment verdicts"]

    G --> G1["Automation tasks"]
    G --> G2["Notifications"]
    G --> G3["Worker runs"]

    H --> H1["Audit log filtering"]
```

### Why the lane split matters

Before the simplification pass, this page forced operators to scan everything together.

Now the reviewer can:

- act on reviews without accidentally touching runtime controls,
- issue disputes without mixing them into audit work,
- use score/runtime controls separately from case decisions.

## Diagram 9: Trust Sharing And Agency Access

```mermaid
sequenceDiagram
    participant Subject as "Tenant/Landlord"
    participant TrustPage as "My Trust"
    participant API as "consents + trust checks routes"
    participant Agency as "Agency Tools > Screening"

    Subject->>TrustPage: Create trust-report consent
    TrustPage->>API: POST /consents/trust-report
    API-->>TrustPage: share token + access code metadata

    Agency->>Agency: Enter share token and access code
    Agency->>API: POST /organizations/{organization_id}/trust-checks/validate
    API-->>Agency: access valid

    Agency->>API: POST /organizations/{organization_id}/trust-checks/profile
    API-->>Agency: trust profile preview

    opt save agency audit record
        Agency->>API: POST /organizations/{organization_id}/trust-checks
        API-->>Agency: trust check record saved
    end

    Subject->>API: GET /consents/trust-report/access-history
    API-->>TrustPage: access history shown
```

## Diagram 10: Scoring And Background Processing

```mermaid
flowchart TD
    A["User action or reviewer verdict"] --> B["Trust-relevant record changes"]
    B --> C{"Needs score recomputation?"}
    C -->|"immediate"| D["Refresh user score"]
    C -->|"queued"| E["Create score recalculation request"]
    E --> F["Review Center > Controls"]
    F --> G["Runtime / worker processing"]
    G --> H["Central scoring service"]
    H --> I["TrustScore updated"]
    H --> J["TrustScoreHistory appended"]
    I --> K["My Trust shows current score"]
    J --> L["My Trust shows history"]
```

### Important implementation note

The scoring effect is not distributed randomly across route files anymore. The routes trigger workflows, but the trust-score computation is centralized in the scoring service.

Score-role note: `tenant_score` and `landlord_score` are both dimensions of the signed-in user's own trust profile. The landlord-side score is not a rating for a tenant's current landlord; it only becomes active when that same account acts as a landlord or property owner.

## Diagram 11: Demo Scenario Coverage

```mermaid
flowchart LR
    A["Harbor Flat"] --> A1["Healthy tenancy"]
    A --> A2["Normal payment/deposit/maintenance usage"]
    B["Old Town Duplex"] --> B1["Verdict-issued dispute examples"]
    C["Hillside Studio"] --> C1["Pending reviewer queues"]
    D["Agency Showcase Loft"] --> D1["Agency publishing and screening flow"]
```

This is useful when we want to test the app without manually building data first.

## Practical Reading Order

If someone is new to the codebase, the best order is:

1. `docs/WORKSPACE_GUIDE.md`
2. `docs/WORKFLOW_DIAGRAMS.md`
3. `docs/WORKFLOW_MAP.md`
4. `docs/CODEBASE_REFERENCE.md`

That order gives:

- plain-language orientation,
- visual understanding,
- structured workflow reference,
- deep technical traceability.
