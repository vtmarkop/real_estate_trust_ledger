# Local Run

This is the fastest way to see the rebuilt app live today.

If you want the same product in a staging-shaped runtime with PostgreSQL, Redis, and containerized web delivery, use [STAGING_RUN.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/STAGING_RUN.md).

If you want a plain-language guide to what each menu item and workflow means once the app is running, use [WORKSPACE_GUIDE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKSPACE_GUIDE.md).

## What You Get

After the steps below, you will have:

- the rebuilt API running at `http://127.0.0.1:8000`,
- the rebuilt web app running at `http://127.0.0.1:5173`,
- seeded demo users, trust history, screening data, operations data, and trust-sharing data.

This local path currently uses SQLite for speed.
Uploaded evidence artifacts are stored privately and opened through signed API URLs rather than public static paths.

By default, local run uses private filesystem storage under `apps\api`.
If you want a more production-like evidence lane locally, the app can also use S3-compatible object storage such as MinIO without changing the user-facing evidence workflow.

## First-Time Setup

From the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r apps\api\requirements.txt
Copy-Item apps\api\.env.example apps\api\.env
```

Install the web dependencies:

```powershell
Push-Location apps\web
npm install
Copy-Item .env.example .env
Pop-Location
```

## Prepare The Database

Run migrations and seed the demo dataset:

```powershell
Push-Location apps\api
..\..\.venv\Scripts\python -m alembic upgrade head
..\..\.venv\Scripts\python dev_seed.py
Pop-Location
```

The seed is idempotent, so you can run `dev_seed.py` again without duplicating the main demo records.

## Start The API

The safest API start command is now the repo-root launcher:

```powershell
.\.venv\Scripts\python run_api.py
```

That command works from the repo root and avoids import-path issues caused by launching `uvicorn` from the wrong directory.

If you prefer the app-folder command, this still works too:

```powershell
Push-Location apps\api
..\..\.venv\Scripts\python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Keep that terminal open.

## Start The Web App

Open a second terminal. The safest frontend start command is now the repo-root launcher:

```powershell
.\.venv\Scripts\python run_web.py
```

That command works from the repo root and avoids needing to change into `apps\web` first.

If you prefer the app-folder command, this still works too:

```powershell
Push-Location apps\web
npm run dev
```

Open `http://127.0.0.1:5173`.

## Optional Worker Check

Open a third terminal if you want to execute one worker cycle manually:

```powershell
.\.venv\Scripts\python apps\worker\run_once.py
```

If you want to keep the worker alive in a staging-like loop instead:

```powershell
.\.venv\Scripts\python apps\worker\run_service.py
```

The worker now resolves shared runtime settings from `apps\api\.env`, so repo-root worker commands and API commands use the same database, artifact, notification, and coordination settings.

## Optional MinIO / S3-Compatible Evidence Storage

If you want to test the evidence system against object storage instead of the default local-private backend, update `apps\api\.env` with values like these:

```env
TRUST_LEDGER_ARTIFACT_STORAGE_BACKEND=s3_compatible
TRUST_LEDGER_ARTIFACT_S3_BUCKET_NAME=trust-ledger-artifacts
TRUST_LEDGER_ARTIFACT_S3_REGION=us-east-1
TRUST_LEDGER_ARTIFACT_S3_ENDPOINT_URL=http://127.0.0.1:9000
TRUST_LEDGER_ARTIFACT_S3_ACCESS_KEY_ID=minio
TRUST_LEDGER_ARTIFACT_S3_SECRET_ACCESS_KEY=minioadmin
TRUST_LEDGER_ARTIFACT_S3_USE_SSL=false
TRUST_LEDGER_ARTIFACT_S3_FORCE_PATH_STYLE=true
```

Example:
- if you run MinIO locally on `127.0.0.1:9000`, the API will upload evidence there,
- users will still open files through the app,
- the API will redirect them to a short-lived signed object-storage URL.

If you switch storage backend settings, restart the API before testing uploads again.

## Demo Accounts

- `Tenant`: `tenant@demo.trustledger.app` / `DemoTenant123!`
- `Landlord`: `landlord@demo.trustledger.app` / `DemoLandlord123!`
- `Agency Owner`: `owner@demo-agency.app` / `DemoAgency123!`
- `Internal Reviewer`: `reviewer@demo.trustledger.app` / `DemoReviewer123!`
- `Platform Admin`: `admin@demo.trustledger.app` / `DemoAdmin123!`

Pre-seeded trust-sharing values:

- share token: `demo-tenant-share-token`
- access code: `4829`

Pre-seeded workflow coverage:

- `Harbor Flat`: a live assigned property with an active tenancy, confirmed rent, held deposit, resolved maintenance, uploaded evidence, and a fulfilled landlord reference.
- `Old Town Duplex`: a closed tenancy with verdict-issued payment, deposit, and maintenance disputes so you can test appeal-ready reviewer outcomes.
- `Hillside Studio`: a closed tenancy with payment, deposit, and maintenance cases still under review so the `Review Center` queues are populated immediately.
- `Agency Showcase Loft`: an agency-managed property and listing for screening, application, and property-tag workflows.

## Suggested Walkthrough

Start with the tenant account:

- `Home`: confirm live score and organization discovery behavior.
- `Home`: try the install panel on a browser that offers a PWA install prompt.
- `Rental Records`: review the active tenancy, imported history, evidence, and reference request trail.
- `Rental Records`: inspect the assigned `Harbor Flat`, the verdict-ready `Old Town Duplex`, and the review-queue `Hillside Studio` records.
- `Rental Records`: create a tenancy by counterparty email and upload a fresh evidence document to prove the end-to-end upload flow.
- `My Trust`: inspect score history, ledger events, consent sharing, and access history.
- `Rent & Issues`: inspect payment, deposit, maintenance, the dispute desk, and the verdict-ready appeal flows.

Then use the agency owner account:

- `Agency Tools`: inspect the dashboard, listing, application, and seeded trust-check history.
- `Agency Tools`: inspect the business snapshot and screening metrics.
- `Agency Tools`: add or edit a property tag, inspect the assigned estate portfolio, and inspect the `Team access` section.
- validate the seeded share token and access code from the trust-check panel,
- change listing lifecycle or screening thresholds to prove the live operator flow.

Then use the reviewer account:

- `Review Center`: inspect the overview, verdict-ready queues, queue a score refresh by email, create a manual follow-up task, inspect due automation tasks, and review the release-readiness panel.

## Fast Reset Strategy

If you want a clean local demo database again, delete `apps\api\trust_ledger.db`, rerun the migration command, and rerun `dev_seed.py`.
