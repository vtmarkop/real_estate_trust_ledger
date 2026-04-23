# GitHub Bootstrap For `real_estate_trust_ledger`

This document is the source of truth for taking the local Trust Ledger rebuild and publishing it safely to GitHub for the first time.

Use it the first time the repository is created, and keep it for future device setup or full rebuild scenarios.

## Target Repository

- Recommended GitHub repository name: `real_estate_trust_ledger`
- Recommended visibility: `Private`

This keeps the project identity clear while protecting the current product, docs, and seeded development state.

## Before The First Push

The local repository should meet these conditions before you push:

- no virtual environments are tracked
- no `node_modules` folders are tracked
- no local SQLite databases are tracked
- no local artifact storage is tracked
- repo-root documentation already contains the handoff and workstation-sync rules

This repository is already prepared for that through:

- `.gitignore`
- `.gitattributes`
- `AGENTS.md`
- `docs/HANDOFF.md`
- `docs/WORKFLOW_GAPS.md`
- `docs/WORKSTATION_SYNC.md`

## Step 1: Create The GitHub Repository

In GitHub:

1. Click `New repository`
2. Repository name: `real_estate_trust_ledger`
3. Visibility: `Private`
4. Do **not** initialize with:
   - README
   - `.gitignore`
   - License

Reason:

- the local project already contains those files
- skipping GitHub-side initialization avoids unnecessary first-pull merge noise

## Step 2: Configure Authentication

The most reliable professional setup is SSH on both home and work machines.

### Generate An SSH Key

Run on each machine:

```powershell
ssh-keygen -t ed25519 -C "your-email@example.com"
```

Accept the default path unless you already manage multiple SSH identities.

### Copy The Public Key

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
```

Copy the output.

### Add It To GitHub

In GitHub:

1. Open `Settings`
2. Open `SSH and GPG keys`
3. Click `New SSH key`
4. Paste the copied public key
5. Save

### Verify SSH Access

```powershell
ssh -T git@github.com
```

Expected result:

- GitHub confirms that authentication succeeded

## Step 3: Initialize The Local Repository

From the repository root:

```powershell
git init
git branch -M main
```

If this has already been done once, these commands are harmless to check or rerun carefully.

## Step 4: Review The First Add

Before the first commit:

```powershell
git add .
git status
```

What you should see:

- source code
- docs
- tests
- launcher scripts

What you should **not** see:

- `.venv`
- `node_modules`
- local `.db` files
- `private_artifacts`
- `apps/api/private_artifacts`

If those unwanted files appear, stop and fix `.gitignore` before committing.

## Step 5: Create The First Commit

```powershell
git commit -m "Initial import: Trust Ledger rebuild through Sprint 20"
```

If Git asks for your name/email first:

```powershell
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Then run the commit again.

## Step 6: Add The GitHub Remote

Replace `YOUR_GITHUB_USERNAME` with your actual GitHub username:

```powershell
git remote add origin git@github.com:YOUR_GITHUB_USERNAME/real_estate_trust_ledger.git
```

If you need to check it later:

```powershell
git remote -v
```

## Step 7: Push The Initial State

```powershell
git push -u origin main
```

After this, the home machine and GitHub become the authoritative shared source for code and repo-based project memory.

## Optional: GitHub CLI Alternative

If `gh` is installed and authenticated, you can create and push from the command line:

```powershell
gh repo create real_estate_trust_ledger --private --source . --remote origin --push
```

Only use this if:

- GitHub CLI is already installed
- `gh auth login` is already complete

Otherwise, the UI + `git remote add` flow is simpler and safer.

## First-Time Work Machine Setup

On the work machine:

```powershell
git clone git@github.com:YOUR_GITHUB_USERNAME/real_estate_trust_ledger.git
cd real_estate_trust_ledger
```

Then the simplest supported setup path is:

```powershell
.\bootstrap_workstation.ps1
```

That one command will:

- create `.venv`
- upgrade `pip`
- install backend requirements
- install frontend dependencies
- run Alembic migrations
- seed demo data

Start the app from the repo root:

```powershell
.\.venv\Scripts\python run_api.py
.\.venv\Scripts\python run_web.py
```

If you need a more manual setup for debugging or recovery, the script is just automating the older explicit steps and can be inspected directly in `bootstrap_workstation.ps1`.

## Daily Push/Pull Routine

For everyday home/work continuity, the operational source of truth is:

- `docs/WORKSTATION_SYNC.md`

That document covers:

- end-of-day checkpoint routine
- start-of-day routine on the other machine
- new Codex thread bootstrap
- repo-root commands
- what should never be relied on

## Fast Sanity Check Before Every Push

Run this from the repo root:

```powershell
.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold
git status
```

If frontend work changed, also run:

```powershell
Push-Location apps\web
npm test
npm run build
Pop-Location
```

## If The Two Machines Use Different Local Paths

That is fine.

The repository continuity system is path-agnostic as long as:

- both machines use the same Git repository contents
- repo-root commands are used where documented
- the handoff files are updated before switching devices
