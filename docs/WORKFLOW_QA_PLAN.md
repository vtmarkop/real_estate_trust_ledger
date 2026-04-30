# Workflow QA Master Plan

Date: 2026-04-29

This plan converts the current Trust Ledger workflow map into a repeatable real-life audit. It exists because backend coverage alone is not enough: every major journey must be checked as a user would experience it, with mouse navigation, keyboard entry, visible feedback, role boundaries, and clear next steps.

## Manual QA Pack

Use these files when the goal is hands-on QA rather than development:

- `docs/MANUAL_QA_RUNBOOK.md`: setup, seed modes, credentials, severity labels, and completion rules.
- `docs/MANUAL_QA_CHECKLIST.md`: exact task IDs and manual steps.
- `docs/MANUAL_QA_RESULTS.md`: pass/fail worksheet and finding template.

When reporting a manual QA issue, include the checklist ID, for example `QA-16 failed after proof upload`.

## Audit Goal

Classify every product workflow as:

- `complete_and_obvious`
- `complete_but_hard_to_understand`
- `partially_implemented`
- `missing`

Each scenario must answer:

- Can the right role find the workflow without knowing implementation details?
- Can the role complete the normal real-life task with visible confirmation?
- Does the next handoff appear in the right workspace?
- Does the wrong role stay out of the workflow?
- Do daily actions stay separate from history/timeline reading?
- Do visible labels, fields, buttons, hover help, and error messages reduce confusion?
- Does the backend state match what the UI claims happened?

## Test Method

Use three layers together:

1. Static continuity scan:
   - read `WORKFLOW_MAP.md`, `WORKFLOW_DIAGRAMS.md`, and page/API surfaces
   - compare expected role sequence with actual frontend lanes and API routes
   - record suspected gaps in `WORKFLOW_GAPS.md`
2. Backend regression check:
   - run targeted Python tests for the workflow being touched
   - add or extend tests when a backend rule changes
3. Browser human-flow check:
   - use the in-app browser
   - click with the mouse
   - tab and type through forms with the keyboard
   - enter harmless dummy data where needed
   - check console errors and React key/hook warnings
   - verify visible success, next action, and role handoff

The browser check should prefer real local accounts from the minimal reset unless a richer seeded state is required:

- `vasilis.markopoulos@accounts.trustledger.app` / `VasilisTenantAdmin123!`
- `lila.tsoutsoura@accounts.trustledger.app` / `LilaLandlord123!`
- `theodore.tsoutsouras@accounts.trustledger.app` / `TheodoreAgent123!`
- `froso.evangeliadou@accounts.trustledger.app` / `FrosoTenantLandlord123!`

Use the rich seed only when a scenario needs existing disputes, evidence, score history, or agency screening history.

## Scenario Matrix

### 1. Sign-In, Role Scope, And Account Safety

- Real-life story: a user signs in and only sees work for the selected assigned role.
- Roles: tenant, landlord, agent, admin, mixed-role user.
- UI path: Login -> Home -> sidebar role switch -> Account.
- Expected result: login has no role dropdown; mixed-role users switch in the shell; tenant does not see landlord/agency/admin work; landlord does not see tenant listings; agent sees agency setup/tools only; admin sees review center only.
- Backend truth: `/auth/me`, `/organizations/mine`, role-gated routes.
- Priority: critical.

### 2. Agent Agency Bootstrap

- Real-life story: Theodore has an agent role but no agency organization, so he creates the first agency workspace.
- Roles: agent.
- UI path: Home -> Create agency workspace -> Agency Tools.
- Expected result: Home explains setup; Agency Tools does not dead-end; after creation the agent becomes owner and can open agency tools.
- Backend truth: `POST /organizations`, `/organizations/mine`.
- Priority: critical.

### 3. Landlord Owner-Managed Property Setup

- Real-life story: Lila saves a property without any agency organization existing.
- Roles: landlord.
- UI path: Rental Records -> Properties & setup -> Create property.
- Expected result: owner-managed is the obvious available path; agency-managed is disabled or explained when no agency exists; save succeeds.
- Backend truth: `POST /properties`, `/properties/mine`.
- Priority: critical.

### 4. Landlord Agency-Managed Assignment

- Real-life story: after an agency exists, a landlord chooses that agency and a real operator instead of typing an agent email.
- Roles: landlord, agent.
- UI path: Agent creates agency -> Landlord creates/edits property -> choose agency -> choose operator.
- Expected result: operator dropdown appears; single operator auto-fills; multiple operators are selectable; property save makes agency assignment visible.
- Backend truth: agency directory operators and property assignment fields.
- Priority: critical.

### 5. Agency Inventory Creation And Owner Linking

- Real-life story: an agent creates agency inventory, optionally links it to an existing landlord owner, then sees it in the agency portfolio.
- Roles: agent, landlord.
- UI path: Agency Tools -> Publishing -> create property -> Portfolio -> landlord owner email.
- Expected result: property remains visible as agency inventory; owner link uses an existing landlord email; linked landlord can see it in landlord mode.
- Backend truth: `owner_landlord_user_id`, agency assignment fields.
- Priority: critical.

