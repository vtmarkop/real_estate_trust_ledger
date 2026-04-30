# Manual QA Checklist

Date: 2026-04-30

Use this checklist with `docs/MANUAL_QA_RUNBOOK.md`. Record results in `docs/MANUAL_QA_RESULTS.md`.

## Round A: Minimal Reset, Role Boundaries, And New Workflow Creation

Run this round after `dev_reset_minimal_users.py`.

### QA-00: Environment Smoke

- Account: any.
- Path: `http://127.0.0.1:5173/app`
- Steps:
  1. Start API and web from the repo root.
  2. Open the app.
  3. Hard refresh once.
  4. Confirm the login page loads without a role dropdown.
- Expected:
  - Login asks only for identity fields.
  - No blank page, crash screen, or console error appears.
  - Language switch is visible.

### QA-01: Tenant/Admin Role Scope

- Account: Vasilis.
- Steps:
  1. Sign in as Vasilis.
  2. Confirm the active role is `Tenant`.
  3. Inspect sidebar menus.
  4. Switch to `Admin`.
  5. Inspect sidebar menus again.
  6. Switch back to `Tenant`.
- Expected:
  - Tenant mode shows tenant trust, listings, rental records, rent/issues, and account.
  - Tenant mode does not show landlord trust, agency tools, or review center.
  - Admin mode shows review center and account.
  - Admin mode does not show personal rental workflows.

### QA-02: Landlord-Only Role Scope

- Account: Lila.
- Steps:
  1. Sign in as Lila.
  2. Inspect sidebar menus.
  3. Try direct navigation to `/app/marketplace`.
  4. Try direct navigation to `/app/agency`.
- Expected:
  - Landlord mode shows home, landlord trust, rental records, rent/issues, and account.
  - Listings and agency tools are not available.
  - Direct route attempts return to an allowed workspace or show an appropriate unavailable state.

### QA-03: Mixed Tenant/Landlord Role Scope

- Account: Froso.
- Steps:
  1. Sign in as Froso.
  2. Switch between `Tenant` and `Landlord`.
  3. Inspect menus and page titles after each switch.
- Expected:
  - Tenant and landlord surfaces stay separate.
  - Role switch returns to Home.
  - The account never sees agency or admin tools.

### QA-04: Agent Agency Bootstrap

- Account: Theodore.
- Steps:
  1. Sign in as Theodore.
  2. Confirm active role is `Agent`.
  3. Open Home.
  4. Create an agency workspace using a QA name, for example `QA Atlas Agency`.
  5. Open Agency Tools.
- Expected:
  - Home explains that the agent needs an agency workspace.
  - Agency creation succeeds.
  - Theodore becomes agency owner.
  - Agency Tools no longer dead-ends.

### QA-05: Landlord Owner-Managed Property Setup

- Account: Lila.
- Steps:
  1. Sign in as Lila.
  2. Open `Rental Records`.
  3. Open `Properties & setup`.
  4. Create a property using `I manage this property myself`.
  5. Use label `QA Owner Home`, city `Athens`, country `GR`, and tags `qa, owner`.
  6. Save property.
- Expected:
  - Owner-managed is available even if no agency exists.
  - Agency-managed is disabled or clearly explained if no agency exists.
  - Saved property appears in the landlord property list.

### QA-06: Landlord Agency-Managed Assignment

- Accounts: Theodore first, then Lila.
- Preconditions: QA-04 created an agency workspace.
- Steps:
  1. Sign in as Lila.
  2. Open `Rental Records > Properties & setup`.
  3. Create or edit a property.
  4. Choose agency-managed.
  5. Select Theodore's agency.
  6. Confirm the managing-agent dropdown appears.
  7. Save the property.
- Expected:
  - Lila does not type Theodore's email manually.
  - Single operator auto-fills or multiple operators are selectable.
  - Saved property shows agency management information.

### QA-07: Agency Inventory Creation And Owner Link

- Account: Theodore.
- Preconditions: QA-04 created an agency workspace.
- Steps:
  1. Open `Agency Tools > Publishing`.
  2. Create agency inventory property `QA Agency Loft`.
  3. Add landlord owner email `lila.tsoutsoura@accounts.trustledger.app`.
  4. Save property.
  5. Open `Portfolio`.
  6. Confirm the property appears with assigned agent and landlord owner.
  7. Sign in as Lila and confirm the property is visible in landlord mode.
