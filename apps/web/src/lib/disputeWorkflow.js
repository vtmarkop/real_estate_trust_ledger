function capitalizeSentence(value) {
  if (!value) {
    return "";
  }
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function formatWorkflowLabel(value) {
  return capitalizeSentence(String(value || "").replace(/_/g, " ").trim());
}

export function buildDisputeLifecycle(options) {
  var status = String((options && options.status) || "");
  var appealRequestedAt = options && options.appealRequestedAt;
  var appealRequestedByName = options && options.appealRequestedByName;
  var reviewRequestedAt = options && options.reviewRequestedAt;
  var reviewRequestedByName = options && options.reviewRequestedByName;
  var disputedByName = options && options.disputedByName;
  var isAppealedBackInReview = status === "under_review" && Boolean(appealRequestedAt);

  if (isAppealedBackInReview) {
    return {
      stageLabel: "Appealed and back in review",
      stageTone: "warning",
      requestedByLabel: "Appealed by",
      requestedByValue: appealRequestedByName || "",
      requestedAtLabel: "Appealed at",
      requestedAtValue: appealRequestedAt,
      stageSummary:
        "An appeal returned this case to Review Center. The previous verdict is no longer final until a reviewer issues a fresh verdict.",
      verdictActionLabel: "Issue fresh verdict",
      appealActionLabel: "Appeal and send back for review"
    };
  }

  if (status === "disputed") {
    return {
      stageLabel: "Waiting for first review",
      stageTone: "danger",
      requestedByLabel: "Requested by",
      requestedByValue: reviewRequestedByName || disputedByName || "",
      requestedAtLabel: "Requested at",
      requestedAtValue: reviewRequestedAt,
      stageSummary: "This case is waiting for the first reviewer verdict.",
      verdictActionLabel: "Issue verdict",
      appealActionLabel: "Appeal and send back for review"
    };
  }

  if (status === "under_review") {
    return {
      stageLabel: "Back in review",
      stageTone: "warning",
      requestedByLabel: "Requested by",
      requestedByValue: reviewRequestedByName || disputedByName || "",
      requestedAtLabel: "Requested at",
      requestedAtValue: reviewRequestedAt,
      stageSummary: "This case is with the reviewer queue right now.",
      verdictActionLabel: "Issue verdict",
      appealActionLabel: "Appeal and send back for review"
    };
  }

  if (status === "verdict_issued") {
    return {
      stageLabel: "Verdict issued",
      stageTone: "accent",
      requestedByLabel: "Requested by",
      requestedByValue: reviewRequestedByName || disputedByName || "",
      requestedAtLabel: "Requested at",
      requestedAtValue: reviewRequestedAt,
      stageSummary:
        "A reviewer has already issued a verdict. Either side can appeal if new context should reopen the case.",
      verdictActionLabel: "Issue verdict",
      appealActionLabel: "Appeal and send back for review"
    };
  }

  return {
    stageLabel: formatWorkflowLabel(status),
    stageTone: "accent",
    requestedByLabel: "Requested by",
    requestedByValue: reviewRequestedByName || disputedByName || "",
    requestedAtLabel: "Requested at",
    requestedAtValue: reviewRequestedAt,
    stageSummary: "",
    verdictActionLabel: "Issue verdict",
    appealActionLabel: "Appeal and send back for review"
  };
}

export function formatVerdictSummary(options) {
  if (!options || !options.verdictSummary) {
    return "";
  }

  var details = ["Reviewer verdict: " + options.verdictSummary];
  if (options.verdictOutcome) {
    details.push("Outcome: " + formatWorkflowLabel(options.verdictOutcome));
  }
  details.push("Tenant delta " + String(options.tenantScoreDelta || 0));
  details.push("Landlord delta " + String(options.landlordScoreDelta || 0));
  return details.join(" | ");
}
