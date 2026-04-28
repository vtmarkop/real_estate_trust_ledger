# Roadmap

## Completed Delivery Track

### Sprint 0

Foundation reset, repo split, architecture definition, workspace scaffold, baseline tests.

### Sprint 1

Identity, sessions, organizations, memberships, RBAC, admin/reviewer role model, and consent primitives.

### Sprint 2

Properties, tenancies, trust events, listings, applications, and the first trust-profile summary signals.

### Sprint 3

Cold-start onboarding through evidence import, reference collection, and reviewer verification flows.

### Sprint 4

Central scoring engine, verification strength, score history, and queued recalculation foundations.

### Sprint 5

Operational trust flows: payments, deposits, maintenance tickets, and dispute-ready operational history.

### Sprint 6

Agency screening product: score-aware listing thresholds, application score snapshots, and dashboard rollups.

### Sprint 7

Automation layer: reminders, follow-up tasks, scheduled score refreshes, and durable queue records.

### Sprint 8

Enterprise hardening: audit logs, trust-sharing access history, consent lockouts, session controls, and login lockouts.

### Sprint 9

Worker runtime: synchronous queue execution, worker-run records, and internal operations overview.

### Sprint 10

Web app foundation and workflows: live shell, marketplace, records, trust, agency, internal operations, and operational ledger UI.

### Sprint 11

Demo and local live path: reconciled roadmap docs, added seeded live-demo data, and made the rebuilt app easy to run and inspect locally.

### Sprint 12

Evidence artifacts and storage: added private local artifact storage, signed short-lived retrieval, evidence artifact upload flows, and web support for uploaded proof files.

### Sprint 13

Deployment runtime foundations: added shared runtime env handling across API and worker lanes, Redis-ready worker coordination, durable notification deliveries, and staging-friendly web/API runtime configuration.

### Sprint 14

Hosted delivery lane: added component readiness checks, structured request logging with request IDs, a first PostgreSQL/Redis/web staging compose shape, and practical staging backup/restore runbooks.

### Sprint 15

Pilot go-live hardening: added a live internal release-readiness surface, baseline API security headers, UAT/security/release-candidate runbooks, and the first monitored cutover checklist for a narrow hosted pilot.

### Sprint 16

Post-pilot expansion: added a PWA-ready web shell, mobile-oriented shell polish, and agency commercial-overview analytics while keeping the pilot-grade core unchanged.

## Post-Pilot Experience Track

The original launch-critical roadmap is complete through Sprint 16.

This file stays summary-only. Detailed sprint history and checkpoint notes belong in `docs/SPRINTS.md`.

The current roadmap lane is intentionally additive: improve operator clarity, bilingual usability, score transparency, visual polish, and release readiness without reopening the core trust, scoring, security, or automation architecture.

### Sprint 17

Frontend parity and information architecture for records, agency, internal operations, dispute visibility, and evidence-backed operator flows.

### Post-Sprint-17 Parity Remediation Checkpoint

Archive-vs-rebuild parity audit, operational upload parity, artifact reopen flows, single-session revoke, and internal cleanup controls.

### Sprint 18: Bilingual Frontend Localization

Reusable English/Greek frontend localization, live language switching, localized error presentation, and locale-aware formatting.

### Pre-Sprint-19 Documentation And Consistency Checkpoint

Codebase reference, documentation cleanup, and checkpoint alignment before the visual redesign track.

### Post-Sprint-18 Workflow Simplification Checkpoint

Focused workspace lanes, stronger separation of concerns, and a workflow map that traces backend logic into frontend use.

### Post-Sprint-18 Workflow Diagram Checkpoint

Mermaid diagrams for the implemented workflows so role handoffs and review paths are visible at a glance.

### Sprint 19: Compact Workspace And Cinematic Visual System

Compact workspace foundations, density tokens, and a cinematic visual system with stronger hierarchy and heavier operational clarity.

### Sprint 20: Page-by-page Visual Conversion

Page-by-page application of the visual system, richer summaries, better scanability, broader localization coverage, and clearer UI semantics.

### Post-Sprint-20 Cross-Device Continuity Checkpoint

Repo-resident handoff, workflow-gap tracking, and workstation sync guidance for cross-device continuity.

### Post-Sprint-20 GitHub Bootstrap Checkpoint

Private GitHub publication and machine-to-machine bootstrap hardening for reliable repo recovery on a new workstation.

### Post-Sprint-20 Archive-Alignment UX Reset

Object-first repair work on the rebuilt presentation layer: selected-property operations, create-new versus existing-record separation, compact payment/issue targeting, strict separation between daily actions and read-only timelines, role-wide history/log lane separation, explicit account workspace-role entitlements for tenant/landlord/agent/admin visibility, sidebar-only role switching after login, fixed compact shell density, a local account-only reset path, clearer role-specific score wording, and completed v1 score-contribution transparency.

### Sprint 21: Motion, Accessibility, Score Transparency, And Release Polish

Score-contribution explainability is complete for the first Sprint 21 slice across `My Trust`, agency trust previews, and internal scoring controls. A Greek localization quality pass is also complete for likely visible web workspace copy, including the archive-reset role, history, score, operations, agency, and internal surfaces. The remaining Sprint 21 lane is motion, accessibility, responsive behavior, design-system documentation, live Greek/English visual review with seeded data, and release-level frontend polish.
