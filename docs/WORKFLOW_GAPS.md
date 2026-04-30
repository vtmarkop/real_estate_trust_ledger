# Workflow Gaps Audit

This file tracks workflows that are incomplete, confusing, or only partially surfaced from a real product point of view.

## Status Vocabulary

- `complete_and_obvious`
- `complete_but_hard_to_understand`
- `partially_implemented`
- `missing`

## How To Use This File

For every audited workflow, capture:

- expected behavior
- actual behavior
- backend status
- frontend status
- current classification
- next fix

This file should stay short, practical, and current. Long explanation belongs in:

- `docs/WORKFLOW_MAP.md`
- `docs/WORKFLOW_DIAGRAMS.md`
- `docs/CODEBASE_REFERENCE.md`

## Active Audit Matrix

### Dispute Appeal -> Reviewer Re-Verdict Continuity

- Expected behavior:
  - tenant or landlord appeals a verdict
  - the dispute returns to internal review
  - reviewer sees it clearly as appealed and awaiting a fresh verdict
  - a new verdict can affect either side's score
  - the user-facing side explains that the old verdict is no longer final
- Actual behavior:
  - backend state transitions and reviewer queue behavior are implemented correctly
  - score deltas are recalculated correctly
  - the user-facing dispute desk now shows explicit stage, appeal, and next-step framing for payment, deposit, and maintenance cases
  - the reviewer dispute queue now distinguishes first verdicts from appealed re-reviews and calls for a fresh verdict when needed
  - the payment counterparty decision path is blocked once a case has moved into reviewer dispute flow
- Backend status: complete
- Frontend status: complete with explicit handoff framing in both user and reviewer lanes
- Classification: `complete_and_obvious`
- Next fix:
  - use this workflow as the reference model for the remaining continuity audit

### Rent & Issues Daily Use Versus Archive Interaction Model

- Expected behavior:
  - tenant or landlord should choose the relevant property quickly
  - they should act inside one focused payment/deposit/maintenance context instead of scanning every tenancy card
  - history should read as a real timeline, not only as separated note blocks
- Actual behavior:
  - the backend and action rules were already strong
  - the rebuilt page had drifted into tenancy-first browsing and forced users to scan too many cards before acting
  - the first UX-reset slice now adds property search, a property dropdown, and a selected-property history timeline in `Rent & Issues`
  - the second UX-reset slice now adds compact payment and issue dropdowns inside the selected property flow
  - the third UX-reset slice separates selected-property `Daily work` from read-only `History`, so action forms are no longer mixed into timeline browsing
  - the fourth UX-reset slice separates `Create new` payment work and `Report new` maintenance work from existing saved record detail/actions, so past items no longer appear underneath blank creation forms
  - the fifth UX-reset slice removes read-only proof, notes, dispute, verdict, and evidence history from operation action cards; those details now live in the selected lane's `History` view
  - tenancy metadata in `Rental Records` and `Rent & Issues` now shows the signed-in user's role and the counterparty instead of the vague `Parties: Tenant and Landlord` label
  - payment and maintenance detail actions now render one focused record at a time under `Daily work`, closer to the archive's details-modal pattern without weakening rebuilt API rules
  - the page still needs live visual review to confirm the form density feels simple enough for normal tenant/landlord use
- Backend status: complete
- Frontend status: materially improved but still mid-reset pending visual review
- Classification: `complete_but_hard_to_understand`
- Next fix:
  - keep normal user work inside one selected property at a time
  - visually review the selected property, `Daily work`, `History`, create-vs-existing payment modes, create-vs-existing maintenance modes, payment menu, and issue menu with seeded demo accounts
  - reduce any remaining form density if the live flow still feels heavier than the archive interaction model

### Role-Wide History Lane Separation

- Expected behavior:
  - action surfaces should show current state and available next actions only
  - read-only history, saved logs, previous notes, evidence files, and audit-style events should live in explicit history/log lanes
  - this rule should hold for tenants, landlords, agencies, and internal operators
