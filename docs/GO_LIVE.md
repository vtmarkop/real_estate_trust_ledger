# Go-Live Path

## What "Live" Means Today

Today, the rebuilt platform can be run live as a local demo with real backend and frontend code, seeded domain data, and repeatable verification.

Use [LOCAL_RUN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/LOCAL_RUN.md) for that path.

## Path To A Real Hosted Pilot

### Stage 1: Local Demo

Current status:

- rebuilt API, worker, and web lanes exist,
- end-to-end domain flows exist for identity, tenancies, evidence, scoring, operations, screening, automation, and auditability,
- seeded local demo path exists for fast product review.

### Stage 2: Staging-Ready Platform

Current status:

- Sprint 14 is complete,
- a staging-shaped delivery lane now exists with compose-managed API, worker, web, PostgreSQL, Redis, and private artifact volume support,
- `/health/live` and `/health/ready` now expose runtime state for staged verification,
- request IDs and structured request logs now exist for API traffic review,
- practical staging run and PostgreSQL backup/restore runbooks now live in [STAGING_RUN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/STAGING_RUN.md) and [BACKUP_RESTORE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/BACKUP_RESTORE.md).

Still needed before an internet-facing staging environment:

- HTTPS hostnames and secure cookie settings,
- managed PostgreSQL and Redis instead of local compose data volumes,
- production-grade private object storage for evidence artifacts,
- hosted secret management and monitoring.

### Stage 3: Pilot Release Candidate

Current status:

- Sprint 15 is complete,
- a monitored release-candidate path now exists in [RELEASE_CANDIDATE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/RELEASE_CANDIDATE.md),
- UAT and security sign-off guides now live in [UAT.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/UAT.md) and [SECURITY_REVIEW.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/SECURITY_REVIEW.md),
- the internal workspace now exposes a live release-readiness panel for pilot go/no-go review.

Still recommended before a broader rollout:

- move notification delivery from log transport to a real provider,
- move artifact storage from a mounted volume to hosted object storage,
- add off-site encrypted backup retention and stronger perimeter controls.

## Recommended Hosting Shape

For the first serious hosted pilot:

- `apps/api` on a small Linux VM or container service,
- `apps/worker` on the same environment or a sibling worker process,
- `apps/web` as a static build behind HTTPS,
- managed PostgreSQL,
- Redis for worker coordination,
- S3-compatible private object storage for evidence files.

## Honest Current Boundary

The rebuilt app is ready for local live review, staging rehearsal, and a narrow hosted pilot with an explicit release-candidate checklist.

Sprint 16 is complete and stays additive. It improved mobile/PWA experience and agency commercial visibility, but it did not become part of the launch-critical path for the current pilot-grade core.
