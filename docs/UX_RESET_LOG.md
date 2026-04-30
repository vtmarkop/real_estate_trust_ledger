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

### 2026-04-28 - Slice 13: Modern visual memorability pass

- Restore point:
  - committed `32db93f` (`Checkpoint fixed compact localized workspace`) before changing the visual layer
- Problem:
  - the dark design system was coherent but too single-note
  - cards, fields, dropdowns, and buttons did not stand out strongly enough from explanatory copy
  - workflows were still too dependent on text labels instead of memorable color, shape, and component treatment
  - different entities and workflow states needed stronger visual separation without changing backend behavior
- Rebuilt files changed:
  - `apps/web/src/app/AppShell.js`
  - `apps/web/src/components/PageChrome.js`
  - `apps/web/src/components/SegmentedTabs.js`
  - `apps/web/src/styles/index.css`
  - workspace page root components
  - `apps/web/tests/navigation.test.mjs`
  - continuity docs
- What changed:
  - each main workspace page now has a root identity class and accent palette
  - sidebar navigation carries stable lane tones for home, trust, listings, records, operations, agency, internal, and account
  - workflow tabs derive semantic visual classes from tab IDs
  - status badges derive semantic visual classes from labels/tokens such as accepted, pending review, rejected, appealed, and verdict issued
  - cards, fact pills, notes, timelines, fields, dropdowns, file inputs, and buttons now use stronger contrast, accent rails, glow, and focus states
  - page copy and field help are visually quieter than interactive controls
- Verification:
  - `node --check apps\web\src\app\AppShell.js`
  - `node --check apps\web\src\components\PageChrome.js`
  - `node --check apps\web\src\components\SegmentedTabs.js`
  - `node --check` across changed workspace page roots
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `git diff --check`

### 2026-04-29 - Follow-up: Owner-managed landlord listing publication

- Problem:
  - a self-managing landlord could save an owner-managed property, but tenants could not find that home because listing publication only existed in the agency workflow
  - using a fake agency for a landlord-direct home would make the product confusing and weaken the agency boundary
- What changed:
  - `Listing` now supports exactly one manager: either `organization_id` for agency listings or `owner_landlord_user_id` for landlord-direct listings
  - `/landlord/listings` publishes only owner-managed properties owned by the signed-in landlord
  - `/landlord/applications` lets that landlord review applications for their direct listings
  - tenant `Listings` remains one marketplace but now labels `Listed by landlord` versus `Listed by agency`
  - mixed tenant/landlord accounts cannot apply to their own landlord-managed listing from tenant mode
  - `Rental Records > Properties & setup` now has a focused `Publish listing` lane instead of hiding landlord publication inside property editing
  - the local SQLite database was upgraded to Alembic `20260429_0033`
- Verification:
  - `.\.venv\Scripts\python -m py_compile apps\api\app\models\listing.py apps\api\app\models\user.py apps\api\app\schemas\listing.py apps\api\app\services\listings.py apps\api\app\api\routes\listings.py apps\api\alembic\versions\20260429_0033_owner_listed_landlord_listings.py tests\test_listing_application_api.py`
  - `.\.venv\Scripts\python -m unittest tests.test_listing_application_api`
  - `node --check apps\web\src\pages\RecordsPage.js apps\web\src\pages\MarketplacePage.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `.\.venv\Scripts\python -m unittest discover -s tests -p "test*.py"` passed 131 backend tests with the existing SQLite `ResourceWarning` noise
  - `git diff --check`
  - `Push-Location apps\api; ..\..\.venv\Scripts\python -m alembic upgrade head; Pop-Location`
- Next likely slice:
  - visually review all role pages with the four clean accounts and the richer demo seed
  - tune the palette if any workflow becomes too loud, too dull, or hard to scan
  - continue Sprint 21 accessibility, responsive, motion, and design-system documentation work

### 2026-04-28 - Slice 14: Guided menu-flow clarity pass

- Problem:
  - the new visual style made cards and fields stronger, but dense menu structures could still show too many workflows at once
  - the landlord `Rental Records` screenshot showed tenancy creation and saved-property setup as equal side-by-side panels, forcing a novice to infer the correct order
  - `Review Center` labels still sounded too much like an expert console instead of jobs an operator can choose
- Rebuilt files changed:
  - `apps/web/src/pages/RecordsPage.js`
  - `apps/web/src/pages/InternalOperationsPage.js`
  - `apps/web/src/styles/index.css`
  - `apps/web/src/lib/i18n-extra.js`
  - continuity docs
- What changed:
  - `Rental Records` now renders only the selected top-level lane below the command menu
  - tenancy setup, property setup, artifacts, and history/references no longer appear as competing side-by-side workflows
  - shared `guided-workflow` styling gives selected work areas a clearer one-job-at-a-time layout
  - `Review Center` menu labels now read as novice-facing jobs: start here, score controls, account roles, daily reviews, dispute decisions, system runtime, and history/audit
  - Greek copy coverage was extended for the new admin labels and dynamic menu count suffixes
- Verification:
  - `node --check apps\web\src\pages\RecordsPage.js`
  - `node --check apps\web\src\pages\InternalOperationsPage.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `git diff --check`
