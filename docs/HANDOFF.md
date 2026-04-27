# Live Handoff

This file is the current resume point for any new device, new Codex thread, or interrupted work session.

## Current Checkpoint

- Program state: completed through Sprint 20
- Latest non-sprint checkpoint: archive-alignment UX reset in progress, with selected-property operations, compact payment/issue targeting, daily/history separation, create-vs-existing action separation, role-wide history lane separation, tenancy role/counterparty clarity, and score-role clarity completed
- Next planned sprint: Sprint 21
- Recommended immediate focus: visually review the updated `Rent & Issues` `Daily work` versus `History` split with demo tenant/landlord data, then continue the broader workflow continuity audit across the remaining role surfaces
- Repository bootstrap state: published to GitHub as `real_estate_trust_ledger` and ready to clone on a new machine

## Current Git Sync State

- Active branch: `codex/archive-ux-reset`
- Latest pushed checkpoint commit: see the current tip of `origin/codex/archive-ux-reset`
- Remote branch status: pushed to `origin/codex/archive-ux-reset`
- Pull request shortcut:
  - `https://github.com/vtmarkop/real_estate_trust_ledger/pull/new/codex/archive-ux-reset`
- Intentional local-only leftover:
  - `apps/web/package-lock.json` is still locally modified and was not included in the UX reset checkpoint push because it looked like unrelated lockfile churn

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
- score presentation in `Home` and `My Trust` now clarifies that landlord-side score is the signed-in user's own landlord/property-owner dimension, not the score of a tenant's current landlord
- a pushed branch checkpoint on `origin/codex/archive-ux-reset` so home/work continuation can resume from the same branch state

## Current Product Reality

The rebuilt application is functionally broad and much more complete than the original MVP, but the current product risk is no longer missing core architecture. The main risk is workflow continuity and user clarity across role handoffs.

That means the highest-value continuation work is not "add random new capability." It is:

- verify every important workflow end to end
- confirm each role sees the minimum necessary surface
- confirm score, dispute, appeal, and review state changes are obvious to users
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
   - visually review the selected property, `Daily work`, `History`, create-vs-existing payment modes, create-vs-existing maintenance modes, payment menu, issue menu, and agency `Screening history` with the seeded demo accounts
   - keep one property active at a time for normal tenant/landlord work
   - continue reducing any remaining action-form density where `Daily work` still feels heavier than the archive pattern
2. Run the broader workflow continuity scan across:
   - property creation and assignment
   - tenancy creation and activation
   - evidence upload and review
   - score side effects outside the live dispute cards
   - consent and trust-sharing flows
   - agency screening and application review flows
   - reviewer-facing history and next-step clarity after non-dispute decisions
3. For each workflow, decide whether the gap is:
   - backend logic
   - frontend visibility
   - wording/status clarity
   - role/handoff continuity
4. Treat the dispute and appeal re-review flow as the reference model for clear role handoffs
5. Fix gaps by extending the existing architecture, not by creating parallel flows
6. Update:
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

We are currently on branch codex/archive-ux-reset, post-Sprint-20. The dispute and appeal handoff pass is complete, and the active checkpoint is the archive-alignment UX reset with selected-property targeting, Daily work versus History separation, create-vs-existing payment/issue modes, selected payment/issue detail focus, role-wide history/log lane separation, tenancy role/counterparty clarity, and score-role clarity complete.
```
