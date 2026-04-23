# Tomorrow Morning Work-Machine Checklist

This is the shortest practical checklist for resuming the project from the work machine.

Use this file when you want the fastest path from:

- clone the repo
- boot the machine
- run the app
- open Codex
- continue development

## If This Is The First Time On The Work Machine

### 1. Clone The Repository

Use either HTTPS or SSH.

HTTPS:

```powershell
git clone https://github.com/vtmarkop/real_estate_trust_ledger.git
cd real_estate_trust_ledger
```

SSH:

```powershell
git clone git@github.com:vtmarkop/real_estate_trust_ledger.git
cd real_estate_trust_ledger
```

### 2. Run The One-Time Machine Bootstrap

```powershell
.\bootstrap_workstation.ps1
```

What this does:

- creates `.venv` if needed
- upgrades `pip`
- installs backend dependencies
- installs frontend dependencies
- runs database migrations
- seeds demo data

### 3. Start The Backend

Open a terminal in the repo root and run:

```powershell
.\.venv\Scripts\python run_api.py
```

### 4. Start The Frontend

Open a second terminal in the repo root and run:

```powershell
.\.venv\Scripts\python run_web.py
```

### 5. Open Codex And Resume Context

Open the repository in Codex and read these files first:

1. `README.md`
2. `AGENTS.md`
3. `docs/HANDOFF.md`
4. `docs/WORKFLOW_GAPS.md`
5. `docs/SPRINTS.md`
6. `docs/ROADMAP.md`
7. `docs/DECISIONS.md`
8. `docs/WORKFLOW_MAP.md`
9. `docs/WORKFLOW_DIAGRAMS.md`

### 6. Use This Prompt In The New Codex Thread

```text
Continue the Trust Ledger rebuild from the current repo state.

Read README.md, AGENTS.md, docs/HANDOFF.md, docs/WORKFLOW_GAPS.md, docs/SPRINTS.md, docs/ROADMAP.md, docs/DECISIONS.md, docs/WORKFLOW_MAP.md, and docs/WORKFLOW_DIAGRAMS.md first.

Treat the repository as the primary continuity source. We are currently post-Sprint-20 and the next recommended focus is a workflow continuity audit and role-handoff clarity pass.
```

## If The Work Machine Already Has The Repo

If the repository was already cloned and bootstrapped before, the morning routine is shorter.

### 1. Pull The Latest State

```powershell
git pull
```

### 2. Start The Backend

```powershell
.\.venv\Scripts\python run_api.py
```

### 3. Start The Frontend

```powershell
.\.venv\Scripts\python run_web.py
```

### 4. Open Codex And Resume

Read:

- `README.md`
- `AGENTS.md`
- `docs/HANDOFF.md`
- `docs/WORKFLOW_GAPS.md`

Then continue from the `Next Recommended Actions` section in `docs/HANDOFF.md`.

## Quick Sanity Check If Something Feels Off

If the app does not behave as expected, run:

```powershell
.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold
```

If frontend behavior looks wrong, also run:

```powershell
Push-Location apps\web
npm test
npm run build
Pop-Location
```

## Where The Deeper Instructions Live

This file is the short version.

For the full operational guidance, use:

- `docs/GITHUB_BOOTSTRAP.md`
- `docs/WORKSTATION_SYNC.md`
- `docs/HANDOFF.md`
- `AGENTS.md`