- Next likely slice:
  - visually review `Rental Records` in the browser with the landlord account path from the screenshot
  - apply the same guided menu-flow rule to any other dense page where multiple workflows still compete for attention
  - keep admin daily review work, account setup, dispute decisions, runtime/system work, and audit/history separated by labels and layout

### 2026-04-28 - Slice 15: Global command-menu visual cleanup

- Problem:
  - the clearer command-menu direction worked, but the visual rule was only applied to `Rental Records` and `Review Center`
  - the screenshot showed a stray cyan accent pill in front of the next section because `.section-switcher::after` reused the same pseudo-element slot as the panel accent rail
  - the strongest hero/detail-panel shadows stacked too heavily when panels sat close together
- Rebuilt files changed:
  - `apps/web/src/styles/index.css`
  - continuity docs
- What changed:
  - all top-level `.section-switcher` menus now use the same larger command-card tab treatment across trust, marketplace, records, rent/issues, agency, review, and account/security pages
  - the conflicting `.section-switcher::after` flourish was removed so panel accent rails no longer turn into floating color pills
  - workspace pages now have deliberate vertical gaps between major cards
  - signed-in workspace ambient background blobs were removed
  - compact hero/detail-panel shadows, nested card shadows, command-tab shadows, accent rail glow, and internal hero/stat spacing were converted from broad glow to tighter elevation so cards still stand out without bleeding into adjacent sections
- Verification:
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `git diff --check`
- Next likely slice:
  - visually review every top-level command menu in the browser with the four clean accounts
  - confirm no remaining page has shadow overlap, stray accents, or decorative elements that compete with the actual workflow
  - continue applying one-job-at-a-time content structure below the menus where dense panels still compete

### 2026-04-28 - Slice 16: Semantic icons and dynamic text hierarchy

- Problem:
  - the stronger color system still relied heavily on text-only recognition in the sidebar and workflow tabs
  - static explanatory labels and dynamic values/statuses were sometimes too similar, making counts, roles, and state harder to scan
- Rebuilt files changed:
  - `apps/web/src/components/VisualIcon.js`
  - `apps/web/src/app/AppShell.js`
  - `apps/web/src/components/SegmentedTabs.js`
  - `apps/web/src/components/PageChrome.js`
  - `apps/web/src/lib/i18n.js`
  - `apps/web/src/styles/index.css`
  - `apps/web/tests/navigation.test.mjs`
  - continuity docs
- What changed:
  - added a shared inline SVG icon component with semantic token resolution
  - shell navigation now shows lane icons for home, trust, listings, rental records, rent/issues, agency tools, review center, and account
  - workflow tabs now derive icons from tab IDs so daily work, history, payments, deposits, maintenance, disputes, review queues, roles, runtime, agency screening, and account-safety lanes are easier to remember
  - submit-form field labels now derive icons from source label text through the shared create-element helper, so city, address, country, email, date, rent, deposit, file, notes, score, status, and role labels are easier to scan
  - shared `text-static`, `text-dynamic`, `data-value`, and `dynamic-token` classes now make labels quieter and values/statuses/counts stronger
  - sidebar role/account rows now separate static labels from dynamic role, access, organization-count, and workspace-mode values
- Verification:
  - `node --check apps\web\src\components\VisualIcon.js`
  - `node --check apps\web\src\lib\i18n.js`
  - `node --check apps\web\src\app\AppShell.js`
  - `node --check apps\web\src\components\SegmentedTabs.js`
  - `node --check apps\web\src\components\PageChrome.js`
  - `npm test`
  - `npm run build`
- Next likely slice:
  - visually review navigation, workflow-tab, and submit-field icons in English and Greek to ensure they help recognition without visual clutter
  - continue tuning static/dynamic hierarchy where page-specific cards still bury values in prose

