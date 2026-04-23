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
  - a new verdict can affect either side’s score
  - the user-facing side explains that the old verdict is no longer final
- Actual behavior:
  - backend state transitions and reviewer queue behavior are implemented correctly
  - score deltas are recalculated correctly
  - user-facing continuity is weaker than it should be because the handoff back to internal review is not explicit enough in the product copy and flow framing
- Backend status: complete
- Frontend status: functionally complete but continuity is weak
- Classification: `complete_but_hard_to_understand`
- Next fix:
  - audit all appeal surfaces
  - add clearer “sent back for review” status language
  - make next-step messaging explicit for appellant and reviewer

### Full Workflow Continuity Audit

- Expected behavior:
  - all major workflows should feel complete and self-explanatory role by role
- Actual behavior:
  - architecture is strong and many workflows are implemented
  - continuity has not yet been re-audited end to end after the large frontend refinement arc
- Backend status: broad coverage in place
- Frontend status: broad coverage in place
- Classification: `partially_implemented`
- Next fix:
  - audit and classify at least these flows:
    - property ownership and management assignment
    - tenancy setup and confirmation
    - artifact creation, library, and reference requests
    - payments, deposits, maintenance, disputes, and appeals
    - reviewer verdict and score side effects
    - agency screening and application movement
    - trust sharing, consent revoke, and access history

## Candidate Workflows For Immediate Review

These are not yet confirmed as gaps, but they are the right places to inspect first in the next continuity pass:

1. Property owner-managed versus agency-managed setup clarity
2. Prospective tenant assignment versus activated tenancy transition
3. Artifact upload versus artifact review/library separation
4. Payment proof -> counterparty response -> dispute -> verdict -> appeal chain
5. Deposit settlement -> dispute -> verdict -> appeal chain
6. Maintenance report -> response -> dispute -> verdict -> appeal chain
7. Reviewer queue visibility for appealed items
8. Score explanation after verdict-issued versus under-review states
9. Agency screening next-step guidance after a trust-check result
10. Consent/share-token lifecycle clarity for end users
