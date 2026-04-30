# Live Handoff

This file is the current resume point for any new device, new Codex thread, or interrupted work session.

## Current Checkpoint

- Program state: completed through Sprint 20
- Latest non-sprint checkpoint: archive-alignment UX reset in progress, with selected-property operations, compact payment/issue targeting, daily/history separation, create-vs-existing action separation, role-wide history lane separation, backend-backed explicit account workspace-role entitlements, sidebar-only role switching after login, account role management, a local account-only reset path, tenancy role/counterparty clarity, score-role clarity, fixed compact workspace density, the first Sprint 21 score-contribution transparency slice completed, a Greek localization quality pass completed across the visible reset workspace copy, the first modern visual memorability slice implemented, the first guided menu-flow clarity slice implemented, the global top-level section-switcher visual cleanup completed, the semantic icon/static-vs-dynamic text hierarchy slice completed, the agent agency-bootstrap clarity fix completed, the agency property/listing assignment continuity fix completed, the agency-created landlord-owner link implemented, direct owner-managed landlord listing publication implemented, the accepted-application-to-tenancy bridge implemented, action button hover-help bubbles added without applying them to workflow tab selectors, a complete workflow QA master-plan/manual QA package, a 2026-04-30 Codex pre-QA pass across QA-00 through QA-27, and strict admin-versus-reviewer internal role separation
- Next planned sprint: Sprint 21
- Recommended immediate focus: the user should run the manual QA package from `docs/MANUAL_QA_RUNBOOK.md`, `docs/MANUAL_QA_CHECKLIST.md`, and `docs/MANUAL_QA_RESULTS.md`. The Codex pre-QA pass already covered QA-00 through QA-27 on desktop browser with minimal and rich seed data; the intentional remaining manual checks are QA-26 real tablet/mobile widths and QA-23 human keyboard-only traversal. Include a quick role sanity check that reviewer accounts see only review/verdict work and admin accounts see only platform controls/account-role work. If manual QA finds a problem, record the checklist ID, role, expected behavior, actual behavior, and screenshot/path in `docs/MANUAL_QA_RESULTS.md`, then update `docs/WORKFLOW_GAPS.md` before fixing. Keep property ownership lifecycle hardening in the future sprint backlog unless manual QA exposes a launch-blocking ownership issue.
- Latest verification: the 2026-04-30 workflow QA stabilization checkpoint passed browser pre-QA coverage for QA-00 through QA-27, then the admin/reviewer separation checkpoint passed a fresh in-app browser reload console sweep with 0 new warnings/errors, `node --check` on `session.js`, `AppShell.js`, and `InternalOperationsPage.js`, `npm test -- --runInBand` with 35 passing frontend tests, `npm run build`, targeted role-separation backend tests with `.\.venv\Scripts\python -m unittest tests.test_payments_api tests.test_internal_automation_api tests.test_internal_scoring_api tests.test_internal_audit_api tests.test_internal_notifications_api tests.test_internal_worker_api tests.test_release_readiness_api tests.test_internal_operations_api` reporting 26 passing tests, repo layout/scaffold tests with 11 passing tests, full backend discovery with `.\.venv\Scripts\python -m unittest discover -s tests -p "test*.py"` reporting 131 passing tests, and `git diff --check`. Backend tests still emit the existing SQLite `ResourceWarning` noise.
- Repository bootstrap state: published to GitHub as `real_estate_trust_ledger` and ready to clone on a new machine

## Current Git Sync State

- Active branch: `codex/archive-ux-reset`
- Latest local checkpoint commit: see the current local tip of `codex/archive-ux-reset` after the score-transparency checkpoint commit
- Remote branch status: may be ahead of `origin/codex/archive-ux-reset` until the latest checkpoint is pushed
- Pull request shortcut:
  - `https://github.com/vtmarkop/real_estate_trust_ledger/pull/new/codex/archive-ux-reset`

## Last Completed Work

The project is currently coming out of a long frontend refinement arc:

