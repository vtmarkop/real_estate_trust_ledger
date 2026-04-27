# Live Handoff

This file is the current resume point for any new device, new Codex thread, or interrupted work session.

## Current Checkpoint

- Program state: completed through Sprint 20
- Latest non-sprint checkpoint: archive-alignment UX reset in progress, with selected-property operations, compact payment/issue targeting, daily/history separation, create-vs-existing action separation, role-wide history lane separation, backend-backed explicit account workspace-role entitlements, sidebar-only role switching after login, account role management, a local account-only reset path, tenancy role/counterparty clarity, score-role clarity, and the first Sprint 21 score-contribution transparency slice completed
- Next planned sprint: Sprint 21
- Recommended immediate focus: visually review the four clean local accounts role by role, confirm the tenant/admin and tenant/landlord mixed accounts only expose their assigned workspaces at a time, continue the broader workflow continuity audit, and then continue the remaining Sprint 21 frontend release polish around motion, accessibility, responsive behavior, and design-system documentation
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

Role visibility is now intentionally account-owned: an account can be tenant, landlord, agent, admin/internal, or a controlled combination, and the UI only offers those assigned roles. This is separate from record access. A user still needs the matching tenancy, property, organization membership, or internal permission before the backend allows actual work.

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

The active concern now is broader audit coverage plus archive-alignment on presentation. Other workflows may still be technically complete but less obvious than they should be, and the operations workspace is now in an active UI reset to recover original task clarity without weakening the rebuild architecture.

## Workflow Audit Standard

Any continuation audit should classify workflows as:

- `complete_and_obvious`
- `complete_but_hard_to_understand`
- `partially_implemented`
- `missing`

Record active findings in `docs/WORKFLOW_GAPS.md`.

## Next Recommended Actions

1. Continue the `Rent & Issues` archive-alignment reset:
   - visually review the selected property, `Daily work`, `History`, create-vs-existing payment modes, create-vs-existing maintenance modes, payment menu, issue menu, and agency `Screening history` with the clean four-account local reset or with the richer demo seed when broader workflow data is needed
   - keep one property active at a time for normal tenant/landlord work
   - continue reducing any remaining action-form density where `Daily work` still feels heavier than the archive pattern
2. Verify role independence after any new role-surface change:
   - tenant-only accounts should not see landlord, agency, or admin menus
   - landlord-only accounts should not see tenant listings or tenant operations
   - agent accounts should only see agency surfaces, and those surfaces should stay empty until an agency organization membership exists
   - admin/internal visibility should come from the `internal` workspace entitlement and matching backend system role
3. Run the broader workflow continuity scan across:
   - property creation and assignment
   - tenancy creation and activation
   - evidence upload and review
   - score side effects and score-contribution transparency outside the live dispute cards
   - consent and trust-sharing flows
   - agency screening and application review flows
   - reviewer-facing history and next-step clarity after non-dispute decisions
4. Visually verify the completed Sprint 21 score-transparency slice:
   - confirm `My Trust` shows the neutral base score and each active contribution for the selected tenant or landlord role
   - confirm verification-strength contributions stay separate from tenant and landlord score contributions
   - confirm reviewer-entered payment, deposit, and maintenance verdict deltas are labeled as adjudication adjustments
   - confirm agency previews explain aggregate score drivers without exposing role-irrelevant private workflow history
   - confirm internal scoring controls use the same vocabulary as user and agency surfaces
5. For each workflow, decide whether the gap is:
   - backend logic
   - frontend visibility
   - wording/status clarity
   - role/handoff continuity
6. Treat the dispute and appeal re-review flow as the reference model for clear role handoffs
7. Fix gaps by extending the existing architecture, not by creating parallel flows
8. Update:
   - `docs/WORKFLOW_GAPS.md`
   - `docs/WORKFLOW_MAP.md`
   - `docs/WORKFLOW_DIAGRAMS.md`
   - `docs/WORKSPACE_GUIDE.md`
   if the user-facing story changes

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

Read README.md, AGENTS.md, docs/HANDOFF.md, docs/WORKFLOW_GAPS.md, docs/SPRINTS.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/WORKFLOW_MAP.md, and docs/WORKFLOW_DIAGRAMS.md first.

We are currently on branch codex/archive-ux-reset, post-Sprint-20. The dispute and appeal handoff pass is complete, and the active checkpoint is the archive-alignment UX reset with selected-property targeting, Daily work versus History separation, create-vs-existing payment/issue modes, selected payment/issue detail focus, role-wide history/log lane separation, explicit account workspace-role entitlements, sidebar-only role switching after login, account role management, local account-only reset support, tenancy role/counterparty clarity, score-role clarity, and the first Sprint 21 score-contribution transparency slice complete.
```
