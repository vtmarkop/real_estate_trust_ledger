# Staging Run

This is the first hosted-delivery lane for the rebuild. It is intentionally practical: one API container, one worker container, one static web container, PostgreSQL, Redis, and a mounted private-artifact volume.

## What This Sprint Adds

- PostgreSQL-ready API runtime
- Redis-backed worker coordination path
- static web build container
- readiness checks at `/health/ready`
- request-id response headers and structured request logs

## First Run

1. Copy the staging env example:

```powershell
Copy-Item deploy\staging\.env.example deploy\staging\.env
```

2. Start the stack:

```powershell
Push-Location deploy\staging
docker compose up --build -d
Pop-Location
```

3. Run migrations:

```powershell
Push-Location deploy\staging
docker compose exec api python -m alembic upgrade head
Pop-Location
```

4. Optional demo seed:

```powershell
Push-Location deploy\staging
docker compose exec api python dev_seed.py
Pop-Location
```

5. Verify readiness:

- API health: `http://127.0.0.1:8000/health`
- API readiness: `http://127.0.0.1:8000/health/ready`
- Web app: `http://127.0.0.1:8080`

6. Log in as the reviewer or admin and inspect the internal release-readiness panel before calling the stack pilot-ready.

## Important Notes

- The default staging compose example keeps `TRUST_LEDGER_APP_ENV=development` and `TRUST_LEDGER_COOKIE_SECURE=false` so the stack stays usable over plain local HTTP during rehearsal.
- For a real hosted staging environment behind HTTPS, switch to `TRUST_LEDGER_APP_ENV=staging`, set `TRUST_LEDGER_COOKIE_SECURE=true`, and update the public API and web base URLs to their HTTPS values.
- Private artifacts stay on the shared `artifacts_data` volume in this sprint. Object storage comes later in the go-live path.

## Useful Commands

View service logs:

```powershell
Push-Location deploy\staging
docker compose logs -f api worker web
Pop-Location
```

Run one worker cycle manually:

```powershell
Push-Location deploy\staging
docker compose exec worker python apps/worker/run_once.py
Pop-Location
```

Stop the stack:

```powershell
Push-Location deploy\staging
docker compose down
Pop-Location
```