- Sprint 17 closed the main frontend parity and information-architecture gaps
- Sprint 18 added the bilingual English/Greek layer
- Sprint 19 added the compact workspace and cinematic design system
- Sprint 20 completed the page-by-page conversion, localization refactor, and UI-semantics pass

The newest repo-level continuity work added:

- `AGENTS.md` for repo operating rules
- this handoff file for live continuation state
- `docs/WORKFLOW_GAPS.md` for imperfect workflow tracking
- `docs/WORKSTATION_SYNC.md` for daily home/work machine continuity
- `docs/GITHUB_BOOTSTRAP.md` for first-repo creation and remote setup

The newest product continuity checkpoint added:

- explicit appealed-versus-first-review stage language in the user dispute desk
- matching reviewer handoff framing in `Review Center > Disputes`
- a payment guard that keeps disputed or re-opened payment cases inside reviewer flow until a fresh verdict is issued

The newest UX-reset checkpoint added:

- a protected pre-reset backup snapshot under `repo_backups\real_estate_trust_ledger\20260424_134119`
- a dedicated reset branch `codex/archive-ux-reset`
- a repo-resident change journal in `docs/UX_RESET_LOG.md`
- the first object-first operations slice, so `Rent & Issues` now starts with property targeting and a selected-property history timeline instead of forcing cross-property scrolling
- the second object-first operations slice, so the selected property now has compact payment and issue dropdowns with one focused action/history pane at a time
- the third object-first operations slice, so selected-property `Daily work` actions are separated from read-only `History` timelines
- the fourth object-first operations slice, so `Create new` payment work and `Report new` maintenance work no longer render existing saved record details underneath the blank forms
- the fifth separation pass, so operations action cards no longer show read-only proof/notes/verdict history inline, and agency saved trust checks now live in `Screening history`
- tenancy metadata in `Rental Records` and `Rent & Issues` now shows `Your role` plus the relevant tenant/landlord counterparty instead of the low-value `Parties: Tenant and Landlord` pill
- active workspace-role scoping now happens after authentication from the shell, not from a pre-login dropdown, and hides role-irrelevant navigation, direct routes, score dimensions, tenancy records, property setup, and operations records in the main tenant/landlord workspaces
- follow-up runtime fix bound the `My Trust` page to the session hook so role-scoped trust score rendering no longer crashes with `session is not defined`
- score presentation in `Home` and `My Trust` now clarifies that landlord-side score is the signed-in user's own landlord/property-owner dimension, not the score of a tenant's current landlord
- the score-transparency slice now exposes contribution breakdowns in `My Trust`, agency trust-check previews, and internal scoring controls, using the same base-score, contribution, verification-strength, and adjudication-delta vocabulary everywhere
- the Greek localization quality pass now extends the patch dictionary for the post-reset visible workspace copy, fixes dynamic phrases such as role-only shell status, selected-property history text, score contribution breakdown labels, contribution-point rules, tenancy-status labels, and application-status confirmations, and adds frontend regression coverage for the newer UX-reset copy
- the weak `Comfort` / `Compact` density switch has been removed from the shell; signed-in workspaces now stay on fixed compact density until a future density option can produce an obvious layout difference
- restore point `32db93f` (`Checkpoint fixed compact localized workspace`) was created before the modern visual memorability pass
- the first modern visual memorability pass now gives each main workspace a color identity, adds colored sidebar lane markers, makes tabs/status badges derive semantic visual classes from workflow IDs/labels, strengthens card elevation, and makes fields, buttons, dropdowns, and file inputs more visible
- the first guided menu-flow clarity pass now makes `Rental Records` render only the selected top-level lane instead of showing tenancy setup and saved-property setup side by side, and renames the `Review Center` menu cards toward novice-facing jobs such as daily reviews, dispute decisions, account roles, system runtime, and history/audit
- the global section-switcher visual cleanup now applies the larger command-card tab treatment to top-level switchers across trust, marketplace, records, operations, agency, review, and account/security pages; it also removed the conflicting `section-switcher::after` accent pill, removed signed-in workspace ambient background blobs, added deliberate vertical space between major workspace panels, increased internal hero/stat spacing, and changed panel/tab/card depth from broad glow to tight negative-spread elevation so adjacent cards do not visually bleed together
- the semantic icon/static-vs-dynamic text hierarchy slice added `VisualIcon.js`, stable shell navigation icons, workflow-tab icons derived from tab IDs, submit-form field-label icons derived centrally from label text, and shared `text-static` / `text-dynamic` / `dynamic-token` classes so labels stay quieter than values, role/status data, counts, and badges
- landlord property setup now keeps the owner-managed path explicit when the agency directory is empty, disables the agency-managed option until a real agency organization exists, explains that agency assignment can happen later, and hardens the submit payload so an empty agency directory cannot accidentally block property creation with an agency-required backend error
- agency workspace bootstrap is now owned by the `Agent` role, not by landlord mode: an unassigned agent sees a Home panel to create an agency organization, successful creation makes that account the agency owner, Agency Tools explains the missing-membership state instead of dead-ending, and the backend rejects agency organization creation unless the account has the `agency` workspace entitlement
- landlord agency assignment now uses an agency operator directory instead of manual email guessing: once an agency is selected, the form exposes active owner/admin/agent operators, auto-fills the operator email when there is only one, and otherwise lets the landlord choose the responsible operator
- agency-created properties are now explicit agency inventory: `Agency Tools > Publishing` creates properties assigned to the selected agency organization and signed-in agent, `/properties/mine` keeps them visible in agency mode, and listing publication is blocked unless the property is assigned to that agency
- agency-created inventory can now be linked to an existing landlord owner: `Agency Tools > Publishing` and `Agency Tools > Portfolio` accept a landlord owner email, the backend requires that account to have the landlord workspace role, and the linked landlord sees/reuses the property in landlord mode while the listing guard remains agency-bound
- self-managed landlords can now publish owner-managed homes without an agency: `Rental Records > Properties & setup > Publish listing` posts to `/landlord/listings`, tenant `Listings` shows both landlord and agency sources, and landlord-owned applications return to `/landlord/applications` for review
- accepted listing applications now have an explicit tenancy bridge: agency and landlord managers accept first, then create the tenancy from the accepted application with lease dates; the bridge links `tenancy_id`, closes the listing, assigns the tenant to the property, and writes tenancy-created trust events
- agency-managed application-to-tenancy creation requires the property to be linked to an existing landlord owner first, while owner-managed landlord applications use the signed-in landlord owner directly
- true action buttons/links now receive hover/focus help bubbles through the shared frontend `e()` wrapper, with targeted English/Greek help for the most common listing, application, property, sign-in, and navigation actions; workflow tabs and command-card selectors opt out so their large segmented cards do not produce clipped pseudo-tooltips
- `docs/WORKFLOW_QA_PLAN.md` now defines the full real-life workflow QA matrix and execution order for sign-in/role scope, agency bootstrap, property setup, listings, tenancies, evidence, payments, deposits, maintenance, disputes, scoring, localization, and visual accessibility
- `docs/MANUAL_QA_RUNBOOK.md`, `docs/MANUAL_QA_CHECKLIST.md`, and `docs/MANUAL_QA_RESULTS.md` now provide the user-run manual QA package with seed commands, credentials, task IDs, expected results, severity labels, and a pass/fail worksheet
- the first browser QA slice used the clean local accounts to run an owner-managed landlord listing from property creation through tenant application, landlord acceptance, tenancy creation, and tenant-side tenancy visibility
- a real continuity bug was fixed: the new tenancy existed, but the `Tenancy records` lane did not show existing tenancy cards; records now appear under `Existing tenancy records`, while uploads and reference artifacts remain in `Artifacts`
- direct tenancy creation help text now explains direct record creation instead of wrongly describing the accepted-application bridge, and targeted help text was added for listing publication, application submission, record confirmation, review requests, evidence submission, references, and artifact opening
- the shared translation element wrapper now normalizes nested child arrays, reducing React key-warning noise caused by translated child collections
- the 2026-04-30 Codex pre-QA pass covered QA-00 through QA-27 across the minimal four-account reset and rich demo seed; results are recorded in `docs/MANUAL_QA_RESULTS.md`
- issues fixed during that pass include fragile native date inputs, landlord access to tenant marketplace routes, closed-listing/applicant-note wording, selected-tenancy artifact focus, and final Greek browser/session wording
- internal access is now separated by responsibility instead of treated as one power surface: reviewers can see review queues and issue tenancy/evidence/history/dispute verdicts, while admins can manage account workspace roles, scoring controls, automation, notifications, workers, audit, and release readiness; only internal access/overview is shared
- explicit account workspace-role entitlements now live on `User.workspace_roles`, are returned from `/auth/me`, drive the shell role menu, and are editable from `Review Center > Roles` by platform admins
- tenant, landlord, and agency backend routes now check the matching workspace entitlement in addition to existing tenancy/property/membership permissions, so a visible role and a record permission are separate requirements
- the current local database was reset with the destructive account-only script; it wipes local data and creates only the four requested accounts:
  - `vasilis.markopoulos@accounts.trustledger.app` / `VasilisTenantAdmin123!` with tenant + admin/internal roles
  - `lila.tsoutsoura@accounts.trustledger.app` / `LilaLandlord123!` with landlord role
  - `theodore.tsoutsouras@accounts.trustledger.app` / `TheodoreAgent123!` with agent role and no agency organization yet
  - `froso.evangeliadou@accounts.trustledger.app` / `FrosoTenantLandlord123!` with tenant + landlord roles
