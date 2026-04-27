# UX Reset Log

This file tracks the archive-alignment reset that began after the post-Sprint-20 continuity pass.

The goal is not to weaken the rebuilt backend or role model. The goal is to restore the original interaction clarity:

- object-first navigation
- direct task entry
- dropdown/search targeting before action
- compact detail views
- visible timeline history

## Reset Snapshot

- Start date: 2026-04-24
- Base commit: `a6cfeb4`
- Working branch: `codex/archive-ux-reset`
- Latest pushed checkpoint commit: see the current tip of `origin/codex/archive-ux-reset`
- Backup snapshot: `C:\Users\vmarkopoulos\Documents\dev_projects\MESITIS_app\repo_backups\real_estate_trust_ledger\20260424_134119`

Backup contents:

- `repo.bundle` for repository refs
- `working-tree-vs-head.patch` for tracked working-tree changes
- `staged.patch` for staged diff state
- `git-status.txt` for snapshot status
- `head.txt` for exact base commit
- `untracked/` for untracked files present at reset start

## Comparison Standard

Primary reference files from the archive app:

- `archive/mesitis-mvp-2026-04-09/frontend/src/components/layout/DashboardLayout.jsx`
- `archive/mesitis-mvp-2026-04-09/frontend/src/pages/Payments.jsx`
- `archive/mesitis-mvp-2026-04-09/frontend/src/pages/landlord/Tickets.jsx`
- `archive/mesitis-mvp-2026-04-09/frontend/src/components/TicketTimeline.jsx`

## Working Rules

For each slice of this reset:

1. State the UX problem plainly
2. Name the archive reference pattern
3. Record the rebuilt files changed
4. Record what was intentionally preserved from the rebuild
5. Record verification actually run

## Running Log

### 2026-04-24 - Reset bootstrap

- Backed up the current repo state before major UX changes
- Created the dedicated working branch `codex/archive-ux-reset`
- Confirmed the main drift point: `apps/web/src/pages/OperationsPage.js` is tenancy-first, while the archive `Payments.jsx` and `Tickets.jsx` are object-first with search, dropdown targeting, compact detail focus, and timeline-style history
- Confirmed a secondary drift point: the rebuild already has a reusable `TimelineEntry` component but does not use it in the main tenant/landlord operational workflows
- First implementation target:
  - restore direct property/tenancy targeting in `Rent & Issues`
  - reduce scan-heavy all-tenancy rendering
  - begin reintroducing history timelines in operational detail views

### 2026-04-24 - Slice 1: Rent & Issues property targeting

- Problem:
  - tenants and landlords had to scroll across all tenancy cards to reach the correct property before acting
- Archive reference:
  - `Payments.jsx` and `Tickets.jsx` used search plus direct item/property targeting before action
- Rebuilt files changed:
  - `apps/web/src/pages/OperationsPage.js`
- What stayed preserved from the rebuild:
  - existing backend APIs
  - dispute desk
  - reviewer handoff logic
  - current payment/deposit/maintenance action rules
- What changed:
  - `Rent & Issues` now starts with a property search input and a property dropdown
  - non-dispute work now renders one selected tenancy at a time instead of dumping every tenancy card on the page
  - the selected property now shows a combined operational history timeline built from existing payment, deposit, and maintenance timestamps
- Verification:
  - `node --check apps/web/src/pages/OperationsPage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`
- Next likely slice:
  - restore tighter payment/ticket detail focus inside the selected property workflow
  - continue replacing note-heavy operational cards with more compact timeline/detail patterns where appropriate

### 2026-04-24 - Home/work handoff note

- The active reset branch was pushed to `origin/codex/archive-ux-reset`
- The remote checkpoint should be read from the current branch tip because this reset now has multiple small pushed checkpoints
- The repo handoff state is now recorded in:
  - `docs/HANDOFF.md`
  - `docs/WORKFLOW_GAPS.md`
  - `docs/WORKFLOW_MAP.md`
  - this log file
- One local file remains intentionally outside the checkpoint:
  - `apps/web/package-lock.json`

### 2026-04-27 - Slice 2: Selected payment and issue detail focus

- Problem:
  - after selecting one property, tenants and landlords still saw every payment or maintenance ticket as a full card, so the page remained noisy inside the selected-property flow
- Archive reference:
  - `Payments.jsx` and `Tickets.jsx` used compact row/detail selection, details modals, and local history areas instead of expanding every action surface at once
- Rebuilt files changed:
  - `apps/web/src/pages/OperationsPage.js`
- What stayed preserved from the rebuild:
  - existing payment and maintenance APIs
  - proof upload, counterparty decision, dispute, verdict, and appeal action rules
  - selected-property context from Slice 1
  - the separate dispute desk and reviewer handoff model
- What changed:
  - the selected property `Payments` lane now has a payment dropdown and renders one selected payment detail/action pane
  - the selected property `Maintenance` lane now has an issue dropdown and renders one selected issue detail/action pane
  - newly created payments or issues become the selected detail target after refresh
  - selected payment and issue details now include local timeline histories using the rebuild's `TimelineEntry` component
- Verification:
  - `node --check apps/web/src/pages/OperationsPage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`
- Next likely slice:
  - visually review the tenant and landlord demo flows in the browser
  - reduce any remaining form density if the live interaction still feels heavier than the archive pattern

### 2026-04-27 - Slice 3: Daily work/history separation and score-role clarity

