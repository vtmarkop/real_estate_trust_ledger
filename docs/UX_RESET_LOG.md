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

### 2026-04-27 - Slice 7: Active workspace role scoping

- Problem:
  - mixed-role accounts could still see too many unrelated menus and records at once
  - tenant, landlord, agency, and reviewer work needed stronger separation without creating duplicate accounts or weakening backend permissions
- Rebuilt files changed:
  - `apps/web/src/app/session.js`
  - `apps/web/src/app/AppShell.js`
  - `apps/web/src/app/router.js`
  - `apps/web/src/pages/AuthPage.js`
  - `apps/web/src/pages/WorkspaceHomePage.js`
  - `apps/web/src/pages/TrustProfilePage.js`
  - `apps/web/src/pages/RecordsPage.js`
  - `apps/web/src/pages/OperationsPage.js`
  - `apps/web/src/styles/index.css`
  - `apps/web/tests/navigation.test.mjs`
  - `tests/test_web_scaffold.py`
- What changed:
  - the shell persists and switches the active workspace role among roles available to the account
  - this slice originally experimented with requesting a workspace role at sign-in, but that pre-login selector was later removed in Slice 9
  - navigation and direct route guards now honor the active role
  - tenant mode hides landlord/agency/reviewer lanes and shows tenant-side records, listings, scores, and operations
  - landlord mode hides listings and tenant-only views, shows landlord-side records, property setup, scores, and operations
  - agent mode shows agency tools without personal rental lanes
  - admin/internal mode shows review center without personal rental lanes
  - `Rental Records`, `Rent & Issues`, `Home`, and `My Trust` now scope visible frontend data to the active role
- Guardrail:
  - this is UI/workspace scoping, not authorization; backend RBAC, organization membership, and record-participation checks remain authoritative
- Verification:
  - `node --check` on all changed frontend files
  - `npm test`
  - `npm run build`

### 2026-04-27 - Slice 7 follow-up: Trust profile session binding

- Problem:
  - `My Trust` crashed at runtime with `session is not defined` after active workspace-role scoping because `TrustProfilePage` read the active role without binding the session hook
- Rebuilt files changed:
  - `apps/web/src/pages/TrustProfilePage.js`
  - `tests/test_web_scaffold.py`
- What changed:
  - `TrustProfilePage` now imports and calls `useSession()` before using `session.activeWorkspaceRole`
  - the web scaffold test now guards that the trust page keeps the session hook binding
- Verification:
  - `node --check apps/web/src/pages/TrustProfilePage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`
  - `git diff --check`

### 2026-04-27 - Slice 8: Explicit account role entitlements and clean reset

- Problem:
  - tenant/admin and agent accounts could not be represented cleanly by the old `system_role` plus organization-membership model
  - frontend role availability still risked inferring personas too broadly, which made tenant-only review feel polluted by unrelated landlord, agency, or admin surfaces
  - local review needed a clean four-user state with no demo properties, tenancies, organizations, or history data
- Rebuilt files changed:
  - `packages/domain/trustledger_domain/access.py`
  - `apps/api/app/models/user.py`
  - `apps/api/app/api/deps.py`
  - `apps/api/app/api/routes/internal.py`
  - tenant, landlord, agency, property, listing, payment, deposit, and maintenance route guards
  - `apps/web/src/app/session.js`
  - `apps/web/src/pages/InternalOperationsPage.js`
  - `apps/api/dev_reset_minimal_users.py`
  - role-related tests and continuity docs
- What changed:
  - `User.workspace_roles` now stores explicit account entitlements for tenant, landlord, agent/agency, and admin/internal visibility
  - `/auth/me` returns those entitlements, and the frontend only offers assigned roles at sign-in and in the shell
  - `Review Center > Roles` lets an admin add or remove account workspace-role entitlements while keeping at least one role
  - tenant, landlord, and agency backend routes now check the matching workspace entitlement in addition to record participation or organization membership
  - `dev_reset_minimal_users.py` wipes local data and creates only the requested four accounts
- Verification:
  - `.\.venv\Scripts\python -m unittest discover tests`
  - `node --check apps\web\src\pages\InternalOperationsPage.js`
  - `node --test apps\web\tests\navigation.test.mjs`
- Next likely slice:
  - visually review the clean four-account role matrix in the browser
  - continue workflow continuity audit from the role-specific surfaces that still feel too dense or too implicit

### 2026-04-27 - Slice 9: Remove pre-login role dropdown

- Problem:
  - the login form asked users to pick a workspace role before authentication
  - this was counter-intuitive because the app cannot know the account's true entitlements until after `/auth/me`
  - the sidebar already provides a better role switch for mixed-role accounts
- Rebuilt files changed:
  - `apps/web/src/pages/AuthPage.js`
  - `tests/test_web_scaffold.py`
  - continuity and operator docs