- Actual behavior:
  - personal trust history, account security events, internal audit logs, and worker-run history were already separated into their own lanes
  - operations proof/notes/verdict details have now been moved out of action cards and into selected-property `History`
  - agency saved trust checks have moved out of the screening action lane into a dedicated `Screening history` lane
  - `Rental Records > Artifacts` now uses one selected tenancy at a time instead of rendering every tenancy's upload/library/reference block together
  - the 2026-04-30 pre-QA browser pass checked the main tenant, landlord, agency, reviewer, and admin history/daily-action separations with minimal reset and rich seed data
- Backend status: complete
- Frontend status: complete for the current desktop browser pass; responsive and full human keyboard traversal remain manual QA checks
- Classification: `complete_and_obvious`
- Next fix:
  - repeat the separation check during user manual QA on tablet/mobile widths
  - keep current actions and read-only history separated in future UI changes

### Shell Density Choice

- Expected behavior:
  - workspace display options should create an obvious workflow benefit
  - if a control only changes spacing like a weak zoom setting, it should not distract users from role and task choices
- Actual behavior:
  - the old `Comfort` / `Compact` switch did not create a clear enough product difference
  - signed-in workspaces now use fixed compact density, which is the more useful view for the current operational pages
  - the shell no longer renders a density control
- Backend status: not applicable
- Frontend status: complete
- Classification: `complete_and_obvious`
- Next fix:
  - only reintroduce a density option if it produces a visibly different layout model, not just slightly different spacing

### Visual Memorability And Control Clarity

- Expected behavior:
  - every major role/workflow lane should be visually distinguishable, not just textually labeled
  - users should be able to remember common actions by color, shape, card treatment, and control placement
  - fields, dropdowns, file inputs, and buttons should stand out more than explanatory copy
- Actual behavior:
  - the prior dark design system was coherent but too single-note, with many cards sharing the same red glow and muted panel treatment
  - the first modern visual memorability slice now adds page-level color identities for home, trust, marketplace, records, operations, agency, internal review, and account lanes
  - sidebar navigation items now carry stable color markers
  - workflow tabs derive visual classes from their tab IDs, so daily work, history, payments, deposits, maintenance, screening, audit, and review lanes can look different
  - status badges derive visual classes from their labels/tokens, so accepted, pending review, rejected, appealed, verdict, and similar states are easier to recognize
  - shared cards, fact pills, note blocks, timeline entries, fields, dropdowns, file inputs, and buttons now have stronger contrast, rails, glows, and focus states
  - follow-up CSS now adds deliberate spacing between major workspace blocks, removes signed-in workspace ambient background blobs, replaces broad glow shadows with tighter negative-spread elevation on panels/cards/tabs, increases internal hero/stat spacing, and removes the stray section-switcher accent pill caused by pseudo-element overlap
  - semantic icons now mark shell navigation, workflow tabs, and submit-form field labels, while shared text classes distinguish static labels from dynamic values, role names, counts, and statuses
- Backend status: not applicable
- Frontend status: materially improved, pending live visual review
- Classification: `complete_but_hard_to_understand`
- Next fix:
  - visually review all main workspaces in English and Greek with seeded data
  - tune any page whose color identity is too loud, too dull, or semantically confusing
  - confirm icons help novice users identify lanes without adding visual clutter
  - confirm field-label icons make submit forms easier to scan without making every field feel equally loud
  - confirm dynamic values/statuses are stronger than static explanatory copy
  - confirm no top-level menu creates odd shadow stacking, floating color artifacts, or distracting decorative elements
  - confirm the stronger fields and buttons improve task completion instead of adding visual noise

### Guided Menu-Flow Clarity

- Expected behavior:
  - a novice should choose one job first, then see one focused work area
  - setup, daily work, history, admin controls, and system/runtime work should not appear as equal competing panels
  - admin menus should use job language, not only internal system vocabulary
- Actual behavior:
  - `Rental Records` previously showed tenancy creation and saved-property setup side by side, which made the user infer whether property setup or tenancy setup came first
  - `Rental Records` now renders only the selected top-level lane: tenancies, properties, artifacts, or history/references
  - `Review Center` section labels now use more novice-facing job names such as daily reviews, dispute decisions, account roles, system runtime, and history/audit
  - the shared section switcher is now styled globally as a command-card menu across all top-level workspace tabs so it reads as the first decision on the page