### 2026-04-28 - Slice 17: Landlord property setup agency-empty guard

- Problem:
  - the minimal four-account reset creates the requested users only and no agency organization
  - the landlord property form still offered `An agency manages this property`, which made a landlord think an agency was required and could lead to the backend `Choose an agency` validation path
- Rebuilt files changed:
  - `apps/web/src/pages/RecordsPage.js`
  - `apps/web/src/lib/i18n-extra.js`
  - `apps/web/tests/navigation.test.mjs`
  - continuity docs
- What changed:
  - owner-managed property creation remains the clear default and does not require agency data
  - agency-managed setup is disabled with explicit help text when the agency directory is empty
  - create/update payloads fall back to owner-managed when no agency directory option exists, preventing accidental agency-required submissions
  - Greek copy was added for the new agency-empty property setup guidance
  - a frontend regression test now pins that landlord property setup does not require an agency when none exist
- Verification:
  - `node --check apps\web\src\pages\RecordsPage.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - `node --check apps\web\tests\navigation.test.mjs`
  - `npm test`
- Next likely slice:
  - visually verify the landlord property setup form with `lila.tsoutsoura@accounts.trustledger.app`
  - verify the agency-managed branch again after an agency organization exists

### 2026-04-28 - Slice 18: Agent agency-workspace bootstrap clarity

- Problem:
  - the minimal four-account reset intentionally creates no agency organization
  - landlord mode could still imply agency workspace setup, while the actual agent account could open Agency Tools but only see that no agency organization was attached
  - this made the roles technically independent but operationally stranded for the clean `Agent` account
- Rebuilt files changed:
  - `apps/web/src/app/session.js`
  - `apps/web/src/pages/WorkspaceHomePage.js`
  - `apps/web/src/pages/AgencyWorkbenchPage.js`
  - `apps/api/app/api/routes/organizations.py`
  - `apps/web/src/lib/i18n-extra.js`
  - `apps/web/tests/navigation.test.mjs`
  - `apps/web/tests/i18n.test.mjs`
  - `tests/test_organization_rbac_api.py`
  - `tests/test_internal_automation_api.py`
  - continuity docs
- What changed:
  - `canCreateAgencyWorkspace` now belongs to accounts with the `agency` workspace role and no agency membership, not landlord accounts
  - `Home` now renders the agency creation panel in Agent mode
  - `Agency Tools` now explains the missing organization/membership state and links back to Home instead of feeling like a dead end
  - backend agency organization creation now requires the `agency` workspace entitlement
  - organization creation still creates the current user as agency owner, so a clean agent can bootstrap the first agency workspace
  - organization test fixtures were updated so agency owners explicitly carry the agency entitlement
  - Greek copy coverage was added for the new agent-bootstrap guidance
- Verification:
  - `node --check apps\web\src\app\session.js`
  - `node --check apps\web\src\pages\WorkspaceHomePage.js`
  - `node --check apps\web\src\pages\AgencyWorkbenchPage.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - `.\.venv\Scripts\python -m py_compile apps\api\app\api\routes\organizations.py`
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_organization_rbac_api`
  - `.\.venv\Scripts\python -m unittest tests.test_internal_automation_api`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `.\.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"`
  - `git diff --check`
- Note:
  - the full backend sweep passes but still emits existing SQLite `ResourceWarning` noise from test database connections
- Next likely slice:
  - visually verify the Theodore agent account can create the first agency workspace from Home and then open Agency Tools
  - visually verify landlord-only accounts do not see agency bootstrap and can continue owner-managed property setup
  - decide whether future agency membership invites should also grant the `agency` workspace entitlement automatically or remain an admin-managed role action

### 2026-04-28 - Slice 19: Agency property/listing assignment continuity

- Problem:
  - landlord agency assignment still asked for a manual agent email even after the landlord selected an agency
  - agency-created properties were saved as loose properties, so agency mode did not reliably show them and listing creation had no usable property to attach
  - listing creation did not enforce that the chosen property belonged to the agency publishing the listing
- Rebuilt files changed:
  - `apps/api/app/schemas/organization.py`
  - `apps/api/app/api/routes/organizations.py`
  - `apps/api/app/api/routes/properties.py`
  - `apps/api/app/api/routes/listings.py`
  - `apps/web/src/pages/RecordsPage.js`
  - `apps/web/src/pages/AgencyWorkbenchPage.js`
  - `apps/web/src/lib/i18n-extra.js`
  - `apps/web/tests/navigation.test.mjs`
  - `apps/web/tests/i18n.test.mjs`
  - `tests/test_organization_rbac_api.py`
  - `tests/test_property_assignments_api.py`
  - `tests/test_listing_application_api.py`
  - continuity docs