- What changed:
  - login and registration now stay focused on identity only
  - the app opens the last valid workspace role saved in the browser, or the first assigned role if the saved one is not available to the signed-in account
  - mixed-role users switch roles from the signed-in sidebar
  - docs now describe role switching as a post-login shell behavior and keep the current minimal-reset credentials visible
- Verification:
  - `node --check apps\web\src\pages\AuthPage.js`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `node --test apps\web\tests\navigation.test.mjs`
  - `npm test`
  - `npm run build`

### 2026-04-27 - Slice 10: Score contribution transparency

- Problem:
  - users could see tenant-side and landlord-side scores but still had to infer how each score was built
  - agency previews and internal scoring controls did not share the same user-facing vocabulary for base score, fixed inputs, verification strength, and adjudication deltas
  - score explanation needed to stay in trust/preview/control lanes instead of being mixed into daily payment or ticket action forms
- Rebuilt files changed:
  - `apps/api/app/schemas/trust_check.py`
  - `apps/api/app/services/trust_profiles.py`
  - `apps/web/src/lib/scoreTransparency.js`
  - `apps/web/src/components/ScoreTransparency.js`
  - `apps/web/src/pages/TrustProfilePage.js`
  - `apps/web/src/pages/AgencyWorkbenchPage.js`
  - `apps/web/src/pages/InternalOperationsPage.js`
  - score-transparency tests and continuity docs
- What changed:
  - agency trust profile previews now include aggregate score inputs
  - `My Trust` shows the active tenant or landlord role's point-by-point score contribution breakdown
  - verification-strength contribution rows are separate from tenant/landlord score rows
  - agency trust previews show aggregate tenant score drivers with a privacy boundary
  - internal scoring controls show the formula reference and exact immediate recalculation breakdowns
- Verification:
  - `.\.venv\Scripts\python -m unittest tests.test_trust_scores_api tests.test_consent_trust_checks_api tests.test_internal_scoring_api`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `npm test`
  - `npm run build`

### 2026-04-28 - Slice 11: Greek localization quality pass

- Problem:
  - the Greek UI had become uneven after the UX reset and score-transparency work because newer visible strings were not consistently covered by the Sprint 18 dictionary
  - one later patch block also overrode several dispute/review Greek strings back into English
  - dynamic phrases such as role-only shell status, score contribution breakdown titles, selected-property history text, tenancy status labels, and application status confirmations needed whole-phrase translation rather than fragment-by-fragment fallback
- Rebuilt files changed:
  - `apps/web/src/lib/i18n.js`
  - `apps/web/src/lib/i18n-extra.js`
  - `apps/web/tests/i18n.test.mjs`
  - continuity docs
- What stayed preserved from the rebuild:
  - the existing `LanguageProvider`, `translateText`, and `e(...)` wrapper architecture
  - English source copy as the canonical UI source language
  - role/workflow behavior, backend APIs, and score logic
- What changed:
  - the Greek patch dictionary now covers the likely visible app copy across public, shell, tenant, landlord, agency, internal, score, history, and operations reset surfaces
  - the final Greek override block fixes the dispute/review strings that had been reintroduced in English
  - dynamic translation rules now cover role-only shell status, loaded/showing messages, account role updates, score contribution breakdown labels, contribution-point rules, tenancy-status labels, selected-property history phrases, and listing-application status confirmations
  - localization tests now pin newer UX-reset and score-transparency copy in addition to the older Sprint 18 coverage
- Verification:
  - `node --check apps\web\src\lib\i18n.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - focused static scan of likely visible frontend strings returned zero likely untranslated visible strings after filtering code-only tokens and intentional data placeholders
  - `npm test`
- Next likely slice:
  - visually review the Greek UI with both the minimal account-only reset and the rich demo seed
  - continue Sprint 21 accessibility, responsive, motion, and design-system documentation work

### 2026-04-28 - Slice 12: Fixed compact workspace density

- Problem:
  - the `Comfort` / `Compact` density switch did not create a meaningful enough layout difference
  - the control felt like another choice for users while mostly acting like a weak zoom/spacing toggle
  - the compact view is currently the clearer view for data-heavy tenant, landlord, agency, and internal workspaces
- Rebuilt files changed:
  - `apps/web/src/app/AppShell.js`
  - `apps/web/src/styles/index.css`
  - `apps/web/src/lib/i18n.js`
  - `apps/web/src/lib/i18n-extra.js`
  - `apps/web/tests/navigation.test.mjs`
  - continuity docs
- What changed:
  - signed-in workspaces now always set the shell density to `compact`
  - the topbar density switch was removed
  - unused Greek dictionary entries for the removed density labels were removed
  - stale local density preferences are ignored by the shell contract
  - docs now state that future density options should only return if they create an obvious workflow/layout difference
- Verification:
  - `node --check apps\web\src\app\AppShell.js`
  - `node --check apps\web\src\lib\i18n.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - stale density switch scan found no old shell helpers or CSS controls
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
