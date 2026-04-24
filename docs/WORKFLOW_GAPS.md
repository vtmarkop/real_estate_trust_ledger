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
  - the page still does not yet match the archive's tighter detail-focus pattern for payments and tickets
- Backend status: complete
- Frontend status: improved but still mid-reset
- Classification: `complete_but_hard_to_understand`
- Next fix:
  - keep normal user work inside one selected property at a time
  - continue restoring compact payment/ticket detail focus and stronger timeline readability inside `OperationsPage.js`

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
    - trust-score explanation outside live dispute cards
    - agency screening and application movement
    - trust sharing, consent revoke, and access history
    - cross-role history and next-step framing after reviewer decisions

## Candidate Workflows For Immediate Review

These are not yet confirmed as gaps, but they are the right places to inspect first in the next continuity pass:

1. Property owner-managed versus agency-managed setup clarity
2. Prospective tenant assignment versus activated tenancy transition
3. Artifact upload versus artifact review/library separation
4. Trust-score explanation outside live dispute cards and reviewer queues
5. Agency screening next-step guidance after a trust-check result
6. Consent/share-token lifecycle clarity for end users
7. Cross-role history and timeline clarity after reviewer decisions
8. Payment/ticket detail focus versus archive interaction clarity in `Rent & Issues`