- Backend status: not applicable
- Frontend status: global section-switcher styling complete, pending live visual review
- Classification: `complete_but_hard_to_understand`
- Next fix:
  - visually review the landlord `Rental Records` flow from the screenshot path and confirm the first decision is now obvious
  - visually review trust, marketplace, rent/issues, agency, review, and account/security top-level menus for the same novice clarity
  - continue applying the one-job-at-a-time rule to dense page content below the menus when too many panels still compete at once
  - review the admin panel with a novice operator lens and tune any remaining labels that sound like implementation details

### Property Owner-Managed Versus Agency-Managed Setup Clarity

- Expected behavior:
  - a landlord should always be able to save an owner-managed property without needing an agency organization
  - agency-managed setup should only be selectable when a real agency organization exists
  - the clean four-account reset should not make property creation feel blocked just because the agent account has no agency organization yet
- Actual behavior:
  - the backend already supports owner-managed property creation without an agency and correctly requires an agency organization for agency-managed assignment
  - the frontend now disables the agency-managed option when the agency directory is empty
  - the frontend now explains that the landlord can save the property as owner-managed first and assign an agency later
  - property-create and property-update payloads are hardened so an empty agency directory cannot accidentally submit `agency_managed`
- Backend status: complete
- Frontend status: complete for the no-agency landlord path
- Classification: `complete_and_obvious`
- Next fix:
  - visually verify the landlord `Rental Records > Properties & setup` path with the minimal four-account reset
  - when an agency organization is created later, verify the same form exposes the agency-managed path and validates active agency membership clearly

### Self-Managed Landlord Listing Publication

- Expected behavior:
  - a landlord who manages a property personally should be able to publish that property as available for rent without needing an agency
  - tenants should discover both owner-listed and agency-listed open homes from `Listings`
  - tenant applications should route back to the actual listing manager: the landlord for owner-listed homes, the agency for agency-listed homes
  - the UI should make the listing source obvious, for example `Listed by landlord` versus `Listed by agency`
  - after an application is accepted, the manager should see a clear next step to create the tenancy
- Actual behavior:
  - `Listing` now supports either an agency manager or a landlord manager
  - `/landlord/listings` lets a landlord publish only properties they own and that remain `owner_managed`
  - `/landlord/applications` lets the landlord review applications for those owner-listed homes
  - tenant `Listings` remains unified and now shows the listing manager/source instead of assuming every listing is agency-managed
  - `Rental Records > Properties & setup` now has a focused `Publish listing` lane for owner-managed landlord homes
  - accepted landlord applications now show a compact tenancy bridge with lease dates and `Create tenancy`
  - a browser QA pass with the clean accounts verified the path from Lila creating an owner-managed property, publishing it, Vasilis applying as tenant, Lila accepting, and Lila creating the tenancy
  - the tenant application did submit successfully and became visible as already applied, but the success feedback is still weaker than ideal because it relies mostly on the changed application state instead of a strong persistent confirmation
- Backend status: complete for owner-managed listing publication and landlord-owned application review
- Frontend status: complete for landlord-side publish/listing/application management, tenant source labeling, and the accepted-application tenancy bridge; post-submit confirmation polish remains a minor UX improvement
- Classification: `complete_and_obvious`
- Next fix:
  - verify the same owner-managed listing flow in Greek
  - add stronger application-submitted confirmation if the marketplace still feels ambiguous during the full keyboard/mouse pass
  - consider later whether owner-listed applications should offer a richer message thread before tenancy creation

### Accepted Application -> Tenancy Handoff

- Expected behavior:
  - acceptance should not be a dead end
  - the managing agency or landlord should explicitly create a tenancy from an accepted application
  - the UI should explain that acceptance is only the decision, while tenancy creation creates the rental relationship
  - agency-created inventory should require a linked landlord owner before tenancy creation