- What changed:
  - added an authenticated agency operator directory endpoint for active owner/admin/agent members of an active agency organization
  - landlord property setup now shows a managing-agent dropdown after agency selection and fills the assignment email from that operator choice
  - agency-created properties are posted as `agency_managed` inventory assigned to the selected agency organization and signed-in agent account
  - agency-created inventory remains visible through `/properties/mine` and can be selected immediately by the listing form
  - agency tag updates work for agency-created inventory without requiring the landlord entitlement
  - listing creation now rejects properties that are not assigned to the target agency organization
  - UI and docs now state the product rule: agency-created properties are agency inventory; landlord-owned properties should be created by the landlord and assigned to the agency/operator unless a future owner-link workflow is added
- Verification:
  - `node --check apps\web\src\pages\RecordsPage.js`
  - `node --check apps\web\src\pages\AgencyWorkbenchPage.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - `node --check apps\web\tests\navigation.test.mjs`
  - `node --check apps\web\tests\i18n.test.mjs`
  - `.\.venv\Scripts\python -m py_compile apps\api\app\api\routes\organizations.py apps\api\app\api\routes\listings.py apps\api\app\api\routes\properties.py apps\api\app\schemas\organization.py`
  - `.\.venv\Scripts\python -m unittest tests.test_property_assignments_api`
  - `.\.venv\Scripts\python -m unittest tests.test_organization_rbac_api`
  - `.\.venv\Scripts\python -m unittest tests.test_listing_application_api`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `.\.venv\Scripts\python -m unittest discover -s tests -p "test*.py"`
  - `npm test`
  - `npm run build`
  - `git diff --check`
- Next likely slice:
  - visually verify Theodore can create an agency workspace, create agency inventory, see it in the listing property dropdown, and publish a listing
  - visually verify a landlord selecting that agency sees a managing-agent dropdown and no longer needs to type the agent email manually

### 2026-04-28 - Slice 20: Agency-created landlord owner link

- Problem:
  - an agent can create agency inventory for listing, but sometimes that property already belongs to a real landlord account
  - treating the signed-in agent as the only property creator made the UI and backend too rigid for agency-prepared listings
  - overloading `created_by_user_id` would blur audit history, agency listing assignment, and landlord owner visibility
- Rebuilt files changed:
  - `apps/api/app/models/property.py`
  - `apps/api/app/models/user.py`
  - `apps/api/app/schemas/property.py`
  - `apps/api/app/services/properties.py`
  - `apps/api/app/api/routes/properties.py`
  - `apps/api/app/api/routes/tenancies.py`
  - `apps/api/alembic/versions/20260428_0032_property_landlord_owner_assignment.py`
  - `apps/web/src/pages/AgencyWorkbenchPage.js`
  - `apps/web/src/pages/RecordsPage.js`
  - `apps/web/src/lib/i18n-extra.js`
  - `tests/test_property_assignments_api.py`
  - continuity docs
- What changed:
  - properties now have a separate `owner_landlord_user_id` for the real landlord owner while keeping `created_by_user_id` as the audit creator
  - agency publishing can link an agency-created property to an existing landlord by email during creation
  - agency portfolio cards can save or clear that landlord owner link later for the creating or assigned agent
  - backend validation requires the selected owner account to be active and to have the landlord workspace role
  - linked landlords see the property in landlord mode and can reuse it for tenancy setup
  - agency listing publication still requires agency assignment, so landlord owner linking does not turn loose properties into agency listings
- Verification:
  - `node --check apps\web\src\pages\AgencyWorkbenchPage.js`
  - `node --check apps\web\src\pages\RecordsPage.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - `.\.venv\Scripts\python -m py_compile apps\api\app\models\property.py apps\api\app\models\user.py apps\api\app\schemas\property.py apps\api\app\services\properties.py apps\api\app\api\routes\properties.py apps\api\app\api\routes\tenancies.py apps\api\alembic\versions\20260428_0032_property_landlord_owner_assignment.py`
  - `.\.venv\Scripts\python -m unittest tests.test_property_assignments_api`
  - `.\.venv\Scripts\python -m unittest tests.test_listing_application_api`
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `.\.venv\Scripts\python -m unittest discover -s tests -p "test*.py"`
  - `git diff --check`
  - backend tests pass with the existing SQLite `ResourceWarning` noise
