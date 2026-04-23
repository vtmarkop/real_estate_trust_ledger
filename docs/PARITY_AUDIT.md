# Parity Audit

This document records the post-Sprint-17 audit that compared:

- the archived legacy MVP in `archive/mesitis-mvp-2026-04-09/`, and
- the rebuilt platform under `apps/`.

It also records the follow-up remediation pass that closed the highest-value parity gaps before the visual redesign track begins.

## Executive Summary

The rebuilt app now covers the important operational intent of the archived MVP and goes beyond it in most areas.

In plain language:

- the old app's main workflows are present in the rebuilt app,
- the rebuilt app has broader role support and stronger workflow safety,
- the rebuilt app now exposes the important backend workflows through the frontend rather than leaving them API-only,
- a few low-level helper endpoints remain intentionally indirect because they are transport endpoints used by higher-level UI actions.

The biggest remediation items completed in this audit pass were:

- real uploaded document support for payment, deposit, and maintenance operations,
- single-session revoke in the account workspace,
- cleanup actions for internal automation tasks,
- written parity mapping between the archive MVP and the rebuilt platform.

## Legacy MVP To Rebuild Mapping

### Login And Session Access

Legacy MVP:
- login page

Rebuild equivalent:
- `Auth`
- `Account`

What changed:
- the rebuilt app keeps login,
- adds session lists,
- adds sign-in event history,
- adds revoke-other-sessions,
- now also adds single-session revoke.

### Landlord Dashboard

Legacy MVP:
- one landlord dashboard page

Rebuild equivalent:
- `Home`
- `My Trust`
- `Rent & Issues`
- `Agency Tools`
- `Review Center` for internal staff only

What changed:
- the rebuild splits the old dashboard into role-appropriate work areas,
- this is broader than the MVP but closer to a real operational product.

### Properties

Legacy MVP:
- landlord property management

Rebuild equivalent:
- `Rental Records` for tenancy-linked property context,
- `Agency Tools` for agency portfolio management,
- custom property tags and fast filtering.

What changed:
- properties are now reusable domain records,
- agencies can tag and filter them,
- tenancies keep their own address snapshot and property linkage.

### Payments

Legacy MVP:
- payment records and proof flow

Rebuild equivalent:
- `Rent & Issues`

What changed:
- payment creation, proof submission, confirmation, and rejection are all present,
- payment proof can now use real private uploaded artifacts,
- proof files can now be reopened from the UI using signed access.

### Tickets

Legacy MVP:
- maintenance/dispute tickets

Rebuild equivalent:
- `Rent & Issues`
- `Dispute desk`

What changed:
- maintenance tickets now live beside payment and deposit operations,
- disputes are surfaced in a dedicated desk instead of being hidden inside separate record lists,
- report and resolution evidence can now use real private uploaded artifacts.

### Assign Judge

Legacy MVP:
- assign a judge to a property

Rebuild equivalent:
- `Review Center`
- internal reviewer/admin workflow

What changed:
- this was not ported 1:1 on purpose,
- the rebuild replaces per-property judge assignment with centralized internal review, audit, and queue control,
- this is an intentional architectural replacement rather than a missing feature.

## Backend To Frontend Parity Verdict

## User And Tenant/Landlord Workflows

Implemented in the frontend:

- auth register/login/logout,
- current-session and session-history visibility,
- single-session revoke,
- revoke all other sessions,
- trust score and trust history views,
- trust-report sharing and revocation,
- access history for shared trust reports,
- tenancy creation by counterparty email,
- tenancy confirmation,
- tenancy review request,
- tenancy evidence upload,
- history import creation and submission,
- reference request creation and fulfillment,
- listing browse and application flows,
- payments,
- deposit handling,
- maintenance handling,
- dispute submission.

## Agency Workflows

Implemented in the frontend:

- property creation,
- property tags,
- portfolio filtering,
- membership/team management,
- listing creation and status updates,
- application review,
- threshold updates,
- trust check validation,
- trust profile preview,
- saved trust checks,
- commercial overview metrics.

## Internal Reviewer/Admin Workflows

Implemented in the frontend:

- tenancy review queue,
- evidence review queue,
- history import review queue,
- score refresh queueing,
- immediate recalculation,
- score batch queueing,
- follow-up creation,
- automation claim,
- automation execute/process,
- automation cleanup for expired consent reminders,
- automation cleanup for stale follow-ups,
- worker-run visibility,
- audit-log visibility,
- release-readiness visibility.

## Intentionally Indirect Backend Endpoints

The following are considered implemented through higher-level frontend workflows rather than direct raw buttons:

- signed artifact download `GET` endpoints:
  - the UI uses the safer access-creation `POST` endpoints first, then opens the signed URL,
- raw artifact access helper endpoints:
  - these are now exercised from `Rental Records` and `Rent & Issues`,
- some internal UUID-oriented APIs:
  - the UI usually exposes the workflow through email-based or queue-based actions instead of asking operators to provide raw IDs.

That means these endpoints are not "missing" in product terms even if they are not each represented by a literal standalone form.

## Real-World Workflow Checks

The rebuilt app now behaves more like a real operational product in these areas:

### Private Evidence Handling

- documents are uploaded as stored artifacts,
- artifacts are private by default,
- downloads use signed short-lived access,
- operational records can now link real uploaded files instead of only free-text names.

Examples:
- payment proof receipt,
- deposit settlement statement,
- maintenance report photo,
- maintenance resolution report.

### Account Safety

- users can inspect active sessions,
- users can sign out of all other devices,
- users can now sign out one stale device at a time.

### Dispute Handling

- deposit disputes are visible,
- maintenance disputes are visible,
- disputable items are surfaced in a single dispute desk,
- open disputes are easier to find than they were in the archived MVP.

### Agency Daily Use

- agencies can manage a property portfolio,
- agencies can tag estates with custom labels,
- agencies can filter quickly without searching every property manually.

## Honest Caveats

This audit does not claim that the rebuilt app is already visually polished to the level planned for Sprint 18 through Sprint 20.

It also does not claim that every backend helper endpoint has a one-button UI for its raw transport form.

What it does claim, accurately, is this:

- the important workflows from the archived MVP are present,
- the rebuilt backend's important user-facing and operator-facing workflows now have frontend paths,
- the app now behaves more like a real product in operations that depend on documents, disputes, and session control.

## Result Of The Remediation Pass

The parity/remediation checkpoint added:

- operational artifact links in payments, deposits, and maintenance,
- web upload/open flows for those artifacts,
- single-session revoke in the account page,
- automation cleanup controls in the internal workspace,
- regression tests that protect the new artifact-linked operational workflows.

This checkpoint is the handoff point before Sprint 18 begins.