- Actual behavior:
  - `ListingApplication.tenancy_id` stores the bridge from application to tenancy
  - `/organizations/{organization_id}/applications/{application_id}/tenancy` creates a tenancy from an accepted agency-managed application
  - `/landlord/applications/{application_id}/tenancy` creates a tenancy from an accepted owner-managed landlord application
  - the bridge closes the listing, assigns the accepted tenant to the property, copies listing/property terms into the tenancy, and writes tenancy-created trust events
  - `Agency Tools > Pipeline` and landlord `Rental Records > Properties & setup > Publish listing` both surface the next-step bridge only after acceptance
  - the frontend also shows when the application is already linked to a tenancy
  - the owner-managed landlord path has now been browser-verified through visible tenancy creation and tenant-side record visibility
- Backend status: complete with migration, route contracts, ownership guards, and regression coverage
- Frontend status: complete for agency and landlord application review lanes
- Classification: `complete_and_obvious`
- Next fix:
  - visually verify the agency-managed path with real local data and confirm the explanatory copy stays clear in Greek
  - keep richer pre-tenancy messaging, holding deposits, or lease-document generation as future workflow candidates, not hidden inside acceptance

### Tenancy Records Lane Visibility After Bridge Creation

- Expected behavior:
  - when a tenancy is created, the tenant and landlord should find it from `Rental Records > Tenancy records`
  - artifact uploads, evidence, and references should remain in their own lane instead of acting as the only place to see current tenancy cards
  - if the counterparty must confirm or request review, those next actions should appear on the tenancy record itself
- Actual behavior:
  - the accepted-application bridge created the tenancy correctly
  - the tenant could see the tenancy count increase, but existing tenancy cards were hidden under `Artifacts`, making the completed workflow look broken
  - `Tenancy records` now includes `Existing tenancy records` with role, counterparty, rent, lease start, verification/status badges, and the next valid action
  - the UI now shows `Confirm record` before offering `Request review`; the counterparty is not asked to choose between confirmation and review at the same time
  - `Artifacts` remains the lane for uploads and reference/evidence work, not the only tenancy overview surface
- Backend status: complete; no backend change was required
- Frontend status: fixed and browser-verified on reload with no fresh React key/hook warnings
- Classification: `complete_and_obvious`
- Next fix:
  - include this visibility check in the direct-tenancy QA pass as well as accepted-application bridge QA

### Agent Workspace Bootstrap Without Existing Agency Membership

- Expected behavior:
  - a landlord-only account should not be responsible for creating or solving agency workspace setup
  - an agent-entitled account with no agency organization membership should see a clear setup or invite path
  - agency organization creation should be impossible for accounts without the `agency` workspace entitlement
- Actual behavior:
  - the frontend capability model now exposes `canCreateAgencyWorkspace` only for accounts with the `agency` workspace role and no agency membership
  - `Home` now shows the create-agency panel in Agent mode, not Landlord mode
  - after successful creation, the account becomes the agency owner through the existing organization owner-membership bootstrap
  - `Agency Tools` now explains that the agent role is active but no agency organization is attached yet, and links back to Home for setup
  - the backend now rejects `POST /organizations` for `agency` organizations unless the current user has the `agency` workspace entitlement
- Backend status: complete for entitlement-gated agency creation and owner-membership bootstrap
- Frontend status: complete for the clean minimal-reset agent setup path
- Classification: `complete_and_obvious`
- Next fix:
  - visually verify `theodore.tsoutsouras@accounts.trustledger.app` can create the first agency workspace from Home, then open Agency Tools
  - visually verify `lila.tsoutsoura@accounts.trustledger.app` stays in landlord-only owner-managed property setup and never sees agency bootstrap work
  - decide later whether agency membership invitations should automatically grant the `agency` workspace entitlement or remain admin-managed only

### Agency Property Inventory And Listing Assignment

- Expected behavior:
  - a landlord assigning a property to agency management should choose a real agency operator without typing or guessing that operator's email
  - an agency creating a property for publication should see the property remain in the agency workspace and be able to publish a listing from it immediately
  - a listing should only publish against property inventory actually assigned to that agency
  - an agency-created property is agency inventory, but it can be explicitly linked to an existing landlord account when the agency is working on behalf of that owner