- Expected:
  - Agency property remains visible as agency inventory.
  - Owner link uses an existing landlord account.
  - Lila can see the linked property but the agency assignment still belongs to Theodore's agency.

### QA-08: Tenant Discovery And Application

- Accounts: Lila then Vasilis.
- Preconditions: QA-05 created an owner-managed property.
- Steps:
  1. Sign in as Lila.
  2. Open `Rental Records > Properties & setup > Publish listing`.
  3. Publish `QA Owner Home` with rent and deposit.
  4. Sign in as Vasilis in Tenant mode.
  5. Open `Listings`.
  6. Confirm the listing says `Listed by landlord`.
  7. Add application note `QA application from Vasilis`.
  8. Submit application.
  9. Open submitted applications.
- Expected:
  - Listing source and manager are clear.
  - Application submission gives a clear state change.
  - Application appears in the tenant's applications.

### QA-09: Owner-Managed Application To Tenancy

- Accounts: Lila then Vasilis.
- Preconditions: QA-08 submitted an application.
- Steps:
  1. Sign in as Lila.
  2. Open `Rental Records > Properties & setup > Publish listing`.
  3. Locate the QA application.
  4. Accept it.
  5. Use `Create tenancy`.
  6. Enter lease start and end dates.
  7. Create tenancy.
  8. Sign in as Vasilis.
  9. Open `Rental Records > Tenancy records`.
  10. Confirm the tenancy appears under existing records.
- Expected:
  - Acceptance is not the final step.
  - The create-tenancy bridge is visible after acceptance.
  - Listing closes or no longer behaves like an open application target.
  - Both parties can see the tenancy.

### QA-10: Agency Listing To Tenancy

- Accounts: Theodore then Vasilis.
- Preconditions: QA-07 created agency inventory linked to Lila.
- Steps:
  1. Sign in as Theodore.
  2. Open `Agency Tools > Publishing`.
  3. Publish `QA Agency Loft`.
  4. Sign in as Vasilis.
  5. Open `Listings`.
  6. Confirm source says `Listed by agency`.
  7. Submit an application.
  8. Sign in as Theodore.
  9. Open `Agency Tools > Pipeline`.
  10. Accept the application.
  11. Use `Create tenancy`.
- Expected:
  - Agency-created property is listable.
  - Tenant can distinguish agency listing from landlord listing.
  - Pipeline shows accepted-application bridge.
  - If owner link is missing, the UI tells Theodore exactly to link a landlord owner first.
  - After owner link exists, tenancy creation succeeds.

### QA-11: Direct Tenancy Creation And Counterparty Confirmation

- Accounts: Froso then Lila.
- Steps:
  1. Sign in as Froso in Tenant mode.
  2. Open `Rental Records > Tenancy records`.
  3. Create a tenancy with landlord email `lila.tsoutsoura@accounts.trustledger.app`.
  4. Use property label `QA Direct Tenancy`.
  5. Sign in as Lila.
  6. Open `Rental Records > Tenancy records`.
  7. Confirm the record.
  8. Confirm `Request review` appears only after confirmation is no longer the primary action.
- Expected:
  - Active role locks the form to the correct side.
  - Counterparty sees the record.
  - Confirmation changes the verification status visibly.
  - Review request is not competing with confirmation at the same time.

### QA-12: Account Safety

- Accounts: any two.
- Steps:
  1. Sign in.
  2. Open `Account`.
  3. Review Sessions.
  4. Review sign-in activity.
  5. Hover/focus session actions.
- Expected:
  - Sessions and sign-in activity are visually separate.
  - Action hover help does not appear on workflow tabs.
  - No clipped hover bubble appears.

## Round B: Rich Seed, Evidence, Dispute, Score, And Internal Review

Run this round after `dev_seed.py`.

### QA-13: Tenancy Review And Evidence Review

- Accounts: Tenant, then Reviewer.
- Steps:
  1. Sign in as rich Tenant.
  2. Open `Rental Records > Artifacts`.
  3. Upload or inspect an evidence artifact.
  4. Request review where available.
  5. Sign in as Reviewer.
  6. Open `Review Center > Daily reviews`.
  7. Review pending tenancy/evidence cards.
