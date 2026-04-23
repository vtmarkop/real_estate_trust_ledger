# Worker App

This folder will contain background job processing for:

- scheduled score recalculation,
- reminders,
- reviewer queues,
- document expiry checks,
- report generation,
- cleanup and maintenance automation.

Status: runtime service foundations implemented.

Current capabilities:

- claim due automation tasks,
- coordinate worker execution with an optional Redis-backed lease,
- execute due automation tasks,
- queue and dispatch notification deliveries created by runtime automation,
- claim and process due score recalculation requests with attempt tracking,
- clean expired consent reminders and stale follow-up tasks before claiming executable work,
- append audit logs for worker claim, execution, cleanup, and score processing,
- persist structured worker-run records for internal operational review,
- run one worker cycle from `worker/main.py`,
- run as a long-lived service loop from `run_service.py`.

Quick local run from repo root:

```powershell
.\.venv\Scripts\python apps\worker\run_once.py
```

Long-lived worker loop from repo root:

```powershell
.\.venv\Scripts\python apps\worker\run_service.py
```

The worker now resolves runtime settings from [apps/api/.env](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/apps/api/.env), so local runs from the repo root and staging-style runs share the same environment contract.