- Actual behavior:
  - the agency directory now exposes active owner/admin/agent operators for each active agency organization
  - landlord `Properties & setup` fetches those operators, auto-fills the operator email when there is only one, and otherwise lets the landlord select the managing agent from a dropdown
  - `Agency Tools > Publishing` now creates properties as `agency_managed`, assigned to the selected agency organization and the signed-in agent account
  - `Agency Tools > Publishing` can add a landlord owner email during creation, and `Agency Tools > Portfolio` can save or clear the owner link later for the creating or assigned agent
  - the backend stores that owner link separately from `created_by_user_id`; the selected user must already exist and have the landlord workspace role
  - assigned landlord owners see the property in landlord mode and can reuse it for tenancy creation
  - `/properties/mine` returns those agency-assigned properties in agency mode, so the listing form has a usable property immediately after creation
  - backend listing creation now rejects properties that are not assigned to the target agency organization
- Backend status: complete for agency inventory assignment, explicit landlord owner linking, operator directory, agency property visibility, tag/owner updates, and listing assignment guard
- Frontend status: complete for landlord operator selection, agency publishing inventory creation, and agency-side landlord owner linking
- Classification: `complete_and_obvious`
- Next fix:
  - visually verify the path with a clean agent-created agency workspace and an existing landlord account
  - confirm the owner-link UI is clear enough that agents understand they are linking to an existing landlord, not creating a new landlord account

### Property Ownership Production Hardening

- Expected behavior:
  - every landlord-owner assignment, change, and clear action should be audit logged
  - the UI should make it obvious that owner linking uses an existing landlord account and does not create a new account
  - future ownership transfers should preserve history instead of overwriting meaning
  - the model should be ready for company ownership or multiple owners if the product needs it
  - edge cases should be tested for inactive owners, removed landlord roles, changed agency memberships, and ownership reassignment
- Actual behavior:
  - `owner_landlord_user_id` is now a clean foundation for a single existing landlord owner
  - the audit creator, landlord owner, and agency listing assignment are separated
  - current tests cover assigning an agency-created property to an existing landlord and rejecting tenant-only owner assignment
  - full ownership history, audit events, company/multiple-owner support, and deeper role-change edge cases are not implemented yet
- Backend status: partially implemented as a clean single-owner foundation
- Frontend status: partially implemented for create/edit owner linking, but not yet hardened with confirmation or ownership-history UX
- Classification: `partially_implemented`
- Next fix:
  - schedule a production-hardening slice for property ownership lifecycle audit logs, owner history, stronger confirmation copy, and expanded permission regression tests

### Tenant-Side Versus Landlord-Side Score Meaning

- Expected behavior:
  - a tenant should understand that the landlord-side score shown in their account is their own dormant landlord/property-owner dimension, not a rating for the landlord of the selected tenancy
  - a landlord or mixed-role user should understand that the same account can build trust in both persona dimensions
- Actual behavior:
  - the scoring backend already stores separate tenant-side and landlord-side score inputs on the signed-in user
  - `Home` and `My Trust` now label the landlord-side score as the user's own landlord/property-owner dimension
  - tenant-only accounts now see copy explaining that landlord-side score is inactive/neutral until they rent out property
  - score history now says `Tenant-side` and `Landlord-side` instead of implying an external landlord rating
- Backend status: complete
- Frontend status: complete for the current score summary/history surfaces
- Classification: `complete_and_obvious`
- Next fix:
  - keep this wording style when agency previews or future score surfaces are audited

### Score Contribution Transparency

- Expected behavior:
  - users should understand exactly why their current score and verification strength are what they are
  - `My Trust` should show the neutral base score, fixed contribution rows, verification-strength rows, and any reviewer-entered adjudication deltas
  - agency previews should explain the score dimensions and thresholds without exposing role-irrelevant private workflow detail
  - internal scoring controls should make the same scoring inputs inspectable for support and review
