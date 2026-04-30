# Workspace Guide

This guide explains the rebuilt Trust Ledger app in plain language.

The rebuilt frontend now supports both English and Greek. Use the floating `EN` / `ΕΛ` language switch in the bottom-right corner of the web app to move between languages at any time. The switch now updates the live workspace immediately, so you should not need to refresh the page after changing language. The current Greek pass covers the likely visible app copy across the public page, signed-in shell, tenant/landlord workspaces, agency tools, internal review center, score explanations, and reset operations flows; names, uploaded filenames, emails, and user-entered notes remain exactly as entered.

The signed-in workspace now uses the compact layout by default. The earlier `Comfort` / `Compact` density choice was removed because it behaved too much like a simple zoom control instead of a meaningful workflow mode. If a future density option returns, it should create an obvious layout difference rather than slightly changing spacing.

The current visual system uses the dark cinematic base intentionally, but each major workspace now has its own color identity. The goal is that users remember the product by shape and color as well as by text:

- `Home` uses a red/orange launch palette for next steps.
- `My Trust` uses teal/green for score and verification confidence.
- `Listings` uses green/yellow for marketplace discovery.
- `Rental Records` uses blue/cyan for evidence and property records.
- `Rent & Issues` uses amber/red for payments, deposits, maintenance, and disputes.
- `Agency Tools` uses violet/cyan for screening and portfolio work.
- `Review Center` uses pink/orange for internal decisions and risk.
- `Account` uses blue/teal for security and sessions.

The signed-in shell now also supports an active role mode. Sign in with email and password first, then switch assigned roles from the sidebar when your account has more than one role:

- `Tenant` shows tenant trust, listings, tenant records, and tenant-side rent/issue work.
- `Landlord` shows landlord trust, landlord property/tenant records, and landlord-side rent/issue work.
- `Agent` shows agency tools without personal rental lanes.
- `Admin` shows review-center tools without personal rental lanes.

The role choices come from explicit account workspace-role entitlements. Login does not ask for a role before authentication; the app opens the last valid role for this browser, or the first assigned role if the saved role no longer belongs to the account. An admin can add or remove those entitlements from `Review Center > Roles`. This role mode is a workspace filter, not a permission grant: the backend still checks tenancy participation, property ownership, agency organization membership, and internal privileges before allowing real work. The agent role has one bootstrap path: if an account has `Agent` but no agency organization yet, `Home` lets that account create the agency workspace and become its owner.

Most workspaces now also use focused section tabs inside the page itself. Good examples are:

- `My Trust`: overview, sharing, history, and access log are separated.
- `Listings`: discovery and submitted applications are separated.
- `Account`: sessions and sign-in activity are separated.
- `Agency Tools` and `Review Center`: each lane is intentionally separated so operators can work one concern at a time.

The intended menu pattern is now: choose one job first, then work inside that one visible lane. For example, `Rental Records` no longer shows tenancy setup and saved-property setup as equal side-by-side workflows; choosing `Tenancy records`, `Properties & setup`, `Artifacts`, or `History & references` changes the work area below. The same rule should guide admin work: daily reviews, account roles, dispute decisions, runtime/system work, and audit/history should stay visibly separate.

The denser workflow cards now also use clearer visual meaning:

- `status badges` show current state or workflow stage and now get semantic colors from labels such as accepted, pending review, rejected, appealed, or verdict issued,
- `fact pills` show compact business facts like score, rent, verification, or counts,
- `note blocks` hold comments, evidence summaries, dispute notes, and verdict text,
- `timeline entries` are used where activity should read as a sequence instead of a generic card,
- `tabs` and sidebar lanes use stable color markers so different workflows are easier to recognize quickly,
- `fields`, `dropdowns`, `file inputs`, and `buttons` are intentionally brighter than explanatory copy so actions do not get buried under text.
- true action `buttons` and button-styled links also show short hover/focus help bubbles explaining what the action does before you click. Workflow tabs and command-card section selectors do not show those bubbles because their job is navigation, not submission.

