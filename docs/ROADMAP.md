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

The original launch-critical roadmap is complete, and Sprint 17 has now closed the first frontend-parity/operator-clarity lane.

The next roadmap lane is focused on operator experience, bilingual usability, visual polish, and frontend parity. This is intentionally additive: it should improve usability and brand perception without reopening the core trust, scoring, security, or automation architecture.

### Sprint 17

Frontend parity and information architecture:

- completed record-creation parity for tenancy creation by counterparty email,
- completed estate portfolio helpers with custom tags and fast filtering,
- completed agency team-access management from the web app with email-based membership adds and role/access updates,
- completed internal operator parity for score refresh controls, follow-up creation, automation execution, and score-batch visibility,
- completed a clearer dispute desk in the operational workspace so disputable items and open disputes are visible at a glance,
- upgraded private evidence storage from a local-only assumption to a pluggable local-private or S3-compatible/MinIO-ready lane while preserving signed API-controlled access,
- laid the structural foundation for Sprint 18 compact-mode work by improving information architecture before the visual redesign.

### Post-Sprint-17 Parity Remediation Checkpoint

Archive-vs-rebuild audit and parity hardening:

- verified that the important archive MVP workflows are represented in the rebuild, with intentional replacement of the old judge model by the internal reviewer/admin model,
- completed document-backed operational uploads for payments, deposits, and maintenance flows,
- completed artifact reopening from operational records through signed access URLs,
- completed single-session revoke in the account workspace,
- completed internal cleanup controls for expired consent reminders and stale follow-up tasks,
- added written parity documentation before moving into Sprint 18 visual/design work.

### Sprint 18: Bilingual Frontend Localization

Bilingual frontend localization:

- add a reusable frontend language layer instead of one-off translated screens,
- ship a visible English/Greek switcher that works in both public and authenticated surfaces,
- translate the rebuilt frontend text surface into Greek while preserving English as a supported language,
- localize common frontend error presentation and locale-aware number formatting before the visual redesign begins.

### Pre-Sprint-19 Documentation And Consistency Checkpoint

Documentation and consistency hardening:

- add a full technical codebase reference covering models, schemas, services, routes, worker runtime, frontend pages, and seeded workflows,
- correct documentation inconsistencies uncovered during the scan,
- align runtime stage/status markers with the actual rebuild checkpoint,
- make the next visual sprint easier to enter without rediscovering the current architecture from scratch.

### Post-Sprint-18 Workflow Simplification Checkpoint

Workflow and separation-of-concerns hardening:

- split the densest frontend workspaces into focused lanes so users work in one operational concern at a time,
- finish the agency and internal workspace separation pattern started in records and operations,
- add a dedicated workflow map that traces the main business flows from backend models/services/routes into frontend pages and sections,
- reduce cross-lane cognitive overload before starting visual redesign work.

### Post-Sprint-18 Workflow Diagram Checkpoint

Visual workflow traceability:

- add Mermaid diagrams for the main implemented product workflows instead of relying on prose alone,
- make role handoffs, dispute escalation, and review responsibilities easier to understand at a glance,
- keep the diagrams aligned with the current rebuild rather than the original archive assumptions.

### Sprint 19: Compact Workspace And Cinematic Visual System

Compact workspace and cinematic design system:

- introduce density tokens and a compact view option for operational pages,
- redesign the color system around deep neutrals, controlled red accents, stronger contrast, and media-like depth,
- add typography, spacing, elevation, and hover-state rules that feel more premium and modern,
- take inspiration from Netflix's cinematic clarity and confident contrast without copying Netflix branding or product patterns literally.

Completed checkpoint notes:

- the shell now exposes a real compact/comfortable density toggle,
- spacing is now driven by shared density tokens rather than fixed values alone,
- the visual system now uses a darker cinematic palette with clearer panel hierarchy and stronger active states,
- the next sprint can focus on page-by-page conversion instead of inventing the base style system.

### Sprint 20: Page-by-page Visual Conversion

Page-by-page visual conversion:

- apply the new compact/cinematic design system to home, trust, records, operations, agency, and internal pages,
- improve card hierarchy, filters, tables, and action placement for faster scanning,
- add denser list and queue treatments for agencies and reviewers,
- preserve role-based clarity while making the product feel more polished and cohesive.

Completed checkpoint notes:

- user-facing pages now separate discovery, sharing, history, and security activity more cleanly through focused section tabs,
- operator-heavy pages now expose richer top-level summaries so agencies and reviewers can scan live workload faster,
- the cinematic shell is now reflected in the actual page compositions instead of only in shared design tokens,
- the language-switch layer was refactored after the visual pass so the live English/Greek toggle updates correctly during render and covers much more of the visible workspace copy,
- a surgical UI-semantics pass then differentiated status badges, fact pills, notes, and timeline-style activity across the remaining dense pages so operational cards are more self-explanatory at a glance.

### Post-Sprint-20 Cross-Device Continuity Checkpoint

Cross-device continuity and durable handoff system:

- add a repo-level operating guide for future agent threads,
- add a live handoff file that records the exact current checkpoint and next actions,
- add a workflow-gap tracker for incomplete or confusing real-world flows,
- add a workstation sync guide so daily home/work machine transitions do not depend on chat memory alone.

### Post-Sprint-20 GitHub Bootstrap Checkpoint

Repository publication and machine-to-machine bootstrap hardening:

- prepare the repo for a first private GitHub push under the selected project name,
- exclude local-only databases and artifact storage from version control,
- add a dedicated GitHub bootstrap guide so the repository can be reconnected cleanly on any new machine,
- fold the full project/chat handoff routine into repo docs so the workflow is repeatable by either a human or a future AI thread.

### Sprint 21: Motion, Accessibility, And Release Polish

Motion, accessibility, and release polish:

- add intentional transitions and state changes instead of abrupt interface jumps,
- verify accessibility contrast, focus treatment, keyboard behavior, and responsive behavior,
- document the design system and compact mode rules,
- close with a visually upgraded, production-safe frontend release candidate.
