import React from "react";

import {
  BASE_SCORE,
  MAX_SCORE,
  MAX_VERIFICATION_STRENGTH,
  buildScoreContributionRows,
  buildVerificationContributionRows,
  formatContributionRule,
  formatSignedPoints,
  getScoreForRole,
  getScoreInputs,
  sumContributionRows
} from "../lib/scoreTransparency.js";
import {
  FactPill,
  NoteBlock,
  SectionHeading,
  StatusBadge
} from "./PageChrome.js";
import { e } from "../lib/i18n.js";

function renderContributionRow(row) {
  return e("article", { className: "stack-card score-contribution-row", key: row.key }, [
    e("div", { className: "timeline-entry-head", key: "head" }, [
      e("strong", { className: "stack-card-title", key: "title" }, row.label),
      e("div", { className: "status-row", key: "badges" }, [
        e(StatusBadge, {
          key: "points",
          tone: row.tone,
          label: formatSignedPoints(row.points) + " pts"
        })
      ])
    ]),
    e("p", { className: "empty-copy", key: "description" }, row.description),
    e("div", { className: "fact-grid", key: "facts" }, [
      row.count == null
        ? e(FactPill, {
            key: "rule",
            label: "Rule",
            value: formatContributionRule(row),
            tone: "accent"
          })
        : e(FactPill, {
            key: "count",
            label: "Count",
            value: String(row.count)
          }),
      row.count == null
        ? null
        : e(FactPill, {
            key: "rule",
            label: "Rule",
            value: formatContributionRule(row),
            tone: "accent"
          }),
      e(FactPill, {
        key: "points-total",
        label: "Contribution",
        value: formatSignedPoints(row.points) + " pts",
        tone: row.tone
      })
    ])
  ]);
}

export function ScoreFormulaReference() {
  return e("div", { className: "list-stack score-transparency-panel" }, [
    e(SectionHeading, {
      key: "heading",
      title: "Scoring formula reference",
      copy:
        "Use the same vocabulary when explaining scores to users, agencies, and reviewers."
    }),
    e("div", { className: "fact-grid", key: "score-rules" }, [
      e(FactPill, {
        key: "base",
        label: "Base score",
        value: String(BASE_SCORE),
        tone: "accent"
      }),
      e(FactPill, {
        key: "confirmed",
        label: "Confirmed tenancy",
        value: "+25 pts each",
        tone: "success"
      }),
      e(FactPill, {
        key: "verified",
        label: "Verified tenancy",
        value: "+50 pts additional",
        tone: "success"
      }),
      e(FactPill, {
        key: "evidence",
        label: "Accepted evidence",
        value: "+10 pts each"
      }),
      e(FactPill, {
        key: "reference",
        label: "Accepted reference",
        value: "+25 pts each",
        tone: "accent"
      }),
      e(FactPill, {
        key: "verdict",
        label: "Verdict delta",
        value: "-200 to +200",
        tone: "warning"
      })
    ]),
    e("div", { className: "fact-grid", key: "verification-rules" }, [
      e(FactPill, {
        key: "history",
        label: "Accepted import",
        value: "+10 strength",
        tone: "warning"
      }),
      e(FactPill, {
        key: "evidence-strength",
        label: "Evidence strength",
        value: "+8 each"
      }),
      e(FactPill, {
        key: "reference-strength",
        label: "Reference strength",
        value: "+15 each",
        tone: "accent"
      }),
      e(FactPill, {
        key: "verified-strength",
        label: "Verified tenancy strength",
        value: "+12 each",
        tone: "success"
      }),
      e(FactPill, {
        key: "confirmed-strength",
        label: "Confirmed tenancy strength",
        value: "+6 each"
      })
    ]),
    e(
      NoteBlock,
      { key: "note", label: "Important overlap", tone: "warning" },
      "A verified tenancy also counts as counterparty-confirmed, so one verified tenancy is +75 score and +18 verification strength before any evidence or verdict adjustments."
    )
  ]);
}

export function ScoreContributionPanel(props) {
  var summary = props.summary || null;
  var inputs = props.inputs || getScoreInputs(summary);
  if (!inputs) {
    return null;
  }

  var role = props.role === "landlord" ? "landlord" : "tenant";
  var roleLabel = role === "landlord" ? "Landlord-side" : "Tenant-side";
  var scoreRows = buildScoreContributionRows(inputs, role);
  var verificationRows = buildVerificationContributionRows(inputs);
  var rawScore = sumContributionRows(scoreRows);
  var targetScore =
    props.targetScore == null ? getScoreForRole(summary, role) : Number(props.targetScore || 0);
  var verificationStrength =
    summary && summary.verification_strength != null
      ? Number(summary.verification_strength)
      : sumContributionRows(verificationRows);
  var showVerification = props.showVerification !== false;

  return e("div", { className: "list-stack score-transparency-panel" }, [
    e(SectionHeading, {
      key: "heading",
      title: props.title || roleLabel + " score contribution breakdown",
      copy:
        props.copy ||
        "This shows the current aggregate inputs that feed the visible score. It explains categories and totals, not private case-by-case history."
    }),
    e("div", { className: "fact-grid", key: "totals" }, [
      e(FactPill, {
        key: "target",
        label: "Visible score",
        value: String(targetScore),
        tone: "accent"
      }),
      e(FactPill, {
        key: "raw",
        label: "Before clamp",
        value: String(rawScore),
        tone: rawScore === targetScore ? "success" : "warning"
      }),
      e(FactPill, {
        key: "cap",
        label: "Score range",
        value: "0-" + String(MAX_SCORE)
      }),
      showVerification
        ? e(FactPill, {
            key: "verification",
            label: "Verification strength",
            value: String(Math.min(verificationStrength, MAX_VERIFICATION_STRENGTH)) + "%",
            tone: "success"
          })
        : null
    ]),
    e("div", { className: "list-stack", key: "score-rows" }, scoreRows.map(renderContributionRow)),
    e(
      NoteBlock,
      { key: "score-note", label: "How to read verified tenancies", tone: "warning" },
      "A verified tenancy is intentionally counted in both confirmed and verified rows because it passed both trust gates."
    ),
    showVerification
      ? e(
          "div",
          { className: "list-stack", key: "verification-rows" },
          [
            e(SectionHeading, {
              key: "verification-heading",
              title: "Verification-strength contribution breakdown",
              copy:
                "Verification strength is separate from the trust score. It measures confidence in the record and is capped at 100%."
            })
          ].concat(verificationRows.map(renderContributionRow))
        )
      : null
  ]);
}