- a pushed branch checkpoint on `origin/codex/archive-ux-reset` so home/work continuation can resume from the same branch state

## Current Product Reality

The rebuilt application is functionally broad and much more complete than the original MVP, but the current product risk is no longer missing core architecture. The main risk is workflow continuity and user clarity across role handoffs.

Role visibility is now intentionally account-owned: an account can be tenant, landlord, agent, reviewer/internal, admin/internal, or a controlled combination, and the UI only offers those assigned roles. This is separate from record access. A user still needs the matching tenancy, property, organization membership, reviewer system role, admin system role, or internal permission before the backend allows actual work. The agency role has one explicit bootstrap exception: an account with the `agency` entitlement and no agency membership may create the first agency workspace from Home, becoming that agency's owner.

Login is intentionally plain email/password now. The pre-auth role dropdown was removed because it asked users to make a workspace decision before the app knew which roles the account really had. After `/auth/me`, the shell opens the last valid role for that browser or falls back to the first assigned role, then mixed-role users can switch from the sidebar.

There are two local data modes documented in `docs/LOCAL_RUN.md` and `docs/WORKSPACE_GUIDE.md`: the current simple account-only reset via `dev_reset_minimal_users.py`, and the legacy/rich workflow demo seed via `dev_seed.py`. The rich demo accounts are not present after the account-only reset.

