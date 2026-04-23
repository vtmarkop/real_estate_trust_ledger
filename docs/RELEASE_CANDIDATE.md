# Release Candidate Runbook

Sprint 15 adds the first monitored release-candidate path for the rebuilt platform.

## Pre-Flight Verification

From the repo root:

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -p "test_*.py"
Push-Location apps\web
npm run build
Pop-Location
Push-Location apps\api
..\..\.venv\Scripts\python -m alembic upgrade head
Pop-Location
.\.venv\Scripts\python apps\worker\run_once.py
```

## Hosted Rehearsal Flow

1. Start the staged stack from [STAGING_RUN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/STAGING_RUN.md).
2. Run migrations.
3. Seed demo data only if the environment is still a rehearsal environment.
4. Verify `/health/ready`.
5. Log in to the internal workspace and review the pilot release-readiness panel.
6. Confirm the latest worker run completed and there are no unaccepted blocking issues.

## Go / No-Go Checklist

- regression suite passed,
- web build passed,
- database migration passed,
- worker one-shot run passed,
- `/health/ready` returns ready,
- release-readiness reports zero blocking issues,
- UAT from [UAT.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/UAT.md) is signed off,
- security review from [SECURITY_REVIEW.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/SECURITY_REVIEW.md) is signed off.

## Rollback Direction

- stop write traffic,
- restore the latest verified PostgreSQL backup using [BACKUP_RESTORE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/BACKUP_RESTORE.md),
- restart API and worker,
- verify `/health/ready`,
- rerun one worker cycle,
- confirm the internal release-readiness view is back in an acceptable state.
