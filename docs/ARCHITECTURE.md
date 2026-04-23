# Target Architecture

## Product Shape

Trust Ledger is an evidence-verified rental trust platform for:

- tenants,
- landlords,
- agencies,
- internal reviewers/admins.

The system will support cold-start onboarding without bank APIs by using uploaded evidence, counterparty confirmation, reviewer verification, and automation.

## Delivery Principles

- Monolith first, not microservices first.
- Web first, mobile-responsive first, native mobile later if still needed.
- Structured audit events instead of free-form timeline strings.
- One central scoring engine module.
- Consent-first access to trust reports.
- Security defaults must be production-grade from the beginning.

## Runtime Topology

The rebuild will target this shape:

- `apps/web`: React web application for tenants, landlords, agencies, and admins.
- `apps/api`: FastAPI application exposing the product API.
- `apps/worker`: background jobs for automation, notifications, recalculation, and cleanup.
- `PostgreSQL`: primary relational datastore.
- `Redis`: queue and short-lived coordination/cache.
- `Object Storage`: documents and evidence files.

## Core Domains

The platform will be organized around these domains:

- Identity and Access
- Organizations and Agency Membership
- Properties and Listings
- Tenancies and Lease Periods
- Applications and Screening
- Documents and Verification
- Trust Ledger and Audit Events
- Payments and Deposit Flows
- Maintenance Tickets and Disputes
- Consents and Shared Reports
- Automation and Notifications
- Scoring and Verification Strength

## Verification Model

Trust events will carry a verification state:

- `self_reported`
- `counterparty_confirmed`
- `reviewed`
- `verified`

The system must never treat weak evidence the same as strong evidence.

## Scoring Model

The scoring engine will be centralized and deterministic.

Outputs:

- `tenant_score`
- `landlord_score`
- `verification_strength`

Rules:

- New users start neutral, not at zero.
- Verified history matters more than self-reported history.
- Disputes do not create permanent trust damage until confirmed or resolved.
- Score mutations must be written through structured audit events.

## Security Baseline

- Environment-based secrets only.
- HTTPS-only production deployment.
- Secure cookies in production.
- RBAC on every protected route.
- Consent checks for every agency trust check and report view.
- Signed/private access for sensitive files.
- Full audit trail for verification, consent, and score-impacting actions.

## Why The Legacy MVP Was Archived

The old MVP remains useful for product flow reference, but it is not a safe foundation for the full rebuild because it contains MVP shortcuts in auth, storage, schema evolution, and score handling.
