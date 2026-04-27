export var BASE_SCORE = 500;
export var MAX_SCORE = 1000;
export var MAX_VERIFICATION_STRENGTH = 100;

function readInput(inputs, key) {
  return Number((inputs && inputs[key]) || 0);
}

function buildContributionRow(config) {
  var count = config.count == null ? null : Number(config.count || 0);
  var unit = config.unit == null ? null : Number(config.unit || 0);
  var points =
    config.points == null
      ? Number(count || 0) * Number(unit || 0)
      : Number(config.points || 0);

  return {
    key: config.key,
    label: config.label,
    description: config.description,
    count: count,
    unit: unit,
    points: points,
    kind: config.kind || "weighted",
    tone: config.tone || resolveContributionTone(points)
  };
}

function resolveContributionTone(points) {
  if (points > 0) {
    return "success";
  }
  if (points < 0) {
    return "danger";
  }
  return "neutral";
}

export function formatSignedPoints(points) {
  var normalizedPoints = Number(points || 0);
  if (normalizedPoints > 0) {
    return "+" + String(normalizedPoints);
  }
  return String(normalizedPoints);
}

export function formatContributionRule(row) {
  if (row.kind === "base") {
    return "Starting value";
  }
  if (row.kind === "adjustment") {
    return "Reviewer verdict total";
  }
  return String(row.count || 0) + " x " + formatSignedPoints(row.unit) + " pts";
}

export function getScoreInputs(record) {
  if (!record) {
    return null;
  }
  return record.inputs || record.score_inputs || null;
}

export function buildScoreContributionRows(inputs, role) {
  var isLandlord = role === "landlord";
  var roleLabel = isLandlord ? "landlord/property-owner" : "renter";
  var confirmedTenancies = readInput(
    inputs,
    isLandlord
      ? "landlord_counterparty_confirmed_tenancies"
      : "tenant_counterparty_confirmed_tenancies"
  );
  var verifiedTenancies = readInput(
    inputs,
    isLandlord ? "landlord_verified_tenancies" : "tenant_verified_tenancies"
  );
  var acceptedEvidence = readInput(
    inputs,
    isLandlord
      ? "accepted_landlord_evidence_documents"
      : "accepted_tenant_evidence_documents"
  );
  var acceptedReferences = readInput(
    inputs,
    isLandlord
      ? "accepted_landlord_counterparty_references"
      : "accepted_tenant_counterparty_references"
  );
  var adjudicationAdjustment = readInput(
    inputs,
    isLandlord ? "landlord_adjudication_adjustment" : "tenant_adjudication_adjustment"
  );

  return [
    buildContributionRow({
      key: "base-score",
      label: "Neutral base score",
      description: "Every account starts neutral, not at zero.",
      points: BASE_SCORE,
      kind: "base",
      tone: "accent"
    }),
    buildContributionRow({
      key: "confirmed-tenancies",
      label: "Counterparty-confirmed tenancies",
      description:
        "Rental relationships confirmed by the other side add stable " +
        roleLabel +
        " trust.",
      count: confirmedTenancies,
      unit: 25
    }),
    buildContributionRow({
      key: "verified-tenancies",
      label: "Reviewer-verified tenancies",
      description:
        "Formal reviewer verification adds extra weight on top of counterparty confirmation.",
      count: verifiedTenancies,
      unit: 50
    }),
    buildContributionRow({
      key: "accepted-evidence",
      label: "Accepted evidence documents",
      description:
        "Reviewer-accepted documents add smaller but concrete proof to this score side.",
      count: acceptedEvidence,
      unit: 10
    }),
    buildContributionRow({
      key: "accepted-references",
      label: "Accepted counterparty references",
      description:
        "Requested and accepted references count more than generic self-uploaded evidence.",
      count: acceptedReferences,
      unit: 25
    }),
    buildContributionRow({
      key: "adjudication-adjustment",
      label: "Adjudication adjustment",
      description:
        "Payment, deposit, or maintenance verdict deltas apply only while a verdict is final.",
      points: adjudicationAdjustment,
      kind: "adjustment"
    })
  ];
}

export function buildVerificationContributionRows(inputs) {
  var acceptedTenantEvidence = readInput(inputs, "accepted_tenant_evidence_documents");
  var acceptedLandlordEvidence = readInput(inputs, "accepted_landlord_evidence_documents");
  var acceptedTenantReferences = readInput(inputs, "accepted_tenant_counterparty_references");
  var acceptedLandlordReferences = readInput(inputs, "accepted_landlord_counterparty_references");
  var tenantVerifiedTenancies = readInput(inputs, "tenant_verified_tenancies");
  var landlordVerifiedTenancies = readInput(inputs, "landlord_verified_tenancies");
  var tenantConfirmedTenancies = readInput(inputs, "tenant_counterparty_confirmed_tenancies");
  var landlordConfirmedTenancies = readInput(inputs, "landlord_counterparty_confirmed_tenancies");

  return [
    buildContributionRow({
      key: "accepted-history-imports",
      label: "Accepted history imports",
      description:
        "Accepted cold-start import bundles increase confidence, not direct score points.",
      count: readInput(inputs, "accepted_history_imports"),
      unit: 10
    }),
    buildContributionRow({
      key: "accepted-evidence-strength",
      label: "Accepted evidence documents",
      description: "All accepted tenant and landlord evidence increases confidence.",
      count: acceptedTenantEvidence + acceptedLandlordEvidence,
      unit: 8
    }),
    buildContributionRow({
      key: "accepted-reference-strength",
      label: "Accepted counterparty references",
      description: "Accepted references add a stronger confidence signal.",
      count: acceptedTenantReferences + acceptedLandlordReferences,
      unit: 15
    }),
    buildContributionRow({
      key: "verified-tenancy-strength",
      label: "Reviewer-verified tenancies",
      description: "Verified tenancies add dedicated verification-strength points.",
      count: tenantVerifiedTenancies + landlordVerifiedTenancies,
      unit: 12
    }),
    buildContributionRow({
      key: "confirmed-tenancy-strength",
      label: "Counterparty-confirmed tenancies",
      description:
        "Confirmed tenancies also add confidence; verified tenancies count here too.",
      count: tenantConfirmedTenancies + landlordConfirmedTenancies,
      unit: 6
    })
  ];
}

export function sumContributionRows(rows) {
  return rows.reduce(function sumRows(total, row) {
    return total + Number(row.points || 0);
  }, 0);
}

export function getScoreForRole(summary, role) {
  if (!summary) {
    return 0;
  }
  return role === "landlord"
    ? Number(summary.landlord_score || 0)
    : Number(summary.tenant_score || 0);
}
