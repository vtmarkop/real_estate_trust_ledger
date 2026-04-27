import React from "react";

import { SegmentedTabs } from "../components/SegmentedTabs.js";
import {
  FactPill,
  HeroStat,
  NoteBlock,
  PageHero,
  SectionHeading,
  StatusBadge,
  TimelineEntry
} from "../components/PageChrome.js";
import { apiRequest } from "../lib/api.js";
import { e } from "../lib/i18n.js";

function formatLabel(rawValue) {
  return rawValue.replace(/[_:]/g, " ");
}

function inferStatusTone(value) {
  var normalized = String(value || "").toLowerCase();
  if (
    normalized.indexOf("accept") >= 0 ||
    normalized.indexOf("verif") >= 0 ||
    normalized.indexOf("success") >= 0 ||
    normalized.indexOf("active") >= 0
  ) {
    return "success";
  }
  if (
    normalized.indexOf("reject") >= 0 ||
    normalized.indexOf("fail") >= 0 ||
    normalized.indexOf("deny") >= 0 ||
    normalized.indexOf("lock") >= 0
  ) {
    return "danger";
  }
  if (
    normalized.indexOf("review") >= 0 ||
    normalized.indexOf("pending") >= 0 ||
    normalized.indexOf("open") >= 0
  ) {
    return "warning";
  }
  return "accent";
}

function MetricCard(props) {
  return e("article", { className: "metric-card" }, [
    e("p", { className: "metric-kicker", key: "kicker" }, props.kicker),
    e("strong", { className: "metric-value", key: "value" }, props.value),
    e("p", { className: "metric-copy", key: "copy" }, props.copy)
  ]);
}

function hasLandlordSideSignals(summary) {
  var inputs = summary && summary.inputs ? summary.inputs : {};
  return Boolean(
    inputs.landlord_counterparty_confirmed_tenancies ||
      inputs.landlord_verified_tenancies ||
      inputs.accepted_landlord_evidence_documents ||
      inputs.accepted_landlord_counterparty_references ||
      inputs.landlord_adjudication_adjustment
  );
}

function buildInitialConsentForm() {
  return {
    grantee_organization_id: "",
    access_code: "",
    expires_in_days: "30"
  };
}

function updateNamedField(setter) {
  return function handleFieldChange(event) {
    var target = event.target;
    setter(function mergeFields(previous) {
      var next = Object.assign({}, previous);
      next[target.name] = target.value;
      return next;
    });
  };
}

