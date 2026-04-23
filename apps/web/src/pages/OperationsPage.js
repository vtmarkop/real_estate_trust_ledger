import React from "react";

import { useSession } from "../app/session.js";
import {
  FactPill,
  HeroStat,
  NoteBlock,
  PageHero,
  SectionHeading,
  StatusBadge
} from "../components/PageChrome.js";
import { SegmentedTabs } from "../components/SegmentedTabs.js";
import { ApiError, apiRequest } from "../lib/api.js";
import { e, getLanguageLocale } from "../lib/i18n.js";

function formatMinorAmount(minorAmount, currencyCode) {
  return new Intl.NumberFormat(getLanguageLocale(), {
    style: "currency",
    currency: currencyCode || "EUR",
    maximumFractionDigits: 2
  }).format((minorAmount || 0) / 100);
}

function parseMinorAmount(value) {
  return Math.round(Number(value || 0) * 100);
}

function inferStatusTone(value) {
  var normalized = String(value || "").toLowerCase();
  if (
    normalized.indexOf("confirm") >= 0 ||
    normalized.indexOf("accept") >= 0 ||
    normalized.indexOf("resolve") >= 0
  ) {
    return "success";
  }
  if (
    normalized.indexOf("reject") >= 0 ||
    normalized.indexOf("appeal") >= 0 ||
    normalized.indexOf("verdict") >= 0 ||
    normalized.indexOf("disput") >= 0
  ) {
    return "danger";
  }
  if (normalized.indexOf("review") >= 0 || normalized.indexOf("pending") >= 0) {
    return "warning";
  }
  return "accent";
}

function updateEntityForm(setter, entityId, name, value) {
  setter(function mergeForms(previous) {
    var next = Object.assign({}, previous);
    var existing = Object.assign({}, next[entityId] || {});
    existing[name] = value;
    next[entityId] = existing;
    return next;
  });
}

function buildPaymentForm(sessionUserId, tenancy) {
  var payerUserId =
    sessionUserId === tenancy.landlord_user_id ? tenancy.landlord_user_id : tenancy.tenant_user_id;
  return {
    payer_user_id: payerUserId,
    payee_user_id:
      payerUserId === tenancy.tenant_user_id ? tenancy.landlord_user_id : tenancy.tenant_user_id,
    payment_type: "rent",
    amount: String((tenancy.monthly_rent_minor || 0) / 100),
    due_date: "",
    proof_artifact_name: "",
    proof_summary: "",
    proof_file: null
  };
}

function buildPaymentProofForm() {
  return {
    proof_artifact_name: "",
    proof_summary: "",
    external_reference: "",
    proof_file: null
  };
}

function buildPaymentDecisionForm() {
  return {
    counterparty_notes: "",
    counterparty_file: null
  };
}

function buildPaymentDisputeForm() {
  return {
    dispute_notes: ""
  };
}

function buildAppealForm() {
  return {
    appeal_notes: ""
  };
}

function buildDepositSettlementForm(tenancy) {
  return {
    proposed_return: String((tenancy.deposit_minor || 0) / 100),
    withheld_amount: "0",
    settlement_summary: "",
    settlement_notes: "",
    settlement_file: null
  };
}

function buildDepositDisputeForm() {
  return {
    dispute_notes: ""
  };
}

function buildMaintenanceForm() {
  return {
    title: "",
    description: "",
    priority: "normal",
    reported_file: null
  };
}

function buildSimpleNotesForm() {
  return {
    notes: ""
  };
}