- Expected:
  - Upload path is clear and private artifact access is obvious.
  - Reviewer cards show what is being reviewed and what decision is next.
  - User can later see the result.

### QA-14: History Imports And Reference Requests

- Accounts: Tenant, Landlord, Reviewer.
- Steps:
  1. Sign in as rich Tenant.
  2. Open `Rental Records > History & references`.
  3. Create or inspect a history import.
  4. Create a reference request.
  5. Sign in as the counterparty.
  6. Fulfill the request if one is available.
  7. Sign in as Reviewer and inspect review queue.
- Expected:
  - History imports and references are separate from daily tenancy operations.
  - Incoming and outgoing request states are understandable.
  - Reviewer handoff is visible where relevant.

### QA-15: Trust Sharing And Agency Screening

- Accounts: Tenant and Agency Owner.
- Seed values: `demo-tenant-share-token` / `4829`.
- Steps:
  1. Sign in as rich Tenant.
  2. Open `My Trust > Sharing`.
  3. Confirm share and access-history surfaces are separate.
  4. Sign in as Agency Owner.
  5. Open `Agency Tools > Screening`.
  6. Validate token and code.
  7. Preview profile.
  8. Save trust check.
  9. Open `Screening history`.
  10. Return as Tenant and inspect access log.
- Expected:
  - Validate, preview, save, and history are separate actions.
  - Agency preview shows score contribution context without private daily history.
  - Subject access log records agency access.

### QA-16: Payment Daily Work And History

- Accounts: Tenant and Landlord.
- Demo case: `Harbor Flat` or another active tenancy.
- Steps:
  1. Sign in as Tenant.
  2. Open `Rent & Issues`.
  3. Select one property.
  4. Open `Payments`.
  5. Use `Daily work > Create new` for a new payment.
  6. Use `Existing records` to select one payment.
  7. Attach proof where available.
  8. Switch to `History`.
  9. Sign in as Landlord and decide on the payment.
- Expected:
  - One property stays active.
  - Create-new form is not mixed with past records.
  - Existing payment detail is focused.
  - Proof, notes, and old decisions live in History.

### QA-17: Payment Dispute, Verdict, And Appeal

- Accounts: Tenant/Landlord and Reviewer.
- Demo case: `Old Town Duplex` or `Hillside Studio`.
- Steps:
  1. Open `Rent & Issues > Dispute desk`.
  2. Locate a disputed or appeal-capable payment.
  3. Confirm normal counterparty decision is blocked while reviewer flow is active.
  4. Sign in as Reviewer.
  5. Open `Review Center > Dispute decisions`.
  6. Issue or inspect verdict.
  7. Return as a party and appeal if available.
- Expected:
  - Reviewer handoff is explicit.
  - Appealed state returns to review.
  - Previous verdict is not presented as final after appeal.

### QA-18: Deposit Settlement, Dispute, Verdict, And Appeal

- Accounts: Tenant/Landlord and Reviewer.
- Steps:
  1. Open `Rent & Issues > Deposit`.
  2. Inspect or create settlement proposal.
  3. Use `Dispute desk` for disputed state.
  4. Open reviewer `Dispute decisions`.
  5. Verify verdict/appeal state.
- Expected:
  - Settlement action and dispute history are separate.
  - Reviewer handoff is visible.
  - Appeal reopens the case clearly.

### QA-19: Maintenance Ticket, Resolution, Dispute, Verdict, And Appeal

- Accounts: Tenant/Landlord and Reviewer.
- Steps:
  1. Open `Rent & Issues > Maintenance`.
  2. Use `Report new` for a blank ticket.
  3. Use `Existing issues` for one selected issue.
  4. Acknowledge/resolve as landlord where available.
  5. Dispute as tenant where available.
  6. Review verdict/appeal from `Review Center > Dispute decisions`.
- Expected:
  - Report-new and existing-issue modes are separate.
  - Evidence and resolution history are in History.
  - Reviewer state is clear.

### QA-20: Score Transparency

- Accounts: Tenant, Landlord, Agency Owner, Admin.
- Steps:
  1. Open `My Trust > Overview`.
  2. Confirm base score, role contributions, verification-strength rows, and adjudication deltas.
  3. Open agency trust preview from Screening.
  4. Open internal score controls.
