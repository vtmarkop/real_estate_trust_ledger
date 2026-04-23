# Security Review

Sprint 15 adds the first explicit pre-pilot security review checklist for the rebuild.

## Controls Already In Place

- server-side session auth with revocation and session visibility,
- temporary lockouts for repeated invalid login attempts and invalid trust-report access-code attempts,
- private evidence artifact storage with signed short-lived access URLs,
- append-only audit logs for sensitive actions,
- structured request logs with request IDs,
- readiness checks for database, artifact storage, and Redis-backed worker coordination,
- secure-cookie and HTTPS validation in non-development runtime settings.

## Pre-Pilot Checklist

- replace all development secrets with environment-managed secrets,
- run with `TRUST_LEDGER_APP_ENV=staging` or `production`,
- set `TRUST_LEDGER_COOKIE_SECURE=true`,
- set HTTPS public API and web base URLs,
- use PostgreSQL instead of SQLite,
- use Redis-backed worker coordination,
- confirm `/health/ready` is healthy,
- confirm `/api/v1/internal/release-readiness` reports zero blocking issues,
- confirm security headers are present on API responses,
- verify backup and restore drill status from [BACKUP_RESTORE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/BACKUP_RESTORE.md).

## Known Gaps Before A Wider Rollout

- notification transport still terminates in structured logs instead of a hosted email provider,
- private evidence storage is still volume-backed in the staging lane instead of using production object storage,
- off-site encrypted backup retention is not yet implemented,
- external perimeter controls such as WAF/rate-limiting infrastructure are still deployment responsibilities, not app-owned controls.

## Review Outcome Rule

Do not proceed to a hosted pilot if the release-readiness endpoint reports blocking issues in addition to any unresolved high-risk security findings.