async function fetchDepositRecord(tenancyId) {
  try {
    return await apiRequest("/deposits/tenancies/" + tenancyId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

function formatArtifactMeta(contentType, sizeBytes) {
  var parts = [];
  if (contentType) {
    parts.push(contentType);
  }
  if (typeof sizeBytes === "number") {
    if (sizeBytes >= 1024 * 1024) {
      parts.push((sizeBytes / (1024 * 1024)).toFixed(1) + " MB");
    } else if (sizeBytes >= 1024) {
      parts.push(Math.round(sizeBytes / 1024) + " KB");
    } else {
      parts.push(String(sizeBytes) + " B");
    }
  }
  return parts.join(" | ");
}

async function uploadOperationalArtifact(tenancyId, file, artifactPurpose) {
  var formData = new FormData();
  formData.append("artifact", file);
  return apiRequest(
    "/evidence/tenancies/" +
      tenancyId +
      "/artifacts?artifact_purpose=" +
      encodeURIComponent(artifactPurpose),
    {
      method: "POST",
      body: formData
    }
  );
}

async function openStoredArtifact(artifactId) {
  var accessResponse = await apiRequest("/evidence/artifacts/" + artifactId + "/access", {
    method: "POST"
  });
  if (typeof window !== "undefined") {
    window.open(accessResponse.download_url, "_blank", "noopener");
  }
}

export function OperationsPage() {
  var session = useSession();
  var stateTuple = React.useState({
    status: "loading",
    tenancies: [],
    paymentsByTenancy: {},
    depositsByTenancy: {},
    maintenanceByTenancy: {},
    error: null
  });
  var state = stateTuple[0];
  var setState = stateTuple[1];
  var paymentFormsTuple = React.useState({});
  var paymentForms = paymentFormsTuple[0];
  var setPaymentForms = paymentFormsTuple[1];
  var paymentProofFormsTuple = React.useState({});
  var paymentProofForms = paymentProofFormsTuple[0];
  var setPaymentProofForms = paymentProofFormsTuple[1];
  var paymentDecisionFormsTuple = React.useState({});
  var paymentDecisionForms = paymentDecisionFormsTuple[0];
  var setPaymentDecisionForms = paymentDecisionFormsTuple[1];
  var paymentDisputeFormsTuple = React.useState({});
  var paymentDisputeForms = paymentDisputeFormsTuple[0];
  var setPaymentDisputeForms = paymentDisputeFormsTuple[1];
  var paymentAppealFormsTuple = React.useState({});
  var paymentAppealForms = paymentAppealFormsTuple[0];
  var setPaymentAppealForms = paymentAppealFormsTuple[1];
  var depositSettlementFormsTuple = React.useState({});
  var depositSettlementForms = depositSettlementFormsTuple[0];
  var setDepositSettlementForms = depositSettlementFormsTuple[1];
  var depositDisputeFormsTuple = React.useState({});
  var depositDisputeForms = depositDisputeFormsTuple[0];
  var setDepositDisputeForms = depositDisputeFormsTuple[1];
  var depositAppealFormsTuple = React.useState({});
  var depositAppealForms = depositAppealFormsTuple[0];
  var setDepositAppealForms = depositAppealFormsTuple[1];
  var maintenanceFormsTuple = React.useState({});
  var maintenanceForms = maintenanceFormsTuple[0];
  var setMaintenanceForms = maintenanceFormsTuple[1];
  var maintenanceAcknowledgeFormsTuple = React.useState({});
  var maintenanceAcknowledgeForms = maintenanceAcknowledgeFormsTuple[0];
  var setMaintenanceAcknowledgeForms = maintenanceAcknowledgeFormsTuple[1];
  var maintenanceResolveFormsTuple = React.useState({});
  var maintenanceResolveForms = maintenanceResolveFormsTuple[0];
  var setMaintenanceResolveForms = maintenanceResolveFormsTuple[1];
  var maintenanceDisputeFormsTuple = React.useState({});
  var maintenanceDisputeForms = maintenanceDisputeFormsTuple[0];
  var setMaintenanceDisputeForms = maintenanceDisputeFormsTuple[1];
  var maintenanceAppealFormsTuple = React.useState({});
  var maintenanceAppealForms = maintenanceAppealFormsTuple[0];
  var setMaintenanceAppealForms = maintenanceAppealFormsTuple[1];
  var actionTuple = React.useState({
    kind: "",
    id: "",
    message: null
  });
  var actionState = actionTuple[0];
  var setActionState = actionTuple[1];
  var operationsFocusTuple = React.useState("payments");
  var operationsFocus = operationsFocusTuple[0];
  var setOperationsFocus = operationsFocusTuple[1];

  var loadOperations = React.useCallback(async function loadOperations() {
    setState(function markLoading(previous) {
      return {
        status: previous.tenancies.length ? "refreshing" : "loading",
        tenancies: previous.tenancies,
        paymentsByTenancy: previous.paymentsByTenancy,
        depositsByTenancy: previous.depositsByTenancy,
        maintenanceByTenancy: previous.maintenanceByTenancy,
        error: null
      };
    });

    try {
      var tenancies = await apiRequest("/tenancies/mine");
      var tenancyPayloads = await Promise.all(
        tenancies.map(async function loadTenancyOperations(tenancy) {
          var results = await Promise.all([
            apiRequest("/payments/tenancies/" + tenancy.id),
            fetchDepositRecord(tenancy.id),
            apiRequest("/maintenance-tickets/tenancies/" + tenancy.id)
          ]);
          return {
            tenancyId: tenancy.id,
            payments: results[0],
            deposit: results[1],
            maintenance: results[2]
          };
        })
      );

      var paymentsByTenancy = {};
      var depositsByTenancy = {};
      var maintenanceByTenancy = {};
      tenancyPayloads.forEach(function assignPayload(payload) {
        paymentsByTenancy[payload.tenancyId] = payload.payments;
        depositsByTenancy[payload.tenancyId] = payload.deposit;
        maintenanceByTenancy[payload.tenancyId] = payload.maintenance;
      });

      setState({
        status: "ready",
        tenancies: tenancies,
        paymentsByTenancy: paymentsByTenancy,
        depositsByTenancy: depositsByTenancy,
        maintenanceByTenancy: maintenanceByTenancy,
        error: null
      });

      setPaymentForms(function syncForms(previous) {
        var next = Object.assign({}, previous);
        tenancies.forEach(function ensureForm(tenancy) {
          if (!next[tenancy.id]) {
            next[tenancy.id] = buildPaymentForm(session.user.id, tenancy);
          }
        });
        return next;
      });
      setDepositSettlementForms(function syncForms(previous) {
        var next = Object.assign({}, previous);
        tenancies.forEach(function ensureForm(tenancy) {
          if (!next[tenancy.id]) {
            next[tenancy.id] = buildDepositSettlementForm(tenancy);
          }
        });
        return next;
      });
      setMaintenanceForms(function syncForms(previous) {
        var next = Object.assign({}, previous);
        tenancies.forEach(function ensureForm(tenancy) {
          if (!next[tenancy.id]) {
            next[tenancy.id] = buildMaintenanceForm();
          }
        });
        return next;
      });
      setPaymentProofForms(function syncProofForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.payments.forEach(function ensureForm(payment) {
            if (!next[payment.id]) {
              next[payment.id] = buildPaymentProofForm();
            }
          });
        });
        return next;
      });
      setPaymentDecisionForms(function syncDecisionForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.payments.forEach(function ensureForm(payment) {
            if (!next[payment.id]) {
              next[payment.id] = buildPaymentDecisionForm();
            }
          });
        });
        return next;
      });
      setPaymentDisputeForms(function syncDisputeForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.payments.forEach(function ensureForm(payment) {
            if (!next[payment.id]) {
              next[payment.id] = buildPaymentDisputeForm();
            }
          });
        });
        return next;
      });
      setPaymentAppealForms(function syncAppealForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.payments.forEach(function ensureForm(payment) {
            if (!next[payment.id]) {
              next[payment.id] = buildAppealForm();
            }
          });
        });
        return next;
      });
      setDepositDisputeForms(function syncDisputeForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          if (payload.deposit && !next[payload.deposit.id]) {
            next[payload.deposit.id] = buildDepositDisputeForm();
          }
        });
        return next;
      });
      setDepositAppealForms(function syncAppealForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          if (payload.deposit && !next[payload.deposit.id]) {
            next[payload.deposit.id] = buildAppealForm();
          }
        });
        return next;
      });
      setMaintenanceAcknowledgeForms(function syncAcknowledgeForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.maintenance.forEach(function ensureForm(ticket) {
            if (!next[ticket.id]) {
              next[ticket.id] = buildSimpleNotesForm();
            }
          });
        });
        return next;
      });
      setMaintenanceResolveForms(function syncResolveForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.maintenance.forEach(function ensureForm(ticket) {
            if (!next[ticket.id]) {
              next[ticket.id] = {
                resolution_summary: "",
                landlord_response_notes: "",
                resolution_file: null
              };
            }
          });
        });
        return next;
      });
      setMaintenanceDisputeForms(function syncDisputeForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.maintenance.forEach(function ensureForm(ticket) {
            if (!next[ticket.id]) {
              next[ticket.id] = {
                dispute_notes: ""
              };
            }
          });
        });
        return next;
      });
      setMaintenanceAppealForms(function syncAppealForms(previous) {
        var next = Object.assign({}, previous);
        tenancyPayloads.forEach(function eachTenancy(payload) {
          payload.maintenance.forEach(function ensureForm(ticket) {
            if (!next[ticket.id]) {
              next[ticket.id] = buildAppealForm();
            }
          });
        });
        return next;
      });
    } catch (error) {
      setState({
        status: "error",
        tenancies: [],
        paymentsByTenancy: {},
        depositsByTenancy: {},
        maintenanceByTenancy: {},
        error: error.message || "Unable to load operational ledger data."
      });
    }
  }, [session.user.id]);

  React.useEffect(function bootstrapOperations() {
    loadOperations();
  }, [loadOperations]);

  async function runAction(kind, id, task, successMessage) {
    setActionState({ kind: kind, id: id, message: null });
    try {
      await task();
      await loadOperations();
      setActionState({ kind: "", id: "", message: successMessage });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to complete the requested operation."
      });
    }
  }

  if (state.status === "loading") {
    return e("div", { className: "state-panel" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Rent & Issues"),
      e("h1", { className: "state-title", key: "title" }, "Loading operational ledger"),
      e(
        "p",
        { className: "state-copy", key: "copy" },
        "We are loading payments, deposit activity, and maintenance updates."
      )
    ]);
  }

  if (state.status === "error") {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Rent & Issues"),
      e("h1", { className: "state-title", key: "title" }, "Operations unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  var openDepositDisputes = [];
  var openPaymentDisputes = [];
  var openMaintenanceDisputes = [];
  var paymentCount = 0;
  var maintenanceCount = 0;
  var depositCount = 0;
  var disputeOpportunities = [];
  state.tenancies.forEach(function collectDisputeData(tenancy) {
    var payments = state.paymentsByTenancy[tenancy.id] || [];
    var depositRecord = state.depositsByTenancy[tenancy.id];
    var maintenanceTickets = state.maintenanceByTenancy[tenancy.id] || [];
    paymentCount += payments.length;
    maintenanceCount += maintenanceTickets.length;
    if (depositRecord) {
      depositCount += 1;
    }
    payments.forEach(function collectPayment(payment) {
      if (["disputed", "under_review"].indexOf(payment.payment_status) !== -1) {
        openPaymentDisputes.push({
          tenancy: tenancy,
          payment: payment
        });
      }
      if (
        payment.payment_status === "rejected" &&
        session.user.id !== payment.counterparty_action_by_user_id
      ) {
        disputeOpportunities.push({
          type: "payment",
          tenancy: tenancy,
          payment: payment
        });
      }
    });
    if (depositRecord && ["disputed", "under_review"].indexOf(depositRecord.deposit_status) !== -1) {
      openDepositDisputes.push({
        tenancy: tenancy,
        depositRecord: depositRecord
      });
    }
    if (
      session.user.id === tenancy.tenant_user_id &&
      depositRecord &&
      ["return_submitted", "returned", "partially_withheld"].indexOf(depositRecord.deposit_status) !== -1
    ) {
      disputeOpportunities.push({
        type: "deposit",
        tenancy: tenancy,
        depositRecord: depositRecord
      });
    }
    maintenanceTickets.forEach(function collectTicket(ticket) {
      if (["disputed", "under_review"].indexOf(ticket.ticket_status) !== -1) {
        openMaintenanceDisputes.push({
          tenancy: tenancy,
          ticket: ticket
        });
      }
      if (session.user.id === tenancy.tenant_user_id && ticket.ticket_status === "resolved") {
        disputeOpportunities.push({
          type: "maintenance",
          tenancy: tenancy,
          ticket: ticket
        });
      }
    });
  });
  var operationsFocusTabs = [
    {
      id: "payments",
      label: "Payments",
      meta: "Create, confirm, dispute, or appeal payment records"
    },
    {
      id: "deposit",
      label: "Deposit",
      meta: "Open, settle, dispute, or appeal deposit handling"
    },
    {
      id: "maintenance",
      label: "Maintenance",
      meta: "Report, resolve, dispute, or appeal repair issues"
    },
    {
      id: "disputes",
      label: "Dispute desk",
      meta: String(disputeOpportunities.length + openDepositDisputes.length + openPaymentDisputes.length + openMaintenanceDisputes.length) + " live items"
    }
  ];

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Rent & Issues",
      title: "Rent, deposit, and repair tracking",
      copy:
        "Use this page for the day-to-day side of a tenancy: rent records, deposit handling, and maintenance issues.",
      details: [
        "The goal here is operational clarity: record the event, attach proof when needed, and only open the dispute lane when a disagreement actually exists."
      ],
      stats: [
        e(HeroStat, {
          label: "Payments",
          value: String(paymentCount),
          copy: "Payment records currently linked to your tenancies."
        }),
        e(HeroStat, {
          label: "Deposit records",
          value: String(depositCount),
          copy: "Deposit workflows currently in play."
        }),
        e(HeroStat, {
          label: "Maintenance & disputes",
          value: String(
            maintenanceCount +
              openDepositDisputes.length +
              openPaymentDisputes.length +
              openMaintenanceDisputes.length
          ),
          copy: String(
            openDepositDisputes.length + openPaymentDisputes.length + openMaintenanceDisputes.length
          ) + " items already need intervention."
        })
      ]
    }),
    actionState.message ? e("div", { className: "form-alert", key: "message" }, actionState.message) : null,
    e("section", { className: "detail-panel section-switcher", key: "focus-switcher" }, [
      e(SectionHeading, {
        title: "Focus on one operational lane",
        copy:
          operationsFocus === "disputes"
            ? "Use the dispute desk when you only want to see cases that already need intervention."
            : "Keep the day-to-day workspace lighter by focusing on one kind of task at a time.",
        key: "heading"
      }),
      e(SegmentedTabs, {
        key: "tabs",
        tabs: operationsFocusTabs,
        activeTab: operationsFocus,
        onChange: setOperationsFocus,
        "aria-label": "Operational workflow sections"
      })
    ]),
    operationsFocus === "disputes"
      ? e("section", { className: "detail-panel", key: "disputes-desk" }, [
      e("h2", { className: "detail-title", key: "title" }, "Dispute desk"),
      e(
        "p",
        { className: "empty-copy", key: "copy" },
        "This area surfaces anything already disputed and anything you can dispute right now, so you do not have to hunt through each tenancy to find the next step."
      ),
      e("div", { className: "fact-grid", key: "counts" }, [
        e(FactPill, { key: "deposit-open", label: "Open deposit disputes", value: String(openDepositDisputes.length), tone: "danger" }),
        e(FactPill, { key: "payment-open", label: "Open payment disputes", value: String(openPaymentDisputes.length), tone: "danger" }),
        e(FactPill, { key: "maintenance-open", label: "Open maintenance disputes", value: String(openMaintenanceDisputes.length), tone: "danger" }),
        e(FactPill, { key: "available", label: "You can dispute now", value: String(disputeOpportunities.length), tone: "warning" })
      ]),
      disputeOpportunities.length
        ? e(
            "div",
            { className: "list-stack", key: "opportunities" },
            disputeOpportunities.map(function renderOpportunity(item) {
              if (item.type === "payment") {
                var paymentDisputeForm =
                  paymentDisputeForms[item.payment.id] || buildPaymentDisputeForm();
                return e("article", { className: "stack-card", key: "payment:" + item.payment.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, item.tenancy.property_label + " | Payment can be disputed"),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, { key: "type", tone: "accent", label: item.payment.payment_type }),
                    e(StatusBadge, {
                      key: "status",
                      tone: inferStatusTone(item.payment.payment_status),
                      label: item.payment.payment_status
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "facts" }, [
                    e(FactPill, {
                      key: "amount",
                      label: "Amount",
                      value: formatMinorAmount(item.payment.amount_minor, item.payment.currency_code),
                      tone: "accent"
                    }),
                    e(FactPill, {
                      key: "route",
                      label: "Route",
                      value: item.payment.payer_user_full_name + " to " + item.payment.payee_user_full_name
                    })
                  ]),
                  e(NoteBlock, { key: "notes", tone: "danger", label: "Counterparty notes" }, item.payment.counterparty_notes || "Rejected without extra notes."),
                  e("input", {
                    className: "field-input",
                    value: paymentDisputeForm.dispute_notes,
                    onChange: function onChange(event) {
                      updateEntityForm(
                        setPaymentDisputeForms,
                        item.payment.id,
                        "dispute_notes",
                        event.target.value
                      );
                    },
                    placeholder: "Why are you disputing this payment decision?"
                  }),
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-small",
                      disabled: actionState.kind === "payment-dispute" && actionState.id === item.payment.id,
                      onClick: function onClick() {
                        runAction(
                          "payment-dispute",
                          item.payment.id,
                          function task() {
                            return apiRequest("/payments/" + item.payment.id + "/dispute", {
                              method: "POST",
                              body: paymentDisputeForm
                            });
                          },
                          "Payment dispute submitted."
                        );
                      }
                    },
                    actionState.kind === "payment-dispute" && actionState.id === item.payment.id
                      ? "Saving..."
                      : "Dispute payment"
                  )
                ]);
              }

              if (item.type === "deposit") {
                var depositDisputeForm =
                  depositDisputeForms[item.depositRecord.id] || buildDepositDisputeForm();
                return e("article", { className: "stack-card", key: "deposit:" + item.depositRecord.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, item.tenancy.property_label + " | Deposit settlement can be disputed"),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "deposit-status",
                      tone: inferStatusTone(item.depositRecord.deposit_status),
                      label: item.depositRecord.deposit_status
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "facts" }, [
                    e(FactPill, {
                      key: "proposed",
                      label: "Proposed return",
                      value: formatMinorAmount(item.depositRecord.proposed_return_minor, item.depositRecord.currency_code),
                      tone: "accent"
                    }),
                    e(FactPill, {
                      key: "withheld",
                      label: "Withheld amount",
                      value: formatMinorAmount(item.depositRecord.withheld_amount_minor, item.depositRecord.currency_code),
                      tone: "warning"
                    })
                  ]),
                  e("input", {
                    className: "field-input",
                    value: depositDisputeForm.dispute_notes,
                    onChange: function onChange(event) {
                      updateEntityForm(
                        setDepositDisputeForms,
                        item.depositRecord.id,
                        "dispute_notes",
                        event.target.value
                      );
                    },
                    placeholder: "Why are you disputing this deposit settlement?"
                  }),
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-small",
                      disabled: actionState.kind === "deposit-dispute" && actionState.id === item.depositRecord.id,
                      onClick: function onClick() {
                        runAction(
                          "deposit-dispute",
                          item.depositRecord.id,
                          function task() {
                            return apiRequest("/deposits/" + item.depositRecord.id + "/dispute", {
                              method: "POST",
                              body: depositDisputeForm
                            });
                          },
                          "Deposit dispute submitted."
                        );
                      }
                    },
                    actionState.kind === "deposit-dispute" && actionState.id === item.depositRecord.id
                      ? "Saving..."
                      : "Dispute deposit settlement"
                  )
                ]);
              }

              var maintenanceDisputeForm =
                maintenanceDisputeForms[item.ticket.id] || { dispute_notes: "" };
              return e("article", { className: "stack-card", key: "maintenance:" + item.ticket.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, item.tenancy.property_label + " | Maintenance resolution can be disputed"),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, { key: "ticket", tone: "accent", label: item.ticket.title }),
                  e(StatusBadge, { key: "resolved", tone: "success", label: "Resolved by landlord" })
                ]),
                e(NoteBlock, { key: "summary", tone: "accent", label: "Resolution summary" }, item.ticket.resolution_summary || "No resolution summary recorded."),
                e("input", {
                  className: "field-input",
                  value: maintenanceDisputeForm.dispute_notes,
                  onChange: function onChange(event) {
                    updateEntityForm(
                      setMaintenanceDisputeForms,
                      item.ticket.id,
                      "dispute_notes",
                      event.target.value
                    );
                  },
                  placeholder: "Why are you disputing this resolution?"
                }),
                e(
                  "button",
                  {
                    type: "button",
                    className: "button button-small",
                    disabled: actionState.kind === "maintenance-dispute" && actionState.id === item.ticket.id,
                    onClick: function onClick() {
                      runAction(
                        "maintenance-dispute",
                        item.ticket.id,
                        function task() {
                          return apiRequest("/maintenance-tickets/" + item.ticket.id + "/dispute", {
                            method: "POST",
                            body: maintenanceDisputeForm
                          });
                        },
                        "Maintenance dispute submitted."
                      );
                    }
                  },
                  actionState.kind === "maintenance-dispute" && actionState.id === item.ticket.id
                    ? "Saving..."
                    : "Dispute maintenance resolution"
                )
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "no-opportunities" },
            "Nothing is waiting for a new dispute from you right now."
          ),
      openDepositDisputes.length || openMaintenanceDisputes.length
        ? e("div", { className: "list-stack", key: "open-disputes" }, [
            openDepositDisputes.map(function renderDepositDispute(item) {
              return e("article", { className: "stack-card", key: "open-deposit:" + item.depositRecord.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, item.tenancy.property_label + " | Deposit dispute is open"),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, { key: "open", tone: "danger", label: "Disputed" }),
                  e(StatusBadge, {
                    key: "deposit-status",
                    tone: inferStatusTone(item.depositRecord.deposit_status),
                    label: item.depositRecord.deposit_status
                  })
                ]),
                e(NoteBlock, { key: "meta", tone: "danger", label: "Dispute notes" }, item.depositRecord.dispute_notes || "No dispute notes were recorded.")
              ]);
            }),
            openMaintenanceDisputes.map(function renderMaintenanceDispute(item) {
              return e("article", { className: "stack-card", key: "open-maintenance:" + item.ticket.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, item.tenancy.property_label + " | Maintenance dispute is open"),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, { key: "open", tone: "danger", label: "Disputed" }),
                  e(StatusBadge, {
                    key: "ticket-status",
                    tone: inferStatusTone(item.ticket.ticket_status),
                    label: item.ticket.ticket_status
                  })
                ]),
                e(NoteBlock, {
                  key: "meta",
                  tone: "danger",
                  label: item.ticket.title
                }, item.ticket.dispute_notes || "No dispute notes were recorded.")
              ]);
            })
          ])
        : e(
            "p",
            { className: "empty-copy", key: "no-open-disputes" },
            "There are no open disputes across your current tenancy records."
          )
    ])
      : null,
    operationsFocus !== "disputes" && state.tenancies.length
      ? e(
          "div",
          { className: "list-stack", key: "tenancies" },
          state.tenancies.map(function renderTenancy(tenancy) {
             var paymentForm = paymentForms[tenancy.id] || buildPaymentForm(session.user.id, tenancy);
             var depositRecord = state.depositsByTenancy[tenancy.id];
             var depositSettlementForm = depositSettlementForms[tenancy.id] || buildDepositSettlementForm(tenancy);
             var depositDisputeForm = depositRecord
               ? depositDisputeForms[depositRecord.id] || buildDepositDisputeForm()
               : buildDepositDisputeForm();
             var depositAppealForm = depositRecord
               ? depositAppealForms[depositRecord.id] || buildAppealForm()
               : buildAppealForm();
             var maintenanceForm = maintenanceForms[tenancy.id] || buildMaintenanceForm();

            return e("section", { className: "detail-panel", key: tenancy.id }, [
              e("h2", { className: "detail-title", key: "title" }, tenancy.property_label),
              e("div", { className: "status-row", key: "status" }, [
                e(StatusBadge, {
                  key: "tenancy",
                  tone: "accent",
                  label: tenancy.tenancy_status
                }),
                e(StatusBadge, {
                  key: "verification",
                  tone: inferStatusTone(tenancy.verification_status),
                  label: "Verification " + tenancy.verification_status
                })
              ]),
              e("div", { className: "fact-grid", key: "meta" }, [
                e(FactPill, { key: "city", label: "City", value: tenancy.city }),
                e(FactPill, {
                  key: "parties",
                  label: "Parties",
                  value: tenancy.tenant_full_name + " and " + tenancy.landlord_full_name,
                  tone: "accent"
                })
              ]),
              e("div", { className: "split-grid", key: "top" }, [
                operationsFocus === "payments" ? e("article", { className: "stack-card", key: "payments" }, [
                  e("strong", { className: "stack-card-title", key: "title" }, "Payments"),
                  e("div", { className: "auth-form", key: "create-payment" }, [
                    e("label", { className: "field", key: "payer" }, [
                      e("span", { className: "field-label", key: "label" }, "Payer"),
                      e(
                        "select",
                        {
                          className: "field-input field-select",
                          value: paymentForm.payer_user_id,
                          onChange: function onChange(event) {
                            var nextPayerId = event.target.value;
                            var nextPayeeId =
                              nextPayerId === tenancy.tenant_user_id
                                ? tenancy.landlord_user_id
                                : tenancy.tenant_user_id;
                            updateEntityForm(setPaymentForms, tenancy.id, "payer_user_id", nextPayerId);
                            updateEntityForm(setPaymentForms, tenancy.id, "payee_user_id", nextPayeeId);
                          }
                        },
                        [
                          e("option", { value: tenancy.tenant_user_id, key: "tenant" }, tenancy.tenant_full_name),
                          e("option", { value: tenancy.landlord_user_id, key: "landlord" }, tenancy.landlord_full_name)
                        ]
                      )
                    ]),
                    e("div", { className: "form-grid", key: "row" }, [
                      e("input", {
                        className: "field-input",
                        type: "number",
                        min: "0",
                        step: "0.01",
                        value: paymentForm.amount,
                        onChange: function onChange(event) {
                          updateEntityForm(setPaymentForms, tenancy.id, "amount", event.target.value);
                        },
                        placeholder: "Amount"
                      }),
                      e("input", {
                        className: "field-input",
                        type: "date",
                        value: paymentForm.due_date,
                        onChange: function onChange(event) {
                          updateEntityForm(setPaymentForms, tenancy.id, "due_date", event.target.value);
                        }
                      }),
                      e(
                        "select",
                        {
                          className: "field-input field-select",
                          value: paymentForm.payment_type,
                          onChange: function onChange(event) {
                            updateEntityForm(setPaymentForms, tenancy.id, "payment_type", event.target.value);
                          }
                        },
                        [
                          e("option", { value: "rent", key: "rent" }, "Rent"),
                          e("option", { value: "utility_reimbursement", key: "utility" }, "Utility reimbursement"),
                          e("option", { value: "maintenance_reimbursement", key: "maintenance" }, "Maintenance reimbursement"),
                          e("option", { value: "other", key: "other" }, "Other")
                        ]
                      )
                    ]),
                    e("input", {
                      className: "field-input",
                      value: paymentForm.proof_artifact_name,
                      onChange: function onChange(event) {
                        updateEntityForm(setPaymentForms, tenancy.id, "proof_artifact_name", event.target.value);
                      },
                      placeholder: "Proof artifact name"
                    }),
                    e("input", {
                      className: "field-input",
                      type: "file",
                      onChange: function onChange(event) {
                        updateEntityForm(
                          setPaymentForms,
                          tenancy.id,
                          "proof_file",
                          event.target.files && event.target.files[0] ? event.target.files[0] : null
                        );
                      }
                    }),
                    e("input", {
                      className: "field-input",
                      value: paymentForm.proof_summary,
                      onChange: function onChange(event) {
                        updateEntityForm(setPaymentForms, tenancy.id, "proof_summary", event.target.value);
                      },
                      placeholder: "Proof summary"
                    }),
                    e(
                      "button",
                      {
                        type: "button",
                        className: "button button-secondary",
                        disabled: actionState.kind === "payment-create" && actionState.id === tenancy.id,
                        onClick: function onClick() {
                          runAction(
                            "payment-create",
                            tenancy.id,
                            async function task() {
                              if (paymentForm.proof_file && !String(paymentForm.proof_summary || "").trim()) {
                                throw new Error("Add a short proof summary before uploading a payment proof file.");
                              }
                              var storedArtifact = null;
                              if (paymentForm.proof_file) {
                                storedArtifact = await uploadOperationalArtifact(
                                  tenancy.id,
                                  paymentForm.proof_file,
                                  "payment_proof"
                                );
                              }
                              var body = {
                                payer_user_id: paymentForm.payer_user_id,
                                payee_user_id: paymentForm.payee_user_id,
                                payment_type: paymentForm.payment_type,
                                amount_minor: parseMinorAmount(paymentForm.amount),
                                currency_code: tenancy.currency_code,
                                due_date: paymentForm.due_date
                              };
                              if (
                                paymentForm.proof_summary &&
                                (paymentForm.proof_artifact_name || storedArtifact)
                              ) {
                                body.proof_artifact_name =
                                  paymentForm.proof_artifact_name ||
                                  storedArtifact.original_file_name;
                                body.proof_summary = paymentForm.proof_summary;
                                body.proof_stored_artifact_id = storedArtifact
                                  ? storedArtifact.id
                                  : undefined;
                              }
                              await apiRequest("/payments/tenancies/" + tenancy.id, {
                                method: "POST",
                                body: body
                              });
                              setPaymentForms(function resetPaymentForm(previous) {
                                var next = Object.assign({}, previous);
                                next[tenancy.id] = buildPaymentForm(session.user.id, tenancy);
                                return next;
                              });
                            },
                            "Payment record created."
                          );
                        }
                      },
                      actionState.kind === "payment-create" && actionState.id === tenancy.id
                        ? "Saving..."
                        : "Create payment record"
                    )
                  ]),
                  state.paymentsByTenancy[tenancy.id] && state.paymentsByTenancy[tenancy.id].length
                    ? e(
                        "div",
                        { className: "list-stack", key: "payment-list" },
                        state.paymentsByTenancy[tenancy.id].map(function renderPayment(payment) {
                          var paymentProofForm = paymentProofForms[payment.id] || buildPaymentProofForm();
                          var paymentDecisionForm = paymentDecisionForms[payment.id] || buildPaymentDecisionForm();
                          var paymentDisputeForm = paymentDisputeForms[payment.id] || buildPaymentDisputeForm();
                          var paymentAppealForm = paymentAppealForms[payment.id] || buildAppealForm();
                          return e("article", { className: "stack-card", key: payment.id }, [
                            e("strong", { className: "stack-card-title", key: "title" }, payment.payment_type),
                            e("div", { className: "status-row", key: "status" }, [
                              e(StatusBadge, {
                                key: "payment-status",
                                tone: inferStatusTone(payment.payment_status),
                                label: payment.payment_status
                              })
                            ]),
                            e("div", { className: "fact-grid", key: "facts" }, [
                              e(FactPill, {
                                key: "amount",
                                label: "Amount",
                                value: formatMinorAmount(payment.amount_minor, payment.currency_code),
                                tone: "accent"
                              }),
                              e(FactPill, {
                                key: "route",
                                label: "Route",
                                value: payment.payer_user_full_name + " to " + payment.payee_user_full_name
                              })
                            ]),
                            payment.proof_artifact_name
                              ? e(
                                  NoteBlock,
                                  { key: "proof-name", label: "Proof file", tone: "accent" },
                                  "Proof: " +
                                    payment.proof_artifact_name +
                                    (formatArtifactMeta(
                                      payment.proof_artifact_content_type,
                                      payment.proof_artifact_size_bytes
                                    )
                                      ? " | " +
                                        formatArtifactMeta(
                                          payment.proof_artifact_content_type,
                                          payment.proof_artifact_size_bytes
                                        )
                                      : "")
                                )
                              : null,
                            payment.proof_summary
                              ? e(
                                  NoteBlock,
                                  { key: "proof-summary", label: "Proof summary", tone: "accent" },
                                  payment.proof_summary
                                )
                              : null,
                            payment.proof_stored_artifact_id
                              ? e(
                                  "button",
                                  {
                                    type: "button",
                                    className: "button button-small",
                                    onClick: function onClick() {
                                      openStoredArtifact(payment.proof_stored_artifact_id);
                                    },
                                    key: "open-proof"
                                  },
                                  "Open proof file"
                                )
                              : null,
                            payment.counterparty_artifact_name
                              ? e(
                                  NoteBlock,
                                  { key: "counterparty-file", label: "Counterparty evidence", tone: "warning" },
                                  "Counterparty evidence: " +
                                    payment.counterparty_artifact_name +
                                    (formatArtifactMeta(
                                      payment.counterparty_artifact_content_type,
                                      payment.counterparty_artifact_size_bytes
                                    )
                                      ? " | " +
                                        formatArtifactMeta(
                                          payment.counterparty_artifact_content_type,
                                          payment.counterparty_artifact_size_bytes
                                        )
                                      : "")
                                )
                              : null,
                            payment.counterparty_stored_artifact_id
                              ? e(
                                  "button",
                                  {
                                    type: "button",
                                    className: "button button-small",
                                    onClick: function onClick() {
                                      openStoredArtifact(payment.counterparty_stored_artifact_id);
                                    },
                                    key: "open-counterparty-proof"
                                  },
                                  "Open counterparty evidence"
                                )
                              : null,
                            payment.counterparty_notes
                              ? e(
                                  NoteBlock,
                                  { key: "counterparty-notes", label: "Counterparty notes", tone: "warning" },
                                  payment.counterparty_notes
                                )
                              : null,
                            payment.dispute_notes
                              ? e(
                                  NoteBlock,
                                  { key: "dispute-notes", label: "Dispute notes", tone: "danger" },
                                  payment.dispute_notes
                                )
                              : null,
                            payment.verdict_summary
                              ? e(
                                  NoteBlock,
                                  { key: "verdict-summary", label: "Verdict", tone: "danger" },
                                  "Judge verdict: " +
                                    payment.verdict_summary +
                                    " | Outcome: " +
                                    payment.verdict_outcome +
                                    " | Tenant delta " +
                                    String(payment.verdict_tenant_score_delta) +
                                    " | Landlord delta " +
                                    String(payment.verdict_landlord_score_delta)
                                )
                              : null,
                            payment.appeal_notes
                              ? e(
                                  NoteBlock,
                                  { key: "appeal-notes", label: "Appeal notes", tone: "danger" },
                                  payment.appeal_notes
                                )
                              : null,
                            session.user.id === payment.payer_user_id && payment.payment_status !== "confirmed"
                            && ["disputed", "under_review", "verdict_issued"].indexOf(payment.payment_status) === -1
                              ? e("div", { className: "form-grid", key: "proof" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: paymentProofForm.proof_artifact_name,
                                    onChange: function onChange(event) {
                                      updateEntityForm(setPaymentProofForms, payment.id, "proof_artifact_name", event.target.value);
                                    },
                                    placeholder: "Proof artifact"
                                  }),
                                  e("input", {
                                    className: "field-input",
                                    type: "file",
                                    onChange: function onChange(event) {
                                      updateEntityForm(
                                        setPaymentProofForms,
                                        payment.id,
                                        "proof_file",
                                        event.target.files && event.target.files[0]
                                          ? event.target.files[0]
                                          : null
                                      );
                                    }
                                  }),
                                  e("input", {
                                    className: "field-input",
                                    value: paymentProofForm.proof_summary,
                                    onChange: function onChange(event) {
                                      updateEntityForm(setPaymentProofForms, payment.id, "proof_summary", event.target.value);
                                    },
                                    placeholder: "Proof summary"
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-secondary button-small",
                                      disabled: actionState.kind === "payment-proof" && actionState.id === payment.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "payment-proof",
                                          payment.id,
                                          async function task() {
                                            if (
                                              paymentProofForm.proof_file &&
                                              !String(paymentProofForm.proof_summary || "").trim()
                                            ) {
                                              throw new Error(
                                                "Add a short proof summary before uploading a payment proof file."
                                              );
                                            }
                                            var storedArtifact = null;
                                            if (paymentProofForm.proof_file) {
                                              storedArtifact = await uploadOperationalArtifact(
                                                tenancy.id,
                                                paymentProofForm.proof_file,
                                                "payment_proof"
                                              );
                                            }
                                            await apiRequest("/payments/" + payment.id + "/proof", {
                                              method: "POST",
                                              body: {
                                                proof_artifact_name:
                                                  paymentProofForm.proof_artifact_name ||
                                                  (storedArtifact
                                                    ? storedArtifact.original_file_name
                                                    : ""),
                                                proof_summary: paymentProofForm.proof_summary,
                                                external_reference:
                                                  paymentProofForm.external_reference || undefined,
                                                proof_stored_artifact_id: storedArtifact
                                                  ? storedArtifact.id
                                                  : undefined
                                              }
                                            });
                                            setPaymentProofForms(function resetPaymentProof(previous) {
                                              var next = Object.assign({}, previous);
                                              next[payment.id] = buildPaymentProofForm();
                                              return next;
                                            });
                                          },
                                          "Payment proof submitted."
                                        );
                                      }
                                    },
                                    actionState.kind === "payment-proof" && actionState.id === payment.id
                                      ? "Saving..."
                                      : "Submit proof"
                                  )
                                ])
                              : null,
                            session.user.id === payment.payee_user_id
                              ? e("div", { className: "form-grid", key: "decision" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: paymentDecisionForm.counterparty_notes,
                                    onChange: function onChange(event) {
                                      updateEntityForm(setPaymentDecisionForms, payment.id, "counterparty_notes", event.target.value);
                                    },
                                    placeholder: "Decision notes"
                                  }),
                                  e("input", {
                                    className: "field-input",
                                    type: "file",
                                    onChange: function onChange(event) {
                                      updateEntityForm(
                                        setPaymentDecisionForms,
                                        payment.id,
                                        "counterparty_file",
                                        event.target.files && event.target.files[0]
                                          ? event.target.files[0]
                                          : null
                                      );
                                    }
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-secondary button-small",
                                      disabled: actionState.kind === "payment-confirm" && actionState.id === payment.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "payment-confirm",
                                          payment.id,
                                          async function task() {
                                            var storedArtifact = null;
                                            if (paymentDecisionForm.counterparty_file) {
                                              storedArtifact = await uploadOperationalArtifact(
                                                tenancy.id,
                                                paymentDecisionForm.counterparty_file,
                                                "payment_counterparty"
                                              );
                                            }
                                            return apiRequest("/payments/" + payment.id + "/decision", {
                                              method: "POST",
                                              body: {
                                                payment_status: "confirmed",
                                                counterparty_notes: paymentDecisionForm.counterparty_notes,
                                                counterparty_stored_artifact_id: storedArtifact
                                                  ? storedArtifact.id
                                                  : undefined,
                                                counterparty_artifact_name: storedArtifact
                                                  ? storedArtifact.original_file_name
                                                  : undefined
                                              }
                                            });
                                          },
                                          "Payment confirmed."
                                        );
                                      }
                                    },
                                    actionState.kind === "payment-confirm" && actionState.id === payment.id
                                      ? "Saving..."
                                      : "Confirm"
                                  ),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-small",
                                      disabled: actionState.kind === "payment-reject" && actionState.id === payment.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "payment-reject",
                                          payment.id,
                                          async function task() {
                                            var storedArtifact = null;
                                            if (paymentDecisionForm.counterparty_file) {
                                              storedArtifact = await uploadOperationalArtifact(
                                                tenancy.id,
                                                paymentDecisionForm.counterparty_file,
                                                "payment_counterparty"
                                              );
                                            }
                                            return apiRequest("/payments/" + payment.id + "/decision", {
                                              method: "POST",
                                              body: {
                                                payment_status: "rejected",
                                                counterparty_notes: paymentDecisionForm.counterparty_notes,
                                                counterparty_stored_artifact_id: storedArtifact
                                                  ? storedArtifact.id
                                                  : undefined,
                                                counterparty_artifact_name: storedArtifact
                                                  ? storedArtifact.original_file_name
                                                  : undefined
                                              }
                                            });
                                          },
                                          "Payment rejected."
                                        );
                                      }
                                    },
                                    actionState.kind === "payment-reject" && actionState.id === payment.id
                                      ? "Saving..."
                                      : "Reject"
                                  )
                                ])
                              : null,
                            payment.payment_status === "rejected" &&
                            session.user.id !== payment.counterparty_action_by_user_id
                              ? e("div", { className: "form-grid", key: "payment-dispute" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: paymentDisputeForm.dispute_notes,
                                    onChange: function onChange(event) {
                                      updateEntityForm(
                                        setPaymentDisputeForms,
                                        payment.id,
                                        "dispute_notes",
                                        event.target.value
                                      );
                                    },
                                    placeholder: "Dispute notes"
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-small",
                                      disabled: actionState.kind === "payment-dispute" && actionState.id === payment.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "payment-dispute",
                                          payment.id,
                                          function task() {
                                            return apiRequest("/payments/" + payment.id + "/dispute", {
                                              method: "POST",
                                              body: paymentDisputeForm
                                            });
                                          },
                                          "Payment dispute submitted."
                                        );
                                      }
                                    },
                                    actionState.kind === "payment-dispute" && actionState.id === payment.id
                                      ? "Saving..."
                                      : "Dispute payment"
                                  )
                                ])
                              : null,
                            payment.payment_status === "verdict_issued"
                              ? e("div", { className: "form-grid", key: "payment-appeal" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: paymentAppealForm.appeal_notes,
                                    onChange: function onChange(event) {
                                      updateEntityForm(
                                        setPaymentAppealForms,
                                        payment.id,
                                        "appeal_notes",
                                        event.target.value
                                      );
                                    },
                                    placeholder: "Appeal notes"
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-secondary button-small",
                                      disabled: actionState.kind === "payment-appeal" && actionState.id === payment.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "payment-appeal",
                                          payment.id,
                                          function task() {
                                            return apiRequest("/payments/" + payment.id + "/appeal", {
                                              method: "POST",
                                              body: paymentAppealForm
                                            });
                                          },
                                          "Payment appeal submitted."
                                        );
                                      }
                                    },
                                    actionState.kind === "payment-appeal" && actionState.id === payment.id
                                      ? "Saving..."
                                      : "Appeal verdict"
                                  )
                                ])
                              : null
                          ]);
                        })
                      )
                    : e("p", { className: "empty-copy", key: "empty" }, "No payment records yet.")
                ]) : null,
                operationsFocus === "deposit" ? e("article", { className: "stack-card", key: "deposit" }, [
                  e("strong", { className: "stack-card-title", key: "title" }, "Deposit"),
                  depositRecord
                    ? [
                        e("div", { className: "status-row", key: "status" }, [
                          e(StatusBadge, {
                            key: "deposit-status",
                            tone: inferStatusTone(depositRecord.deposit_status),
                            label: depositRecord.deposit_status
                          })
                        ]),
                        e("div", { className: "fact-grid", key: "totals" }, [
                          e(FactPill, {
                            key: "held",
                            label: "Held",
                            value: formatMinorAmount(depositRecord.held_amount_minor, depositRecord.currency_code),
                            tone: "accent"
                          }),
                          e(FactPill, {
                            key: "return",
                            label: "Return",
                            value: formatMinorAmount(depositRecord.proposed_return_minor, depositRecord.currency_code),
                            tone: "success"
                          }),
                          e(FactPill, {
                            key: "withheld",
                            label: "Withheld",
                            value: formatMinorAmount(depositRecord.withheld_amount_minor, depositRecord.currency_code),
                            tone: "warning"
                          })
                        ]),
                        depositRecord.settlement_artifact_name
                          ? e(
                              NoteBlock,
                              { key: "settlement-file", label: "Settlement proof", tone: "accent" },
                              "Settlement proof: " +
                                depositRecord.settlement_artifact_name +
                                (formatArtifactMeta(
                                  depositRecord.settlement_artifact_content_type,
                                  depositRecord.settlement_artifact_size_bytes
                                )
                                  ? " | " +
                                    formatArtifactMeta(
                                      depositRecord.settlement_artifact_content_type,
                                      depositRecord.settlement_artifact_size_bytes
                                    )
                                  : "")
                            )
                          : null,
                        depositRecord.settlement_summary
                          ? e(
                              NoteBlock,
                              { key: "settlement-summary", label: "Settlement summary", tone: "accent" },
                              depositRecord.settlement_summary
                            )
                          : null,
                        depositRecord.dispute_notes
                          ? e(
                              NoteBlock,
                              { key: "deposit-dispute-notes", label: "Dispute notes", tone: "danger" },
                              depositRecord.dispute_notes
                            )
                          : null,
                        depositRecord.verdict_summary
                          ? e(
                              NoteBlock,
                              { key: "deposit-verdict-summary", label: "Verdict", tone: "danger" },
                              depositRecord.verdict_summary
                            )
                          : null,
                        depositRecord.appeal_notes
                          ? e(
                              NoteBlock,
                              { key: "deposit-appeal-notes", label: "Appeal notes", tone: "danger" },
                              depositRecord.appeal_notes
                            )
                          : null,
                        depositRecord.settlement_stored_artifact_id
                          ? e(
                              "button",
                              {
                                type: "button",
                                className: "button button-small",
                                onClick: function onClick() {
                                  openStoredArtifact(depositRecord.settlement_stored_artifact_id);
                                },
                                key: "open-settlement-proof"
                              },
                              "Open settlement proof"
                            )
                          : null,
                        session.user.id === tenancy.landlord_user_id &&
                        ["held", "return_submitted", "returned", "partially_withheld"].indexOf(depositRecord.deposit_status) !== -1
                          ? e("div", { className: "auth-form", key: "settlement" }, [
                              e("div", { className: "form-grid", key: "amounts" }, [
                                e("input", {
                                  className: "field-input",
                                  type: "number",
                                  min: "0",
                                  step: "0.01",
                                  value: depositSettlementForm.proposed_return,
                                  onChange: function onChange(event) {
                                    updateEntityForm(setDepositSettlementForms, tenancy.id, "proposed_return", event.target.value);
                                  },
                                  placeholder: "Return amount"
                                }),
                                e("input", {
                                  className: "field-input",
                                  type: "number",
                                  min: "0",
                                  step: "0.01",
                                  value: depositSettlementForm.withheld_amount,
                                  onChange: function onChange(event) {
                                    updateEntityForm(setDepositSettlementForms, tenancy.id, "withheld_amount", event.target.value);
                                  },
                                  placeholder: "Withheld amount"
                                })
                              ]),
                              e("input", {
                                className: "field-input",
                                value: depositSettlementForm.settlement_summary,
                                onChange: function onChange(event) {
                                  updateEntityForm(setDepositSettlementForms, tenancy.id, "settlement_summary", event.target.value);
                                },
                                placeholder: "Settlement summary"
                              }),
                              e("input", {
                                className: "field-input",
                                type: "file",
                                onChange: function onChange(event) {
                                  updateEntityForm(
                                    setDepositSettlementForms,
                                    tenancy.id,
                                    "settlement_file",
                                    event.target.files && event.target.files[0]
                                      ? event.target.files[0]
                                      : null
                                  );
                                }
                              }),
                              e("input", {
                                className: "field-input",
                                value: depositSettlementForm.settlement_notes,
                                onChange: function onChange(event) {
                                  updateEntityForm(setDepositSettlementForms, tenancy.id, "settlement_notes", event.target.value);
                                },
                                placeholder: "Settlement notes"
                              }),
                              e(
                                "button",
                                {
                                  type: "button",
                                  className: "button button-secondary",
                                  disabled: actionState.kind === "deposit-settlement" && actionState.id === depositRecord.id,
                                  onClick: function onClick() {
                                    runAction(
                                      "deposit-settlement",
                                      depositRecord.id,
                                      async function task() {
                                        if (
                                          depositSettlementForm.settlement_file &&
                                          !String(depositSettlementForm.settlement_summary || "").trim()
                                        ) {
                                          throw new Error(
                                            "Add a short settlement summary before uploading a settlement proof file."
                                          );
                                        }
                                        var storedArtifact = null;
                                        if (depositSettlementForm.settlement_file) {
                                          storedArtifact = await uploadOperationalArtifact(
                                            tenancy.id,
                                            depositSettlementForm.settlement_file,
                                            "deposit_settlement"
                                          );
                                        }
                                        await apiRequest("/deposits/" + depositRecord.id + "/settlement", {
                                          method: "POST",
                                          body: {
                                            proposed_return_minor: parseMinorAmount(depositSettlementForm.proposed_return),
                                            withheld_amount_minor: parseMinorAmount(depositSettlementForm.withheld_amount),
                                            settlement_summary: depositSettlementForm.settlement_summary,
                                            settlement_notes: depositSettlementForm.settlement_notes,
                                            settlement_stored_artifact_id: storedArtifact
                                              ? storedArtifact.id
                                              : undefined,
                                            settlement_artifact_name: storedArtifact
                                              ? storedArtifact.original_file_name
                                              : undefined
                                          }
                                        });
                                        setDepositSettlementForms(function resetSettlementForm(previous) {
                                          var next = Object.assign({}, previous);
                                          next[tenancy.id] = buildDepositSettlementForm(tenancy);
                                          return next;
                                        });
                                      },
                                      "Deposit settlement submitted."
                                    );
                                  }
                                },
                                actionState.kind === "deposit-settlement" && actionState.id === depositRecord.id
                                  ? "Saving..."
                                  : "Submit settlement"
                              )
                            ])
                          : null
                        ,
                        session.user.id === tenancy.tenant_user_id &&
                        ["return_submitted", "returned", "partially_withheld"].indexOf(depositRecord.deposit_status) !== -1
                          ? e("div", { className: "form-grid", key: "dispute" }, [
                              e("input", {
                                className: "field-input",
                                value: depositDisputeForm.dispute_notes,
                                onChange: function onChange(event) {
                                  updateEntityForm(setDepositDisputeForms, depositRecord.id, "dispute_notes", event.target.value);
                                },
                                placeholder: "Dispute notes"
                              }),
                              e(
                                "button",
                                {
                                  type: "button",
                                  className: "button button-small",
                                  disabled: actionState.kind === "deposit-dispute" && actionState.id === depositRecord.id,
                                  onClick: function onClick() {
                                    runAction(
                                      "deposit-dispute",
                                      depositRecord.id,
                                      function task() {
                                        return apiRequest("/deposits/" + depositRecord.id + "/dispute", {
                                          method: "POST",
                                          body: depositDisputeForm
                                        });
                                      },
                                      "Deposit dispute submitted."
                                    );
                                  }
                                },
                                actionState.kind === "deposit-dispute" && actionState.id === depositRecord.id
                                  ? "Saving..."
                                  : "Dispute settlement"
                              )
                            ])
                          : null
                        ,
                        depositRecord.deposit_status === "verdict_issued"
                          ? e("div", { className: "form-grid", key: "deposit-appeal" }, [
                              e("input", {
                                className: "field-input",
                                value: depositAppealForm.appeal_notes,
                                onChange: function onChange(event) {
                                  updateEntityForm(
                                    setDepositAppealForms,
                                    depositRecord.id,
                                    "appeal_notes",
                                    event.target.value
                                  );
                                },
                                placeholder: "Appeal notes"
                              }),
                              e(
                                "button",
                                {
                                  type: "button",
                                  className: "button button-secondary button-small",
                                  disabled: actionState.kind === "deposit-appeal" && actionState.id === depositRecord.id,
                                  onClick: function onClick() {
                                    runAction(
                                      "deposit-appeal",
                                      depositRecord.id,
                                      function task() {
                                        return apiRequest("/deposits/" + depositRecord.id + "/appeal", {
                                          method: "POST",
                                          body: depositAppealForm
                                        });
                                      },
                                      "Deposit appeal submitted."
                                    );
                                  }
                                },
                                actionState.kind === "deposit-appeal" && actionState.id === depositRecord.id
                                  ? "Saving..."
                                  : "Appeal verdict"
                              )
                            ])
                          : null
                      ]
                    : tenancy.deposit_minor > 0
                      ? e(
                          "button",
                          {
                            type: "button",
                            className: "button button-secondary",
                            disabled: actionState.kind === "deposit-create" && actionState.id === tenancy.id,
                            onClick: function onClick() {
                              runAction(
                                "deposit-create",
                                tenancy.id,
                                function task() {
                                  return apiRequest("/deposits/tenancies/" + tenancy.id, {
                                    method: "POST",
                                    body: {}
                                  });
                                },
                                "Deposit record opened."
                              );
                            }
                          },
                          actionState.kind === "deposit-create" && actionState.id === tenancy.id
                            ? "Saving..."
                            : "Open deposit record"
                        )
                      : e("p", { className: "empty-copy", key: "none" }, "This tenancy does not have a recorded deposit.")
                ]) : null,
                operationsFocus === "maintenance" ? e("article", { className: "stack-card", key: "maintenance" }, [
                  e("strong", { className: "stack-card-title", key: "title" }, "Maintenance"),
                  e("div", { className: "auth-form", key: "report" }, [
                    e("div", { className: "form-grid", key: "top" }, [
                      e("input", {
                        className: "field-input",
                        value: maintenanceForm.title,
                        onChange: function onChange(event) {
                          updateEntityForm(setMaintenanceForms, tenancy.id, "title", event.target.value);
                        },
                        placeholder: "Issue title"
                      }),
                      e(
                        "select",
                        {
                          className: "field-input field-select",
                          value: maintenanceForm.priority,
                          onChange: function onChange(event) {
                            updateEntityForm(setMaintenanceForms, tenancy.id, "priority", event.target.value);
                          }
                        },
                        [
                          e("option", { value: "low", key: "low" }, "Low"),
                          e("option", { value: "normal", key: "normal" }, "Normal"),
                          e("option", { value: "high", key: "high" }, "High"),
                          e("option", { value: "urgent", key: "urgent" }, "Urgent")
                        ]
                      )
                    ]),
                    e("input", {
                      className: "field-input",
                      value: maintenanceForm.description,
                      onChange: function onChange(event) {
                        updateEntityForm(setMaintenanceForms, tenancy.id, "description", event.target.value);
                      },
                      placeholder: "Issue description"
                    }),
                    e("input", {
                      className: "field-input",
                      type: "file",
                      onChange: function onChange(event) {
                        updateEntityForm(
                          setMaintenanceForms,
                          tenancy.id,
                          "reported_file",
                          event.target.files && event.target.files[0] ? event.target.files[0] : null
                        );
                      }
                    }),
                    e(
                      "button",
                      {
                        type: "button",
                        className: "button button-secondary",
                        disabled: actionState.kind === "maintenance-create" && actionState.id === tenancy.id,
                        onClick: function onClick() {
                          runAction(
                            "maintenance-create",
                            tenancy.id,
                            async function task() {
                              var storedArtifact = null;
                              if (maintenanceForm.reported_file) {
                                storedArtifact = await uploadOperationalArtifact(
                                  tenancy.id,
                                  maintenanceForm.reported_file,
                                  "maintenance_report"
                                );
                              }
                              await apiRequest("/maintenance-tickets/tenancies/" + tenancy.id, {
                                method: "POST",
                                body: {
                                  title: maintenanceForm.title,
                                  description: maintenanceForm.description,
                                  priority: maintenanceForm.priority,
                                  reported_stored_artifact_id: storedArtifact
                                    ? storedArtifact.id
                                    : undefined,
                                  reported_artifact_name: storedArtifact
                                    ? storedArtifact.original_file_name
                                    : undefined
                                }
                              });
                              setMaintenanceForms(function resetMaintenanceForm(previous) {
                                var next = Object.assign({}, previous);
                                next[tenancy.id] = buildMaintenanceForm();
                                return next;
                              });
                            },
                            "Maintenance issue reported."
                          );
                        }
                      },
                      actionState.kind === "maintenance-create" && actionState.id === tenancy.id
                        ? "Saving..."
                        : "Report issue"
                    )
                  ]),
                  state.maintenanceByTenancy[tenancy.id] && state.maintenanceByTenancy[tenancy.id].length
                    ? e(
                        "div",
                        { className: "list-stack", key: "maintenance-list" },
                        state.maintenanceByTenancy[tenancy.id].map(function renderTicket(ticket) {
                          var acknowledgeForm = maintenanceAcknowledgeForms[ticket.id] || buildSimpleNotesForm();
                          var resolveForm = maintenanceResolveForms[ticket.id] || {
                            resolution_summary: "",
                            landlord_response_notes: "",
                            resolution_file: null
                          };
                          var disputeForm = maintenanceDisputeForms[ticket.id] || { dispute_notes: "" };
                          var appealForm = maintenanceAppealForms[ticket.id] || buildAppealForm();
                          return e("article", { className: "stack-card", key: ticket.id }, [
                            e("strong", { className: "stack-card-title", key: "title" }, ticket.title),
                            e("div", { className: "status-row", key: "status" }, [
                              e(StatusBadge, {
                                key: "ticket-status",
                                tone: inferStatusTone(ticket.ticket_status),
                                label: ticket.ticket_status
                              }),
                              e(StatusBadge, {
                                key: "priority",
                                tone: "warning",
                                label: ticket.priority
                              })
                            ]),
                            e(NoteBlock, { key: "description", label: "Reported issue", tone: "accent" }, ticket.description),
                            ticket.reported_artifact_name
                              ? e(
                                  NoteBlock,
                                  { key: "reported-artifact", label: "Reported evidence", tone: "accent" },
                                  "Reported with: " +
                                    ticket.reported_artifact_name +
                                    (formatArtifactMeta(
                                      ticket.reported_artifact_content_type,
                                      ticket.reported_artifact_size_bytes
                                    )
                                      ? " | " +
                                        formatArtifactMeta(
                                          ticket.reported_artifact_content_type,
                                          ticket.reported_artifact_size_bytes
                                        )
                                      : "")
                                )
                              : null,
                            ticket.reported_stored_artifact_id
                              ? e(
                                  "button",
                                  {
                                    type: "button",
                                    className: "button button-small",
                                    onClick: function onClick() {
                                      openStoredArtifact(ticket.reported_stored_artifact_id);
                                    },
                                    key: "open-reported-artifact"
                                  },
                                  "Open reported evidence"
                                )
                              : null,
                            session.user.id === tenancy.landlord_user_id &&
                            ticket.ticket_status !== "resolved" &&
                            ticket.ticket_status !== "disputed"
                              ? e("div", { className: "form-grid", key: "ack" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: acknowledgeForm.notes,
                                    onChange: function onChange(event) {
                                      updateEntityForm(setMaintenanceAcknowledgeForms, ticket.id, "notes", event.target.value);
                                    },
                                    placeholder: "Acknowledgement notes"
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-secondary button-small",
                                      disabled: actionState.kind === "maintenance-ack" && actionState.id === ticket.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "maintenance-ack",
                                          ticket.id,
                                          function task() {
                                            return apiRequest("/maintenance-tickets/" + ticket.id + "/acknowledge", {
                                              method: "POST",
                                              body: { landlord_response_notes: acknowledgeForm.notes }
                                            });
                                          },
                                          "Maintenance ticket acknowledged."
                                        );
                                      }
                                    },
                                    actionState.kind === "maintenance-ack" && actionState.id === ticket.id
                                      ? "Saving..."
                                      : "Acknowledge"
                                  )
                                ])
                              : null,
                            session.user.id === tenancy.landlord_user_id && ticket.ticket_status !== "disputed"
                              ? e("div", { className: "form-grid", key: "resolve" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: resolveForm.resolution_summary,
                                    onChange: function onChange(event) {
                                      updateEntityForm(setMaintenanceResolveForms, ticket.id, "resolution_summary", event.target.value);
                                    },
                                    placeholder: "Resolution summary"
                                  }),
                                  e("input", {
                                    className: "field-input",
                                    value: resolveForm.landlord_response_notes,
                                    onChange: function onChange(event) {
                                      updateEntityForm(setMaintenanceResolveForms, ticket.id, "landlord_response_notes", event.target.value);
                                    },
                                    placeholder: "Resolution notes"
                                  }),
                                  e("input", {
                                    className: "field-input",
                                    type: "file",
                                    onChange: function onChange(event) {
                                      updateEntityForm(
                                        setMaintenanceResolveForms,
                                        ticket.id,
                                        "resolution_file",
                                        event.target.files && event.target.files[0]
                                          ? event.target.files[0]
                                          : null
                                      );
                                    }
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-secondary button-small",
                                      disabled: actionState.kind === "maintenance-resolve" && actionState.id === ticket.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "maintenance-resolve",
                                          ticket.id,
                                          async function task() {
                                            var storedArtifact = null;
                                            if (resolveForm.resolution_file) {
                                              storedArtifact = await uploadOperationalArtifact(
                                                tenancy.id,
                                                resolveForm.resolution_file,
                                                "maintenance_resolution"
                                              );
                                            }
                                            await apiRequest("/maintenance-tickets/" + ticket.id + "/resolve", {
                                              method: "POST",
                                              body: {
                                                resolution_summary: resolveForm.resolution_summary,
                                                landlord_response_notes:
                                                  resolveForm.landlord_response_notes || undefined,
                                                resolution_stored_artifact_id: storedArtifact
                                                  ? storedArtifact.id
                                                  : undefined,
                                                resolution_artifact_name: storedArtifact
                                                  ? storedArtifact.original_file_name
                                                  : undefined
                                              }
                                            });
                                            setMaintenanceResolveForms(function resetResolveForm(previous) {
                                              var next = Object.assign({}, previous);
                                              next[ticket.id] = {
                                                resolution_summary: "",
                                                landlord_response_notes: "",
                                                resolution_file: null
                                              };
                                              return next;
                                            });
                                          },
                                          "Maintenance ticket resolved."
                                        );
                                      }
                                    },
                                    actionState.kind === "maintenance-resolve" && actionState.id === ticket.id
                                      ? "Saving..."
                                      : "Resolve"
                                  )
                                ])
                              : null,
                            ticket.resolution_summary
                              ? e(
                                  NoteBlock,
                                  { key: "resolution-summary", label: "Resolution", tone: "success" },
                                  ticket.resolution_summary
                                )
                              : null,
                            ticket.resolution_artifact_name
                              ? e(
                                  NoteBlock,
                                  { key: "resolution-artifact", label: "Resolution file", tone: "success" },
                                  "Resolution file: " +
                                    ticket.resolution_artifact_name +
                                    (formatArtifactMeta(
                                      ticket.resolution_artifact_content_type,
                                      ticket.resolution_artifact_size_bytes
                                    )
                                      ? " | " +
                                        formatArtifactMeta(
                                          ticket.resolution_artifact_content_type,
                                          ticket.resolution_artifact_size_bytes
                                        )
                                      : "")
                                )
                              : null,
                            ticket.resolution_stored_artifact_id
                              ? e(
                                  "button",
                                  {
                                    type: "button",
                                    className: "button button-small",
                                    onClick: function onClick() {
                                      openStoredArtifact(ticket.resolution_stored_artifact_id);
                                    },
                                    key: "open-resolution-artifact"
                                  },
                                  "Open resolution file"
                                )
                              : null,
                            ticket.verdict_summary
                              ? e(
                                  NoteBlock,
                                  { key: "verdict-summary", label: "Verdict", tone: "danger" },
                                  "Judge verdict: " +
                                    ticket.verdict_summary +
                                    " | Outcome: " +
                                    ticket.verdict_outcome +
                                    " | Tenant delta " +
                                    String(ticket.verdict_tenant_score_delta) +
                                    " | Landlord delta " +
                                    String(ticket.verdict_landlord_score_delta)
                                )
                              : null,
                            ticket.appeal_notes
                              ? e(
                                  NoteBlock,
                                  { key: "appeal-notes", label: "Appeal notes", tone: "danger" },
                                  ticket.appeal_notes
                                )
                              : null,
                            session.user.id === tenancy.tenant_user_id && ticket.ticket_status === "resolved"
                              ? e("div", { className: "form-grid", key: "dispute" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: disputeForm.dispute_notes,
                                    onChange: function onChange(event) {
                                      updateEntityForm(setMaintenanceDisputeForms, ticket.id, "dispute_notes", event.target.value);
                                    },
                                    placeholder: "Dispute notes"
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-small",
                                      disabled: actionState.kind === "maintenance-dispute" && actionState.id === ticket.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "maintenance-dispute",
                                          ticket.id,
                                          function task() {
                                            return apiRequest("/maintenance-tickets/" + ticket.id + "/dispute", {
                                              method: "POST",
                                              body: disputeForm
                                            });
                                          },
                                          "Maintenance dispute submitted."
                                        );
                                      }
                                    },
                                    actionState.kind === "maintenance-dispute" && actionState.id === ticket.id
                                      ? "Saving..."
                                      : "Dispute"
                                  )
                                ])
                              : null,
                            ticket.ticket_status === "verdict_issued"
                              ? e("div", { className: "form-grid", key: "maintenance-appeal" }, [
                                  e("input", {
                                    className: "field-input",
                                    value: appealForm.appeal_notes,
                                    onChange: function onChange(event) {
                                      updateEntityForm(
                                        setMaintenanceAppealForms,
                                        ticket.id,
                                        "appeal_notes",
                                        event.target.value
                                      );
                                    },
                                    placeholder: "Appeal notes"
                                  }),
                                  e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-secondary button-small",
                                      disabled: actionState.kind === "maintenance-appeal" && actionState.id === ticket.id,
                                      onClick: function onClick() {
                                        runAction(
                                          "maintenance-appeal",
                                          ticket.id,
                                          function task() {
                                            return apiRequest("/maintenance-tickets/" + ticket.id + "/appeal", {
                                              method: "POST",
                                              body: appealForm
                                            });
                                          },
                                          "Maintenance appeal submitted."
                                        );
                                      }
                                    },
                                    actionState.kind === "maintenance-appeal" && actionState.id === ticket.id
                                      ? "Saving..."
                                      : "Appeal verdict"
                                  )
                                ])
                              : null
                          ]);
                        })
                      )
                    : e("p", { className: "empty-copy", key: "empty" }, "No maintenance tickets yet.")
                ]) : null
              ])
            ]);
          })
        )
      : operationsFocus !== "disputes"
        ? e("div", { className: "detail-panel", key: "empty" }, [
          e("p", { className: "empty-copy", key: "copy" }, "No tenancy records are attached to this account yet.")
        ])
        : null
  ]);
}
