# Trust Ledger Rebuild Workspace

This workspace now has two tracks:

- `archive/mesitis-mvp-2026-04-09/` preserves the previous MVP as legacy reference.
- `apps/`, `packages/`, `docs/`, and `tests/` are the new rebuild.

## Current Status

The rebuild is completed through `Sprint 20: Page-by-page Visual Conversion`.

The post-Sprint-17 parity remediation checkpoint is also complete. That checkpoint closed the main backend/frontend parity gaps discovered in the archive-vs-rebuild audit, especially around operational document uploads, session control, internal automation controls, and role-gated operational flows.

Sprint 18 added a bilingual frontend localization layer with a live language switcher, English/Greek UI coverage across the rebuilt web workspace, and localized frontend error presentation before the visual redesign track begins.

The pre-Sprint-19 documentation and consistency checkpoint is also complete. That checkpoint added a full technical codebase reference, corrected documentation inconsistencies, and aligned the runtime stage marker with the current rebuild state so the next sprint can start from a cleaner base.

The workflow simplification checkpoint is now also complete. The heaviest frontend workspaces have been split into focused lanes, and a new workflow map now traces the main business flows from backend models/services/routes into the frontend pages where users actually execute them.

The visual workflow diagram checkpoint is now also complete. The repo now includes Mermaid diagrams for the real implemented flows so product logic can be understood visually as well as textually.

Sprint 19 added the first real frontend design system pass on top of the simplified workflows: a darker cinematic palette, denser panel hierarchy, stronger contrast, variable-driven spacing, and a compact shell foundation for heavier operational workspaces.

Sprint 20 applied that system across the main product pages: richer hero summaries, cleaner section framing, clearer separation on trust, marketplace, security, agency, review, records, and operations surfaces, a follow-up localization refactor that fixed the live language switch and expanded English/Greek coverage across the Sprint 20 workspace copy, and a surgical UI-semantics pass that makes statuses, facts, notes, and timeline-style activity read as clearly different information types instead of generic card text.

The cross-device continuity checkpoint is now also complete. The repo now carries a professional handoff system for moving the project between machines and new Codex threads without depending on chat memory alone.

The GitHub bootstrap checkpoint is now also complete. The repo is published to the private GitHub repository `real_estate_trust_ledger`, with local-only runtime data excluded and the full home/work handoff routine documented in-project.

The first post-Sprint-20 workflow continuity checkpoint is now also complete for dispute and appeal handoffs. Payment, deposit, and maintenance cases now surface clearer re-review states in both personal and reviewer lanes, and payment disputes no longer allow a counterparty override once reviewer flow has started.

The post-Sprint-20 archive-alignment UX reset is in progress on `codex/archive-ux-reset`. The web app now supports an active workspace role switch inside the signed-in shell, backed by explicit account workspace-role entitlements stored on the user account and managed from the admin workspace. Login no longer asks for a role before authentication; the app opens the last valid workspace role for the browser, or the first assigned role if the saved role no longer belongs to the account. Tenant, landlord, agency, and admin workspaces now show only roles assigned to that account, while backend authorization still checks tenancy participation, property ownership, organization membership, and internal privileges. `Rent & Issues` now follows a stricter object-first pattern: choose one property, keep `Daily work` actions separate from read-only `History`, split create-new work from existing saved records, and use compact payment or maintenance dropdowns to focus one record at a time. The reset now also treats saved history/log surfaces as their own lanes across roles, including agency screening history, replaces generic tenancy party labels with current-user role and counterparty context, includes a local account-only reset path for the four requested clean users, and keeps the signed-in shell on a fixed compact layout instead of offering a weak density toggle. The first Sprint 21 score-transparency slice is now complete: `My Trust`, agency trust previews, and internal scoring controls show the neutral base score, active tenant/landlord contributions, verification-strength contributions, and reviewer adjudication deltas without scattering scoring text through daily action forms. A follow-up Greek localization quality pass now scans the visible web workspace copy, expands the Greek patch dictionary across the reset surfaces, fixes dynamic phrase translation around role scoping and score explanations, and adds regression coverage for the newer UX-reset copy. The newest Sprint 21 visual and guided-flow slices established a restore-point commit, then added stronger Netflix-like dark contrast, page-specific color identities, semantic workflow/status color tokens, brighter cards, more readable fields/buttons/dropdowns, a single active lane in `Rental Records`, selected-tenancy artifact focus, clearer novice-facing admin menu labels, global command-card styling for top-level section switchers, a cleanup for the stray accent/shadow overlap caused by pseudo-element collisions, semantic icons for shell navigation, workflow tabs, and submit-form field labels, clearer static-label versus dynamic-value visual hierarchy, a property setup clarity fix so landlords can save owner-managed properties even when no agency organization exists yet, an agent bootstrap fix so only accounts with the `agency` workspace role can create an agency organization and unassigned agents see the setup path from Home instead of a dead-end agency-tools screen, an agency inventory/listing fix so landlord agency assignment uses real operator choices while agency-created properties remain visible and listable only inside their assigned agency, an explicit landlord-owner link so an agent can assign agency-created inventory to an existing landlord account without confusing audit creator, agency listing assignment, and owner visibility, a direct owner-managed landlord listing path so self-managed homes can appear in tenant `Listings` without creating a fake agency, an explicit accepted-application-to-tenancy bridge in both landlord and agency application review lanes, and automatic hover-help bubbles on true action buttons/links while workflow tab selectors stay clean. The newest workflow QA stabilization pass adds a repo-resident master plan in `docs/WORKFLOW_QA_PLAN.md`, records results in `docs/MANUAL_QA_RESULTS.md`, and browser-tested QA-00 through QA-27 across the clean minimal accounts and rich demo seed; the only intentional manual follow-ups are real responsive-width QA and human keyboard-only traversal.

