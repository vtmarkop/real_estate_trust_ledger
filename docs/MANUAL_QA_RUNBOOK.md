# Manual QA Runbook

Date: 2026-04-30

This runbook turns the workflow QA plan into a practical manual testing routine. Use it when you want to test the app by hand and report issues in a way that can be fixed without rediscovering the workflow.

## What To Open

- Manual task checklist: `docs/MANUAL_QA_CHECKLIST.md`
- Result worksheet: `docs/MANUAL_QA_RESULTS.md`
- Strategy and scenario matrix: `docs/WORKFLOW_QA_PLAN.md`
- Current known gaps: `docs/WORKFLOW_GAPS.md`

## Local Start

From the repo root:

```powershell
.\.venv\Scripts\python run_api.py
```

In another terminal:

```powershell
.\.venv\Scripts\python run_web.py
```

Open:

```text
http://127.0.0.1:5173/app
```

## Data Modes

Use the minimal reset for role-boundary and create-from-zero workflows:

```powershell
Push-Location apps\api
..\..\.venv\Scripts\python -m alembic upgrade head
..\..\.venv\Scripts\python dev_reset_minimal_users.py
Pop-Location
```

Use the rich seed for dispute, evidence, score, history, and reviewer workflows:

```powershell
Push-Location apps\api
..\..\.venv\Scripts\python -m alembic upgrade head
..\..\.venv\Scripts\python dev_seed.py
Pop-Location
```

Use one data mode at a time. The minimal reset is destructive for local data. The rich seed is idempotent, but it creates more demo records than the clean four-account reset.

## Minimal Reset Accounts

| Role | Email | Password |
| --- | --- | --- |
| Tenant + Admin | `vasilis.markopoulos@accounts.trustledger.app` | `VasilisTenantAdmin123!` |
| Landlord | `lila.tsoutsoura@accounts.trustledger.app` | `LilaLandlord123!` |
| Agent | `theodore.tsoutsouras@accounts.trustledger.app` | `TheodoreAgent123!` |
| Tenant + Landlord | `froso.evangeliadou@accounts.trustledger.app` | `FrosoTenantLandlord123!` |

## Rich Seed Accounts

| Role | Email | Password |
| --- | --- | --- |
| Tenant | `tenant@demo.trustledger.app` | `DemoTenant123!` |
| Landlord | `landlord@demo.trustledger.app` | `DemoLandlord123!` |
| Agency Owner | `owner@demo-agency.app` | `DemoAgency123!` |
| Internal Reviewer | `reviewer@demo.trustledger.app` | `DemoReviewer123!` |
| Platform Admin | `admin@demo.trustledger.app` | `DemoAdmin123!` |

Seeded trust sharing values:

- Share token: `demo-tenant-share-token`
- Access code: `4829`

## QA Rules

- Run the checklist in order unless a test explicitly says it can be skipped.
- Use the task ID when reporting a failure, for example `QA-08 failed at step 7`.
- Fill `docs/MANUAL_QA_RESULTS.md` as you test.
- Switch language to Greek for the dedicated localization pass, not during every workflow unless the task asks for it.
- Use dummy data with the `QA` prefix so new records are easy to identify.
- After a create/update action, look for visible feedback, changed status, and the next handoff. A silent success is still a UX issue.
- Watch for console errors, React key warnings, hook warnings, inaccessible buttons, clipped hover bubbles, and horizontal overflow.
- If a task creates data that blocks a later task, keep going and record the state instead of deleting local data mid-run.

## Severity Labels

- `S1`: blocker; cannot complete the workflow or role data leaks badly.
- `S2`: major; workflow completes only with confusing hidden steps or wrong role visibility.
- `S3`: medium; wording, visual hierarchy, missing confirmation, or awkward but recoverable flow.
- `S4`: polish; small visual, translation, spacing, or hover/focus issue.

## Completion Definition

Manual QA is complete when:

- all checklist rows are marked `Pass`, `Fail`, `Blocked`, or `Skipped`,
- every `Fail` or `Blocked` row has a short reproduction note,
- every issue has a severity,
- screenshots are saved for visual bugs,
- `docs/WORKFLOW_GAPS.md` is updated for any workflow-level failure.

## What Not To Treat As A Bug

- The minimal reset has no properties, tenancies, organizations, or rich demo history until you create them.
- The rich seed accounts are not available immediately after the minimal reset.
- A landlord cannot publish an agency-managed property from landlord mode.
- An agency cannot create a tenancy from an accepted application until agency inventory is linked to an existing landlord owner.
- `Landlord-side score` is the signed-in user's own landlord/property-owner dimension, not a score for the tenant's current landlord.