That means the highest-value continuation work is not "add random new capability." It is:

- verify every important workflow end to end
- confirm each role sees the minimum necessary surface
- confirm score, score-contribution, dispute, appeal, and review state changes are obvious to users
- fix any workflow that is technically implemented but operationally confusing

## Latest Audit Outcome

The first workflow continuity checkpoint after Sprint 20 focused on dispute appeal continuity.

This checkpoint confirmed and tightened the following behavior:

- appealed maintenance/payment/deposit items return to `UNDER_REVIEW`
- the reviewer queue now surfaces them as appealed re-reviews awaiting a fresh verdict
- the user-facing dispute desk now shows explicit stage, notes, and next-step messaging
- payment disputes can no longer be overridden through the normal payee decision path once reviewer flow has started
- score deltas still only count while a case is in `VERDICT_ISSUED`

The latest role-separation checkpoint corrected the internal workspace boundary after manual review found that an admin could issue a dispute verdict. Reviewer-only APIs now own tenancy/evidence/history-import decisions and payment/deposit/maintenance verdicts. Admin-only APIs now own platform controls: account workspace roles, scoring control, automation, notifications, workers, audit, and release readiness. The frontend labels the same internal shell as `Review Center` for reviewers and `Admin Center` for admins, and it only loads the sections each role can actually use.