Internal access is now deliberately split: reviewers handle case decisions and dispute verdicts, while admins manage platform controls such as account roles, scoring, automation, notifications, workers, audit, and release readiness. The shared internal shell still has a common overview/access entry, but backend routes and frontend sections now enforce that separation.

The original launch-critical roadmap remains complete through Sprint 16. The current post-pilot track is now:

- Sprint 17: frontend parity and information architecture
- Sprint 18: bilingual frontend localization
- Sprint 19: compact workspace and cinematic visual system
- Sprint 20: page-by-page visual conversion and UI semantics refinement
- Sprint 21: motion, accessibility, score transparency, and release-level frontend refinement

## Source Of Truth

Read these files first before making product or architectural changes:

- `AGENTS.md`
- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `docs/SPRINTS.md`
- `docs/DECISIONS.md`
- `docs/HANDOFF.md`
- `docs/WORKFLOW_GAPS.md`
- `docs/WORKFLOW_QA_PLAN.md`
- `docs/MANUAL_QA_RUNBOOK.md`
- `docs/MANUAL_QA_CHECKLIST.md`
- `docs/MANUAL_QA_RESULTS.md`
- `docs/WORKSTATION_SYNC.md`
- `docs/GITHUB_BOOTSTRAP.md`
- `docs/CODEBASE_REFERENCE.md`
- `docs/WORKFLOW_MAP.md`
- `docs/WORKFLOW_DIAGRAMS.md`
- `docs/WORKSPACE_GUIDE.md`
- `docs/PARITY_AUDIT.md`
- `docs/LOCAL_RUN.md`
- `docs/STAGING_RUN.md`
- `docs/BACKUP_RESTORE.md`
- `docs/UAT.md`
- `docs/SECURITY_REVIEW.md`
- `docs/RELEASE_CANDIDATE.md`
- `docs/POST_PILOT.md`
- `docs/GO_LIVE.md`

## Repository Layout

```text
archive/
  mesitis-mvp-2026-04-09/

apps/
  api/
  web/
  worker/

packages/
  config/
  domain/
  scoring/
  ui/

docs/
tests/
```

## Working Rules

- All new product code goes under `apps/` or `packages/`.
- The archived MVP is reference-only unless we explicitly extract or migrate something from it.
- We deliver in sprints, and each sprint must end in a testable state.
- We keep the platform evidence-verified and automation-ready, without bank API dependency.

## Quick Verification

Run the current regression suite with:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
```

## First-Time Machine Bootstrap

For a brand-new home or work machine, the fastest setup path is now:

```powershell
.\bootstrap_workstation.ps1
```

That script creates the virtual environment, installs backend/frontend dependencies, runs migrations, and seeds demo data.

If you want the fastest possible work-machine resume checklist, open [docs/TOMORROW_MORNING.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/TOMORROW_MORNING.md).

## Fastest Way To See It Live

Use [docs/LOCAL_RUN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/LOCAL_RUN.md) for the local live demo path and [docs/GO_LIVE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/GO_LIVE.md) for the staged path from local demo to hosted pilot.

For the API specifically, the repo-root launcher `.\.venv\Scripts\python run_api.py` is now the safest local start path because it bootstraps the correct import path automatically.

For the web app, the matching repo-root launcher `.\.venv\Scripts\python run_web.py` is now the safest local start path because it starts Vite in `apps\web` without requiring a manual directory change first.

If you want a plain-language walkthrough of the product itself, start with [docs/WORKSPACE_GUIDE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKSPACE_GUIDE.md).

If you want the code-level map of models, schemas, services, routes, worker logic, frontend pages, and seeded workflows, start with [docs/CODEBASE_REFERENCE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/CODEBASE_REFERENCE.md).

If you want the business-flow map that shows how each workflow moves from backend logic into the frontend workspace, start with [docs/WORKFLOW_MAP.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKFLOW_MAP.md).

If you want the same flows visually as diagrams, start with [docs/WORKFLOW_DIAGRAMS.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKFLOW_DIAGRAMS.md).

If you are auditing the app as a real tenant, landlord, agent, or reviewer would use it, start with [docs/WORKFLOW_QA_PLAN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKFLOW_QA_PLAN.md).

If you want to run manual QA yourself, use [docs/MANUAL_QA_RUNBOOK.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/MANUAL_QA_RUNBOOK.md), [docs/MANUAL_QA_CHECKLIST.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/MANUAL_QA_CHECKLIST.md), and [docs/MANUAL_QA_RESULTS.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/MANUAL_QA_RESULTS.md).

If you need to move between home/work devices or restart in a new Codex thread, start with [AGENTS.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/AGENTS.md), then [docs/HANDOFF.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/HANDOFF.md), [docs/WORKFLOW_GAPS.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKFLOW_GAPS.md), and [docs/WORKSTATION_SYNC.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKSTATION_SYNC.md).

If you are publishing or reconnecting the repository itself on a new machine, use [docs/GITHUB_BOOTSTRAP.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/GITHUB_BOOTSTRAP.md).