If you need the code-level explanation behind these workflows, use [CODEBASE_REFERENCE.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/CODEBASE_REFERENCE.md).

If you want the same workflows as diagrams instead of prose, use [WORKFLOW_DIAGRAMS.md](C:/Users/penty/Documents/dev_apps/gna_version/f33f50b4c7c20f826cd265fc68a54d4cc5921865/docs/WORKFLOW_DIAGRAMS.md).

Use it when:

- you are learning the app for the first time,
- you are not sure which menu item to open,
- you want a role-by-role explanation of how the product works,
- you want a walkthrough for the seeded demo accounts.

## Seeded Demo Cases

The local demo seed now gives you more than one example of each workflow, so you can test normal operations and dispute handling without having to create everything by hand.

- `Harbor Flat`
  - Active tenancy.
  - Assigned to the agency workspace and the current tenant.
  - Shows the "healthy live tenancy" path: confirmed payment, held deposit, resolved maintenance, uploaded evidence, and a fulfilled reference.

- `Old Town Duplex`
  - Ended tenancy.
  - Shows the "review already happened" path: verdict-issued payment, deposit, and maintenance disputes.
  - Best place to test appeal-capable flows.

- `Hillside Studio`
  - Ended tenancy.
  - Shows the "still waiting for reviewer action" path: payment, deposit, and maintenance disputes under review.
  - Best place to test reviewer queues and operational follow-ups.

- `Agency Showcase Loft`
  - Agency-facing property and listing.
  - Best place to test listing management, applications, screening, and custom property tags.

## What The App Does

Trust Ledger is a shared rental-trust workspace for:

- tenants,
- landlords,
- agencies,
- internal reviewers and admins.

Instead of treating rental history as private notes scattered across email, chat, and folders, the app keeps the important parts in one place:

- tenancy records,
- supporting evidence,
- payment and deposit history,
- maintenance history,
- references,
- trust scores,
- consent-based profile sharing,
- agency screening records,
- internal review and audit trails.

## The Main Menu

The signed-in workspace uses these menu items, depending on the active role:

- `Home`
  - Your role-scoped starting page.
  - Use it to understand where to go next.

- `Tenant Trust` or `Landlord Trust`
  - The score, score history, trust events, and sharing controls for the active role.
  - Use it when you want to understand or share your trust profile.

- `Listings`
  - Public/open listings plus your applications.
  - Tenant mode only.

- `Rental Records`
  - Current role-specific tenancies, uploaded evidence, past rental history, properties in landlord mode, and references.
  - Use it when you want to build or strengthen your trust record.

- `Rent & Issues`
  - Role-specific payments, deposits, and maintenance tickets.
  - Use it for the day-to-day running of an active tenancy.

- `Agency Tools`
  - Agency-only workspace for properties, listings, applications, and trust checks.
  - Agent mode only. The account needs agency organization membership before real agency data appears, unless it is using `Home` to create the first agency workspace for that account.

- `Account`
  - Sessions and sign-in activity.
  - Use it when you want to review account access and sign out of other devices.

- `Review Center`
  - Internal-only area for queue reviews, automation, audit logs, release readiness, and account role management.
  - Admin mode only, and only if your account has internal access.

## Roles And What They Usually Do

### Tenant

Typical goals:

- build a trust profile,
- upload evidence,
- import older rental history,
- request references,
- share a profile with an agency,
- apply to listings,
- track rent, deposits, and repairs.

Best menu order:

1. `Home`
2. `Rental Records`
3. `Tenant Trust`
4. `Listings`
5. `Rent & Issues`
6. `Account`

### Landlord

Typical goals:

- confirm tenancy details,
- upload landlord-side evidence,
- respond to reference requests,
- publish owner-managed homes directly to tenant listings,
- track rent, deposits, and repairs,
- maintain a landlord trust record.

Best menu order:

1. `Home`
2. `Rental Records`
3. `Rent & Issues`
4. `Landlord Trust`
5. `Account`

### Agency Owner Or Agent

Typical goals:

- add properties,
- create listings,
- review applicants,
- run trust checks with consent,
- monitor agency activity.

Best menu order:

1. `Home`
2. `Create agency workspace` from `Home` if the account has no agency organization yet
3. `Agency Tools`
4. `Account`

### Internal Reviewer

Typical goals:

- review pending tenancies,
- review evidence and history imports,
- decide payment, deposit, and maintenance disputes.

Best menu order:

1. `Home`
2. `Review Center`
3. `Account`

### Platform Admin

Typical goals:

- add or remove account workspace-role entitlements,
- manage score controls and recalculation queues,
- monitor automation, notifications, and workers,
- inspect audit logs,
- check release readiness.

Best menu order:

1. `Home`
2. `Admin Center`
3. `Account`

## Page-By-Page Guide

### Home

Purpose:
- Gives you a quick summary and helps you decide where to go next.

What you can do:
- see the score or organization summary relevant to the active role,
- use shortcuts to key areas,
- install the web app if your browser supports it,
- read the built-in menu guide,
- create an agency workspace when the active role is `Agent` and no agency organization is attached yet.

When to use it:
- every time you sign in,
- when you feel lost and want to re-orient quickly.

### Tenant Trust Or Landlord Trust

Purpose:
- Shows the trust profile for the active tenant or landlord role and lets you share it safely.

What you can do:
- view only the active role's score dimension,
- view verification strength,
- see what affects that role-specific score,
- create a share token and access code for an agency,
- revoke a share permission,
- inspect score history,
- inspect trust-event history,
- inspect access history for shared trust reports.

When to use it:
- after adding evidence,
- before sharing with an agency,
- when you want to understand score changes.

Friendly explanation:
- `Tenant-side score` evaluates you as a renter.
- `Landlord-side score` evaluates the same account only when you act as a landlord or property owner. It is not a score for your current landlord.
- The active workspace role decides which score dimension is shown first.
- The score breakdown starts from a neutral `500`, then shows exactly what was added by confirmed tenancies, reviewer-verified tenancies, accepted evidence, accepted references, and final reviewer adjudication adjustments.
- Verification strength is shown separately from the trust score. It measures confidence in the record and is capped at `100%`.
- A verified tenancy also counts as counterparty-confirmed, so one verified tenancy contributes to both rows.

### Listings

Purpose:
- Lets a user browse available properties and apply.

What you can do:
- review open listings,
- see whether each home is listed by an agency or directly by a landlord,
- see the current listing manager,
- see rent and deposit amounts,
- see minimum score and verification requirements,
- add an application note,
- submit an application,
- review your past and current applications.

When to use it:
- when you are looking for a home,
- after you have built enough trust data to apply confidently.

### Rental Records

Purpose:
- Holds the records that support your trust profile.

What you can do:
- create a new tenancy record by using a counterparty email,
- view only the tenancies where you match the active role,
- create and manage saved properties in landlord mode,
- request review on a tenancy,
- confirm a tenancy if you are the counterparty,
- upload evidence for a tenancy,
- open stored evidence artifacts through signed private access links,
- create a past-rental-history import,
- submit a history import for review,
- create reference requests,
- fulfill incoming reference requests.

When to use it:
- when onboarding a current tenancy,
- when proving older rental history,
- when adding documents that support your trust record.