- Actual behavior:
  - the backend returns score inputs and persists score history, including aggregate score inputs inside consent-based agency trust profile previews
  - the formula is centralized and deterministic in the scoring service
  - `My Trust` now shows the selected role's base score, confirmed tenancy, verified tenancy, accepted evidence, accepted reference, and adjudication-adjustment rows
  - verification-strength contributions are shown separately from tenant/landlord score contributions
  - agency trust previews show aggregate tenant score drivers with an explicit privacy boundary instead of exposing private payment/deposit/maintenance timelines
  - internal scoring controls show the same scoring formula reference and immediate recalculation contribution breakdowns
- Backend status: complete for the v1 transparency slice
- Frontend status: complete for `My Trust`, agency trust previews, and internal scoring controls
- Classification: `complete_and_obvious`
- Next fix:
  - visually verify the score panels with seeded records that include accepted evidence, references, verified tenancies, and final dispute verdict deltas
  - keep score explanation separate from daily payment, deposit, and maintenance action forms in future UI work
  - use the same shared score-transparency helper if new score surfaces are added

### Greek Localization Coverage

- Expected behavior:
  - switching the web app to Greek should translate visible product copy across public, tenant, landlord, agency, and internal workspaces
  - workflow-critical wording should read as real product Greek, not partial literal labels mixed with English fallback text
  - dynamic UI phrases should translate as whole product phrases where possible, especially role scoping, selected-property history, score contribution explanations, tenancy status labels, and application status confirmations
- Actual behavior:
  - the localization layer already existed from Sprint 18, but later UX-reset copy and score-transparency copy had outgrown the original dictionary
  - a later patch block also reintroduced several dispute/review strings in English, which made the Greek UI look inconsistent on the very workflows under active review
  - the current pass extends the Greek patch dictionary across visible reset surfaces, fixes the English dispute/review overrides with a final Greek override block, and adds dynamic translation rules for role-only shell status, score contribution breakdown titles, contribution-point rules, tenancy-status labels, and listing-application status messages
  - a focused static scan of likely visible frontend strings now reports no likely untranslated visible strings after filtering out code-only tokens, storage keys, API paths, and intentional placeholder names
  - user-entered data, uploaded filenames, email addresses, organization/property names, and API-provided free text remain untranslated by design
- Backend status: not applicable
- Frontend status: complete for the current visible app copy pass, with regression coverage for key labels and dynamic phrases
- Classification: `complete_and_obvious`
- Next fix:
  - visually review the app in Greek with both the minimal four-account reset and the richer demo seed
  - when adding new visible copy, extend `EL_PATCH_TRANSLATIONS` or a dynamic translation rule in the same change
  - avoid using concatenated fragments for user-facing sentences unless the composed final string is still translated by `translateText`

### Active Workspace Role Scoping

- Expected behavior:
  - users should sign in with email/password first, then work from only one assigned role at a time
  - mixed-role users should switch roles from the signed-in shell, not from a confusing pre-auth dropdown
  - role selection should narrow the workspace but should not bypass backend record permissions
- Actual behavior:
  - login no longer includes a workspace-role dropdown
  - `User.workspace_roles` stores explicit tenant, landlord, agent, and admin/internal workspace entitlements
  - the admin workspace includes account role management so roles can be added or removed without creating duplicate accounts
  - after `/auth/me`, the authenticated shell opens the last valid role saved in this browser or falls back to the first assigned role
  - the authenticated shell switches the active workspace role only among roles assigned to the account
  - tenant mode shows tenant trust, listings, tenant records, and tenant-side operations
  - landlord mode shows landlord trust, landlord property/tenant records, and landlord-side operations
  - agency mode shows agency tools without personal rental lanes
  - reviewer/internal mode shows review queues and dispute verdict lanes without personal rental lanes
  - admin/internal mode shows platform controls and account-role management without personal rental lanes
  - backend list/create/access routes now filter or reject tenant, landlord, and agency workflows when the account lacks the matching workspace entitlement
  - reviewer-only backend routes now own tenancy/evidence/history-import decisions and payment/deposit/maintenance verdicts
  - admin-only backend routes now own account role management, scoring controls, automation, notifications, workers, audit, and release readiness
  - agency actions still require agency organization membership, and tenancy/property actions still require domain participation
