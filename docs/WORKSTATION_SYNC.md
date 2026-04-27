# Workstation Sync Guide

This guide is the professional operating path for moving the Trust Ledger rebuild between home and work machines without depending on chat memory alone.

## Goal

The repository should carry the project state, the sprint state, and the current continuation state well enough that a new device or a new Codex thread can pick up work safely.

## Recommended Source Of Truth Stack

When moving between devices, treat these files as the minimum continuity bundle:

1. `README.md`
2. `AGENTS.md`
3. `docs/HANDOFF.md`
4. `docs/WORKFLOW_GAPS.md`
5. `docs/SPRINTS.md`
6. `docs/ROADMAP.md`
7. `docs/DECISIONS.md`
8. `docs/GITHUB_BOOTSTRAP.md`

If the work is workflow-heavy, also read:

9. `docs/WORKFLOW_MAP.md`
10. `docs/WORKFLOW_DIAGRAMS.md`

## Preferred Transport Between Devices

The recommended daily flow is:

1. keep the repository in Git
2. commit/push or otherwise synchronize the latest code and docs
3. open the same repository state on the other machine
4. bootstrap the next thread from the repo docs, not from memory

If Git is temporarily unavailable, a synchronized copy of the repository can still work, but the repo docs remain mandatory.

For the first-time repository publish flow, use `docs/GITHUB_BOOTSTRAP.md`.

For the shortest ready-to-run morning checklist on the next machine, use `docs/TOMORROW_MORNING.md`.

## End-Of-Day Checklist On The Current Machine

Before stopping work:

1. finish at a clean checkpoint if possible
2. update:
   - `docs/HANDOFF.md`
   - `docs/WORKFLOW_GAPS.md`
   - `docs/SPRINTS.md` if sprint state changed
3. run the smallest honest verification for the work
4. sync the repository to the remote or transfer channel you use

### Minimum End-Of-Day Verification

For doc/checkpoint changes:

```powershell
.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold
```

For frontend changes:

```powershell
Push-Location apps\web
npm test
npm run build
Pop-Location
```

For backend logic changes, also run the relevant targeted backend tests and any migration/seed checks needed for confidence.

## Start-Of-Day Checklist On The Next Machine

1. sync or pull the latest repository state
   - if you are continuing the active UX reset, switch to `codex/archive-ux-reset`
2. open the repository in Codex
3. read:
   - `README.md`
   - `AGENTS.md`
   - `docs/HANDOFF.md`
   - `docs/WORKFLOW_GAPS.md`
   - `docs/GITHUB_BOOTSTRAP.md`
4. run the baseline verification:

```powershell
.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold
```

5. continue from the `Next Recommended Actions` in `docs/HANDOFF.md`

If this is the first time the repository is being used on that machine, run:

```powershell
.\bootstrap_workstation.ps1
```

## Repo-Root Runtime Commands

These are the safest cross-device commands because they do not depend on manually changing into subfolders first.

### API

```powershell
.\.venv\Scripts\python run_api.py
```

### Web

```powershell
.\.venv\Scripts\python run_web.py
```

### Baseline Regression

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
```

## New Codex Thread Bootstrap

If you need to start a fresh Codex thread on the new device, begin with a handoff prompt like this:

```text
Continue the Trust Ledger rebuild from the current repo state.

Read README.md, AGENTS.md, docs/HANDOFF.md, docs/WORKFLOW_GAPS.md, docs/SPRINTS.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/WORKFLOW_MAP.md, and docs/WORKFLOW_DIAGRAMS.md first.

Treat the repository as the primary continuity source. We are currently on branch codex/archive-ux-reset, post-Sprint-20, and the current checkpoint is the archive-alignment UX reset with property targeting, Daily work versus History separation, create-vs-existing payment/issue modes, selected payment/issue detail focus, and score-role clarity complete.
```

## Daily Chat Handoff Procedure

The safest way to move not just the code but the active project understanding between machines is:

1. update `docs/HANDOFF.md`
2. update `docs/WORKFLOW_GAPS.md` if needed
3. push the repo
4. pull the repo on the other machine
5. open the repository in Codex
6. start or continue a thread
7. read:
   - `README.md`
   - `AGENTS.md`
   - `docs/HANDOFF.md`
   - `docs/WORKFLOW_GAPS.md`
8. continue from the exact next actions in the handoff file

This is intentionally better than trying to preserve the whole old chat by memory alone.

## Example Daily Flow

### Work Machine -> Home Machine

1. finish a checkpoint on the work machine
2. update `docs/HANDOFF.md`
3. update `docs/WORKFLOW_GAPS.md` if needed
4. run verification
5. sync/push the repo
6. pull/open the repo at home
7. if this is the first time on that machine, run `.\bootstrap_workstation.ps1`
8. read the continuity docs
9. continue from the exact next actions

### Home Machine -> Work Machine

The same flow in reverse:

1. checkpoint
2. update handoff docs
3. verify
4. sync
5. open on the other device
6. if this is the first time on that machine, run `.\bootstrap_workstation.ps1`
7. read the continuity docs
8. resume

## What Not To Rely On

Do not rely on:

- memory of the last chat alone
- the visible sidebar thread history alone
- "I think we were about to..."
- a single monolithic note that mixes architecture, sprint state, and current tasks together

The continuity system is intentionally split:

- `AGENTS.md` = how to work in this repo
- `docs/HANDOFF.md` = where the project is paused right now
- `docs/WORKFLOW_GAPS.md` = what still feels broken or unclear
- `docs/SPRINTS.md` = what has been completed historically

## If The Two Machines Use Different Local Paths

That is acceptable.

The continuity system is designed around repo-root commands and repository-relative docs, so the project can move between different local directory names as long as the same repository contents are present and the same startup/verification flow is used.