- Next likely slice:
  - visually verify Theodore can create agency inventory, link it to Lila or Froso by landlord email, publish a listing from it, and confirm the linked landlord sees the property in landlord mode
  - confirm the owner-link copy is clear that the landlord account must already exist

### 2026-04-29 - Follow-up: Local migration fix and ownership hardening backlog

- Problem:
  - after the agency-created landlord owner link landed, the local SQLite database was still at Alembic `20260427_0031`
  - opening Lila's landlord `Rental Records` page hit `/properties/mine`, which queried the new `owner_landlord_user_id` column before the local database had that column
  - the UI therefore showed `Records unavailable` / `Internal Server Error`
- What changed:
  - the local database was upgraded non-destructively to Alembic `20260428_0032`
  - `docs/LOCAL_RUN.md` now has a troubleshooting note for this migration-missing failure mode
  - future sprint docs now capture production ownership-hardening work: owner assignment audit logs, owner history, confirmation UX, company/multiple-owner decisions, and deeper permission regression tests
- Verification:
  - confirmed `apps/api/trust_ledger.db` now reports Alembic `20260428_0032`
  - confirmed the `properties` table now includes `owner_landlord_user_id`
  - logged in through the local API as `lila.tsoutsoura@accounts.trustledger.app`
  - confirmed `GET /api/v1/properties/mine` returns successfully

### 2026-04-29 - Follow-up: Agency portfolio card action cleanup

- Problem:
  - `Agency Tools > Portfolio` rendered the landlord-owner save action as a huge translucent pill because the button was placed as a full grid cell beside the field
  - the same card then showed a much smaller `Save tags` action, making the card feel inconsistent and not production-grade
  - single custom tags stretched across the card as large transparent pills instead of compact tags
- What changed:
  - portfolio owner and tag edits now use the same compact action-row structure
  - inline card buttons now keep a consistent compact size instead of inheriting the large page-level button treatment
  - custom tags use a wrapping compact tag row instead of the generic full-width pill grid
  - owner-link helper copy was shortened to a production-style instruction and translated to Greek
- Verification:
  - `node --check apps\web\src\pages\AgencyWorkbenchPage.js`
  - `node --check apps\web\src\lib\i18n-extra.js`
  - `npm test`
  - `npm run build`

### 2026-04-29 - Follow-up: Portfolio tag color treatment

- Problem:
  - custom estate tags were compact after the portfolio action cleanup, but they still did not stand out enough as meaningful searchable metadata
- What changed:
  - portfolio tags now rotate through sky, mint, amber, rose, violet, and cyan treatments
  - each tag gets a compact `#` marker, brighter text, stronger border, and subtle colored elevation
  - tag styling stays separate from button styling so tags look important without looking clickable as actions
- Verification:
  - `node --check apps\web\src\pages\AgencyWorkbenchPage.js`
  - `npm test`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `git diff --check`

### 2026-04-29 - Follow-up: Accepted application to tenancy bridge and button help

- Problem:
  - a landlord or agency could accept a tenant application, but acceptance still felt like the end of the pipeline instead of a visible handoff into the real tenancy record
  - tenants could apply to listings, but the manager-side next step was not obvious enough for a novice user
  - many button actions were visually stronger after the reset, but still relied on the label alone to explain what would happen after click
- What changed:
  - accepted applications now expose a compact `Create tenancy` bridge in both agency `Pipeline` and landlord `Publish listing` lanes
  - the bridge asks for lease dates, creates or links the tenancy, closes the listing, assigns the accepted tenant to the property, and stores the new `tenancy_id` on the application
  - agency-managed listings require the property to have a linked existing landlord owner before the bridge can create the tenancy
  - owner-managed landlord listings use the signed-in listing owner as the landlord side of the tenancy
  - button-like actions now receive hover/focus help bubbles through the shared frontend element wrapper, with targeted help for common application, listing, property, navigation, and sign-in actions
- Verification:
  - `..\..\.venv\Scripts\python -m alembic upgrade head` from `apps/api`
  - `..\..\.venv\Scripts\python -m alembic current` from `apps/api`, confirming `20260429_0034 (head)`
  - `.\.venv\Scripts\python -m py_compile apps\api\app\api\routes\listings.py apps\api\app\models\application.py apps\api\app\models\tenancy.py apps\api\app\schemas\listing.py apps\api\app\services\listings.py apps\api\alembic\versions\20260429_0034_application_tenancy_bridge.py`
  - `.\.venv\Scripts\python -m unittest tests.test_listing_application_api`
  - `npm test -- --runInBand`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `.\.venv\Scripts\python -m unittest discover -s tests -p "test*.py"`
  - `git diff --check`
  - backend tests pass with the existing SQLite `ResourceWarning` noise