- Backend status: complete with explicit account workspace-role entitlements, role-specific internal checks, and route-level checks
- Frontend status: complete for shell navigation, route guards, `Home`, `My Trust`, `Rental Records`, `Rent & Issues`, and internal admin/reviewer section scoping
- Classification: `complete_and_obvious`
- Next fix:
  - visually review the four clean local accounts to confirm no role-irrelevant cards remain in each active workspace mode
  - if future API responses expose a new role surface, add backend role-entitlement checks at the route boundary instead of relying only on the frontend role selector

### Admin Versus Reviewer Internal Role Separation

- Expected behavior:
  - reviewers should make neutral case decisions only: tenancy verification, evidence/history-import review, and payment/deposit/maintenance verdicts
  - admins should manage platform controls only: account workspace roles, scoring control, automation, notifications, worker runs, audit, and release readiness
  - internal overview/access can be shared, but decision authority and platform authority should not leak across roles
- Actual behavior:
  - manual review found that an admin could still issue a dispute verdict through the old shared internal route guard
  - review queue and dispute verdict endpoints now require the reviewer system role only
  - platform-control endpoints now require the admin system role only
  - frontend capabilities now split `canReviewCases` from `canManagePlatform`
  - `InternalOperationsPage` loads only the sections the active internal role can use and labels the workspace as `Review Center` for reviewers or `Admin Center` for admins
  - regression coverage now asserts admins are blocked from payment dispute verdict APIs and reviewers do not receive platform-management capabilities
- Backend status: complete
- Frontend status: complete for role-specific labels, navigation, capability loading, and section visibility
- Classification: `complete_and_obvious`
- Next fix:
  - keep this separation in manual QA and future tests: if a route makes a verdict, use reviewer; if it manages platform machinery, use admin

### Full Workflow Continuity Audit

- Expected behavior:
  - all major workflows should feel complete and self-explanatory role by role
- Actual behavior:
  - architecture is strong and many workflows are implemented
  - the first continuity pass is now complete for dispute and appeal handoffs
  - `docs/WORKFLOW_QA_PLAN.md` now defines the full real-life workflow matrix, method, order, and fix policy
  - `docs/MANUAL_QA_RUNBOOK.md`, `docs/MANUAL_QA_CHECKLIST.md`, and `docs/MANUAL_QA_RESULTS.md` now let the user run the full manual QA pass with clear task IDs and pass/fail notes
  - the first browser QA slice verified the owner-managed landlord listing-to-tenancy chain and fixed the discovered tenancy-lane visibility gap
  - the 2026-04-30 Codex pre-QA pass then covered QA-00 through QA-27 across the clean minimal accounts and the rich demo seed
  - fixes from that pass include explicit date fields, tenant-only marketplace routing, closed-listing copy, agency application note clarity, selected-tenancy artifact focus, and Greek wording cleanup
  - QA-26 responsive-width review and a full human keyboard traversal for QA-23 intentionally remain for the user's manual pass because the in-app browser automation cannot resize the viewport or fully emulate a human accessibility pass
- Backend status: broad coverage in place, with targeted listing/property/organization tests required before checkpoint close
- Frontend status: pre-QA desktop browser stabilization complete; manual responsive and keyboard signoff pending
- Classification: `complete_but_hard_to_understand`
- Next fix:
  - user should run `docs/MANUAL_QA_RUNBOOK.md`, `docs/MANUAL_QA_CHECKLIST.md`, and `docs/MANUAL_QA_RESULTS.md` as the final human QA pass
  - record any new failed checklist item here with its role, expected behavior, actual behavior, and next fix

## Candidate Workflows For Immediate Review

These are the remaining human-review targets after the Codex pre-QA pass:

1. Real tablet/mobile responsive pass for QA-26.
2. Human keyboard-only traversal for QA-23, including focus order, dropdowns, date fields, and action help.
3. Marketplace post-submit confirmation strength after tenant applications.
4. Property ownership lifecycle hardening after the current UX release-polish lane.