### 6. Tenant Discovery And Application

- Real-life story: a tenant browses open homes and applies to one.
- Roles: tenant.
- UI path: Listings -> Browse listings -> submit application -> My applications.
- Expected result: listing source is clear (`Listed by landlord` or `Listed by agency`); application submit gives confirmation; own landlord listing is blocked for mixed tenant/landlord accounts.
- Backend truth: `/listings/open`, `/listings/{id}/applications`, `/applications/mine`.
- Priority: critical.

### 7. Owner-Managed Listing To Tenancy

- Real-life story: landlord publishes a self-managed home, tenant applies, landlord accepts, landlord creates the tenancy.
- Roles: landlord, tenant.
- UI path: Rental Records -> Properties & setup -> Publish listing; tenant Listings; landlord application review; Create tenancy.
- Expected result: acceptance is not a dead end; bridge creates tenancy; listing closes; both parties see the tenancy.
- Backend truth: `/landlord/listings`, `/landlord/applications`, `/landlord/applications/{id}/tenancy`, `/tenancies/mine`.
- Priority: critical.

### 8. Agency Listing To Tenancy

- Real-life story: agency publishes inventory, tenant applies, agency accepts, agency creates the tenancy only after owner link exists.
- Roles: agent, tenant, landlord.
- UI path: Agency Tools -> Publishing -> Pipeline -> Create tenancy.
- Expected result: if owner link is missing, UI tells the agent exactly what to fix; after owner link, bridge creates tenancy and closes listing.
- Backend truth: `/organizations/{org_id}/listings`, `/organizations/{org_id}/applications`, `/organizations/{org_id}/applications/{id}/tenancy`.
- Priority: critical.

### 9. Direct Tenancy Creation And Counterparty Confirmation

- Real-life story: a landlord or tenant creates a tenancy by counterparty email, and the other side confirms it.
- Roles: tenant, landlord.
- UI path: Rental Records -> Tenancy records -> create; counterparty signs in -> confirm.
- Expected result: role is locked to active workspace; counterparty email is clear; confirmation next step is visible; status changes are obvious.
- Backend truth: `/tenancies`, `/tenancies/mine`, `/tenancies/{id}/confirm`.
- Priority: high.

### 10. Tenancy Review And Evidence Review

- Real-life story: a user requests verification and uploads evidence; reviewer accepts or rejects it.
- Roles: tenant, landlord, admin/reviewer.
- UI path: Rental Records -> Artifacts/evidence; Review Center -> Reviews.
- Expected result: upload path is obvious; private artifact access works; reviewer queue has clear decision cards; user sees the result later.
- Backend truth: evidence routes, internal review queue routes, trust events.
- Priority: high.

### 11. History Imports And Reference Requests

- Real-life story: a user imports old rental history and asks a counterparty for a reference.
- Roles: tenant, landlord, counterparty, reviewer.
- UI path: Rental Records -> History & references.
- Expected result: creation, submit, incoming request, fulfillment, and review handoff are each distinguishable from daily tenancy operations.
- Backend truth: history import and reference request routes.
- Priority: high.

### 12. Trust Sharing And Agency Screening

- Real-life story: a tenant creates a share token/access code and an agency previews or saves a trust check.
- Roles: tenant/landlord subject, agent.
- UI path: My Trust -> Sharing; Agency Tools -> Screening; Screening history; My Trust -> Access log.
- Expected result: token/code lifecycle is clear; validation, preview, save, and access history are separate actions; revoked consent blocks access.
- Backend truth: consent and trust-check routes plus audit log.
- Priority: high.

### 13. Payment Daily Work And History

- Real-life story: tenant records rent, attaches proof, landlord accepts or rejects, history remains separate.
- Roles: tenant, landlord.
- UI path: Rent & Issues -> choose property -> Daily work -> Payments -> Create new / Existing records -> History.
- Expected result: user acts on one property; one payment detail is open at a time; proof/notes/history do not sit under blank forms.
- Backend truth: payment routes and selected tenancy access.
- Priority: critical.

### 14. Payment Dispute, Verdict, And Appeal

- Real-life story: a rejected payment becomes a dispute, reviewer decides, party appeals, reviewer re-decides.
- Roles: tenant, landlord, admin/reviewer.
- UI path: Rent & Issues -> Dispute desk; Review Center -> Dispute decisions.
- Expected result: once disputed or appealed, normal counterparty decision is blocked; reviewer handoff is visible; previous verdict is not presented as final after appeal.
- Backend truth: payment dispute/verdict/appeal routes and scoring recalculation.
- Priority: critical.

### 15. Deposit Settlement, Dispute, Verdict, And Appeal

- Real-life story: landlord proposes deposit return/withholding; tenant disputes; reviewer decides; appeal reopens.
- Roles: tenant, landlord, admin/reviewer.
- UI path: Rent & Issues -> Deposit; Dispute desk; Review Center -> Dispute decisions.
- Expected result: settlement action and dispute timeline are separate; appealed state clearly returns to reviewer queue.
- Backend truth: deposit routes and internal dispute routes.
- Priority: high.

