import React from "react";

import {
  FactPill,
  HeroStat,
  NoteBlock,
  PageHero,
  SectionHeading,
  StatusBadge,
  TimelineEntry
} from "../components/PageChrome.js";
import { SegmentedTabs } from "../components/SegmentedTabs.js";
import {
  buildDisputeLifecycle,
  formatWorkflowLabel
} from "../lib/disputeWorkflow.js";
import { apiRequest } from "../lib/api.js";
import { e } from "../lib/i18n.js";

function OverviewCard(props) {
  return e("article", { className: "metric-card" }, [
    e("p", { className: "metric-kicker", key: "kicker" }, props.kicker),
    e("strong", { className: "metric-value", key: "value" }, String(props.value)),
    e("p", { className: "metric-copy", key: "copy" }, props.copy)
  ]);
}

function buildDecisionKey(kind, id) {
  return kind + ":" + id;
}

function updateNote(setter, kind, id, value) {
  setter(function mergeNotes(previous) {
    var next = Object.assign({}, previous);
    next[buildDecisionKey(kind, id)] = value;
    return next;
  });
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

function updateEntityForm(setter, entityId, name, value) {
  setter(function mergeForms(previous) {
    var next = Object.assign({}, previous);
    var existing = Object.assign({}, next[entityId] || {});
    existing[name] = value;
    next[entityId] = existing;
    return next;
  });
}

function buildDisputeVerdictForm() {
  return {
    verdict_outcome: "inconclusive",
    verdict_summary: "",
    tenant_score_delta: "0",
    landlord_score_delta: "0"
  };
}

function inferStatusTone(value) {
  var normalized = String(value || "").toLowerCase();
  if (
    normalized.indexOf("ready") >= 0 ||
    normalized.indexOf("healthy") >= 0 ||
    normalized.indexOf("complete") >= 0 ||
    normalized.indexOf("success") >= 0 ||
    normalized.indexOf("reviewed") >= 0
  ) {
    return "success";
  }
  if (
    normalized.indexOf("block") >= 0 ||
    normalized.indexOf("fail") >= 0 ||
    normalized.indexOf("error") >= 0 ||
    normalized.indexOf("rejected") >= 0
  ) {
    return "danger";
  }
  if (
    normalized.indexOf("warning") >= 0 ||
    normalized.indexOf("pending") >= 0 ||
    normalized.indexOf("review") >= 0 ||
    normalized.indexOf("queued") >= 0
  ) {
    return "warning";
  }
  return "accent";
}

function canExecuteAutomationTask(task) {
  return (
    task.task_type === "consent_expiry_reminder" ||
    task.task_type === "user_score_recalculation" ||
    task.task_type === "organization_score_recalculation_batch"
  );
}

var auditActionOptions = [
  { value: "", label: "All actions" },
  { value: "trust_check_created", label: "Trust checks created" },
  { value: "trust_profile_previewed", label: "Trust profile previews" },
  { value: "trust_check_validated", label: "Trust check validation" },
  { value: "trust_report_consent_created", label: "Consent creation" },
  { value: "trust_report_consent_revoked", label: "Consent revocation" },
  { value: "automation_task_executed", label: "Automation executed" },
  { value: "score_recalculation_request_processed", label: "Score recalculation processed" },
  { value: "auth_login_denied", label: "Denied logins" }
];

export function InternalOperationsPage() {
  var viewState = React.useState({
    status: "loading",
    overview: null,
    releaseReadiness: null,
    tenancies: [],
    evidenceDocuments: [],
    historyImports: [],
    depositDisputes: [],
    maintenanceDisputes: [],
    paymentDisputes: [],
    organizations: [],
    scoreRequests: [],
    scoreBatches: [],
    automationTasks: [],
    notifications: [],
    workerRuns: [],
    auditLogs: [],
    error: null
  });
  var state = viewState[0];
  var setState = viewState[1];
  var notesTuple = React.useState({});
  var decisionNotes = notesTuple[0];
  var setDecisionNotes = notesTuple[1];
  var actionTuple = React.useState({
    kind: "",
    id: "",
    decision: ""
  });
  var reviewAction = actionTuple[0];
  var setReviewAction = actionTuple[1];
  var disputeVerdictFormsTuple = React.useState({});
  var disputeVerdictForms = disputeVerdictFormsTuple[0];
  var setDisputeVerdictForms = disputeVerdictFormsTuple[1];
  var auditFilterTuple = React.useState("");
  var auditActionType = auditFilterTuple[0];
  var setAuditActionType = auditFilterTuple[1];
  var scoreRequestFormTuple = React.useState({
    user_email: "",
    scheduled_for: ""
  });
  var scoreRequestForm = scoreRequestFormTuple[0];
  var setScoreRequestForm = scoreRequestFormTuple[1];
  var scoreRequestActionTuple = React.useState({
    kind: "",
    id: "",
    message: null
  });
  var scoreRequestAction = scoreRequestActionTuple[0];
  var setScoreRequestAction = scoreRequestActionTuple[1];
  var batchFormTuple = React.useState({
    organization_id: "",
    scheduled_for: ""
  });
  var batchForm = batchFormTuple[0];
  var setBatchForm = batchFormTuple[1];
  var batchActionTuple = React.useState({
    kind: "",
    id: "",
    message: null
  });
  var batchAction = batchActionTuple[0];
  var setBatchAction = batchActionTuple[1];
  var followUpFormTuple = React.useState({
    title: "",
    details: "",
    subject_user_email: "",
    organization_id: "",
    scheduled_for: ""
  });
  var followUpForm = followUpFormTuple[0];
  var setFollowUpForm = followUpFormTuple[1];
  var automationActionTuple = React.useState({
    kind: "",
    id: "",
    message: null
  });
  var automationAction = automationActionTuple[0];
  var setAutomationAction = automationActionTuple[1];
  var internalSectionTuple = React.useState("overview");
  var internalSection = internalSectionTuple[0];
  var setInternalSection = internalSectionTuple[1];
  var updateScoreRequestField = React.useMemo(function buildScoreRequestFieldUpdater() {
    return updateNamedField(setScoreRequestForm);
  }, []);
  var updateBatchField = React.useMemo(function buildBatchFieldUpdater() {
    return updateNamedField(setBatchForm);
  }, []);
  var updateFollowUpField = React.useMemo(function buildFollowUpFieldUpdater() {
    return updateNamedField(setFollowUpForm);
  }, []);

  var loadOperationsState = React.useCallback(async function loadOperationsState() {
    setState(function setLoading(previous) {
      return {
        status:
          previous.overview ||
          previous.releaseReadiness ||
          previous.tenancies.length ||
          previous.evidenceDocuments.length ||
          previous.historyImports.length ||
          previous.depositDisputes.length ||
          previous.maintenanceDisputes.length ||
          previous.paymentDisputes.length ||
          previous.scoreRequests.length ||
          previous.scoreBatches.length ||
          previous.automationTasks.length ||
          previous.workerRuns.length ||
          previous.auditLogs.length
            ? "refreshing"
            : "loading",
        overview: previous.overview,
        releaseReadiness: previous.releaseReadiness,
        tenancies: previous.tenancies,
        evidenceDocuments: previous.evidenceDocuments,
        historyImports: previous.historyImports,
        depositDisputes: previous.depositDisputes,
        maintenanceDisputes: previous.maintenanceDisputes,
        paymentDisputes: previous.paymentDisputes,
        organizations: previous.organizations,
        scoreRequests: previous.scoreRequests,
        scoreBatches: previous.scoreBatches,
        automationTasks: previous.automationTasks,
        notifications: previous.notifications,
        workerRuns: previous.workerRuns,
        auditLogs: previous.auditLogs,
        error: null
      };
    });

    try {
      var auditPath = "/internal/audit-logs?limit=20";
      if (auditActionType) {
        auditPath += "&action_type=" + encodeURIComponent(auditActionType);
      }
      var results = await Promise.all([
        apiRequest("/internal/operations/overview"),
        apiRequest("/internal/release-readiness"),
        apiRequest("/internal/review-queue/tenancies"),
        apiRequest("/internal/review-queue/evidence"),
        apiRequest("/internal/review-queue/history-imports"),
        apiRequest("/internal/disputes/deposits"),
        apiRequest("/internal/disputes/maintenance"),
        apiRequest("/internal/disputes/payments"),
        apiRequest("/organizations/directory/agencies"),
        apiRequest("/internal/scoring/requests?limit=10"),
        apiRequest("/internal/scoring/batches?limit=10"),
        apiRequest("/internal/automation/tasks?due_only=true"),
        apiRequest("/internal/notifications?limit=10"),
        apiRequest("/internal/workers/runs?limit=10"),
        apiRequest(auditPath)
      ]);
      setState({
        status: "ready",
        overview: results[0],
        releaseReadiness: results[1],
        tenancies: results[2],
        evidenceDocuments: results[3],
        historyImports: results[4],
        depositDisputes: results[5],
        maintenanceDisputes: results[6],
        paymentDisputes: results[7],
        organizations: results[8],
        scoreRequests: results[9],
        scoreBatches: results[10],
        automationTasks: results[11],
        notifications: results[12],
        workerRuns: results[13],
        auditLogs: results[14],
        error: null
      });
      setBatchForm(function ensureOrganizationSelection(previous) {
        if (previous.organization_id || !results[8].length) {
          return previous;
        }
        return Object.assign({}, previous, { organization_id: results[8][0].id });
      });
      setFollowUpForm(function ensureFollowUpOrganization(previous) {
        if (previous.organization_id || !results[8].length) {
          return previous;
        }
        return Object.assign({}, previous, { organization_id: results[8][0].id });
      });
      setDisputeVerdictForms(function syncDisputeVerdictForms(previous) {
        var next = Object.assign({}, previous);
        results[5].forEach(function ensureDepositForm(deposit) {
          if (!next["deposit:" + deposit.id]) {
            next["deposit:" + deposit.id] = buildDisputeVerdictForm();
          }
        });
        results[6].forEach(function ensureMaintenanceForm(ticket) {
          if (!next["maintenance:" + ticket.id]) {
            next["maintenance:" + ticket.id] = buildDisputeVerdictForm();
          }
        });
        results[7].forEach(function ensurePaymentForm(payment) {
          if (!next["payment:" + payment.id]) {
            next["payment:" + payment.id] = buildDisputeVerdictForm();
          }
        });
        return next;
      });
    } catch (error) {
      setState({
        status: "error",
        overview: null,
        releaseReadiness: null,
        tenancies: [],
        evidenceDocuments: [],
        historyImports: [],
        depositDisputes: [],
        maintenanceDisputes: [],
        paymentDisputes: [],
        organizations: [],
        scoreRequests: [],
        scoreBatches: [],
        automationTasks: [],
        notifications: [],
        workerRuns: [],
        auditLogs: [],
        error: error.message || "Unable to load the operations overview."
      });
    }
  }, [auditActionType]);

  React.useEffect(function bootstrapInternalOperations() {
    loadOperationsState();
  }, [loadOperationsState]);

  async function submitTenancyDecision(tenancy, verificationStatus) {
    setReviewAction({
      kind: "tenancy",
      id: tenancy.id,
      decision: verificationStatus
    });
    try {
      await apiRequest("/internal/review-queue/tenancies/" + tenancy.id + "/decision", {
        method: "POST",
        body: {
          verification_status: verificationStatus,
          review_notes:
            decisionNotes[buildDecisionKey("tenancy", tenancy.id)] ||
            "Reviewed from the rebuilt internal operations workspace."
        }
      });
      await loadOperationsState();
    } finally {
      setReviewAction({
        kind: "",
        id: "",
        decision: ""
      });
    }
  }

  async function submitEvidenceDecision(evidenceDocument, reviewStatus) {
    setReviewAction({
      kind: "evidence",
      id: evidenceDocument.id,
      decision: reviewStatus
    });
    try {
      await apiRequest(
        "/internal/review-queue/evidence/" + evidenceDocument.id + "/decision",
        {
          method: "POST",
          body: {
            review_status: reviewStatus,
            review_notes:
              decisionNotes[buildDecisionKey("evidence", evidenceDocument.id)] ||
              "Reviewed from the rebuilt internal operations workspace."
          }
        }
      );
      await loadOperationsState();
    } finally {
      setReviewAction({
        kind: "",
        id: "",
        decision: ""
      });
    }
  }

  async function submitHistoryImportDecision(historyImport, nextStatus) {
    setReviewAction({
      kind: "history-import",
      id: historyImport.id,
      decision: nextStatus
    });
    try {
      await apiRequest(
        "/internal/review-queue/history-imports/" + historyImport.id + "/decision",
        {
          method: "POST",
          body: {
            status: nextStatus,
            review_notes:
              decisionNotes[buildDecisionKey("history-import", historyImport.id)] ||
              "Reviewed from the rebuilt internal operations workspace."
          }
        }
      );
      await loadOperationsState();
    } finally {
      setReviewAction({
        kind: "",
        id: "",
        decision: ""
      });
    }
  }

  async function submitDepositVerdict(depositRecord) {
    var verdictKey = "deposit:" + depositRecord.id;
    var verdictForm = disputeVerdictForms[verdictKey] || buildDisputeVerdictForm();
    setReviewAction({
      kind: "deposit-dispute",
      id: depositRecord.id,
      decision: verdictForm.verdict_outcome
    });
    try {
      await apiRequest("/internal/disputes/deposits/" + depositRecord.id + "/verdict", {
        method: "POST",
        body: {
          verdict_outcome: verdictForm.verdict_outcome,
          verdict_summary: verdictForm.verdict_summary,
          tenant_score_delta: Number(verdictForm.tenant_score_delta || 0),
          landlord_score_delta: Number(verdictForm.landlord_score_delta || 0)
        }
      });
      await loadOperationsState();
    } finally {
      setReviewAction({
        kind: "",
        id: "",
        decision: ""
      });
    }
  }

  async function submitMaintenanceVerdict(ticket) {
    var verdictKey = "maintenance:" + ticket.id;
    var verdictForm = disputeVerdictForms[verdictKey] || buildDisputeVerdictForm();
    setReviewAction({
      kind: "maintenance-dispute",
      id: ticket.id,
      decision: verdictForm.verdict_outcome
    });
    try {
      await apiRequest("/internal/disputes/maintenance/" + ticket.id + "/verdict", {
        method: "POST",
        body: {
          verdict_outcome: verdictForm.verdict_outcome,
          verdict_summary: verdictForm.verdict_summary,
          tenant_score_delta: Number(verdictForm.tenant_score_delta || 0),
          landlord_score_delta: Number(verdictForm.landlord_score_delta || 0)
        }
      });
      await loadOperationsState();
    } finally {
      setReviewAction({
        kind: "",
        id: "",
        decision: ""
      });
    }
  }

  async function submitPaymentVerdict(payment) {
    var verdictKey = "payment:" + payment.id;
    var verdictForm = disputeVerdictForms[verdictKey] || buildDisputeVerdictForm();
    setReviewAction({
      kind: "payment-dispute",
      id: payment.id,
      decision: verdictForm.verdict_outcome
    });
    try {
      await apiRequest("/internal/disputes/payments/" + payment.id + "/verdict", {
        method: "POST",
        body: {
          verdict_outcome: verdictForm.verdict_outcome,
          verdict_summary: verdictForm.verdict_summary,
          tenant_score_delta: Number(verdictForm.tenant_score_delta || 0),
          landlord_score_delta: Number(verdictForm.landlord_score_delta || 0)
        }
      });
      await loadOperationsState();
    } finally {
      setReviewAction({
        kind: "",
        id: "",
        decision: ""
      });
    }
  }

  async function queueScoreRefreshRequest(runImmediately) {
    setScoreRequestAction({
      kind: runImmediately ? "score-now" : "score-queue",
      id: "",
      message: null
    });
    try {
      var payload = {
        user_email: scoreRequestForm.user_email
      };
      if (scoreRequestForm.scheduled_for) {
        payload.scheduled_for = scoreRequestForm.scheduled_for;
      }
      await apiRequest(
        runImmediately ? "/internal/scoring/recalculate" : "/internal/scoring/requests",
        {
          method: "POST",
          body: payload
        }
      );
      setScoreRequestForm({
        user_email: "",
        scheduled_for: ""
      });
      await loadOperationsState();
      setScoreRequestAction({
        kind: "",
        id: "",
        message: runImmediately
          ? "Score recalculated immediately."
          : "Score refresh request queued."
      });
    } catch (error) {
      setScoreRequestAction({
        kind: "",
        id: "",
        message: error.message || "Unable to queue the score refresh request."
      });
    }
  }

  async function processScoreRequest(request) {
    setScoreRequestAction({
      kind: "score-process",
      id: request.id,
      message: null
    });
    try {
      await apiRequest("/internal/scoring/requests/" + request.id + "/process", {
        method: "POST"
      });
      await loadOperationsState();
      setScoreRequestAction({
        kind: "",
        id: "",
        message: "Score request processed."
      });
    } catch (error) {
      setScoreRequestAction({
        kind: "",
        id: "",
        message: error.message || "Unable to process this score request."
      });
    }
  }

  async function createScoreBatch() {
    setBatchAction({
      kind: "batch-create",
      id: "",
      message: null
    });
    try {
      var payload = {
        scope_type: "organization_members",
        organization_id: batchForm.organization_id
      };
      if (batchForm.scheduled_for) {
        payload.scheduled_for = batchForm.scheduled_for;
      }
      await apiRequest("/internal/scoring/batches", {
        method: "POST",
        body: payload
      });
      setBatchForm(function resetBatch(previous) {
        return {
          organization_id: previous.organization_id,
          scheduled_for: ""
        };
      });
      await loadOperationsState();
      setBatchAction({
        kind: "",
        id: "",
        message: "Organization score batch queued."
      });
    } catch (error) {
      setBatchAction({
        kind: "",
        id: "",
        message: error.message || "Unable to create the score batch."
      });
    }
  }

  async function createFollowUpTask(event) {
    event.preventDefault();
    setAutomationAction({
      kind: "follow-up-create",
      id: "",
      message: null
    });
    try {
      var payload = {
        title: followUpForm.title,
        details: followUpForm.details || null,
        organization_id: followUpForm.organization_id || null,
        subject_user_email: followUpForm.subject_user_email || null,
        scheduled_for: followUpForm.scheduled_for || null
      };
      await apiRequest("/internal/automation/tasks/follow-ups", {
        method: "POST",
        body: payload
      });
      setFollowUpForm(function resetFollowUp(previous) {
        return {
          title: "",
          details: "",
          subject_user_email: "",
          organization_id: previous.organization_id,
          scheduled_for: ""
        };
      });
      await loadOperationsState();
      setAutomationAction({
        kind: "",
        id: "",
        message: "Follow-up task created."
      });
    } catch (error) {
      setAutomationAction({
        kind: "",
        id: "",
        message: error.message || "Unable to create the follow-up task."
      });
    }
  }

  async function claimDueAutomationTasks() {
    setAutomationAction({
      kind: "automation-claim",
      id: "",
      message: null
    });
    try {
      await apiRequest("/internal/automation/tasks/claim", {
        method: "POST",
        body: {
          limit: 5
        }
      });
      await loadOperationsState();
      setAutomationAction({
        kind: "",
        id: "",
        message: "Due automation tasks claimed."
      });
    } catch (error) {
      setAutomationAction({
        kind: "",
        id: "",
        message: error.message || "Unable to claim automation tasks."
      });
    }
  }

  async function executeAutomationTask(task) {
    setAutomationAction({
      kind: "automation-execute",
      id: task.id,
      message: null
    });
    try {
      await apiRequest("/internal/automation/tasks/" + task.id + "/execute", {
        method: "POST"
      });
      await loadOperationsState();
      setAutomationAction({
        kind: "",
        id: "",
        message: "Automation task executed."
      });
    } catch (error) {
      setAutomationAction({
        kind: "",
        id: "",
        message: error.message || "Unable to execute this automation task."
      });
    }
  }

  async function cleanupAutomationTasks(kind) {
    var path =
      kind === "cleanup-expired-consents"
        ? "/internal/automation/cleanup/expired-consent-reminders"
        : "/internal/automation/cleanup/stale-follow-ups";
    var payload =
      kind === "cleanup-expired-consents"
        ? {}
        : {
            stale_after_days: 30
          };

    setAutomationAction({
      kind: kind,
      id: "",
      message: null
    });
    try {
      var result = await apiRequest(path, {
        method: "POST",
        body: payload
      });
      await loadOperationsState();
      setAutomationAction({
        kind: "",
        id: "",
        message: "Cleanup finished. Closed " + result.processed_task_count + " task(s)."
      });
    } catch (error) {
      setAutomationAction({
        kind: "",
        id: "",
        message: error.message || "Unable to run the cleanup right now."
      });
    }
  }

  async function processAutomationTask(task, nextStatus, resultNotes) {
    setAutomationAction({
      kind: "automation-process",
      id: task.id,
      message: null
    });
    try {
      await apiRequest("/internal/automation/tasks/" + task.id + "/process", {
        method: "POST",
        body: {
          status: nextStatus,
          result_notes: resultNotes
        }
      });
      await loadOperationsState();
      setAutomationAction({
        kind: "",
        id: "",
        message: "Automation task updated."
      });
    } catch (error) {
      setAutomationAction({
        kind: "",
        id: "",
        message: error.message || "Unable to update this automation task."
      });
    }
  }

  if (state.status === "loading") {
    return e("div", { className: "state-panel" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Review Center"),
      e("h1", { className: "state-title", key: "title" }, "Loading live operational state"),
      e(
        "p",
        { className: "state-copy", key: "copy" },
        "We are loading review queues, automation tasks, audits, and release-readiness data."
      )
    ]);
  }

  if (state.status === "error") {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Review Center"),
      e("h1", { className: "state-title", key: "title" }, "Overview unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  var overview = state.overview;
  var releaseReadiness = state.releaseReadiness;
  var internalSectionTabs = [
    {
      id: "overview",
      label: "Overview",
      meta: "Health, readiness, and system snapshot"
    },
    {
      id: "controls",
      label: "Controls",
      meta: "Score and follow-up controls"
    },
    {
      id: "reviews",
      label: "Review queues",
      meta: String(state.tenancies.length + state.evidenceDocuments.length + state.historyImports.length) + " pending items"
    },
    {
      id: "disputes",
      label: "Disputes",
      meta: String(state.depositDisputes.length + state.maintenanceDisputes.length + state.paymentDisputes.length) + " cases"
    },
    {
      id: "runtime",
      label: "Runtime",
      meta: String(state.automationTasks.length + state.notifications.length + state.workerRuns.length) + " runtime items"
    },
    {
      id: "audit",
      label: "Audit",
      meta: String(state.auditLogs.length) + " recent events"
    }
  ];
  var internalSectionCopyByTab = {
    overview: "Start with the platform picture before acting on any queue or control.",
    controls: "Keep manual controls separate from review decisions so operators do not mix system actions with case work.",
    reviews: "Use this lane only for tenancy, evidence, and history review decisions.",
    disputes: "Use this lane for first verdicts and appealed re-reviews. If a case comes back through an appeal, replace the earlier verdict with a fresh one here.",
    runtime: "Use the runtime lane when following automation, notifications, and worker execution.",
    audit: "Use audit when you need traceability, not operations."
  };

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Review Center",
      title: "Review queues and system health",
      copy:
        "Use this page to review pending work, monitor automation, inspect audits, and check whether the platform is ready for release.",
      details: [
        "Runtime lane: " +
          overview.environment +
          " | Database: " +
          overview.database_backend +
          " | Artifact storage: " +
          overview.artifact_storage_backend +
          " | Worker coordination: " +
          overview.worker_coordination_backend +
          " | Notifications: " +
          overview.notification_transport
      ],
      stats: [
        e(HeroStat, {
          label: "Pending reviews",
          value: String(
            overview.pending_tenancy_review_count +
              overview.pending_evidence_review_count +
              overview.pending_history_import_review_count
          ),
          copy: "Tenancy, evidence, and history-import reviews awaiting action."
        }),
        e(HeroStat, {
          label: "Runtime backlog",
          value: String(overview.due_automation_task_count + overview.due_notification_count),
          copy:
            String(overview.due_automation_task_count) +
            " automation tasks and " +
            String(overview.due_notification_count) +
            " notifications due."
        }),
        e(HeroStat, {
          label: "Score queue",
          value: String(overview.due_score_request_count),
          copy: String(overview.failed_worker_run_count) + " failed worker runs currently on record."
        })
      ]
    }),
    e("section", { className: "detail-panel section-switcher", key: "internal-switcher" }, [
      e(SectionHeading, {
        title: "Focus on one internal lane",
        copy: internalSectionCopyByTab[internalSection],
        key: "heading"
      }),
      e(SegmentedTabs, {
        key: "tabs",
        tabs: internalSectionTabs,
        activeTab: internalSection,
        onChange: setInternalSection,
        "aria-label": "Internal workspace sections"
      })
    ]),
    internalSection === "overview" && releaseReadiness
      ? e("section", { className: "detail-panel", key: "release-readiness" }, [
          e("h2", { className: "detail-title", key: "title" }, "Release readiness"),
          e("div", { className: "status-row", key: "summary" }, [
            e(StatusBadge, {
              key: "status",
              tone: inferStatusTone(releaseReadiness.status),
              label: releaseReadiness.status
            }),
            e(StatusBadge, {
              key: "blocks",
              tone: releaseReadiness.blocking_issue_count ? "danger" : "success",
              label: "Blocking issues " + releaseReadiness.blocking_issue_count
            }),
            e(StatusBadge, {
              key: "warnings",
              tone: releaseReadiness.warning_count ? "warning" : "success",
              label: "Warnings " + releaseReadiness.warning_count
            })
          ]),
          e("div", { className: "fact-grid", key: "urls" }, [
            e(FactPill, {
              key: "api",
              label: "Public API",
              value: releaseReadiness.public_api_base_url,
              tone: "accent"
            }),
            e(FactPill, {
              key: "web",
              label: "Public web",
              value: releaseReadiness.public_web_base_url,
              tone: "accent"
            })
          ]),
          e(
            "div",
            { className: "list-stack", key: "checks" },
            releaseReadiness.checks.map(function renderCheck(check) {
              return e("article", { className: "stack-card", key: check.key }, [
                e("strong", { className: "stack-card-title", key: "title" }, check.label),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "check-status",
                    tone: inferStatusTone(check.status),
                    label: check.status
                  })
                ]),
                e(NoteBlock, { key: "detail", label: "Check detail" }, check.detail)
              ]);
            })
          )
        ])
      : null,
    internalSection === "overview"
      ? e("section", { className: "metric-grid", key: "metrics" }, [
      e(OverviewCard, {
        kicker: "Tenancies",
        value: overview.pending_tenancy_review_count,
        copy: "Pending tenancy review queue"
      }),
      e(OverviewCard, {
        kicker: "Evidence",
        value: overview.pending_evidence_review_count,
        copy: "Pending evidence review queue"
      }),
      e(OverviewCard, {
        kicker: "History imports",
        value: overview.pending_history_import_review_count,
        copy: "Cold-start onboarding bundles awaiting review"
      }),
      e(OverviewCard, {
        kicker: "Automation",
        value: overview.due_automation_task_count,
        copy: "Due automation tasks requiring a worker pass"
      }),
      e(OverviewCard, {
        kicker: "Notifications",
        value: overview.due_notification_count,
        copy: "Due notification deliveries waiting on the runtime lane"
      }),
      e(OverviewCard, {
        kicker: "Scores",
        value: overview.due_score_request_count,
        copy: "Due score recalculation requests"
      }),
      e(OverviewCard, {
        kicker: "Workers",
        value: overview.failed_worker_run_count,
        copy: "Failed worker runs requiring follow-up"
      })
    ]) : null,
    internalSection === "overview" && overview.latest_worker_run
      ? e("section", { className: "detail-panel", key: "latest-run" }, [
          e("h2", { className: "detail-title", key: "title" }, "Latest worker run"),
          e("div", { className: "status-row", key: "status" }, [
            e(StatusBadge, {
              key: "run-status",
              tone: inferStatusTone(overview.latest_worker_run.status),
              label: overview.latest_worker_run.status
            })
          ]),
          e("div", { className: "fact-grid", key: "grid" }, [
            e(FactPill, { key: "limit", label: "Requested limit", value: String(overview.latest_worker_run.requested_limit) }),
            e(FactPill, { key: "automation", label: "Claimed automation tasks", value: String(overview.latest_worker_run.claimed_automation_task_count) }),
            e(FactPill, { key: "notifications", label: "Sent notifications", value: String(overview.latest_worker_run.sent_notification_count), tone: "success" }),
            e(FactPill, { key: "scores", label: "Processed score requests", value: String(overview.latest_worker_run.processed_score_request_count), tone: "accent" })
          ])
        ])
      : null,
    internalSection === "controls"
      ? e("section", { className: "split-grid", key: "operator-controls" }, [
      e("article", { className: "detail-panel", key: "score-controls" }, [
        e("h2", { className: "detail-title", key: "title" }, "Score controls"),
        e(
          "p",
          { className: "empty-copy", key: "copy" },
          "Queue a score refresh by user email, run an immediate recalculation, or schedule a batch refresh for an agency organization."
        ),
        e("div", { className: "auth-form", key: "request-form" }, [
          e("div", { className: "form-grid", key: "request-grid" }, [
            e("label", { className: "field", key: "email" }, [
              e("span", { className: "field-label", key: "label" }, "User email"),
              e("input", {
                className: "field-input",
                type: "email",
                name: "user_email",
                value: scoreRequestForm.user_email,
                onChange: updateScoreRequestField,
                placeholder: "user@trustledger.app"
              })
            ]),
            e("label", { className: "field", key: "scheduled" }, [
              e("span", { className: "field-label", key: "label" }, "Schedule for"),
              e("input", {
                className: "field-input",
                type: "datetime-local",
                name: "scheduled_for",
                value: scoreRequestForm.scheduled_for,
                onChange: updateScoreRequestField
              })
            ])
          ]),
          e("div", { className: "action-row", key: "request-actions" }, [
            e(
              "button",
              {
                type: "button",
                className: "button button-secondary button-small",
                disabled: !scoreRequestForm.user_email || Boolean(scoreRequestAction.kind),
                onClick: function onClick() {
                  queueScoreRefreshRequest(false);
                },
                key: "queue"
              },
              scoreRequestAction.kind === "score-queue" ? "Queueing..." : "Queue refresh"
            ),
            e(
              "button",
              {
                type: "button",
                className: "button button-small",
                disabled: !scoreRequestForm.user_email || Boolean(scoreRequestAction.kind),
                onClick: function onClick() {
                  queueScoreRefreshRequest(true);
                },
                key: "now"
              },
              scoreRequestAction.kind === "score-now" ? "Running..." : "Recalculate now"
            )
          ]),
          scoreRequestAction.message
            ? e("div", { className: "form-alert", key: "message" }, scoreRequestAction.message)
            : null
        ]),
        e("div", { className: "auth-form", key: "batch-form" }, [
          e("div", { className: "form-grid", key: "batch-grid" }, [
            e("label", { className: "field", key: "organization" }, [
              e("span", { className: "field-label", key: "label" }, "Agency organization"),
              e(
                "select",
                {
                  className: "field-input field-select",
                  name: "organization_id",
                  value: batchForm.organization_id,
                  onChange: updateBatchField
                },
                [
                  e("option", { value: "", key: "blank" }, "Choose an agency"),
                  state.organizations.map(function renderOrganization(organization) {
                    return e("option", { value: organization.id, key: organization.id }, organization.name);
                  })
                ]
              )
            ]),
            e("label", { className: "field", key: "batch-scheduled" }, [
              e("span", { className: "field-label", key: "label" }, "Schedule for"),
              e("input", {
                className: "field-input",
                type: "datetime-local",
                name: "scheduled_for",
                value: batchForm.scheduled_for,
                onChange: updateBatchField
              })
            ])
          ]),
          e(
            "button",
            {
              type: "button",
              className: "button button-secondary button-small",
              disabled: !batchForm.organization_id || Boolean(batchAction.kind),
              onClick: createScoreBatch,
              key: "create"
            },
            batchAction.kind === "batch-create" ? "Queueing..." : "Queue organization batch"
          ),
          batchAction.message
            ? e("div", { className: "form-alert", key: "message" }, batchAction.message)
            : null
        ])
      ]),
      e("article", { className: "detail-panel", key: "follow-up-controls" }, [
        e("h2", { className: "detail-title", key: "title" }, "Follow-up controls"),
        e(
          "p",
          { className: "empty-copy", key: "copy" },
          "Create manual follow-up tasks when a reviewer needs to chase missing evidence, contact a user, or track an operational edge case."
        ),
        e("form", { className: "auth-form", onSubmit: createFollowUpTask, key: "form" }, [
          e("input", {
            className: "field-input",
            name: "title",
            value: followUpForm.title,
            onChange: updateFollowUpField,
            placeholder: "Follow-up title",
            required: true
          }),
          e("input", {
            className: "field-input",
            name: "details",
            value: followUpForm.details,
            onChange: updateFollowUpField,
            placeholder: "What should the reviewer do?"
          }),
          e("div", { className: "form-grid", key: "grid" }, [
            e("input", {
              className: "field-input",
              type: "email",
              name: "subject_user_email",
              value: followUpForm.subject_user_email,
              onChange: updateFollowUpField,
              placeholder: "Subject email (optional)"
            }),
            e(
              "select",
              {
                className: "field-input field-select",
                name: "organization_id",
                value: followUpForm.organization_id,
                onChange: updateFollowUpField
              },
              [
                e("option", { value: "", key: "blank" }, "No organization"),
                state.organizations.map(function renderOrganization(organization) {
                  return e("option", { value: organization.id, key: organization.id }, organization.name);
                })
              ]
            )
          ]),
          e("input", {
            className: "field-input",
            type: "datetime-local",
            name: "scheduled_for",
            value: followUpForm.scheduled_for,
            onChange: updateFollowUpField
          }),
          e(
            "button",
            {
              type: "submit",
              className: "button button-secondary",
              disabled: automationAction.kind === "follow-up-create",
              key: "submit"
            },
            automationAction.kind === "follow-up-create" ? "Creating..." : "Create follow-up task"
          ),
          automationAction.message &&
          automationAction.kind !== "automation-execute" &&
          automationAction.kind !== "automation-process"
            ? e("div", { className: "form-alert", key: "message" }, automationAction.message)
            : null
        ])
      ])
    ]) : null,
    internalSection === "controls"
      ? e("section", { className: "split-grid", key: "score-runtime" }, [
      e("article", { className: "detail-panel", key: "score-requests" }, [
        e("h2", { className: "detail-title", key: "title" }, "Score refresh queue"),
        state.scoreRequests.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              state.scoreRequests.map(function renderRequest(request) {
                return e("article", { className: "stack-card", key: request.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, "User " + request.user_id),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "request-status",
                      tone: inferStatusTone(request.status),
                      label: request.status
                    }),
                    e(StatusBadge, {
                      key: "reason",
                      tone: "accent",
                      label: request.calculation_reason
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "meta" }, [
                    e(FactPill, { key: "attempts", label: "Attempts", value: String(request.attempt_count), tone: "warning" }),
                    e(FactPill, { key: "scheduled", label: "Scheduled for", value: request.scheduled_for })
                  ]),
                  request.last_error
                    ? e(NoteBlock, { key: "error", tone: "danger", label: "Last error" }, request.last_error)
                    : null,
                  request.status === "pending"
                    ? e(
                        "button",
                        {
                          type: "button",
                          className: "button button-secondary button-small",
                          disabled: scoreRequestAction.kind === "score-process",
                          onClick: function onClick() {
                            processScoreRequest(request);
                          },
                          key: "process"
                        },
                        scoreRequestAction.kind === "score-process" && scoreRequestAction.id === request.id
                          ? "Processing..."
                          : "Process request"
                      )
                    : null
                ]);
              })
            )
          : e("p", { className: "empty-copy", key: "empty" }, "No score refresh requests are waiting right now.")
      ]),
      e("article", { className: "detail-panel", key: "score-batches" }, [
        e("h2", { className: "detail-title", key: "title" }, "Recent score batches"),
        state.scoreBatches.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              state.scoreBatches.map(function renderBatch(batch) {
                return e("article", { className: "stack-card", key: batch.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, batch.scope_type),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "batch-status",
                      tone: inferStatusTone(batch.status),
                      label: batch.status
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "meta" }, [
                    e(FactPill, { key: "users", label: "Users", value: String(batch.requested_user_count) }),
                    e(FactPill, { key: "pending", label: "Pending", value: String(batch.pending_request_count), tone: "warning" }),
                    e(FactPill, { key: "completed", label: "Completed", value: String(batch.completed_request_count), tone: "success" }),
                    e(FactPill, { key: "scheduled", label: "Scheduled for", value: batch.scheduled_for, tone: "accent" })
                  ])
                ]);
              })
            )
          : e("p", { className: "empty-copy", key: "empty" }, "No score batches have been queued yet.")
      ])
    ]) : null,
    internalSection === "reviews"
      ? e("section", { className: "detail-panel", key: "tenancies" }, [
      e("h2", { className: "detail-title", key: "title" }, "Pending tenancy reviews"),
      state.tenancies.length
        ? e(
            "div",
            { className: "list-stack", key: "list" },
            state.tenancies.map(function renderTenancy(tenancy) {
              var noteKey = buildDecisionKey("tenancy", tenancy.id);
              return e("article", { className: "stack-card", key: tenancy.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, tenancy.property_label + " | " + tenancy.tenant_full_name + " and " + tenancy.landlord_full_name),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, { key: "review", tone: "warning", label: "Pending review" })
                ]),
                e("div", { className: "fact-grid", key: "meta" }, [
                  e(FactPill, { key: "city", label: "City", value: tenancy.city }),
                  e(FactPill, { key: "rent", label: "Monthly rent", value: String(tenancy.monthly_rent_minor) + " minor units", tone: "accent" }),
                  e(FactPill, { key: "requested", label: "Requested", value: tenancy.review_requested_at })
                ]),
                e("label", { className: "field", key: "notes" }, [
                  e("span", { className: "field-label", key: "label" }, "Review notes"),
                  e("input", {
                    className: "field-input",
                    value: decisionNotes[noteKey] || "",
                    onChange: function onChange(event) {
                      updateNote(setDecisionNotes, "tenancy", tenancy.id, event.target.value);
                    },
                    maxLength: 1000
                  })
                ]),
                e("div", { className: "action-row", key: "actions" }, [
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-secondary button-small",
                      disabled: Boolean(reviewAction.id),
                      onClick: function onClick() {
                        submitTenancyDecision(tenancy, "reviewed");
                      },
                      key: "reviewed"
                    },
                    reviewAction.kind === "tenancy" &&
                      reviewAction.id === tenancy.id &&
                      reviewAction.decision === "reviewed"
                      ? "Saving..."
                      : "Mark reviewed"
                  ),
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-small",
                      disabled: Boolean(reviewAction.id),
                      onClick: function onClick() {
                        submitTenancyDecision(tenancy, "verified");
                      },
                      key: "verified"
                    },
                    reviewAction.kind === "tenancy" &&
                      reviewAction.id === tenancy.id &&
                      reviewAction.decision === "verified"
                      ? "Saving..."
                      : "Verify tenancy"
                  )
                ])
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No tenancy reviews are waiting right now."
          )
    ]) : null,
    internalSection === "reviews"
      ? e("section", { className: "detail-panel", key: "evidence" }, [
      e("h2", { className: "detail-title", key: "title" }, "Pending evidence reviews"),
      state.evidenceDocuments.length
        ? e(
            "div",
            { className: "list-stack", key: "list" },
            state.evidenceDocuments.map(function renderEvidence(evidenceDocument) {
              var noteKey = buildDecisionKey("evidence", evidenceDocument.id);
              return e("article", { className: "stack-card", key: evidenceDocument.id }, [
                e(
                  "strong",
                  { className: "stack-card-title", key: "title" },
                  evidenceDocument.artifact_name + " | " + evidenceDocument.subject_user_full_name
                ),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, { key: "review", tone: "warning", label: "Pending review" }),
                  e(StatusBadge, {
                    key: "type",
                    tone: "accent",
                    label: evidenceDocument.document_type
                  })
                ]),
                evidenceDocument.summary
                  ? e(NoteBlock, {
                      key: "meta",
                      label: "Submitted summary",
                      tone: "accent"
                    }, evidenceDocument.summary)
                  : null,
                e("label", { className: "field", key: "notes" }, [
                  e("span", { className: "field-label", key: "label" }, "Review notes"),
                  e("input", {
                    className: "field-input",
                    value: decisionNotes[noteKey] || "",
                    onChange: function onChange(event) {
                      updateNote(setDecisionNotes, "evidence", evidenceDocument.id, event.target.value);
                    },
                    maxLength: 1000
                  })
                ]),
                e("div", { className: "action-row", key: "actions" }, [
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-small",
                      disabled: Boolean(reviewAction.id),
                      onClick: function onClick() {
                        submitEvidenceDecision(evidenceDocument, "accepted");
                      },
                      key: "accepted"
                    },
                    reviewAction.kind === "evidence" &&
                      reviewAction.id === evidenceDocument.id &&
                      reviewAction.decision === "accepted"
                      ? "Saving..."
                      : "Accept evidence"
                  ),
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-secondary button-small",
                      disabled: Boolean(reviewAction.id),
                      onClick: function onClick() {
                        submitEvidenceDecision(evidenceDocument, "rejected");
                      },
                      key: "rejected"
                    },
                    reviewAction.kind === "evidence" &&
                      reviewAction.id === evidenceDocument.id &&
                      reviewAction.decision === "rejected"
                      ? "Saving..."
                      : "Reject evidence"
                  )
                ])
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No evidence reviews are waiting right now."
          )
    ]) : null,
    internalSection === "reviews"
      ? e("section", { className: "detail-panel", key: "history-imports" }, [
      e("h2", { className: "detail-title", key: "title" }, "Pending history imports"),
      state.historyImports.length
        ? e(
            "div",
            { className: "list-stack", key: "list" },
            state.historyImports.map(function renderHistoryImport(historyImport) {
              var noteKey = buildDecisionKey("history-import", historyImport.id);
              return e("article", { className: "stack-card", key: historyImport.id }, [
                e(
                  "strong",
                  { className: "stack-card-title", key: "title" },
                  historyImport.title + " | " + historyImport.subject_user_full_name
                ),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, { key: "review", tone: "warning", label: "Pending review" })
                ]),
                e("div", { className: "fact-grid", key: "meta" }, [
                  e(FactPill, {
                    key: "tenancies",
                    label: "Tenancies",
                    value: String(historyImport.tenancy_count)
                  }),
                  e(FactPill, {
                    key: "evidence",
                    label: "Evidence documents",
                    value: String(historyImport.evidence_document_count),
                    tone: "accent"
                  })
                ]),
                e("label", { className: "field", key: "notes" }, [
                  e("span", { className: "field-label", key: "label" }, "Review notes"),
                  e("input", {
                    className: "field-input",
                    value: decisionNotes[noteKey] || "",
                    onChange: function onChange(event) {
                      updateNote(setDecisionNotes, "history-import", historyImport.id, event.target.value);
                    },
                    maxLength: 1000
                  })
                ]),
                e("div", { className: "action-row", key: "actions" }, [
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-small",
                      disabled: Boolean(reviewAction.id),
                      onClick: function onClick() {
                        submitHistoryImportDecision(historyImport, "accepted");
                      },
                      key: "accepted"
                    },
                    reviewAction.kind === "history-import" &&
                      reviewAction.id === historyImport.id &&
                      reviewAction.decision === "accepted"
                      ? "Saving..."
                      : "Accept import"
                  ),
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-secondary button-small",
                      disabled: Boolean(reviewAction.id),
                      onClick: function onClick() {
                        submitHistoryImportDecision(historyImport, "rejected");
                      },
                      key: "rejected"
                    },
                    reviewAction.kind === "history-import" &&
                      reviewAction.id === historyImport.id &&
                      reviewAction.decision === "rejected"
                      ? "Saving..."
                      : "Reject import"
                  )
                ])
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No history-import reviews are waiting right now."
          )
      ]) : null,
      internalSection === "disputes"
        ? e("section", { className: "split-grid", key: "dispute-review" }, [
        e("article", { className: "detail-panel", key: "deposit-disputes" }, [
          e("h2", { className: "detail-title", key: "title" }, "Deposit dispute queue"),
          state.depositDisputes.length
            ? e(
                "div",
                { className: "list-stack", key: "list" },
                state.depositDisputes.map(function renderDepositDispute(depositRecord) {
                  var verdictKey = "deposit:" + depositRecord.id;
                  var verdictForm =
                    disputeVerdictForms[verdictKey] || buildDisputeVerdictForm();
                  var lifecycle = buildDisputeLifecycle({
                    status: depositRecord.deposit_status,
                    appealRequestedAt: depositRecord.appeal_requested_at,
                    appealRequestedByName: depositRecord.appeal_requested_by_user_full_name,
                    reviewRequestedAt: depositRecord.review_requested_at,
                    reviewRequestedByName: depositRecord.review_requested_by_user_full_name,
                    disputedByName: depositRecord.disputed_by_user_full_name
                  });
                return e("article", { className: "stack-card", key: depositRecord.id }, [
                    e("strong", { className: "stack-card-title", key: "title" }, "Deposit"),
                    e("div", { className: "status-row", key: "status" }, [
                      e(StatusBadge, {
                        key: "stage",
                        tone: lifecycle.stageTone,
                        label: lifecycle.stageLabel
                      })
                    ]),
                    e("div", { className: "fact-grid", key: "meta" }, [
                      e(FactPill, {
                        key: "created-by",
                        label: "Created by",
                        value: depositRecord.created_by_user_full_name
                      }),
                      e(FactPill, {
                        key: "return",
                        label: "Proposed return",
                        value: String(depositRecord.proposed_return_minor),
                        tone: "accent"
                      }),
                      e(FactPill, {
                        key: "withheld",
                        label: "Withheld",
                        value: String(depositRecord.withheld_amount_minor),
                        tone: "warning"
                      }),
                      lifecycle.requestedByValue
                        ? e(FactPill, {
                            key: "requested-by",
                            label: lifecycle.requestedByLabel,
                            value: lifecycle.requestedByValue
                          })
                        : null,
                      lifecycle.requestedAtValue
                        ? e(FactPill, {
                            key: "requested-at",
                            label: lifecycle.requestedAtLabel,
                            value: lifecycle.requestedAtValue
                          })
                        : null
                    ]),
                    lifecycle.stageSummary
                      ? e(
                          NoteBlock,
                          {
                            key: "handoff",
                            tone: lifecycle.stageTone,
                            label: "Reviewer handoff"
                          },
                          lifecycle.stageSummary
                        )
                      : null,
                    e(NoteBlock, {
                      key: "summary",
                      tone: "danger",
                      label: "Case notes"
                    }, depositRecord.dispute_notes ||
                        depositRecord.appeal_notes ||
                        depositRecord.settlement_summary ||
                        "No deposit notes recorded."),
                    e("div", { className: "form-grid", key: "inputs" }, [
                      e("label", { className: "field", key: "outcome" }, [
                        e("span", { className: "field-label", key: "label" }, "Verdict outcome"),
                        e(
                          "select",
                          {
                            className: "field-input field-select",
                            value: verdictForm.verdict_outcome,
                            onChange: function onChange(event) {
                              updateEntityForm(
                                setDisputeVerdictForms,
                                verdictKey,
                                "verdict_outcome",
                                event.target.value
                              );
                            }
                          },
                          [
                            e("option", { value: "inconclusive", key: "inconclusive" }, "Inconclusive"),
                            e("option", { value: "favors_tenant", key: "tenant" }, "Favors tenant"),
                            e("option", { value: "favors_landlord", key: "landlord" }, "Favors landlord"),
                            e("option", { value: "shared_fault", key: "shared" }, "Shared fault")
                          ]
                        )
                      ]),
                      e("label", { className: "field", key: "tenant-delta" }, [
                        e("span", { className: "field-label", key: "label" }, "Tenant score delta"),
                        e("input", {
                          className: "field-input",
                          type: "number",
                          min: "-200",
                          max: "200",
                          value: verdictForm.tenant_score_delta,
                          onChange: function onChange(event) {
                            updateEntityForm(
                              setDisputeVerdictForms,
                              verdictKey,
                              "tenant_score_delta",
                              event.target.value
                            );
                          }
                        })
                      ]),
                      e("label", { className: "field", key: "landlord-delta" }, [
                        e("span", { className: "field-label", key: "label" }, "Landlord score delta"),
                        e("input", {
                          className: "field-input",
                          type: "number",
                          min: "-200",
                          max: "200",
                          value: verdictForm.landlord_score_delta,
                          onChange: function onChange(event) {
                            updateEntityForm(
                              setDisputeVerdictForms,
                              verdictKey,
                              "landlord_score_delta",
                              event.target.value
                            );
                          }
                        })
                      ])
                    ]),
                    e("label", { className: "field", key: "summary-field" }, [
                      e("span", { className: "field-label", key: "label" }, "Verdict summary"),
                      e("input", {
                        className: "field-input",
                        value: verdictForm.verdict_summary,
                        onChange: function onChange(event) {
                          updateEntityForm(
                            setDisputeVerdictForms,
                            verdictKey,
                            "verdict_summary",
                            event.target.value
                          );
                        },
                        maxLength: 1000
                      })
                    ]),
                    e("div", { className: "action-row", key: "actions" }, [
                      e(
                        "button",
                        {
                          type: "button",
                          className: "button button-small",
                          disabled: Boolean(reviewAction.id),
                          onClick: function onClick() {
                            submitDepositVerdict(depositRecord);
                          },
                          key: "submit"
                        },
                        reviewAction.kind === "deposit-dispute" &&
                          reviewAction.id === depositRecord.id
                          ? "Saving..."
                          : lifecycle.verdictActionLabel
                      )
                    ])
                  ]);
                })
              )
            : e(
                "p",
                { className: "empty-copy", key: "empty" },
                "No deposit disputes are waiting for review right now."
              )
        ]),
        e("article", { className: "detail-panel", key: "maintenance-disputes" }, [
        e("h2", { className: "detail-title", key: "title" }, "Maintenance dispute queue"),
        state.maintenanceDisputes.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              state.maintenanceDisputes.map(function renderMaintenanceDispute(ticket) {
                var verdictKey = "maintenance:" + ticket.id;
                var verdictForm =
                  disputeVerdictForms[verdictKey] || buildDisputeVerdictForm();
                var lifecycle = buildDisputeLifecycle({
                  status: ticket.ticket_status,
                  appealRequestedAt: ticket.appeal_requested_at,
                  appealRequestedByName: ticket.appeal_requested_by_user_full_name,
                  reviewRequestedAt: ticket.review_requested_at,
                  reviewRequestedByName: ticket.review_requested_by_user_full_name,
                  disputedByName: ticket.disputed_by_user_full_name
                });
                return e("article", { className: "stack-card", key: ticket.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, ticket.title),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "stage",
                      tone: lifecycle.stageTone,
                      label: lifecycle.stageLabel
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "meta" }, [
                    e(FactPill, {
                      key: "reporter",
                      label: "Reported by",
                      value: ticket.created_by_user_full_name
                    }),
                    lifecycle.requestedByValue
                      ? e(FactPill, {
                          key: "requested-by",
                          label: lifecycle.requestedByLabel,
                          value: lifecycle.requestedByValue
                        })
                      : null,
                    lifecycle.requestedAtValue
                      ? e(FactPill, {
                          key: "requested-at",
                          label: lifecycle.requestedAtLabel,
                          value: lifecycle.requestedAtValue
                        })
                      : null
                  ]),
                  lifecycle.stageSummary
                    ? e(
                        NoteBlock,
                        {
                          key: "handoff",
                          tone: lifecycle.stageTone,
                          label: "Reviewer handoff"
                        },
                        lifecycle.stageSummary
                      )
                    : null,
                  e(NoteBlock, {
                    key: "dispute-notes",
                    tone: "danger",
                    label: "Dispute notes"
                  }, ticket.dispute_notes || ticket.appeal_notes || "No dispute notes recorded."),
                  e(NoteBlock, {
                    key: "summary",
                    tone: "accent",
                    label: "Resolution or description"
                  }, ticket.resolution_summary || ticket.description),
                  e("div", { className: "form-grid", key: "inputs" }, [
                    e("label", { className: "field", key: "outcome" }, [
                      e("span", { className: "field-label", key: "label" }, "Verdict outcome"),
                      e(
                        "select",
                        {
                          className: "field-input field-select",
                          value: verdictForm.verdict_outcome,
                          onChange: function onChange(event) {
                            updateEntityForm(
                              setDisputeVerdictForms,
                              verdictKey,
                              "verdict_outcome",
                              event.target.value
                            );
                          }
                        },
                        [
                          e("option", { value: "inconclusive", key: "inconclusive" }, "Inconclusive"),
                          e("option", { value: "favors_tenant", key: "tenant" }, "Favors tenant"),
                          e("option", { value: "favors_landlord", key: "landlord" }, "Favors landlord"),
                          e("option", { value: "shared_fault", key: "shared" }, "Shared fault")
                        ]
                      )
                    ]),
                    e("label", { className: "field", key: "tenant-delta" }, [
                      e("span", { className: "field-label", key: "label" }, "Tenant score delta"),
                      e("input", {
                        className: "field-input",
                        type: "number",
                        min: "-200",
                        max: "200",
                        value: verdictForm.tenant_score_delta,
                        onChange: function onChange(event) {
                          updateEntityForm(
                            setDisputeVerdictForms,
                            verdictKey,
                            "tenant_score_delta",
                            event.target.value
                          );
                        }
                      })
                    ]),
                    e("label", { className: "field", key: "landlord-delta" }, [
                      e("span", { className: "field-label", key: "label" }, "Landlord score delta"),
                      e("input", {
                        className: "field-input",
                        type: "number",
                        min: "-200",
                        max: "200",
                        value: verdictForm.landlord_score_delta,
                        onChange: function onChange(event) {
                          updateEntityForm(
                            setDisputeVerdictForms,
                            verdictKey,
                            "landlord_score_delta",
                            event.target.value
                          );
                        }
                      })
                    ])
                  ]),
                  e("label", { className: "field", key: "summary-field" }, [
                    e("span", { className: "field-label", key: "label" }, "Verdict summary"),
                    e("input", {
                      className: "field-input",
                      value: verdictForm.verdict_summary,
                      onChange: function onChange(event) {
                        updateEntityForm(
                          setDisputeVerdictForms,
                          verdictKey,
                          "verdict_summary",
                          event.target.value
                        );
                      },
                      maxLength: 1000
                    })
                  ]),
                  e("div", { className: "action-row", key: "actions" }, [
                    e(
                      "button",
                      {
                        type: "button",
                        className: "button button-small",
                        disabled: Boolean(reviewAction.id),
                        onClick: function onClick() {
                          submitMaintenanceVerdict(ticket);
                        },
                        key: "submit"
                      },
                      reviewAction.kind === "maintenance-dispute" &&
                        reviewAction.id === ticket.id
                        ? "Saving..."
                        : lifecycle.verdictActionLabel
                    )
                  ])
                ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No maintenance disputes are waiting for review right now."
            )
      ]),
      e("article", { className: "detail-panel", key: "payment-disputes" }, [
        e("h2", { className: "detail-title", key: "title" }, "Payment dispute queue"),
        state.paymentDisputes.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              state.paymentDisputes.map(function renderPaymentDispute(payment) {
                var verdictKey = "payment:" + payment.id;
                var verdictForm =
                  disputeVerdictForms[verdictKey] || buildDisputeVerdictForm();
                var lifecycle = buildDisputeLifecycle({
                  status: payment.payment_status,
                  appealRequestedAt: payment.appeal_requested_at,
                  appealRequestedByName: payment.appeal_requested_by_user_full_name,
                  reviewRequestedAt: payment.review_requested_at,
                  reviewRequestedByName: payment.review_requested_by_user_full_name,
                  disputedByName: payment.disputed_by_user_full_name
                });
                return e("article", { className: "stack-card", key: payment.id }, [
                  e(
                    "strong",
                    { className: "stack-card-title", key: "title" },
                    formatWorkflowLabel(payment.payment_type)
                  ),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "stage",
                      tone: lifecycle.stageTone,
                      label: lifecycle.stageLabel
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "meta" }, [
                    e(FactPill, {
                      key: "route",
                      label: "Route",
                      value: payment.payer_user_full_name + " -> " + payment.payee_user_full_name
                    }),
                    lifecycle.requestedByValue
                      ? e(FactPill, {
                          key: "requested-by",
                          label: lifecycle.requestedByLabel,
                          value: lifecycle.requestedByValue
                        })
                      : null,
                    lifecycle.requestedAtValue
                      ? e(FactPill, {
                          key: "requested-at",
                          label: lifecycle.requestedAtLabel,
                          value: lifecycle.requestedAtValue
                        })
                      : null
                  ]),
                  lifecycle.stageSummary
                    ? e(
                        NoteBlock,
                        {
                          key: "handoff",
                          tone: lifecycle.stageTone,
                          label: "Reviewer handoff"
                        },
                        lifecycle.stageSummary
                      )
                    : null,
                  e(NoteBlock, {
                    key: "dispute-notes",
                    tone: "danger",
                    label: "Dispute or appeal notes"
                  }, payment.dispute_notes || payment.appeal_notes || "No dispute notes recorded."),
                  e(NoteBlock, {
                    key: "summary",
                    tone: "accent",
                    label: "Counterparty or proof notes"
                  }, payment.counterparty_notes ||
                      payment.proof_summary ||
                      "No payment note recorded yet."),
                  e("div", { className: "form-grid", key: "inputs" }, [
                    e("label", { className: "field", key: "outcome" }, [
                      e("span", { className: "field-label", key: "label" }, "Verdict outcome"),
                      e(
                        "select",
                        {
                          className: "field-input field-select",
                          value: verdictForm.verdict_outcome,
                          onChange: function onChange(event) {
                            updateEntityForm(
                              setDisputeVerdictForms,
                              verdictKey,
                              "verdict_outcome",
                              event.target.value
                            );
                          }
                        },
                        [
                          e("option", { value: "inconclusive", key: "inconclusive" }, "Inconclusive"),
                          e("option", { value: "favors_tenant", key: "tenant" }, "Favors tenant"),
                          e("option", { value: "favors_landlord", key: "landlord" }, "Favors landlord"),
                          e("option", { value: "shared_fault", key: "shared" }, "Shared fault")
                        ]
                      )
                    ]),
                    e("label", { className: "field", key: "tenant-delta" }, [
                      e("span", { className: "field-label", key: "label" }, "Tenant score delta"),
                      e("input", {
                        className: "field-input",
                        type: "number",
                        min: "-200",
                        max: "200",
                        value: verdictForm.tenant_score_delta,
                        onChange: function onChange(event) {
                          updateEntityForm(
                            setDisputeVerdictForms,
                            verdictKey,
                            "tenant_score_delta",
                            event.target.value
                          );
                        }
                      })
                    ]),
                    e("label", { className: "field", key: "landlord-delta" }, [
                      e("span", { className: "field-label", key: "label" }, "Landlord score delta"),
                      e("input", {
                        className: "field-input",
                        type: "number",
                        min: "-200",
                        max: "200",
                        value: verdictForm.landlord_score_delta,
                        onChange: function onChange(event) {
                          updateEntityForm(
                            setDisputeVerdictForms,
                            verdictKey,
                            "landlord_score_delta",
                            event.target.value
                          );
                        }
                      })
                    ])
                  ]),
                  e("label", { className: "field", key: "summary-field" }, [
                    e("span", { className: "field-label", key: "label" }, "Verdict summary"),
                    e("input", {
                      className: "field-input",
                      value: verdictForm.verdict_summary,
                      onChange: function onChange(event) {
                        updateEntityForm(
                          setDisputeVerdictForms,
                          verdictKey,
                          "verdict_summary",
                          event.target.value
                        );
                      },
                      maxLength: 1000
                    })
                  ]),
                  e("div", { className: "action-row", key: "actions" }, [
                    e(
                      "button",
                      {
                        type: "button",
                        className: "button button-small",
                        disabled: Boolean(reviewAction.id),
                        onClick: function onClick() {
                          submitPaymentVerdict(payment);
                        },
                        key: "submit"
                      },
                      reviewAction.kind === "payment-dispute" &&
                        reviewAction.id === payment.id
                        ? "Saving..."
                        : lifecycle.verdictActionLabel
                    )
                  ])
                ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No payment disputes are waiting for review right now."
            )
      ])
    ]) : null,
    internalSection === "runtime"
      ? e("section", { className: "split-grid", key: "runtime" }, [
      e("article", { className: "detail-panel", key: "automation" }, [
        e("div", { className: "action-row", key: "header" }, [
          e("h2", { className: "detail-title", key: "title" }, "Due automation tasks"),
          e(
            "button",
            {
              type: "button",
              className: "button button-secondary button-small",
              disabled: automationAction.kind === "automation-claim",
              onClick: claimDueAutomationTasks,
              key: "claim"
            },
            automationAction.kind === "automation-claim" ? "Claiming..." : "Claim due tasks"
          ),
          e(
            "button",
            {
              type: "button",
              className: "button button-secondary button-small",
              disabled: Boolean(automationAction.kind),
              onClick: function onClick() {
                cleanupAutomationTasks("cleanup-expired-consents");
              },
              key: "cleanup-consents"
            },
            automationAction.kind === "cleanup-expired-consents"
              ? "Cleaning..."
              : "Clean expired consent reminders"
          ),
          e(
            "button",
            {
              type: "button",
              className: "button button-secondary button-small",
              disabled: Boolean(automationAction.kind),
              onClick: function onClick() {
                cleanupAutomationTasks("cleanup-stale-follow-ups");
              },
              key: "cleanup-followups"
            },
            automationAction.kind === "cleanup-stale-follow-ups"
              ? "Cleaning..."
              : "Clean stale follow-ups"
          )
        ]),
        automationAction.message &&
        (automationAction.kind === "" ||
          automationAction.kind === "automation-claim" ||
          automationAction.kind === "cleanup-expired-consents" ||
          automationAction.kind === "cleanup-stale-follow-ups" ||
          automationAction.kind === "automation-execute" ||
          automationAction.kind === "automation-process")
          ? e("div", { className: "form-alert", key: "message" }, automationAction.message)
          : null,
        state.automationTasks.length
          ? e(
            "div",
            { className: "list-stack", key: "list" },
            state.automationTasks.map(function renderTask(task) {
              return e("article", { className: "stack-card", key: task.id }, [
                e(
                  "strong",
                  { className: "stack-card-title", key: "title" },
                  task.title
                ),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "type",
                    tone: "accent",
                    label: task.task_type
                  }),
                  e(StatusBadge, {
                    key: "task-status",
                    tone: inferStatusTone(task.status),
                    label: task.status
                  })
                ]),
                e("div", { className: "fact-grid", key: "meta" }, [
                  e(FactPill, {
                    key: "scheduled",
                    label: "Scheduled for",
                    value: task.scheduled_for
                  })
                ]),
                e(
                  NoteBlock,
                  { key: "details", label: "Task details", tone: "accent" },
                  task.details || task.result_notes || "No extra details recorded."
                ),
                e("div", { className: "action-row", key: "actions" }, [
                    canExecuteAutomationTask(task)
                      ? e(
                          "button",
                          {
                            type: "button",
                            className: "button button-secondary button-small",
                            disabled: Boolean(automationAction.kind),
                            onClick: function onClick() {
                              executeAutomationTask(task);
                            },
                            key: "execute"
                          },
                          automationAction.kind === "automation-execute" && automationAction.id === task.id
                            ? "Executing..."
                            : "Execute now"
                        )
                      : e(
                          "button",
                          {
                            type: "button",
                            className: "button button-secondary button-small",
                            disabled: Boolean(automationAction.kind),
                            onClick: function onClick() {
                              processAutomationTask(
                                task,
                                "processing",
                                "Picked up from the review center."
                              );
                            },
                            key: "processing"
                          },
                          automationAction.kind === "automation-process" && automationAction.id === task.id
                            ? "Updating..."
                            : "Mark processing"
                        ),
                    e(
                      "button",
                      {
                        type: "button",
                        className: "button button-small",
                        disabled: Boolean(automationAction.kind),
                        onClick: function onClick() {
                          processAutomationTask(
                            task,
                            "completed",
                            "Closed from the rebuilt review center."
                          );
                        },
                        key: "complete"
                      },
                      automationAction.kind === "automation-process" && automationAction.id === task.id
                        ? "Updating..."
                        : "Mark complete"
                    ),
                    e(
                      "button",
                      {
                        type: "button",
                        className: "button button-secondary button-small",
                        disabled: Boolean(automationAction.kind),
                        onClick: function onClick() {
                          processAutomationTask(
                            task,
                            "canceled",
                            "Canceled from the rebuilt review center."
                          );
                        },
                        key: "cancel"
                      },
                      automationAction.kind === "automation-process" && automationAction.id === task.id
                        ? "Updating..."
                        : "Cancel"
                    )
                  ])
                ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No due automation tasks are waiting right now."
            )
      ]),
      e("article", { className: "detail-panel", key: "notifications" }, [
        e("h2", { className: "detail-title", key: "title" }, "Recent notifications"),
        state.notifications.length
          ? e(
            "div",
            { className: "list-stack", key: "list" },
            state.notifications.map(function renderNotification(notification) {
              return e("article", { className: "stack-card", key: notification.id }, [
                e(
                  "strong",
                  { className: "stack-card-title", key: "title" },
                  notification.subject_line
                ),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "notification-status",
                    tone: inferStatusTone(notification.status),
                    label: notification.status
                  })
                ]),
                e("div", { className: "fact-grid", key: "meta" }, [
                  e(FactPill, {
                    key: "recipient",
                    label: "Recipient",
                    value: notification.recipient_address
                  }),
                  e(FactPill, {
                    key: "scheduled",
                    label: "Scheduled for",
                    value: notification.scheduled_for
                  }),
                  e(FactPill, {
                    key: "attempts",
                    label: "Attempts",
                    value: String(notification.attempt_count),
                    tone: "warning"
                  })
                ]),
                e(
                  NoteBlock,
                  { key: "template", label: "Template", tone: "accent" },
                  notification.template_key
                ),
                notification.last_error
                  ? e(
                      NoteBlock,
                      { key: "error", label: "Last error", tone: "danger" },
                      notification.last_error
                    )
                  : null
              ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No notification deliveries have been queued yet."
            )
      ]),
      e("article", { className: "detail-panel", key: "worker-runs" }, [
        e("h2", { className: "detail-title", key: "title" }, "Recent worker runs"),
        state.workerRuns.length
          ? e(
            "div",
            { className: "list-stack", key: "list" },
            state.workerRuns.map(function renderWorkerRun(workerRun) {
              return e("article", { className: "stack-card", key: workerRun.id }, [
                e(
                  "strong",
                  { className: "stack-card-title", key: "title" },
                  "Run " + workerRun.id
                ),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "run-status",
                    tone: inferStatusTone(workerRun.status),
                    label: workerRun.status
                  })
                ]),
                e("div", { className: "fact-grid", key: "counts" }, [
                  e(FactPill, {
                    key: "started",
                    label: "Started",
                    value: workerRun.run_started_at
                  }),
                  e(FactPill, {
                    key: "automation",
                    label: "Automation claimed",
                    value: String(workerRun.claimed_automation_task_count)
                  }),
                  e(FactPill, {
                    key: "notifications",
                    label: "Notifications sent",
                    value: String(workerRun.sent_notification_count),
                    tone: "success"
                  }),
                  e(FactPill, {
                    key: "scores",
                    label: "Scores processed",
                    value: String(workerRun.processed_score_request_count),
                    tone: "accent"
                  })
                ]),
                workerRun.last_error
                  ? e(
                      NoteBlock,
                      { key: "error", label: "Last error", tone: "danger" },
                      workerRun.last_error
                    )
                  : null
              ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No worker runs have been recorded yet."
            )
      ])
    ]) : null,
    internalSection === "audit"
      ? e("section", { className: "detail-panel", key: "audit-logs" }, [
      e("div", { className: "action-row", key: "header" }, [
        e("h2", { className: "detail-title", key: "title" }, "Recent audit activity"),
        e(
          "select",
          {
            className: "field-input field-select",
            value: auditActionType,
            onChange: function onChange(event) {
              setAuditActionType(event.target.value);
            },
            key: "filter"
          },
          auditActionOptions.map(function renderOption(option) {
            return e("option", { value: option.value, key: option.value || "all" }, option.label);
          })
        )
      ]),
        state.auditLogs.length
          ? e(
              "div",
              { className: "timeline-list", key: "list" },
              state.auditLogs.map(function renderAuditLog(auditLog) {
                return e(TimelineEntry, {
                  key: auditLog.id,
                  eyebrow: auditLog.created_at,
                  title: auditLog.action_type,
                  badges: [
                    e(StatusBadge, {
                      key: "outcome",
                      tone: inferStatusTone(auditLog.outcome_status),
                      label: auditLog.outcome_status
                    })
                  ],
                  meta:
                    (auditLog.actor_user_email || "System actor") +
                    " | " +
                    (auditLog.organization_name || "No organization"),
                  summary: auditLog.details || "No extra audit details recorded.",
                  details: auditLog.target_type
                    ? [
                        e(FactPill, {
                          key: "target",
                          label: "Target",
                          value:
                            auditLog.target_type + " | " + (auditLog.target_id || "n/a")
                        })
                      ]
                    : []
                });
              })
            )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No audit events match the current filter."
          )
    ]) : null
  ]);
}
