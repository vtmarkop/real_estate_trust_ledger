# Trust Ledger Agent Operating Guide

This repository is designed to survive long-running work across multiple Codex threads, multiple devices, and interrupted sprint execution.

Any agent continuing work here should treat the repository itself as the primary memory system and the chat as a temporary execution surface.

## Read Order Before Changing Code

Read these files first, in this order, before making product, architectural, or sprint decisions:

1. `README.md`
2. `docs/HANDOFF.md`
3. `docs/WORKFLOW_GAPS.md`
4. `docs/SPRINTS.md`
5. `docs/ROADMAP.md`
6. `docs/DECISIONS.md`
7. `docs/ARCHITECTURE.md`
8. `docs/WORKFLOW_MAP.md`
9. `docs/WORKFLOW_DIAGRAMS.md`
10. `docs/CODEBASE_REFERENCE.md`

If the work is operational or local-run related, also read:

- `docs/LOCAL_RUN.md`
- `docs/STAGING_RUN.md`
- `docs/WORKSTATION_SYNC.md`
- `docs/GITHUB_BOOTSTRAP.md`

## Operating Principles

- Stay loyal to the current architecture. Extend existing models, services, routes, and UI lanes instead of inventing parallel systems.
- Preserve the sprint/checkpoint methodology. Large work should end at a clean checkpoint with updated repo memory.
- Prefer real workflow continuity over feature-count optics. A smaller but complete user journey is better than a broader but confusing one.
- Treat frontend/backend parity honestly. If the backend supports something but the frontend continuity is weak, record that as a real gap.
- Keep the archive as reference-only unless work is explicitly about migration or parity comparison.
- Avoid hidden assumptions. If a workflow relies on a role handoff, status change, or scoring side effect, document it where future agents can find it.

## Checkpoint Discipline

At the end of any meaningful checkpoint:

1. Update `docs/HANDOFF.md`
2. Update `docs/WORKFLOW_GAPS.md` if any workflow is incomplete, confusing, or only partially surfaced
3. Update `docs/SPRINTS.md` if the checkpoint materially changes sprint state
4. Update `README.md` if the source-of-truth reading order or current status changed
5. Update supporting docs if operator behavior changed

Do not leave “what happened last” only in chat history.

## Verification Rules

Before declaring a checkpoint complete:

1. Run the smallest relevant verification that honestly covers the change
2. If repo structure or docs changed, run:

```powershell
.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold
```

3. If backend logic changed, run targeted backend tests and any necessary migration/seed checks
4. If frontend logic changed, run:

```powershell
npm test
npm run build
```

from `apps\web` or through the repo-root launcher path as appropriate.

5. If runtime entrypoints or environment docs changed, verify the documented command path still works

Never claim a clean checkpoint without noting what was actually verified.

## Cross-Device Continuity Rules

- Use repo-resident docs for continuity, not chat memory alone.
- Keep instructions path-agnostic where possible and prefer repo-root commands.
- When switching devices, the next thread should be able to recover by reading `README.md`, `docs/HANDOFF.md`, and `docs/WORKFLOW_GAPS.md`.
- If a thread or device transition happens mid-sprint, record the exact resume point in `docs/HANDOFF.md`.
- If a workflow audit is in progress, keep the active findings in `docs/WORKFLOW_GAPS.md`, not in temporary notes.

## Workflow Audit Standard

When auditing workflows, classify each one as:

- `complete_and_obvious`
- `complete_but_hard_to_understand`
- `partially_implemented`
- `missing`

For each workflow, capture:

- expected behavior
- actual behavior
- backend status
- frontend status
- user-facing continuity quality
- next fix or decision

## Product/UX Expectations

- Roles should only see the tabs and actions they are supposed to use.
- Heavy pages should be split into focused lanes rather than mixed dashboards.
- Different information types should look different:
  - statuses
  - facts
  - notes/comments
  - timeline/history
- Localization should cover real product copy horizontally, not just menu labels.
- Dispute, appeal, and review handoffs must feel explicit in the UI, not merely exist in backend state transitions.

## New Thread Bootstrap

If work resumes in a new Codex thread:

1. Open the repository
2. Read the files listed under `Read Order Before Changing Code`
3. Run the baseline verification in `docs/WORKSTATION_SYNC.md`
4. Continue from the exact `Next recommended actions` section in `docs/HANDOFF.md`

If the repository is being moved to a new device for the first time, also follow `docs/GITHUB_BOOTSTRAP.md` and `docs/WORKSTATION_SYNC.md`.

If any of those files disagree, the order of authority is:

1. `docs/DECISIONS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ROADMAP.md`
4. `docs/SPRINTS.md`
5. `docs/HANDOFF.md`

## Anti-Patterns To Avoid

- Do not invent a second workflow because the first one is hard to discover; fix the continuity instead.
- Do not leave critical state only in chat.
- Do not silently drift the roadmap without updating repo memory.
- Do not bypass verification because a change looks “docs-only” if tests protect those docs.
- Do not weaken architecture discipline in order to finish a sprint faster.