### 16. Maintenance Ticket, Resolution, Dispute, Verdict, And Appeal

- Real-life story: tenant reports an issue, landlord acknowledges/resolves, tenant disputes if needed, reviewer decides.
- Roles: tenant, landlord, admin/reviewer.
- UI path: Rent & Issues -> Maintenance -> Report new / Existing issues -> History.
- Expected result: report and existing issue actions are distinct; evidence/resolution history stays in History; reviewer state is clear.
- Backend truth: maintenance routes and internal dispute routes.
- Priority: high.

### 17. Score Transparency

- Real-life story: a user wants to understand exactly why their score changed.
- Roles: tenant, landlord, agent, admin.
- UI path: My Trust -> Overview/History; Agency Tools -> Screening preview; Review Center -> Score controls.
- Expected result: base score, role-specific contributions, verification strength, and adjudication deltas use the same vocabulary everywhere.
- Backend truth: trust score routes and scoring service.
- Priority: high.

### 18. Automation, Runtime, Audit, And Release Readiness

- Real-life story: an internal operator checks platform health and queue work without touching case decisions.
- Roles: admin/reviewer.
- UI path: Review Center -> Start here / Score controls / System runtime / History & audit.
- Expected result: daily reviews, disputes, account roles, runtime work, and audit history remain visually and conceptually separate.
- Backend truth: internal operations, automation, worker, notifications, audit, release readiness routes.
- Priority: medium.

### 19. Localization And Visual Accessibility

- Real-life story: the same workflows are understandable in Greek and by keyboard.
- Roles: all.
- UI path: switch EN/EL; tab through menus/forms; hover/focus action buttons.
- Expected result: no English fallback on product copy; no React key/hook warnings; keyboard order is sensible; hover help does not obscure fields; buttons and fields stay visually distinct.
- Backend truth: not applicable except error messages.
- Priority: critical for release polish.

## Execution Order

Run the audit in this order to avoid creating confusing data dependencies:

1. role scope and sign-in
2. agent agency bootstrap
3. landlord property setup
4. agency inventory and landlord owner linking
5. landlord direct listing -> tenant apply -> landlord accept -> create tenancy
6. agency listing -> tenant apply -> agency accept -> create tenancy
7. direct tenancy creation and counterparty confirmation
8. daily operations on the created tenancy: payment, deposit, maintenance
9. dispute, reviewer verdict, and appeal loops
10. evidence, imports, references, trust sharing, score, internal runtime
11. Greek, keyboard, hover, responsive, and visual clutter review across all pages

## Fix Policy

When a scenario fails:

- If the backend rule is wrong, fix the route/service/model and add a backend regression.
- If the backend is right but the UI hides the next action, fix the existing page lane and update docs.
- If a page mixes daily action with history, split the existing lane instead of adding a duplicate page.
- If the issue is wording or visual hierarchy, update shared components/styles first when possible.
- If the problem is not safe to finish immediately, record it in `WORKFLOW_GAPS.md` with a concrete next fix.

## Current Audit Status

Initial static scan completed against the current docs, frontend pages, API routes, and existing tests.

First browser QA slice completed for Scenario 7, owner-managed listing to tenancy:

- Lila created an owner-managed property with dummy QA data.
- Lila published the property as a landlord-managed listing.
- Vasilis applied as a tenant from `Listings`.
- Lila accepted the application from the landlord publish-listing lane.
- Lila created the tenancy from the accepted-application bridge.
- Vasilis saw the created tenancy under `Rental Records > Tenancy records`.
- The pass found and fixed a frontend continuity bug where the tenancy existed but only appeared in `Artifacts`; existing tenancies now appear in the tenancy lane.
- Fresh browser reload after the fix showed no new React key/hook warnings.

The manual QA pack is now complete enough for a non-coding pass across all scenarios.

A Codex pre-QA browser pass on 2026-04-30 covered QA-00 through QA-27 across the minimal reset and rich seed, with results recorded in `docs/MANUAL_QA_RESULTS.md`.

Issues fixed during that pass:

- direct tenancy and accepted-application tenancy bridge date fields now use explicit `YYYY-MM-DD` text inputs instead of fragile native date controls
- agency dashboard closed-listing copy no longer renders `undefined`
- agency application cards separate the applicant note from manager/status notes
- closed landlord listings no longer claim they are visible in tenant Listings
- landlord direct access to tenant Listings now redirects to the allowed landlord workspace
- `Rental Records > Artifacts` now starts with one selected tenancy menu and renders only that tenancy's upload/library/reference controls
- Greek copy no longer exposes `browser` in visible help text, and dynamic home titles use clearer Greek grammar

Known manual follow-up:

- repeat QA-26 on real tablet/mobile widths because the Codex in-app browser API does not expose viewport resizing
- repeat a human keyboard traversal for QA-23 even though the CSS focus-visible contract and click/type/submit flows passed
