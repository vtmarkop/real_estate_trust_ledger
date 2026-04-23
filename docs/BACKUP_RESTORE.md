# Backup And Restore

Sprint 14 adds the first practical backup and restore runbook for the staged PostgreSQL path.

## Backup

Create a timestamped PostgreSQL dump from the staging compose stack:

```powershell
New-Item -ItemType Directory -Force deploy\staging\backups | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
Push-Location deploy\staging
docker compose exec -T postgres pg_dump -U $env:POSTGRES_USER -d $env:POSTGRES_DB -Fc > ".\\backups\\trustledger-$stamp.dump"
Pop-Location
```

What to keep with the dump:

- the `.dump` file
- the matching `deploy\staging\.env`
- the current app image tags or commit reference

## Restore Drill

1. Stop services that write to the database.
2. Create a fresh empty database target.
3. Restore the dump.
4. Start the API and worker again.
5. Verify readiness and smoke-test the demo accounts.

Example restore command:

```powershell
Push-Location deploy\staging
docker compose exec -T postgres pg_restore -U $env:POSTGRES_USER -d $env:POSTGRES_DB --clean --if-exists ".\\backups\\trustledger-YYYYMMDD-HHMMSS.dump"
Pop-Location
```

## Restore Verification Checklist

- `http://127.0.0.1:8000/health/ready` returns `ready`
- the web app loads at `http://127.0.0.1:8080`
- tenant and reviewer demo logins succeed
- trust score history loads
- agency dashboard loads
- worker can complete one cycle without failures

## What This Runbook Does Not Cover Yet

- off-site backup retention
- encrypted backup storage
- object-storage backup strategy for private artifacts
- point-in-time recovery

Those are still later hardening work, but this sprint gives us a truthful restore drill for the staged database path.