### 2026-04-29 - Follow-up: Hover-help scope and placement correction

- Problem:
  - workflow section tabs are implemented as accessible HTML buttons, so the shared hover-help decorator treated large tab cards such as `Sessions` as action buttons
  - the resulting pseudo-tooltip could be clipped or partially hidden between panels, which looked broken instead of helpful
  - the same browser pass also surfaced unrelated React key warnings on the login/register switch copy and Records hero stats
- What changed:
  - hover/focus bubbles now apply to true action buttons and button-styled links, but skip elements with `role="tab"` or the `segmented-tab` class
  - action bubbles now open beside the button instead of above or below it, reducing the chance that dense panels, adjacent cards, or nearby form fields hide or get covered by the help text
  - regression coverage now pins that normal actions still receive help while segmented workflow tabs do not
  - the auth switch prompt text is now keyed through a span and Records hero stats now carry stable keys, reducing list-key warning noise during browser checks
- Verification:
  - `node --check apps\web\src\lib\i18n.js`
  - `node --check apps\web\src\pages\AuthPage.js`
  - `npm test -- --runInBand`
  - `npm run build`
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `git diff --check`

### 2026-04-29 - Follow-up: Workflow QA plan and first live owner-managed flow audit

- Problem:
  - the app now has many implemented workflows, but user-visible continuity still needed a full real-life audit instead of isolated page fixes
  - the owner-managed listing bridge created a tenancy correctly, but the tenant initially could not find that created tenancy in the expected `Tenancy records` lane
  - generic action-help text still made some common actions sound interchangeable
- What changed:
  - added `docs/WORKFLOW_QA_PLAN.md` with the full scenario matrix, audit method, execution order, and fix policy
  - browser-verified the owner-managed path with local clean accounts: Lila created an owner-managed property, published a listing, Vasilis applied as tenant, Lila accepted, Lila created the tenancy, and Vasilis could see the created tenancy
  - added `Existing tenancy records` to `Rental Records > Tenancy records` so created tenancies are visible where users expect them, while artifact uploads remain in `Artifacts`
  - ordered tenancy actions so `Confirm record` appears before `Request review`
  - replaced misleading direct-tenancy hover help and added targeted help for listing publication, application submission, record confirmation, review requests, evidence submission, references, and artifact opening
  - normalized nested child arrays in the shared translation wrapper to reduce React key-warning noise from translated render paths
- Verification:
  - `node --check apps\web\src\lib\i18n.js`
  - `node --check apps\web\src\pages\RecordsPage.js`
  - `npm test -- --runInBand`
  - browser reload confirmed `Existing tenancy records` appears, the QA tenancy is visible, and no fresh React key/hook warnings emit after the fix
- Next likely slice:
  - continue `docs/WORKFLOW_QA_PLAN.md` with agent agency bootstrap, agency listing-to-tenancy, direct tenancy confirmation, and selected-property payment/deposit/maintenance daily work

### 2026-04-30 - Follow-up: Manual QA package

- Problem:
  - `docs/WORKFLOW_QA_PLAN.md` defined the strategy, but the user needed a practical manual checklist to run QA independently without translating engineering audit language into browser tasks
- What changed:
  - added `docs/MANUAL_QA_RUNBOOK.md` with local start commands, seed-mode guidance, credentials, severity labels, and completion rules
  - added `docs/MANUAL_QA_CHECKLIST.md` with task IDs `QA-00` through `QA-28`, covering role boundaries, agent bootstrap, property setup, listing/application/tenancy flows, evidence, references, trust sharing, payments, deposits, maintenance, disputes, score transparency, internal runtime, Greek localization, keyboard, hover, responsive, visual density, and console sweeps
  - added `docs/MANUAL_QA_RESULTS.md` as a pass/fail worksheet with a finding template
  - linked the manual QA package from README, handoff, sprint, roadmap, workflow QA, and codebase reference docs
- Verification:
  - `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold`
  - `git diff --check`
- Next likely slice:
  - execute the manual checklist, then convert failed checklist IDs into `docs/WORKFLOW_GAPS.md` entries and code fixes
