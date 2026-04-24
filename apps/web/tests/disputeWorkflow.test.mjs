import test from "node:test";
import assert from "node:assert/strict";

import {
  buildDisputeLifecycle,
  formatVerdictSummary,
  formatWorkflowLabel
} from "../src/lib/disputeWorkflow.js";

test("formatWorkflowLabel humanizes underscore workflow values", function () {
  assert.equal(formatWorkflowLabel("under_review"), "Under review");
  assert.equal(formatWorkflowLabel("verdict_issued"), "Verdict issued");
  assert.equal(formatWorkflowLabel("shared_fault"), "Shared fault");
});

test("buildDisputeLifecycle distinguishes appealed re-review cases", function () {
  var lifecycle = buildDisputeLifecycle({
    status: "under_review",
    appealRequestedAt: "2026-04-24T08:30:00Z",
    appealRequestedByName: "Tenant User"
  });

  assert.equal(lifecycle.stageLabel, "Appealed and back in review");
  assert.equal(lifecycle.requestedByLabel, "Appealed by");
  assert.equal(lifecycle.requestedByValue, "Tenant User");
  assert.equal(lifecycle.verdictActionLabel, "Issue fresh verdict");
});

test("formatVerdictSummary keeps reviewer wording and human-readable outcomes", function () {
  assert.equal(
    formatVerdictSummary({
      verdictSummary: "Additional repair evidence changed the outcome.",
      verdictOutcome: "shared_fault",
      tenantScoreDelta: -5,
      landlordScoreDelta: -10
    }),
    "Reviewer verdict: Additional repair evidence changed the outcome. | Outcome: Shared fault | Tenant delta -5 | Landlord delta -10"
  );
});
