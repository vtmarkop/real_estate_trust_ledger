# User Acceptance Testing

Sprint 15 adds the first explicit UAT lane for the rebuilt platform.

## Goal

Confirm that the rebuilt web app, API, worker, and seeded demo dataset behave coherently enough for a first hosted pilot rehearsal.

## Recommended Test Environment

- use the staged stack from [STAGING_RUN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/STAGING_RUN.md) when possible,
- use the local demo path from [LOCAL_RUN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/LOCAL_RUN.md) for quick regression and walkthroughs,
- run the release-readiness check before sign-off.

## Acceptance Passes

### Pass 1: Identity And Session Safety

- register a fresh user,
- log in and confirm the workspace loads,
- inspect the security page for active sessions and security events,
- revoke another session and confirm the revoked session loses access.

### Pass 2: Tenant Trust Record Management

- log in as the seeded tenant,
- confirm the records page shows live tenancy history,
- upload evidence,
- create or review a history import,
- request a counterparty reference and fulfill one from the landlord side.

### Pass 3: Trust Sharing And Agency Screening

- issue a trust-report consent from the tenant trust page,
- validate the seeded share token and access code from the agency workbench,
- preview the trust profile,
- create a trust check,
- confirm the tenant access-history view reflects the agency action.

### Pass 4: Agency Publishing And Applicant Flow

- create or update a property,
- publish or edit a listing,
- change listing screening thresholds,
- submit an application from an eligible account,
- move the application through the allowed agency statuses.

### Pass 5: Operational Rental Ledger

- create or confirm a payment record,
- submit payment proof and counterparty decision,
- open and settle a deposit record, then dispute it,
- create, acknowledge, resolve, and dispute a maintenance ticket.

### Pass 6: Internal Operations And Pilot Checks

- review tenancy, evidence, and history-import queues,
- inspect automation, notifications, worker runs, and audit activity,
- inspect the release-readiness panel in the internal workspace,
- confirm there are no unexpected blocking issues before sign-off.

## Sign-Off Criteria

- no blocking API or web errors during the walkthrough,
- no unexplained worker failures,
- release readiness reports zero blocking issues,
- any warnings are explicitly accepted by the operator team,
- demo or staging data matches the expected test script.