export function TrustProfilePage() {
  var stateTuple = React.useState({
    status: "loading",
    summary: null,
    history: [],
    trustEvents: [],
    agencyDirectory: [],
    consents: [],
    accessHistory: [],
    error: null
  });
  var state = stateTuple[0];
  var setState = stateTuple[1];
  var consentFormTuple = React.useState(buildInitialConsentForm());
  var consentForm = consentFormTuple[0];
  var setConsentForm = consentFormTuple[1];
  var consentSubmissionTuple = React.useState({
    isSubmitting: false,
    message: null
  });
  var consentSubmission = consentSubmissionTuple[0];
  var setConsentSubmission = consentSubmissionTuple[1];
  var revokeTuple = React.useState("");
  var revokingConsentId = revokeTuple[0];
  var setRevokingConsentId = revokeTuple[1];
  var trustSectionTuple = React.useState("overview");
  var trustSection = trustSectionTuple[0];
  var setTrustSection = trustSectionTuple[1];

  var updateConsentField = React.useMemo(function buildConsentFieldUpdater() {
    return updateNamedField(setConsentForm);
  }, []);

  var loadTrustProfile = React.useCallback(async function loadTrustProfile() {
    setState(function setLoading(previous) {
      return {
        status:
          previous.summary ||
          previous.history.length ||
          previous.trustEvents.length ||
          previous.consents.length ||
          previous.accessHistory.length
            ? "refreshing"
            : "loading",
        summary: previous.summary,
        history: previous.history,
        trustEvents: previous.trustEvents,
        agencyDirectory: previous.agencyDirectory,
        consents: previous.consents,
        accessHistory: previous.accessHistory,
        error: null
      };
    });

    try {
      var results = await Promise.all([
        apiRequest("/trust-scores/mine"),
        apiRequest("/trust-scores/mine/history"),
        apiRequest("/trust-events/mine"),
        apiRequest("/organizations/directory/agencies"),
        apiRequest("/consents/trust-report"),
        apiRequest("/consents/trust-report/access-history")
      ]);
      setState({
        status: "ready",
        summary: results[0],
        history: results[1],
        trustEvents: results[2],
        agencyDirectory: results[3],
        consents: results[4],
        accessHistory: results[5],
        error: null
      });
      setConsentForm(function syncAgencySelection(previous) {
        if (previous.grantee_organization_id || !results[3].length) {
          return previous;
        }
        return Object.assign({}, previous, {
          grantee_organization_id: results[3][0].id
        });
      });
    } catch (error) {
      setState({
        status: "error",
        summary: null,
        history: [],
        trustEvents: [],
        agencyDirectory: [],
        consents: [],
        accessHistory: [],
        error: error.message || "Unable to load your trust profile."
      });
    }
  }, []);

  React.useEffect(function bootstrapTrustProfile() {
    loadTrustProfile();
  }, [loadTrustProfile]);

  async function handleConsentSubmit(event) {
    event.preventDefault();
    setConsentSubmission({
      isSubmitting: true,
      message: null
    });

    try {
      var createdConsent = await apiRequest("/consents/trust-report", {
        method: "POST",
        body: {
          grantee_organization_id: consentForm.grantee_organization_id,
          access_code: consentForm.access_code,
          expires_in_days: Number(consentForm.expires_in_days)
        }
      });
      setConsentForm(function preserveAgencySelection(previous) {
        return Object.assign(buildInitialConsentForm(), {
          grantee_organization_id: previous.grantee_organization_id
        });
      });
      await loadTrustProfile();
      setConsentSubmission({
        isSubmitting: false,
        message:
          "Share token created for " +
          createdConsent.grantee_organization_name +
          ": " +
          createdConsent.share_token +
          ". Pair it with the access code you chose."
      });
    } catch (error) {
      setConsentSubmission({
        isSubmitting: false,
        message: error.message || "Unable to create the trust-report consent."
      });
    }
  }

  async function handleRevokeConsent(consentId) {
    setRevokingConsentId(consentId);
    try {
      await apiRequest("/consents/trust-report/" + consentId + "/revoke", {
        method: "POST"
      });
      await loadTrustProfile();
    } finally {
      setRevokingConsentId("");
    }
  }

  if (state.status === "loading") {
    return e("div", { className: "state-panel" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "My Trust"),
      e("h1", { className: "state-title", key: "title" }, "Loading trust score profile"),
      e(
        "p",
        { className: "state-copy", key: "copy" },
        "We are loading your scores, sharing permissions, and trust history."
      )
    ]);
  }

  if (state.status === "error") {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "My Trust"),
      e("h1", { className: "state-title", key: "title" }, "Trust data unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  var summary = state.summary;
  var inputs = summary.inputs;
  var activeWorkspaceRole = session.activeWorkspaceRole || "tenant";
  var isLandlordWorkspace = activeWorkspaceRole === "landlord";
  var roleScore = isLandlordWorkspace ? summary.landlord_score : summary.tenant_score;
  var roleScoreLabel = isLandlordWorkspace ? "Landlord score" : "Tenant score";
  var roleScoreCopy = isLandlordWorkspace
    ? "Your score for records where you act as a landlord or property owner."
    : "Your score for records where you act as a renter.";
  var roleInputCards = isLandlordWorkspace
    ? [
        e(FactPill, { key: "confirmed-landlord", label: "Confirmed landlord tenancies", value: String(inputs.landlord_counterparty_confirmed_tenancies), tone: "accent" }),
        e(FactPill, { key: "verified-landlord", label: "Verified landlord tenancies", value: String(inputs.landlord_verified_tenancies), tone: "success" }),
        e(FactPill, { key: "landlord-evidence", label: "Accepted landlord evidence", value: String(inputs.accepted_landlord_evidence_documents), tone: "success" }),
        e(FactPill, { key: "landlord-references", label: "Accepted landlord references", value: String(inputs.accepted_landlord_counterparty_references), tone: "accent" }),
        e(FactPill, { key: "history-imports", label: "Accepted history imports", value: String(inputs.accepted_history_imports), tone: "warning" })
      ]
    : [
        e(FactPill, { key: "confirmed-tenant", label: "Confirmed tenant tenancies", value: String(inputs.tenant_counterparty_confirmed_tenancies), tone: "accent" }),
        e(FactPill, { key: "verified-tenant", label: "Verified tenant tenancies", value: String(inputs.tenant_verified_tenancies), tone: "success" }),
        e(FactPill, { key: "tenant-evidence", label: "Accepted tenant evidence", value: String(inputs.accepted_tenant_evidence_documents), tone: "success" }),
        e(FactPill, { key: "tenant-references", label: "Accepted tenant references", value: String(inputs.accepted_tenant_counterparty_references), tone: "accent" }),
        e(FactPill, { key: "history-imports", label: "Accepted history imports", value: String(inputs.accepted_history_imports), tone: "warning" })
      ];
  var landlordSideActive = hasLandlordSideSignals(summary);
  var activeConsents = state.consents.filter(function filterActive(consent) {
    return consent.is_active;
  });
  var trustSections = [
    {
      id: "overview",
      label: "Overview",
      meta: "Scores, inputs, and confidence"
    },
    {
      id: "sharing",
      label: "Sharing",
      meta: String(activeConsents.length) + " active consents"
    },
    {
      id: "history",
      label: "History",
      meta: String(state.history.length + state.trustEvents.length) + " entries"
    },
    {
      id: "access",
      label: "Access log",
      meta: String(state.accessHistory.length) + " report opens"
    }
  ];

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "My Trust",
      title: isLandlordWorkspace ? "My landlord trust profile" : "My tenant trust profile",
      copy:
        isLandlordWorkspace
          ? "Use this page to understand your property-owner trust score, share your report when you choose to, and review landlord-side score history."
          : "Use this page to understand your renter trust score, share it with an agency when you choose to, and review tenant-side score history.",
      details: [
        "The sections below separate score drivers, sharing controls, historical changes, and report-access activity so you do not have to scan everything at once."
      ],
      stats: [
        e(HeroStat, {
          label: roleScoreLabel,
          value: String(roleScore),
          copy: roleScoreCopy
        }),
        isLandlordWorkspace && !landlordSideActive
          ? e(HeroStat, {
              label: "Landlord-side status",
              value: "Inactive",
              copy: "This side stays neutral until you rent out property or build landlord-side evidence."
            })
          : null,
        e(HeroStat, {
          label: "Verification strength",
          value: String(summary.verification_strength) + "%",
          copy: "Confidence derived from accepted evidence and verified history."
        })
      ]
    }),
    e("section", { className: "detail-panel section-switcher", key: "switcher" }, [
      e(SectionHeading, {
        title: "Focus on one trust lane",
        copy:
          trustSection === "overview"
            ? "Start with score drivers, then move into sharing or history only when you need them."
            : trustSection === "sharing"
              ? "Create or revoke agency access without mixing those controls into score history."
              : trustSection === "history"
                ? "Review how your score changed and which trust-ledger events shaped it."
                : "Use the access log when you want to see who opened your shared report.",
        key: "heading"
      }),
      e(SegmentedTabs, {
        key: "tabs",
        tabs: trustSections,
        activeTab: trustSection,
        onChange: setTrustSection,
        "aria-label": "Trust profile sections"
      })
    ]),
    trustSection === "overview"
      ? e("section", { className: "detail-panel", key: "inputs" }, [
      e(SectionHeading, {
        title: "What affects my score",
        copy: "These are the main accepted and confirmed inputs currently feeding the trust engine.",
        key: "heading"
      }),
      e(
        NoteBlock,
        { key: "role-score-note", label: "Score role clarity", tone: "accent" },
        isLandlordWorkspace
          ? "This lane evaluates you as a landlord or property owner. It is not showing tenant-side application behavior."
          : "This lane evaluates you as a renter. It is not a rating for your current landlord."
      ),
      e("div", { className: "fact-grid", key: "inputs" }, roleInputCards)
    ])
      : null,
    trustSection === "sharing"
      ? e("section", { className: "split-grid", key: "sharing" }, [
      e("article", { className: "detail-panel", key: "issue" }, [
        e(SectionHeading, {
          title: "Share my profile with an agency",
          copy: state.agencyDirectory.length
            ? "Choose an agency, set an access code, and create a revocable share token."
            : "No active agencies are currently available in the directory.",
          key: "heading"
        }),
        e(
          "form",
          { className: "auth-form", onSubmit: handleConsentSubmit, key: "form" },
          [
            e("label", { className: "field", key: "grantee_organization_id" }, [
              e("span", { className: "field-label", key: "label" }, "Agency"),
              e(
                "select",
                {
                  className: "field-input field-select",
                  name: "grantee_organization_id",
                  value: consentForm.grantee_organization_id,
                  onChange: updateConsentField,
                  required: true,
                  disabled: !state.agencyDirectory.length
                },
                [
                  e("option", { value: "", key: "blank" }, "Select an agency"),
                  state.agencyDirectory.map(function renderAgency(agency) {
                    return e(
                      "option",
                      { value: agency.id, key: agency.id },
                      agency.name
                    );
                  })
                ]
              )
            ]),
            e("div", { className: "form-grid", key: "row" }, [
              e("label", { className: "field", key: "access_code" }, [
                e("span", { className: "field-label", key: "label" }, "Access code"),
                e("input", {
                  className: "field-input",
                  name: "access_code",
                  type: "password",
                  value: consentForm.access_code,
                  onChange: updateConsentField,
                  minLength: 4,
                  maxLength: 64,
                  required: true
                })
              ]),
              e("label", { className: "field", key: "expires_in_days" }, [
                e("span", { className: "field-label", key: "label" }, "Expires in days"),
                e("input", {
                  className: "field-input",
                  name: "expires_in_days",
                  type: "number",
                  min: "1",
                  max: "365",
                  value: consentForm.expires_in_days,
                  onChange: updateConsentField,
                  required: true
                })
              ])
            ]),
            consentSubmission.message
              ? e("div", { className: "form-alert", key: "message" }, consentSubmission.message)
              : null,
            e(
              "button",
              {
                type: "submit",
                className: "button",
                disabled: consentSubmission.isSubmitting || !state.agencyDirectory.length,
                key: "submit"
              },
              consentSubmission.isSubmitting ? "Creating consent..." : "Create consent"
            )
          ]
        )
      ]),
      e("article", { className: "detail-panel", key: "consents" }, [
        e(SectionHeading, {
          title: "Active sharing permissions",
          copy: "Review live consents here and revoke them the moment you no longer want access to remain open.",
          key: "heading"
        }),
        state.consents.length
          ? e(
              "div",
              { className: "list-stack", key: "consents" },
              state.consents.map(function renderConsent(consent) {
                return e("article", { className: "stack-card", key: consent.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, consent.grantee_organization_name),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "active",
                      tone: consent.is_active ? "success" : "danger",
                      label: consent.is_active ? "Active" : "Inactive"
                    }),
                    e(StatusBadge, {
                      key: "expires",
                      tone: "accent",
                      label: "Expires " + consent.expires_at
                    }),
                    e(StatusBadge, {
                      key: "attempts",
                      tone: consent.failed_access_attempt_count ? "warning" : "neutral",
                      label: "Failed attempts " + String(consent.failed_access_attempt_count)
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "facts" }, [
                    e(FactPill, {
                      key: "validated",
                      label: "Last validated",
                      value: consent.last_validated_at || "Never"
                    }),
                    e(FactPill, {
                      key: "token",
                      label: "Share token",
                      value: consent.share_token,
                      tone: "accent"
                    })
                  ]),
                  consent.access_locked_until
                    ? e(
                        NoteBlock,
                        { key: "locked", tone: "danger", label: "Access lock" },
                        "Temporarily locked until " + consent.access_locked_until
                      )
                    : null,
                  consent.is_active
                    ? e(
                        "button",
                        {
                          type: "button",
                          className: "button button-secondary button-small",
                          disabled: revokingConsentId === consent.id,
                          onClick: function onClick() {
                            handleRevokeConsent(consent.id);
                          },
                          key: "revoke"
                        },
                        revokingConsentId === consent.id ? "Revoking..." : "Revoke consent"
                      )
                    : e(
                        "p",
                        { className: "empty-copy", key: "inactive" },
                        "This consent is no longer active."
                      )
                ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No trust-report consents have been issued yet."
            )
      ])
    ])
      : null,
    trustSection === "history"
      ? e("section", { className: "split-grid", key: "history-panels" }, [
      e("article", { className: "detail-panel", key: "history" }, [
        e(SectionHeading, {
          title: "Score updates over time",
          copy: "This is the canonical score-history timeline written by the scoring engine.",
          key: "heading"
        }),
      state.history.length
        ? e(
            "div",
            { className: "timeline-list", key: "list" },
            state.history.map(function renderHistory(entry) {
              return e(TimelineEntry, {
                key: entry.id,
                eyebrow: "Score snapshot",
                title:
                  roleScoreLabel + " " + String(isLandlordWorkspace ? entry.landlord_score : entry.tenant_score),
                meta: entry.calculated_at,
                badges: [
                  e(StatusBadge, {
                    key: "verification",
                    tone: "accent",
                    label: "Verification " + String(entry.verification_strength) + "%"
                  }),
                  e(StatusBadge, {
                    key: "version",
                    tone: "neutral",
                    label: "Version " + entry.scoring_version.toUpperCase()
                  })
                ],
                details: [
                  e(NoteBlock, {
                    key: "reason",
                    label: "Calculation reason",
                    tone: "accent"
                  }, formatLabel(entry.calculation_reason))
                ]
              });
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No score history entries have been written yet."
          )
    ]),
      e("article", { className: "detail-panel", key: "trust-events" }, [
        e(SectionHeading, {
          title: "Activity that shaped my record",
          copy: "Trust-ledger events explain the evidence, review, and operational actions behind the score history.",
          key: "heading"
        }),
      state.trustEvents.length
        ? e(
            "div",
            { className: "timeline-list", key: "events" },
            state.trustEvents.map(function renderTrustEvent(trustEvent) {
              return e(TimelineEntry, {
                key: trustEvent.id,
                eyebrow: "Trust event",
                title: formatLabel(trustEvent.event_type),
                meta:
                  (trustEvent.property_label || "No property label") +
                  " | " +
                  (trustEvent.actor_user_full_name || "System actor") +
                  " | " +
                  trustEvent.created_at,
                summary: trustEvent.summary,
                badges: [
                  e(StatusBadge, {
                    key: "verification",
                    tone: inferStatusTone(trustEvent.verification_status),
                    label: formatLabel(trustEvent.verification_status)
                  })
                ],
                details: trustEvent.details
                  ? [
                      e(NoteBlock, {
                        key: "details",
                        label: "Recorded details",
                        tone: "accent"
                      }, trustEvent.details)
                    ]
                  : []
              });
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No trust-ledger events have been recorded for this account yet."
          )
    ])])
      : null,
    trustSection === "access"
      ? e("section", { className: "detail-panel", key: "access-history" }, [
        e(SectionHeading, {
          title: "Who opened my shared report",
          copy: "This is the subject-side audit trail for agency access against your shared trust profile.",
          key: "heading"
        }),
      state.accessHistory.length
        ? e(
            "div",
            { className: "timeline-list", key: "access-list" },
            state.accessHistory.map(function renderAccess(entry) {
              return e(TimelineEntry, {
                key: entry.id,
                eyebrow: "Access event",
                title: (entry.organization_name || "Unknown organization") + " | " + formatLabel(entry.action_type),
                meta: entry.created_at,
                badges: [
                  e(StatusBadge, {
                    key: "outcome",
                    tone: inferStatusTone(entry.outcome_status),
                    label: formatLabel(entry.outcome_status)
                  })
                ],
                details: [
                  e(NoteBlock, {
                    key: "details",
                    label: "Audit details"
                  }, entry.details || "No additional details recorded.")
                ]
              });
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No agency access events have been recorded against your shared trust report yet."
          )
    ])
      : null
  ]);
}
