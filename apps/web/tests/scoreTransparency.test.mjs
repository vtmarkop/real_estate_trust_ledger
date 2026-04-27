import test from "node:test";
import assert from "node:assert/strict";

import {
  BASE_SCORE,
  buildScoreContributionRows,
  buildVerificationContributionRows,
  formatSignedPoints,
  sumContributionRows
} from "../src/lib/scoreTransparency.js";

const scoredTenantInputs = {
  tenant_counterparty_confirmed_tenancies: 1,
  tenant_verified_tenancies: 1,
  landlord_counterparty_confirmed_tenancies: 0,
  landlord_verified_tenancies: 0,
  accepted_tenant_evidence_documents: 1,
  accepted_landlord_evidence_documents: 0,
  accepted_tenant_counterparty_references: 1,
  accepted_landlord_counterparty_references: 0,
  accepted_history_imports: 1,
  tenant_adjudication_adjustment: 0,
  landlord_adjudication_adjustment: 0
};

test("tenant contribution rows explain the v1 score formula", function () {
  const rows = buildScoreContributionRows(scoredTenantInputs, "tenant");

  assert.equal(rows[0].points, BASE_SCORE);
  assert.equal(sumContributionRows(rows), 610);
  assert.equal(
    rows.find(function findVerified(row) {
      return row.key === "verified-tenancies";
    }).points,
    50
  );
});

test("verification contribution rows explain confidence separately", function () {
  const rows = buildVerificationContributionRows(scoredTenantInputs);

  assert.equal(sumContributionRows(rows), 51);
  assert.equal(formatSignedPoints(-10), "-10");
  assert.equal(formatSignedPoints(25), "+25");
});