- Expected:
  - The same vocabulary appears in all score surfaces.
  - Score explanation is not buried inside daily payment/deposit/maintenance forms.
  - Tenant-side and landlord-side score meanings are clear.

### QA-21: Admin Automation, Runtime, Audit, And Release Readiness

- Account: Admin.
- Steps:
  1. Open `Admin Center`.
  2. Inspect overview/release readiness.
  3. Inspect score controls.
  4. Inspect system runtime.
  5. Inspect history/audit.
- Expected:
  - Account roles, runtime, scoring controls, release readiness, and audit stay separated.
  - Runtime actions do not look like case decisions and reviewer verdict lanes are not available.
  - Audit history is readable but not mixed into normal review cards.

## Round C: Cross-Cutting Greek, Keyboard, Hover, Responsive, And Visual QA

Run this round against whichever data mode currently has enough records to inspect.

### QA-22: Greek Localization Sweep

- Accounts: all roles.
- Steps:
  1. Switch to Greek.
  2. Visit Home, Trust, Listings, Rental Records, Rent & Issues, Agency Tools, Review Center, and Account where each role allows it.
  3. Inspect forms, tabs, empty states, errors, status badges, score explanations, and hover help.
- Expected:
  - Product copy is translated naturally.
  - User data, filenames, property names, and emails remain unchanged.
  - No important English fallback appears on current product copy.

### QA-23: Keyboard Navigation

- Accounts: at least Tenant, Landlord, Agent, Admin.
- Steps:
  1. Start from Home.
  2. Use Tab and Shift+Tab through sidebar, section menus, fields, dropdowns, and action buttons.
  3. Use Enter or Space on buttons where appropriate.
  4. Check focus states visually.
- Expected:
  - Focus order is sensible.
  - Focus ring is visible.
  - Keyboard does not get trapped.
  - Hover/focus help does not cover the active field.

### QA-24: Hover Help And Action Clarity

- Accounts: all roles.
- Steps:
  1. Hover and keyboard-focus real action buttons.
  2. Hover workflow tabs and command-card section selectors.
  3. Inspect dense pages for clipped bubbles.
- Expected:
  - True actions show useful help.
  - Tabs/selectors do not show action bubbles.
  - Bubbles do not cover fields, cards, or each other.

### QA-25: Visual Separation And Card Density

- Accounts: all roles.
- Steps:
  1. Inspect top-level menus and major panels.
  2. Compare statuses, facts, notes, timelines, fields, and action buttons.
  3. Scroll through dense pages.
- Expected:
  - Different workflow lanes are visually distinct.
  - Static labels are quieter than dynamic values.
  - Cards have breathing room and no shadow bleed.
  - No stray accent pills or decorative color blocks float in front of content.

### QA-26: Responsive Layout

- Accounts: at least Tenant, Landlord, Agent.
- Steps:
  1. Test desktop width.
  2. Narrow the browser to tablet width.
  3. Narrow again to mobile-like width.
  4. Inspect menus, forms, cards, and language dock.
- Expected:
  - No horizontal overflow except intentional browser/devtool constraints.
  - Primary actions remain reachable.
  - Language dock does not hide important buttons.
  - Cards stack without overlapping.

### QA-27: Console And Error Boundary Sweep

- Accounts: all roles.
- Steps:
  1. Keep dev console visible if possible.
  2. Reload each main page.
  3. Trigger one action on each page.
  4. Watch for React hook/key warnings and uncaught errors.
- Expected:
  - No `Rendered more hooks than during the previous render`.
  - No React key warnings.
  - No default React Router error boundary for normal navigation.
  - API errors render as readable product errors.

## Round D: Final Manual Signoff

### QA-28: User-Story Readthrough

- Steps:
  1. Read the completed results table.
  2. For every `Fail` or `Blocked`, confirm there is a reproduction note and severity.
  3. For every `S1` or `S2`, add it to `docs/WORKFLOW_GAPS.md`.
  4. Decide whether remaining `S3` or `S4` issues block the current sprint checkpoint.
- Expected:
  - Manual QA output is actionable without relying on memory or chat history.