- Problem:
  - selected-property action work and timeline reading were still presented together, which made normal tenant/landlord use feel heavier than the archive pattern
  - tenant users could read `Landlord score` as if it referred to their current landlord, even though the rebuild stores it as the signed-in user's own landlord/property-owner score dimension
- Archive reference:
  - `Payments.jsx`, `Tickets.jsx`, and `TicketTimeline.jsx` kept direct action flows and history/timeline reading as distinct mental modes
- Rebuilt files changed:
  - `apps/web/src/pages/OperationsPage.js`
  - `apps/web/src/pages/TrustProfilePage.js`
  - `apps/web/src/pages/WorkspaceHomePage.js`
- What stayed preserved from the rebuild:
  - existing payment, deposit, maintenance, dispute, and appeal APIs
  - selected-property context and compact record dropdowns
  - deterministic tenant-side and landlord-side scoring model
  - reviewer handoff architecture
- What changed:
  - selected-property `Rent & Issues` now has `Daily work` and `History` modes
  - `Daily work` keeps payment/deposit/maintenance actions and compact record dropdowns
  - `History` contains the read-only selected-property timeline for the active operational lane
  - `Home` and `My Trust` now explain that landlord-side score belongs to the signed-in user's own landlord/property-owner persona, not to the tenant's current landlord
- Verification:
  - `node --check apps/web/src/pages/OperationsPage.js`
  - `node --check apps/web/src/pages/TrustProfilePage.js`
  - `node --check apps/web/src/pages/WorkspaceHomePage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`
- Next likely slice:
  - visually review `Daily work` and `History` with seeded tenant and landlord accounts
  - continue the broader workflow continuity audit, especially agency-facing score language and remaining dense action forms

### 2026-04-27 - Slice 4: Create versus existing record separation

- Problem:
  - `Daily work > Payments` still showed the blank create-payment form and an existing saved payment detail in one continuous card
  - the same pattern existed in maintenance, where a blank report form and existing issue actions lived together
  - this made old records look like they belonged under creation, which violated the reset goal of strong separation of concerns
- Archive reference:
  - the original interaction model kept direct creation, selected saved records, and timelines as separate modes instead of stacking all of them together
- Rebuilt files changed:
  - `apps/web/src/pages/OperationsPage.js`
- What stayed preserved from the rebuild:
  - selected-property context
  - `Daily work` versus `History`
  - compact payment and issue dropdowns
  - all existing payment and maintenance action rules
- What changed:
  - `Payments` now has `Create new` and `Existing records` modes
  - `Create new` shows only the blank payment form
  - `Existing records` shows the payment dropdown and the selected saved payment actions
  - `Maintenance` now has `Report new` and `Existing issues` modes
  - `Report new` shows only the blank issue form
  - `Existing issues` shows the issue dropdown and the selected saved issue actions
- Verification:
  - `node --check apps/web/src/pages/OperationsPage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`
- Next likely slice:
  - visually review with the seeded `Hillside Studio` and `Harbor Flat` examples to confirm creation, existing-record actions, and history now feel like separate modes

### 2026-04-27 - Slice 5: Role-wide history lane separation

- Problem:
  - even after `Daily work` and create-vs-existing separation, operation action cards still showed read-only proof summaries, old notes, dispute notes, verdict summaries, and evidence links inline
  - agency screening also mixed the trust-check action form with saved trust-check history
- Archive reference:
  - the original pattern treated history/timeline as a separate reading mode rather than placing old context under action controls
- Rebuilt files changed:
  - `apps/web/src/pages/OperationsPage.js`
  - `apps/web/src/pages/AgencyWorkbenchPage.js`
- What stayed preserved from the rebuild:
  - all existing payment, deposit, maintenance, dispute, appeal, trust-check, and artifact APIs
  - active action controls and current status badges
  - dedicated `My Trust`, `Account`, `Review Center > Audit`, and runtime history lanes that already existed
- What changed:
  - operation action cards now show current state and next actions only
  - proof files, old notes, dispute notes, verdict summaries, appeal notes, reported evidence, and resolution evidence are shown from the selected property's `History` view
  - `Dispute desk` points users to `History` for old notes/evidence instead of repeating case history inline
  - agency `Screening` is now action-only, and saved trust checks moved to `Screening history`
- Verification:
  - `node --check apps/web/src/pages/OperationsPage.js`
  - `node --check apps/web/src/pages/AgencyWorkbenchPage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`
- Next likely slice:
  - visually review tenant, landlord, agency, and reviewer demo accounts for any smaller inline read-only history blocks that should move into explicit history/log lanes

### 2026-04-27 - Slice 6: Tenancy role and counterparty clarity

- Problem:
  - tenancy metadata showed `Parties: Tenant and Landlord`, which looked like a tab but did not explain what the current user should do with that information
  - in demo data, the generic names made the pill especially pointless
- Rebuilt files changed:
  - `apps/web/src/pages/RecordsPage.js`
  - `apps/web/src/pages/OperationsPage.js`
- What changed:
  - tenancy metadata now shows `Your role`
  - tenancy metadata now shows the relevant `Tenant` or `Landlord` counterparty name
  - the `Rent & Issues` property dropdown now describes the current user's relationship to the counterparty instead of listing both parties as a generic pair
  - the vague `Parties` pill was removed from `Rental Records`, the `Rent & Issues` property picker, and the selected-property header
- Verification:
  - `node --check apps/web/src/pages/RecordsPage.js`
  - `node --check apps/web/src/pages/OperationsPage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`
