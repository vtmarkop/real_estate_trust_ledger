# Manual QA Results

Date started: 2026-04-30
Tester: Codex pre-QA browser pass
Browser: Codex in-app browser at `http://127.0.0.1:5173`
Viewport notes: Desktop viewport verified in browser. Responsive resize remains a user manual-QA checkpoint because the in-app browser API does not expose viewport resizing.
Data mode: `minimal reset` for QA-00 to QA-12, then `rich seed` for QA-13 to QA-27
Git branch: `codex/archive-ux-reset`

Use statuses: `Not run`, `Pass`, `Fail`, `Blocked`, `Skipped`.

| ID | Status | Data mode | Account/role | Language | Severity | Screenshot/path | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QA-00 | Pass | minimal | any | EN |  |  | Login loaded without role dropdown; API/web live. |
| QA-01 | Pass | minimal | Vasilis tenant/admin | EN |  |  | Tenant and admin surfaces stayed separate. |
| QA-02 | Pass | minimal | Lila landlord | EN | S3 fixed |  | Direct tenant marketplace route now redirects back to allowed landlord workspace. |
| QA-03 | Pass | minimal | Froso tenant/landlord | EN |  |  | Tenant/landlord switching stayed role-scoped. |
| QA-04 | Pass | minimal | Theodore agent | EN | S3 fixed |  | Agent bootstrap worked; undefined closed-listings copy fixed. |
| QA-05 | Pass | minimal | Lila landlord | EN |  |  | Owner-managed property creation worked without an agency. |
| QA-06 | Pass | minimal | Theodore + Lila | EN |  |  | Agency/operator assignment worked without manual email guessing. |
| QA-07 | Pass | minimal | Theodore + Lila | EN |  |  | Agency inventory and landlord-owner link worked. |
| QA-08 | Pass | minimal | Lila + Vasilis | EN |  |  | Tenant discovered landlord listing and applied. |
| QA-09 | Pass | minimal | Lila + Vasilis | EN | S3 fixed |  | Owner application accepted and bridged to tenancy; closed listing badge wording fixed. |
| QA-10 | Pass | minimal | Theodore + Vasilis | EN | S3 fixed |  | Agency listing to tenancy worked; applicant note/status-note separation fixed. |
| QA-11 | Pass | minimal | Froso + Lila | EN | S2 fixed |  | Direct tenancy creation and confirmation worked after replacing fragile native date fields with explicit `YYYY-MM-DD` fields. |
| QA-12 | Pass | minimal | any | EN |  |  | Sessions and sign-in activity stayed separated; workflow tabs did not show action bubbles. |
| QA-13 | Pass | rich | Tenant + Reviewer | EN | S3 fixed |  | Evidence/review lanes worked; artifacts now use one selected tenancy instead of rendering every upload form at once. |
| QA-14 | Pass | rich | Tenant + Landlord + Reviewer | EN |  |  | History imports/references stayed separate from tenancy setup and daily operations. |
| QA-15 | Pass | rich | Tenant + Agency Owner | EN |  |  | Consent sharing, access validation, profile preview, saved trust check, and screening history worked. |
| QA-16 | Pass | rich | Tenant + Landlord | EN |  |  | Payment create/existing/history lanes stayed separated; landlord confirmation handoff worked in minimal data. |
| QA-17 | Pass | rich | Tenant/Landlord + Reviewer | EN |  |  | Dispute desk and reviewer dispute queue exposed reviewer handoff clearly. |
| QA-18 | Pass | rich | Tenant/Landlord + Reviewer | EN |  |  | Deposit dispute state and reviewer queue were visible and separated. |
| QA-19 | Pass | rich | Tenant/Landlord + Reviewer | EN |  |  | Maintenance report/existing/history lanes stayed separated; reviewer handoff visible. |
| QA-20 | Pass | rich | Tenant/Landlord/Agent/Admin | EN |  |  | Score contribution panels worked in My Trust, agency preview, and internal score controls. |
| QA-21 | Pass | rich | Admin | EN |  |  | Runtime actions and audit history were visually and conceptually separated from reviewer case decisions. |
| QA-22 | Pass | rich | landlord sample plus prior role strings | EL | S3 fixed |  | Greek pass fixed remaining visible `browser` wording and improved dynamic home-title grammar. |
| QA-23 | Pass | rich | landlord sample | EN/EL |  |  | Real click/type/submit flows worked; CSS focus-visible contract present. Manual keyboard traversal should still be repeated by the user. |
| QA-24 | Pass | rich | all sampled roles | EN/EL |  |  | Action buttons kept help bubbles; workflow tabs/selectors stayed clean in snapshots. |
| QA-25 | Pass | rich | tenant/landlord/agent/admin samples | EN/EL |  |  | Main dense surfaces now use selected-object lanes; artifact card sprawl fixed. |
| QA-26 | Skipped | rich | tenant/landlord/agent | EN/EL |  |  | In-app browser API did not expose viewport resizing; keep this for manual QA on tablet/mobile widths. |
| QA-27 | Pass | rich | all sampled roles | EN/EL |  |  | Browser console warning/error sweep returned no React hook/key warnings or error-boundary logs after fixes. |
| QA-28 | Not run | either | tester | EN |  |  | Reserved for user manual signoff after this pre-QA pass. |

## Codex Verification

Completed on 2026-04-30 after the pre-QA fixes:

- `node --check` on the touched frontend files passed.
- A fresh in-app browser reload console sweep after the fixes returned 0 new warnings/errors.
- `npm test -- --runInBand` passed with 33 frontend tests.
- `npm run build` passed.
- `.\.venv\Scripts\python -m unittest tests.test_listing_application_api tests.test_property_assignments_api tests.test_organization_rbac_api tests.test_internal_automation_api` passed with 34 backend workflow tests.
- `.\.venv\Scripts\python -m unittest tests.test_repo_layout tests.test_web_scaffold` passed with 11 docs/scaffold tests.
- `.\.venv\Scripts\python -m unittest discover -s tests -p "test*.py"` passed with 131 backend tests.
- `git diff --check` passed.

Backend tests still emit the existing SQLite `ResourceWarning` noise; no command failed.

## Finding Template

Use this block below the table when a row fails:

```text
Finding ID:
Checklist ID:
Severity:
Role/account:
Language:
Data mode:
Steps to reproduce:
Expected:
Actual:
Screenshot/path:
Notes:
```