Friendly explanation:
- This is the best place to start if you want to "build your file."
- You do not need to know internal IDs. The app now lets you create a tenancy by using the other person's email.
- The active role locks the tenancy form to tenant or landlord so you do not accidentally create the wrong side of a record.
- Tenancy cards show your role and the actual counterparty, not a generic parties label.
- `Tenancy records` now shows existing role-specific tenancy cards as well as the create form. Use those existing cards for confirmation, review requests, and current tenancy facts; use `Artifacts` for uploads, evidence, and reference material.
- `Artifacts` starts by choosing one active tenancy, then shows only that tenancy's upload, library, and reference workspace so history/evidence work does not sprawl across every property at once.
- In landlord mode, `Properties & setup` lets you save an owner-managed property even when no agency organization exists yet. The agency-managed choice only becomes available after there is a real agency workspace to assign. After you select an agency, the managing-agent dropdown uses that agency's active operators and fills the operator email for you instead of asking you to type it manually.
- In landlord mode, `Properties & setup > Publish listing` lets you publish owner-managed properties directly into tenant `Listings`. Agency-managed properties stay in `Agency Tools` so applications route back to the agency instead of the landlord.
- After you accept an application for an owner-managed listing, the same `Publish listing` lane shows `Create tenancy`; use that bridge to turn the accepted application into the actual rental record.
- Your uploaded documents are stored privately. Depending on the environment, that storage may be local private storage or S3-compatible object storage such as MinIO, but the app keeps the same safe download flow either way.

### Rent & Issues

Purpose:
- Manages the operational side of an active tenancy.

What you can do:
- create payment records,
- add payment proof,
- upload a real payment proof file and reopen it later,
- confirm or reject payment proof,
- create or update deposit settlement information,
- upload a real deposit settlement file and reopen it later,
- dispute deposit outcomes,
- create maintenance tickets,
- upload a real maintenance report file,
- acknowledge maintenance tickets,
- resolve maintenance tickets,
- upload a maintenance resolution file,
- dispute maintenance outcomes.

When to use it:
- during an active tenancy,
- whenever rent, deposit, or repair activity happens.

Friendly explanation:
- Think of this page as the day-to-day "running the rental" page.
- Tenant mode only shows properties where you are the tenant. Landlord mode only shows properties where you are the landlord.
- First choose one property. The property summary shows your role in that tenancy and the counterparty you are dealing with.
- Then use `Daily work` for actions and `History` for the read-only timeline of what already happened.
- In `Payments`, use `Create new` only for a blank new payment form, or `Existing records` to open the payment dropdown and act on a saved payment.
- In `Maintenance`, use `Report new` only for a blank new issue form, or `Existing issues` to open the issue dropdown and act on a saved issue.
- Use `History` for saved proof files, old notes, dispute context, verdict details, and timelines. Those details are intentionally not repeated inside action cards.
- If something goes wrong, use the `Dispute desk` at the top of the page. It gathers open disputes and items that can be disputed right now, so you do not have to search through every record one by one.

### Agency Tools

Purpose:
- Gives agencies one place to manage inventory and applicant screening.

What you can do:
- add a property,
- link an agency-created property to an existing landlord owner,
- tag properties with your own custom labels,
- filter your estate portfolio by label, city, or tag,
- invite team members by email,
- change team roles and enable or disable access,
- create a listing,
- change listing status,
- adjust minimum score and verification thresholds,
- review applicants,
- move applications through review,
- create a tenancy from an accepted application after the property has a linked landlord owner,
- validate a share token and access code,
- preview a shared profile,
- save a trust check,
- review saved trust checks in `Screening history`,
- review business snapshot metrics.

When to use it:
- when publishing or managing listings,
- when screening applicants,
- when reviewing agency activity.

Friendly explanation:
- This is your agency operating desk.
- If the account has the `Agent` role but no agency organization yet, open `Home` first and create the agency workspace there. After creation, this account becomes the agency owner and `Agency Tools` becomes usable.
- Properties created from `Agency Tools > Publishing` are agency inventory. They are assigned to the selected agency organization and your agent account so they remain visible in agency mode and can be used for listings immediately.
- If a real landlord owns the agency-created property, add that landlord's existing account email in the publishing form or save it later from `Portfolio > Landlord owner email`. The landlord must already have the `Landlord` role. After that, the property appears in the landlord workspace and can be reused for tenancy setup.
- `created by` and `landlord owner` are separate ideas. The agent can create the record for listing work, while the owner link says which landlord account owns the property.
- After an application is accepted in `Pipeline`, use the `Create tenancy` bridge on that application card. If the bridge is blocked, it usually means the property still needs a linked landlord owner.
- Use property tags for your own mental model, for example: `priority`, `renovation`, `premium`, or `student-market`.
- Use `Team access` when you want another colleague to help manage the portfolio without giving them full uncontrolled access.