The active concern is now human QA signoff plus release polish, not broad unknown workflow architecture. The Codex pre-QA pass exercised the major desktop browser workflows and fixed the visible blockers it found. The remaining intentionally open QA items are real responsive widths and human keyboard-only traversal, because those should be verified by a person in the actual browser before release-candidate confidence.

## Workflow Audit Standard

Any continuation audit should classify workflows as:

- `complete_and_obvious`
- `complete_but_hard_to_understand`
- `partially_implemented`
- `missing`

Record active findings in `docs/WORKFLOW_GAPS.md`.

## Next Recommended Actions

1. Run the user's manual QA pass from `docs/MANUAL_QA_RUNBOOK.md`, `docs/MANUAL_QA_CHECKLIST.md`, and `docs/MANUAL_QA_RESULTS.md`.
2. Pay special attention to QA-26 responsive widths and QA-23 keyboard-only traversal, because those remain intentionally human-verified.
3. If manual QA finds a failure, record it by checklist ID in `docs/MANUAL_QA_RESULTS.md`, classify it in `docs/WORKFLOW_GAPS.md`, then fix the smallest existing workflow surface instead of inventing a parallel flow.
4. Verify admin/reviewer role separation during manual QA: admin should not be able to issue verdicts, and reviewer should not see platform controls.
5. If manual QA passes, continue Sprint 21 release polish: accessibility, motion, responsive tuning, fixed compact shell documentation, and design-system documentation.
6. Keep property ownership lifecycle hardening as a future production sprint unless manual QA exposes a blocking ownership workflow.

## Verification Baseline

Before starting new substantial work, the safest baseline checks are:

```powershell
.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold
```

If frontend work is involved, also run:

```powershell
Push-Location apps\web
npm test
npm run build
Pop-Location
```

If backend workflow logic changes, also run targeted backend tests and any required migration/seed verification.

## Resume Prompt For A New Thread

If work resumes in a new Codex thread, use a prompt like:

```text
Continue the Trust Ledger rebuild from the current repo state.

Read README.md, AGENTS.md, docs/HANDOFF.md, docs/WORKFLOW_GAPS.md, docs/WORKFLOW_QA_PLAN.md, docs/SPRINTS.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/WORKFLOW_MAP.md, and docs/WORKFLOW_DIAGRAMS.md first.

We are currently on branch codex/archive-ux-reset, post-Sprint-20. The dispute and appeal handoff pass is complete, and the active checkpoint is the archive-alignment UX reset with selected-property targeting, Daily work versus History separation, create-vs-existing payment/issue modes, selected payment/issue detail focus, role-wide history/log lane separation, explicit account workspace-role entitlements, sidebar-only role switching after login, account role management, local account-only reset support, tenancy role/counterparty clarity, score-role clarity, the first Sprint 21 score-contribution transparency slice complete, the Greek localization quality pass complete for likely visible web workspace copy, the first modern visual memorability pass implemented after restore point 32db93f, the first guided menu-flow clarity pass implemented for Rental Records and Review Center labels, global section-switcher visual cleanup completed so top-level menus use the same command-card treatment without stray accent/shadow overlap, the agency property/listing assignment continuity fix completed so landlord agency assignment uses operator selection and agency-created properties stay visible as agency inventory for listings, the agency-created landlord-owner link implemented so an agent can connect agency inventory to an existing landlord account without weakening listing boundaries, direct owner-managed landlord listing publication implemented so self-managed homes can appear in tenant Listings without a fake agency, the accepted-application-to-tenancy bridge implemented for landlord and agency application managers, action-button hover-help bubbles added through the shared frontend element wrapper while workflow tab selectors are excluded, selected-tenancy artifact focus implemented, docs/WORKFLOW_QA_PLAN.md and the manual QA package added, the 2026-04-30 Codex pre-QA pass recorded across QA-00 through QA-27, and strict reviewer-versus-admin internal separation enforced in backend routes, frontend capabilities, and docs.
```
