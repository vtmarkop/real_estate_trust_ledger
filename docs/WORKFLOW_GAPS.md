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
  - reviewer/admin sees it clearly as appealed and awaiting a fresh verdict
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
  - remaining audit work should check for smaller wording or metric cards that imply history without giving it a clear lane
- Backend status: complete
- Frontend status: materially improved, pending live visual review across role accounts
- Classification: `complete_but_hard_to_understand`
- Next fix:
  - visually review tenant, landlord, agency, and reviewer demo accounts for any remaining inline read-only history blocks
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
  - admin/internal mode shows review center without personal rental lanes
  - backend list/create/access routes now filter or reject tenant, landlord, and agency workflows when the account lacks the matching workspace entitlement
  - agency actions still require agency organization membership, and tenancy/property actions still require domain participation
- Backend status: complete with explicit account workspace-role entitlements and route-level checks
- Frontend status: complete for shell navigation, route guards, `Home`, `My Trust`, `Rental Records`, and `Rent & Issues`
- Classification: `complete_and_obvious`
- Next fix:
  - visually review the four clean local accounts to confirm no role-irrelevant cards remain in each active workspace mode
  - if future API responses expose a new role surface, add backend role-entitlement checks at the route boundary instead of relying only on the frontend role selector

### Full Workflow Continuity Audit

- Expected behavior:
  - all major workflows should feel complete and self-explanatory role by role
- Actual behavior:
  - architecture is strong and many workflows are implemented
  - the first continuity pass is now complete for dispute and appeal handoffs
  - the rest of the rebuilt product still has not been re-audited end to end after the large frontend refinement arc
- Backend status: broad coverage in place
- Frontend status: broad coverage in place
- Classification: `partially_implemented`
- Next fix:
  - audit and classify at least these flows:
    - property ownership and management assignment
    - tenancy setup and confirmation
    - artifact creation, library, and reference requests
    - agency-facing score explanation and point-by-point contribution transparency outside live dispute cards
    - agency screening and application movement
    - trust sharing, consent revoke, and access history
    - cross-role history and next-step framing after reviewer decisions

## Candidate Workflows For Immediate Review

These are not yet confirmed as gaps, but they are the right places to inspect first in the next continuity pass:

1. Property owner-managed versus agency-managed setup clarity
2. Prospective tenant assignment versus activated tenancy transition
3. Artifact upload versus artifact review/library separation
4. Visual verification of agency-facing score explanation outside live dispute cards and reviewer queues
5. Agency screening next-step guidance after a trust-check result
6. Consent/share-token lifecycle clarity for end users
7. Cross-role history and timeline clarity after reviewer decisions
8. Remaining action-form density versus archive interaction clarity in `Rent & Issues`
9. Visual verification of the completed score contribution breakdowns in `My Trust`, agency previews, and internal scoring controls