### Account

Purpose:
- Shows where the account is signed in and what happened recently.

What you can do:
- review sessions,
- review sign-in events,
- sign out of other devices,
- sign out one specific old device without ending every other session.

When to use it:
- after a password change,
- if you suspect someone else may have used the account,
- when cleaning up old devices.

### Review Center

Purpose:
- Internal control area for reviewers and admins.

What you can do:
- review pending tenancy verification,
- review pending evidence,
- review pending history imports,
- queue or run score refreshes,
- create manual follow-up tasks,
- inspect due automation tasks,
- claim and execute supported automation tasks,
- clean expired consent reminders,
- clean stale follow-up tasks,
- inspect notifications,
- inspect worker runs,
- inspect audit activity,
- add or remove account workspace-role entitlements,
- check release readiness.

When to use it:
- during manual review work,
- when checking platform health,
- before approving a release or pilot cutover.

Friendly explanation:
- This is the control room for the platform team.
- If a user says "my score did not update" or "who can see what storage/runtime we are using," this is the page to inspect first.

## Common Workflows

### 1. Build A New Trust Profile

1. Open `Rental Records`.
2. Add or review your tenancy records.
3. Upload supporting evidence.
4. Add past rental history if you have it.
5. Request references where useful.
6. Open `My Trust` to review the result.

### 2. Share Your Profile With An Agency

1. Open `My Trust`.
2. In the sharing section, choose the agency.
3. Set an access code.
4. Create the share token.
5. Give the token and access code to the agency through your agreed channel.
6. Later, return to `My Trust` to revoke access if needed.

### 3. Apply To A Listing

1. Open `Listings`.
2. Review listing thresholds and details.
3. Add a short application note.
4. Submit the application.
5. Return to the same page to follow the application status.
6. If the agency or landlord accepts the application, they still need to create the tenancy from their manager lane before it becomes an active rental record.

### 4. Accept An Application And Create The Tenancy

Agency path:

1. Open `Agency Tools > Pipeline`.
2. Review the application and select `Accept`.
3. If the accepted application shows `Create tenancy`, enter the lease dates and create it.
4. If the bridge asks for a landlord owner, open `Portfolio`, link the property to an existing landlord account, then return to the accepted application.

Landlord path:

1. Open `Rental Records > Properties & setup > Publish listing`.
2. Review applications for the owner-managed listing.
3. Select `Accept`.
4. Use the visible `Create tenancy` bridge to create the rental record.

After creation, the listing closes and the tenant/landlord can work from `Rental Records` and `Rent & Issues`.

### 5. Run An Agency Trust Check

1. Open `Agency Tools`.
2. Paste the share token and access code.
3. Check access first.
4. Preview the profile.
5. Save the trust check if you want it recorded in agency history.

### 6. Operate An Active Tenancy

1. Open `Rent & Issues`.
2. Record payments and add proof.
3. Confirm or reject proof as the counterparty.
4. Record deposit settlement details when relevant.
5. Use the `Dispute desk` when a deposit or maintenance outcome needs to be challenged.
6. Open and manage maintenance tickets as issues happen.

### 7. Review A Pending Case Internally

1. Open `Review Center`.
2. Pick the correct queue: tenancy, evidence, or history import.
3. Read the notes and attached context.
4. If needed, queue a score refresh or create a follow-up task from the same workspace.
5. Approve or reject with review notes.
6. Refresh the page to confirm the item left the queue.

## Local Accounts

Current account-only reset accounts, created by `apps/api/dev_reset_minimal_users.py`:

- `Tenant + Admin`: `vasilis.markopoulos@accounts.trustledger.app` / `VasilisTenantAdmin123!`
- `Landlord`: `lila.tsoutsoura@accounts.trustledger.app` / `LilaLandlord123!`
- `Agent`: `theodore.tsoutsouras@accounts.trustledger.app` / `TheodoreAgent123!`
- `Tenant + Landlord`: `froso.evangeliadou@accounts.trustledger.app` / `FrosoTenantLandlord123!`

That reset intentionally has no properties, tenancies, organizations, or history records. Login is email/password only. Mixed-role accounts, such as Vasilis and Froso, switch assigned roles from the signed-in sidebar after authentication. Theodore has the `Agent` role but no agency organization yet; sign in as Theodore, open `Home`, and use `Create agency workspace` if you want to begin agency work from the clean reset.

Legacy/rich workflow demo accounts, not present after the current account-only reset and available only after running `apps/api/dev_seed.py`:

- `Tenant`: `tenant@demo.trustledger.app` / `DemoTenant123!`
- `Landlord`: `landlord@demo.trustledger.app` / `DemoLandlord123!`
- `Agency Owner`: `owner@demo-agency.app` / `DemoAgency123!`
- `Internal Reviewer`: `reviewer@demo.trustledger.app` / `DemoReviewer123!`
- `Platform Admin`: `admin@demo.trustledger.app` / `DemoAdmin123!`

Seeded sharing values:

- share token: `demo-tenant-share-token`
- access code: `4829`

## Troubleshooting

### I do not know where to start

Go to `Home`. It now includes a built-in menu guide.

### I cannot see Agency Tools

Switch the active role to `Agent` from the sidebar. If `Agent` is not available, an admin has not assigned that workspace role to your account. If `Agent` is available but the page says no agency organization is attached, open `Home` and create an agency workspace, or ask an agency owner to invite the account.

### I cannot choose an agency while creating a landlord property

This is normal after the minimal four-account reset because it creates users only, not agency organizations. Save the property as `I manage this property myself`; agency-managed assignment becomes available after an agency workspace exists.

### I created a property as an agent but cannot list it

Agency-created properties should now be saved as agency inventory and remain available in the listing form. If the listing form still has no property, confirm that the active role is `Agent`, the account is inside the intended agency organization, and the property was created from `Agency Tools > Publishing` after selecting that agency.

### I need an agency-created property to belong to a landlord

Use an existing landlord account email. In `Agency Tools > Publishing`, fill `Landlord owner email` while creating the property, or open `Agency Tools > Portfolio` later and save `Landlord owner email` on the property card. This does not create a new landlord account; the selected account must already exist and have the `Landlord` workspace role.

### I am a landlord and want tenants to find my self-managed home

Create or keep the property as `I manage this property myself`, then open `Rental Records > Properties & setup > Publish listing`. That publishes a landlord-managed listing into the same tenant `Listings` marketplace. If the property is agency-managed, publish it from `Agency Tools` instead.

### I accepted an application but do not see a tenancy yet

Acceptance is only the decision. Open the manager lane where the application was accepted and use `Create tenancy`. For agency listings, the property must first be linked to an existing landlord owner account. For owner-managed landlord listings, the bridge is in `Rental Records > Properties & setup > Publish listing`.

### I cannot see Review Center or Admin Center

Switch the active role from the sidebar. Reviewer accounts see `Review Center` for case queues and verdicts. Admin accounts see `Admin Center` for account roles, scoring controls, runtime, audit, and release readiness. If neither role is available, your account does not currently have internal access.

### A trust check is denied

Usually one of these is true:

- the share token is wrong,
- the access code is wrong,
- the consent expired,
- the consent was revoked,
- your agency membership is inactive.

### I do not see an Install button

The browser may not support install prompts, or it may not be offering one at that moment.

### I signed in but the page still feels too technical

Use this guide together with the `Home` page first. The workspace labels are now aligned with this document, so the guide and menu should match one another.
