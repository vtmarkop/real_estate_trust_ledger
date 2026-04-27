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
import { apiRequest } from "../lib/api.js";
import { e } from "../lib/i18n.js";

function buildEvidenceForm(sessionUserId, tenancy) {
  return {
    subject_user_id:
      tenancy.tenant_user_id === sessionUserId || tenancy.landlord_user_id === sessionUserId
        ? sessionUserId
        : tenancy.tenant_user_id,
    document_type: "other",
    artifact_name: "",
    summary: "",
    file: null
  };
}

function buildHistoryImportForm() {
  return { title: "", summary: "" };
}

function buildTenancyForm() {
  return {
    user_role: "tenant",
    counterparty_email: "",
    property_id: "",
    property_label: "",
    address_line1: "",
    city: "",
    country_code: "GR",
    lease_start_date: "",
    lease_end_date: "",
    monthly_rent: "",
    deposit: "",
    currency_code: "EUR",
    tenancy_status: "active"
  };
}

function buildPropertyCreateForm() {
  return {
    property_label: "",
    address_line1: "",
    city: "",
    country_code: "GR",
    custom_tags_text: "",
    management_mode: "owner_managed",
    assigned_agency_organization_id: "",
    assigned_agency_user_email: "",
    assigned_tenant_email: ""
  };
}

function buildPropertyEditForm(propertyRecord) {
  return {
    property_label: propertyRecord.property_label || "",
    address_line1: propertyRecord.address_line1 || "",
    city: propertyRecord.city || "",
    country_code: propertyRecord.country_code || "GR",
    custom_tags_text: formatTagText(propertyRecord.custom_tags),
    management_mode: propertyRecord.management_mode || "owner_managed",
    assigned_agency_organization_id: propertyRecord.assigned_agency_organization_id || "",
    assigned_agency_user_email: propertyRecord.assigned_agency_user_email || "",
    assigned_tenant_email: propertyRecord.assigned_tenant_user_email || ""
  };
}

function buildReferenceRequestForm(sessionUserId, tenancy) {
  if (tenancy.tenant_user_id === sessionUserId) {
    return {
      subject_user_id: sessionUserId,
      requested_from_user_id: tenancy.landlord_user_id,
      message: ""
    };
  }
  if (tenancy.landlord_user_id === sessionUserId) {
    return {
      subject_user_id: sessionUserId,
      requested_from_user_id: tenancy.tenant_user_id,
      message: ""
    };
  }
  return null;
}

function buildTenancyPartyContext(tenancy, userId) {
  if (userId === tenancy.tenant_user_id) {
    return {
      role: "Tenant",
      counterpartyLabel: "Landlord",
      counterpartyName: tenancy.landlord_full_name || "Landlord"
    };
  }

  if (userId === tenancy.landlord_user_id) {
    return {
      role: "Landlord",
      counterpartyLabel: "Tenant",
      counterpartyName: tenancy.tenant_full_name || "Tenant"
    };
  }

  return {
    role: "Participant",
    counterpartyLabel: "Other party",
    counterpartyName: [
      tenancy.tenant_full_name || "Tenant",
      tenancy.landlord_full_name || "Landlord"
    ].join(" / ")
  };
}

function buildReferenceFulfillmentForm() {
  return {
    artifact_name: "",
    summary: "",
    file: null
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

function updateSimpleForm(setter, name, value) {
  setter(function mergeForm(previous) {
    var next = Object.assign({}, previous);
    next[name] = value;
    return next;
  });
}

function updateSelectionMap(setter, entityId, value) {
  setter(function mergeSelection(previous) {
    var next = Object.assign({}, previous);
    next[entityId] = value;
    return next;
  });
}

function parseMinorAmount(value) {
  return Math.round(Number(value || 0) * 100);
}

function parseTagText(value) {
  return String(value || "")
    .split(",")
    .map(function normalizeTag(tag) {
      return tag.trim();
    })
    .filter(Boolean);
}

function formatTagText(tags) {
  return (tags || []).join(", ");
}

function applyPropertyManagementMode(form, value) {
  var next = Object.assign({}, form);
  next.management_mode = value;
  if (value !== "agency_managed") {
    next.assigned_agency_organization_id = "";
    next.assigned_agency_user_email = "";
  }
  return next;
}

function isAgencyManagedProperty(form) {
  return (form && form.management_mode) === "agency_managed";
}

function getPropertyWorkspaceAccess(options) {
  var propertyCount = Number((options && options.propertyCount) || 0);
  var ownedPropertyCount = Number((options && options.ownedPropertyCount) || 0);
  var canOperateAgency = Boolean(options && options.canOperateAgency);
  var tenancyRole = String((options && options.tenancyRole) || "");
  var canCreate = tenancyRole === "landlord" || canOperateAgency || ownedPropertyCount > 0;

  return {
    canCreate: canCreate,
    canSee: propertyCount > 0 || canCreate
  };
}

export function RecordsPage() {
  var session = useSession();
  var stateTuple = React.useState({
    status: "loading",
    agencies: [],
    properties: [],
    tenancies: [],
    evidenceByTenancy: {},
    historyImports: [],
    referenceRequests: [],
    error: null
  });
  var state = stateTuple[0];
  var setState = stateTuple[1];
  var evidenceFormsTuple = React.useState({});
  var evidenceForms = evidenceFormsTuple[0];
  var setEvidenceForms = evidenceFormsTuple[1];
  var referenceFormsTuple = React.useState({});
  var referenceForms = referenceFormsTuple[0];
  var setReferenceForms = referenceFormsTuple[1];
  var fulfillmentFormsTuple = React.useState({});
  var fulfillmentForms = fulfillmentFormsTuple[0];
  var setFulfillmentForms = fulfillmentFormsTuple[1];
  var historyImportFormTuple = React.useState(buildHistoryImportForm());
  var historyImportForm = historyImportFormTuple[0];
  var setHistoryImportForm = historyImportFormTuple[1];
  var propertyFormTuple = React.useState(buildPropertyCreateForm());
  var propertyForm = propertyFormTuple[0];
  var setPropertyForm = propertyFormTuple[1];
  var propertyEditFormsTuple = React.useState({});
  var propertyEditForms = propertyEditFormsTuple[0];
  var setPropertyEditForms = propertyEditFormsTuple[1];
  var tenancyFormTuple = React.useState(buildTenancyForm());
  var tenancyForm = tenancyFormTuple[0];
  var setTenancyForm = tenancyFormTuple[1];
  var actionTuple = React.useState({ kind: "", id: "", message: null });
  var actionState = actionTuple[0];
  var setActionState = actionTuple[1];
  var recordsSectionTuple = React.useState("tenancies");
  var activeRecordsSection = recordsSectionTuple[0];
  var setActiveRecordsSection = recordsSectionTuple[1];
  var propertyWorkspaceTuple = React.useState("create");
  var propertyWorkspace = propertyWorkspaceTuple[0];
  var setPropertyWorkspace = propertyWorkspaceTuple[1];
  var historyWorkspaceTuple = React.useState("imports");
  var historyWorkspace = historyWorkspaceTuple[0];
  var setHistoryWorkspace = historyWorkspaceTuple[1];
  var artifactWorkspaceTuple = React.useState({});
  var artifactWorkspace = artifactWorkspaceTuple[0];
  var setArtifactWorkspace = artifactWorkspaceTuple[1];

  var loadRecords = React.useCallback(async function loadRecords() {
    setState(function markLoading(previous) {
      return {
        status:
          previous.tenancies.length ||
          previous.agencies.length ||
          previous.properties.length ||
          previous.historyImports.length ||
          previous.referenceRequests.length
            ? "refreshing"
            : "loading",
        agencies: previous.agencies,
        properties: previous.properties,
        tenancies: previous.tenancies,
        evidenceByTenancy: previous.evidenceByTenancy,
        historyImports: previous.historyImports,
        referenceRequests: previous.referenceRequests,
        error: null
      };
    });

      try {
        var results = await Promise.all([
          apiRequest("/organizations/directory/agencies"),
          apiRequest("/properties/mine"),
          apiRequest("/tenancies/mine"),
          apiRequest("/history-imports/mine"),
          apiRequest("/reference-requests/mine")
        ]);
      var agencies = results[0];
      var properties = results[1];
      var tenancies = results[2];
      var historyImports = results[3];
      var referenceRequests = results[4];
      var evidenceResults = {};

      await Promise.all(
        tenancies.map(async function loadEvidence(tenancy) {
          evidenceResults[tenancy.id] = await apiRequest("/tenancies/" + tenancy.id + "/evidence");
        })
      );

      setState({
        status: "ready",
        agencies: agencies,
        properties: properties,
        tenancies: tenancies,
        evidenceByTenancy: evidenceResults,
        historyImports: historyImports,
        referenceRequests: referenceRequests,
        error: null
      });

      setPropertyEditForms(function syncPropertyForms(previous) {
        var next = Object.assign({}, previous);
        properties.forEach(function ensurePropertyForm(propertyRecord) {
          next[propertyRecord.id] = buildPropertyEditForm(propertyRecord);
        });
        return next;
      });

      setEvidenceForms(function syncEvidence(previous) {
        var next = Object.assign({}, previous);
        tenancies.forEach(function ensureEvidence(tenancy) {
          if (!next[tenancy.id]) {
            next[tenancy.id] = buildEvidenceForm(session.user.id, tenancy);
          }
        });
        return next;
      });

      setArtifactWorkspace(function syncArtifactWorkspace(previous) {
        var next = Object.assign({}, previous);
        tenancies.forEach(function ensureArtifactWorkspace(tenancy) {
          if (!next[tenancy.id]) {
            next[tenancy.id] = "create";
          }
        });
        return next;
      });

      setReferenceForms(function syncReferences(previous) {
        var next = Object.assign({}, previous);
        tenancies.forEach(function ensureReference(tenancy) {
          if (!next[tenancy.id]) {
            var form = buildReferenceRequestForm(session.user.id, tenancy);
            if (form) {
              next[tenancy.id] = form;
            }
          }
        });
        return next;
      });

      setFulfillmentForms(function syncFulfillments(previous) {
        var next = Object.assign({}, previous);
        referenceRequests.forEach(function ensureFulfillment(referenceRequest) {
          if (
            referenceRequest.status === "pending" &&
            referenceRequest.requested_from_user_id === session.user.id &&
            !next[referenceRequest.id]
          ) {
            next[referenceRequest.id] = buildReferenceFulfillmentForm();
          }
        });
        return next;
      });
    } catch (error) {
      setState({
        status: "error",
        agencies: [],
        properties: [],
        tenancies: [],
        evidenceByTenancy: {},
        historyImports: [],
        referenceRequests: [],
        error: error.message || "Unable to load record-management surfaces."
      });
    }
  }, [session.user.id]);

  React.useEffect(function bootstrapRecords() {
    loadRecords();
  }, [loadRecords]);

  async function handleSimplePost(kind, id, path, successMessage) {
    setActionState({ kind: kind, id: id, message: null });
    try {
      await apiRequest(path, { method: "POST" });
      await loadRecords();
      setActionState({ kind: "", id: "", message: successMessage });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Request failed."
      });
    }
  }

  async function handleCreateProperty() {
    setActionState({ kind: "property-create", id: "new", message: null });
    try {
      await apiRequest("/properties", {
        method: "POST",
        body: {
          property_label: propertyForm.property_label,
          address_line1: propertyForm.address_line1,
          city: propertyForm.city,
          country_code: propertyForm.country_code,
          custom_tags: parseTagText(propertyForm.custom_tags_text),
          management_mode: propertyForm.management_mode,
          assigned_agency_organization_id: isAgencyManagedProperty(propertyForm)
            ? propertyForm.assigned_agency_organization_id || null
            : null,
          assigned_agency_user_email: isAgencyManagedProperty(propertyForm)
            ? propertyForm.assigned_agency_user_email || null
            : null,
          assigned_tenant_email: propertyForm.assigned_tenant_email || null
        }
      });
      await loadRecords();
      setPropertyForm(buildPropertyCreateForm());
      setActionState({ kind: "", id: "", message: "Property saved with the selected management setup." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to create property."
      });
    }
  }

  async function handleSaveProperty(propertyRecord) {
    var form = propertyEditForms[propertyRecord.id];
    if (!form) {
      return;
    }

    setActionState({ kind: "property-save", id: propertyRecord.id, message: null });
    try {
      await apiRequest("/properties/" + propertyRecord.id, {
        method: "PATCH",
        body: {
          property_label: form.property_label,
          address_line1: form.address_line1,
          city: form.city,
          country_code: form.country_code,
          custom_tags: parseTagText(form.custom_tags_text),
          management_mode: form.management_mode,
          assigned_agency_organization_id: isAgencyManagedProperty(form)
            ? form.assigned_agency_organization_id || null
            : null,
          assigned_agency_user_email: isAgencyManagedProperty(form)
            ? form.assigned_agency_user_email || null
            : null,
          assigned_tenant_email: form.assigned_tenant_email || null,
          clear_agency_assignment:
            !isAgencyManagedProperty(form) ||
            !String(form.assigned_agency_organization_id || "").trim() &&
            !String(form.assigned_agency_user_email || "").trim(),
          clear_tenant_assignment: !String(form.assigned_tenant_email || "").trim()
        }
      });
      await loadRecords();
      setActionState({ kind: "", id: "", message: "Property setup updated." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to update this property."
      });
    }
  }

  async function handleEvidenceSubmit(tenancyId) {
    var payload = evidenceForms[tenancyId];
    if (!payload) {
      return;
    }

    setActionState({ kind: "evidence", id: tenancyId, message: null });
    try {
      var evidencePayload = {
        subject_user_id: payload.subject_user_id,
        document_type: payload.document_type,
        artifact_name: payload.artifact_name,
        summary: payload.summary
      };
      if (payload.file) {
        var artifactUploadForm = new FormData();
        artifactUploadForm.append("artifact", payload.file);
        var storedArtifact = await apiRequest("/evidence/tenancies/" + tenancyId + "/artifacts", {
          method: "POST",
          body: artifactUploadForm
        });
        evidencePayload.stored_artifact_id = storedArtifact.id;
        evidencePayload.artifact_name = storedArtifact.original_file_name;
      }
      await apiRequest("/tenancies/" + tenancyId + "/evidence", {
        method: "POST",
        body: evidencePayload
      });
      await loadRecords();
      setEvidenceForms(function reset(previous) {
        var next = Object.assign({}, previous);
        var tenancy = state.tenancies.find(function findTenancy(candidate) {
          return candidate.id === tenancyId;
        });
        if (tenancy) {
          next[tenancyId] = buildEvidenceForm(session.user.id, tenancy);
        }
        return next;
      });
      setActionState({ kind: "", id: "", message: "Evidence submitted successfully." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to submit evidence."
      });
    }
  }

  async function handleCreateHistoryImport() {
    setActionState({ kind: "history-import-create", id: "new", message: null });
    try {
      await apiRequest("/history-imports", {
        method: "POST",
        body: historyImportForm
      });
      await loadRecords();
      setHistoryImportForm(buildHistoryImportForm());
      setActionState({ kind: "", id: "", message: "History import draft created." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to create history import."
      });
    }
  }

  async function handleCreateTenancy() {
    setActionState({ kind: "tenancy-create", id: "new", message: null });
    try {
      var payload = {
        property_id: tenancyForm.property_id || null,
        lease_start_date: tenancyForm.lease_start_date,
        lease_end_date: tenancyForm.lease_end_date || null,
        monthly_rent_minor: parseMinorAmount(tenancyForm.monthly_rent),
        deposit_minor: parseMinorAmount(tenancyForm.deposit),
        currency_code: tenancyForm.currency_code,
        tenancy_status: tenancyForm.tenancy_status
      };

      if (!tenancyForm.property_id) {
        payload.property_label = tenancyForm.property_label;
        payload.address_line1 = tenancyForm.address_line1;
        payload.city = tenancyForm.city;
        payload.country_code = tenancyForm.country_code;
      }

      if (tenancyForm.user_role === "tenant") {
        payload.tenant_user_id = session.user.id;
        payload.landlord_email = tenancyForm.counterparty_email;
      } else {
        payload.landlord_user_id = session.user.id;
        payload.tenant_email = tenancyForm.counterparty_email;
      }

      await apiRequest("/tenancies", {
        method: "POST",
        body: payload
      });
      await loadRecords();
      setTenancyForm(buildTenancyForm());
      setActionState({ kind: "", id: "", message: "Tenancy record created successfully." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to create tenancy record."
      });
    }
  }

  async function handleCreateReferenceRequest(tenancy) {
    var payload = referenceForms[tenancy.id];
    if (!payload) {
      return;
    }

    setActionState({ kind: "reference-request-create", id: tenancy.id, message: null });
    try {
      await apiRequest("/reference-requests/tenancies/" + tenancy.id, {
        method: "POST",
        body: payload
      });
      await loadRecords();
      setActionState({ kind: "", id: "", message: "Counterparty reference request created." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to create reference request."
      });
    }
  }

  async function handleFulfillReferenceRequest(referenceRequest) {
    var payload = fulfillmentForms[referenceRequest.id];
    if (!payload) {
      return;
    }

    setActionState({ kind: "reference-request-fulfill", id: referenceRequest.id, message: null });
    try {
      var fulfillmentPayload = {
        artifact_name: payload.artifact_name,
        summary: payload.summary
      };
      if (payload.file) {
        var artifactUploadForm = new FormData();
        artifactUploadForm.append("artifact", payload.file);
        var storedArtifact = await apiRequest(
          "/evidence/tenancies/" + referenceRequest.tenancy_id + "/artifacts",
          {
            method: "POST",
            body: artifactUploadForm
          }
        );
        fulfillmentPayload.stored_artifact_id = storedArtifact.id;
        fulfillmentPayload.artifact_name = storedArtifact.original_file_name;
      }
      await apiRequest("/reference-requests/" + referenceRequest.id + "/fulfill", {
        method: "POST",
        body: fulfillmentPayload
      });
      await loadRecords();
      setFulfillmentForms(function reset(previous) {
        var next = Object.assign({}, previous);
        next[referenceRequest.id] = buildReferenceFulfillmentForm();
        return next;
      });
      setActionState({ kind: "", id: "", message: "Counterparty reference submitted." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to fulfill reference request."
      });
    }
  }

  async function handleEvidenceArtifactAccess(evidence) {
    setActionState({ kind: "evidence-artifact-access", id: evidence.id, message: null });
    try {
      var access = await apiRequest("/evidence/" + evidence.id + "/artifact-access", {
        method: "POST"
      });
      window.open(access.download_url, "_blank", "noopener");
      setActionState({ kind: "", id: "", message: "Evidence artifact opened in a new tab." });
    } catch (error) {
      setActionState({
        kind: "",
        id: "",
        message: error.message || "Unable to open the evidence artifact."
      });
    }
  }

  var ownedPropertyCountForAccess = session.user
    ? state.properties.filter(function countOwnedProperties(propertyRecord) {
        return propertyRecord.created_by_user_id === session.user.id;
      }).length
    : 0;
  var propertyWorkspaceAccessForHooks = getPropertyWorkspaceAccess({
    propertyCount: state.properties.length,
    ownedPropertyCount: ownedPropertyCountForAccess,
    canOperateAgency: session.capabilities.canOperateAgency,
    tenancyRole: tenancyForm.user_role
  });

  React.useEffect(function normalizeRecordLanes() {
    if (!propertyWorkspaceAccessForHooks.canSee && activeRecordsSection === "properties") {
      setActiveRecordsSection("tenancies");
    }
    if (!propertyWorkspaceAccessForHooks.canCreate && propertyWorkspace === "create") {
      setPropertyWorkspace("manage");
    }
  }, [
    activeRecordsSection,
    propertyWorkspace,
    propertyWorkspaceAccessForHooks.canCreate,
    propertyWorkspaceAccessForHooks.canSee
  ]);

  if (state.status === "loading") {
    return e("div", { className: "state-panel" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Rental Records"),
      e("h1", { className: "state-title", key: "title" }, "Loading records and imports"),
      e(
        "p",
        { className: "state-copy", key: "copy" },
        "We are loading your properties, tenancy records, uploaded evidence, past-history imports, and reference requests."
      )
    ]);
  }

  if (state.status === "error") {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Rental Records"),
      e("h1", { className: "state-title", key: "title" }, "Records unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  var pendingIncomingRequests = state.referenceRequests.filter(function filterIncoming(referenceRequest) {
    return (
      referenceRequest.status === "pending" &&
      referenceRequest.requested_from_user_id === session.user.id
    );
  });
  var outgoingReferenceRequests = state.referenceRequests.filter(function filterOutgoing(referenceRequest) {
    return referenceRequest.requested_by_user_id === session.user.id;
  });
  var reusableOwnedProperties = state.properties.filter(function filterOwnedProperties(propertyRecord) {
    return propertyRecord.created_by_user_id === session.user.id;
  });
  var totalArtifactCount = Object.values(state.evidenceByTenancy).reduce(function sumArtifacts(total, list) {
    return total + (Array.isArray(list) ? list.length : 0);
  }, 0);
  var propertyWorkspaceAccess = getPropertyWorkspaceAccess({
    propertyCount: state.properties.length,
    ownedPropertyCount: reusableOwnedProperties.length,
    canOperateAgency: session.capabilities.canOperateAgency,
    tenancyRole: tenancyForm.user_role
  });
  var canCreatePropertyWorkspace = propertyWorkspaceAccess.canCreate;
  var canSeePropertyWorkspace = propertyWorkspaceAccess.canSee;
  var propertyWorkspaceTabs = canCreatePropertyWorkspace
    ? [
        { id: "create", label: "Create property", meta: "New property setup" },
        { id: "manage", label: "Manage saved properties", meta: String(state.properties.length) + " records" }
      ]
    : [];
  var effectivePropertyWorkspace = canCreatePropertyWorkspace ? propertyWorkspace : "manage";
  var recordsSectionTabs = [
    {
      id: "tenancies",
      label: "Tenancy records",
      meta: String(state.tenancies.length) + " active or past records"
    },
    canSeePropertyWorkspace
      ? {
          id: "properties",
          label: "Properties & setup",
          meta: String(state.properties.length) + " saved properties"
        }
      : null,
    {
      id: "artifacts",
      label: "Artifacts",
      meta: state.tenancies.length ? "Create and review supporting files" : "Available after your first tenancy"
    },
    {
      id: "history",
      label: "History & references",
      meta: String(state.historyImports.length + state.referenceRequests.length) + " import or reference items"
    }
  ].filter(Boolean);
  var recordsSectionCopyByTab = {
    tenancies:
      "Focus on tenancy records only. This area is now limited to setting up or validating the tenancy itself.",
    properties:
      "Keep property setup separate from tenancy work. Save the property once, then decide whether you or an agency manages it.",
    artifacts:
      "Keep file work separate from record setup. Use one tab to add a new artifact and another to review what is already on file.",
    history:
      "Handle older rental history and reference activity here, away from live tenancy operations."
  };

  function handleRecordSectionChange(nextSection) {
    setActiveRecordsSection(nextSection);
    if (typeof document !== "undefined") {
      window.requestAnimationFrame(function focusSection() {
        var section = document.getElementById("records-section-" + nextSection);
        if (section && typeof section.scrollIntoView === "function") {
          section.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      });
    }
  }

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Rental Records",
      title: "Rental records, evidence, and references",
      copy:
        "Use this page to manage current and past tenancies, upload supporting documents, import old rental history, and request or answer references.",
      details: [
        "This workspace is now structured so record setup, property setup, artifacts, and historical proof each live in their own lane."
      ],
      stats: [
        e(HeroStat, {
          label: "Tenancies",
          value: String(state.tenancies.length),
          copy: "Active and historical tenancy records."
        }),
        canSeePropertyWorkspace
          ? e(HeroStat, {
              label: "Saved properties",
              value: String(state.properties.length),
              copy: String(reusableOwnedProperties.length) + " reusable by you for future tenancy setup."
            })
          : null,
        e(HeroStat, {
          label: "Artifacts & references",
          value: String(totalArtifactCount + state.referenceRequests.length),
          copy: String(pendingIncomingRequests.length) + " incoming reference requests awaiting action."
        })
      ]
    }),
    actionState.message ? e("div", { className: "form-alert", key: "message" }, actionState.message) : null,
    e("section", { className: "detail-panel section-switcher", key: "section-switcher" }, [
      e(SectionHeading, {
        title: "Work in one lane at a time",
        copy:
          activeRecordsSection === "properties" && !canCreatePropertyWorkspace
            ? "Property setup is handled by the owner or agency operator. This lane only shows the property records already linked to your account."
            : recordsSectionCopyByTab[activeRecordsSection],
        key: "heading"
      }),
      e(SegmentedTabs, {
        key: "tabs",
        tabs: recordsSectionTabs,
        activeTab: activeRecordsSection,
        onChange: handleRecordSectionChange,
        "aria-label": "Rental records sections"
      })
    ]),
    e("section", { className: "split-grid", key: "tenancy-create-row", id: "records-section-tenancies" }, [
      e("article", { className: "detail-panel", key: "tenancy-create" }, [
        e("h2", { className: "detail-title", key: "title" }, "Add a tenancy record"),
        e(
          "p",
          { className: "empty-copy", key: "copy" },
          "Create a tenancy using a saved property or by entering a new address. Use your counterparty's email so the record is linked to the right person."
        ),
        e("div", { className: "auth-form", key: "form" }, [
          e("div", { className: "form-grid", key: "role-row" }, [
            e("label", { className: "field", key: "user_role" }, [
              e("span", { className: "field-label", key: "label" }, "My role in this tenancy"),
              e(
                "select",
                {
                  className: "field-input field-select",
                  value: tenancyForm.user_role,
                  onChange: function onChange(event) {
                    updateSimpleForm(setTenancyForm, "user_role", event.target.value);
                  }
                },
                [
                  e("option", { value: "tenant", key: "tenant" }, "I am the tenant"),
                  e("option", { value: "landlord", key: "landlord" }, "I am the landlord")
                ]
              )
            ]),
            e("label", { className: "field", key: "counterparty_email" }, [
              e(
                "span",
                { className: "field-label", key: "label" },
                tenancyForm.user_role === "tenant" ? "Landlord email" : "Tenant email"
              ),
              e("input", {
                className: "field-input",
                type: "email",
                value: tenancyForm.counterparty_email,
                onChange: function onChange(event) {
                  updateSimpleForm(setTenancyForm, "counterparty_email", event.target.value);
                },
                placeholder:
                  tenancyForm.user_role === "tenant"
                    ? "landlord@example.com"
                    : "tenant@example.com",
                required: true
              })
            ])
          ]),
          e("label", { className: "field", key: "property_id" }, [
            e("span", { className: "field-label", key: "label" }, "Use a saved property"),
            e(
              "select",
              {
                className: "field-input field-select",
                value: tenancyForm.property_id,
                onChange: function onChange(event) {
                  updateSimpleForm(setTenancyForm, "property_id", event.target.value);
                }
              },
                [
                  e("option", { value: "", key: "blank" }, "Create from a new address"),
                reusableOwnedProperties.map(function renderPropertyOption(propertyRecord) {
                  var tagText = propertyRecord.custom_tags && propertyRecord.custom_tags.length
                    ? " | " + propertyRecord.custom_tags.join(", ")
                    : "";
                  return e(
                    "option",
                    { value: propertyRecord.id, key: propertyRecord.id },
                    propertyRecord.property_label + " | " + propertyRecord.city + tagText
                  );
                })
              ]
            ),
            e(
              "span",
              { className: "field-help", key: "help" },
              reusableOwnedProperties.length
                ? "Only properties you created can be reused for a new tenancy record."
                : "No reusable property records yet. Enter a new address below."
            )
          ]),
          !tenancyForm.property_id
            ? e("div", { className: "split-grid", key: "new-property-fields" }, [
                e("label", { className: "field", key: "property_label" }, [
                  e("span", { className: "field-label", key: "label" }, "Property label"),
                  e("input", {
                    className: "field-input",
                    value: tenancyForm.property_label,
                    onChange: function onChange(event) {
                      updateSimpleForm(setTenancyForm, "property_label", event.target.value);
                    },
                    required: true
                  })
                ]),
                e("label", { className: "field", key: "address_line1" }, [
                  e("span", { className: "field-label", key: "label" }, "Address"),
                  e("input", {
                    className: "field-input",
                    value: tenancyForm.address_line1,
                    onChange: function onChange(event) {
                      updateSimpleForm(setTenancyForm, "address_line1", event.target.value);
                    },
                    required: true
                  })
                ]),
                e("label", { className: "field", key: "city" }, [
                  e("span", { className: "field-label", key: "label" }, "City"),
                  e("input", {
                    className: "field-input",
                    value: tenancyForm.city,
                    onChange: function onChange(event) {
                      updateSimpleForm(setTenancyForm, "city", event.target.value);
                    },
                    required: true
                  })
                ]),
                e("label", { className: "field", key: "country_code" }, [
                  e("span", { className: "field-label", key: "label" }, "Country"),
                  e("input", {
                    className: "field-input",
                    value: tenancyForm.country_code,
                    onChange: function onChange(event) {
                      updateSimpleForm(setTenancyForm, "country_code", event.target.value);
                    },
                    minLength: 2,
                    maxLength: 2,
                    required: true
                  })
                ])
              ])
            : null,
          e("div", { className: "form-grid", key: "date-row" }, [
            e("label", { className: "field", key: "lease_start_date" }, [
              e("span", { className: "field-label", key: "label" }, "Lease start date"),
              e("input", {
                className: "field-input",
                type: "date",
                value: tenancyForm.lease_start_date,
                onChange: function onChange(event) {
                  updateSimpleForm(setTenancyForm, "lease_start_date", event.target.value);
                },
                required: true
              })
            ]),
            e("label", { className: "field", key: "lease_end_date" }, [
              e("span", { className: "field-label", key: "label" }, "Lease end date"),
              e("input", {
                className: "field-input",
                type: "date",
                value: tenancyForm.lease_end_date,
                onChange: function onChange(event) {
                  updateSimpleForm(setTenancyForm, "lease_end_date", event.target.value);
                }
              })
            ])
          ]),
          e("div", { className: "form-grid", key: "money-row" }, [
            e("label", { className: "field", key: "monthly_rent" }, [
              e("span", { className: "field-label", key: "label" }, "Monthly rent"),
              e("input", {
                className: "field-input",
                type: "number",
                min: "0",
                step: "0.01",
                value: tenancyForm.monthly_rent,
                onChange: function onChange(event) {
                  updateSimpleForm(setTenancyForm, "monthly_rent", event.target.value);
                },
                required: true
              })
            ]),
            e("label", { className: "field", key: "deposit" }, [
              e("span", { className: "field-label", key: "label" }, "Deposit"),
              e("input", {
                className: "field-input",
                type: "number",
                min: "0",
                step: "0.01",
                value: tenancyForm.deposit,
                onChange: function onChange(event) {
                  updateSimpleForm(setTenancyForm, "deposit", event.target.value);
                },
                required: true
              })
            ])
          ]),
          e("div", { className: "form-grid", key: "status-row" }, [
            e("label", { className: "field", key: "currency_code" }, [
              e("span", { className: "field-label", key: "label" }, "Currency"),
              e("input", {
                className: "field-input",
                value: tenancyForm.currency_code,
                onChange: function onChange(event) {
                  updateSimpleForm(setTenancyForm, "currency_code", event.target.value);
                },
                minLength: 3,
                maxLength: 3,
                required: true
              })
            ]),
            e("label", { className: "field", key: "tenancy_status" }, [
              e("span", { className: "field-label", key: "label" }, "Tenancy status"),
              e(
                "select",
                {
                  className: "field-input field-select",
                  value: tenancyForm.tenancy_status,
                  onChange: function onChange(event) {
                    updateSimpleForm(setTenancyForm, "tenancy_status", event.target.value);
                  }
                },
                [
                  e("option", { value: "active", key: "active" }, "Active"),
                  e("option", { value: "ended", key: "ended" }, "Ended"),
                  e("option", { value: "cancelled", key: "cancelled" }, "Cancelled")
                ]
              )
            ])
          ]),
          e(
            "button",
            {
              type: "button",
              className: "button",
              disabled: actionState.kind === "tenancy-create",
              onClick: handleCreateTenancy
            },
            actionState.kind === "tenancy-create" ? "Creating..." : "Create tenancy record"
          )
        ])
      ]),
      canSeePropertyWorkspace
        ? e("article", { className: "detail-panel", key: "property-summary", id: "records-section-properties" }, [
        e("h2", { className: "detail-title", key: "title" }, "Saved properties"),
        e(
          "p",
          { className: "empty-copy", key: "copy" },
          canCreatePropertyWorkspace
            ? "Landlords can save a property first, assign it to an agency or a prospective tenant, and then reuse it when a tenancy starts."
            : "These property records are linked to your account through live workflows, but property setup stays with the owner or agency operator."
        ),
        canCreatePropertyWorkspace
          ? e(SegmentedTabs, {
              key: "property-workspace-tabs",
              tabs: propertyWorkspaceTabs,
              activeTab: effectivePropertyWorkspace,
              onChange: setPropertyWorkspace,
              "aria-label": "Property workspace tabs"
            })
          : null,
        effectivePropertyWorkspace === "create"
          ? e("div", { className: "auth-form", key: "create-property-form" }, [
          e("div", { className: "form-grid", key: "create-grid" }, [
            e("label", { className: "field", key: "create-property-label" }, [
              e("span", { className: "field-label", key: "label" }, "Property label"),
              e("input", {
                className: "field-input",
                value: propertyForm.property_label,
                onChange: function onChange(event) {
                  updateSimpleForm(setPropertyForm, "property_label", event.target.value);
                },
                placeholder: "Seaside Apartment",
                required: true
              })
            ]),
            e("label", { className: "field", key: "create-address" }, [
              e("span", { className: "field-label", key: "label" }, "Address"),
              e("input", {
                className: "field-input",
                value: propertyForm.address_line1,
                onChange: function onChange(event) {
                  updateSimpleForm(setPropertyForm, "address_line1", event.target.value);
                },
                placeholder: "12 Aegean Avenue",
                required: true
              })
            ]),
            e("label", { className: "field", key: "create-city" }, [
              e("span", { className: "field-label", key: "label" }, "City"),
              e("input", {
                className: "field-input",
                value: propertyForm.city,
                onChange: function onChange(event) {
                  updateSimpleForm(setPropertyForm, "city", event.target.value);
                },
                placeholder: "Athens",
                required: true
              })
            ]),
            e("label", { className: "field", key: "create-country" }, [
              e("span", { className: "field-label", key: "label" }, "Country"),
              e("input", {
                className: "field-input",
                value: propertyForm.country_code,
                onChange: function onChange(event) {
                  updateSimpleForm(setPropertyForm, "country_code", event.target.value);
                },
                minLength: 2,
                maxLength: 2,
                required: true
              })
            ])
          ]),
          e("label", { className: "field", key: "create-tags" }, [
            e("span", { className: "field-label", key: "label" }, "Tags"),
            e("input", {
              className: "field-input",
              value: propertyForm.custom_tags_text,
              onChange: function onChange(event) {
                updateSimpleForm(setPropertyForm, "custom_tags_text", event.target.value);
              },
              placeholder: "prime, family, furnished"
            })
          ]),
          e("label", { className: "field", key: "create-management-mode" }, [
            e("span", { className: "field-label", key: "label" }, "Who manages this property?"),
            e(
              "select",
              {
                className: "field-input field-select",
                value: propertyForm.management_mode,
                onChange: function onChange(event) {
                  setPropertyForm(function updateManagement(previous) {
                    return applyPropertyManagementMode(previous, event.target.value);
                  });
                }
              },
              [
                e("option", { value: "owner_managed", key: "owner_managed" }, "I manage this property myself"),
                e("option", { value: "agency_managed", key: "agency_managed" }, "An agency manages this property")
              ]
            ),
            e(
              "span",
              { className: "field-help", key: "help" },
              propertyForm.management_mode === "agency_managed"
                ? "Choose the agency and, if available, the agent who should operate the property."
                : "Keep the property under your own control without assigning it to an agency."
            )
          ]),
          isAgencyManagedProperty(propertyForm)
            ? e("div", { className: "form-grid", key: "create-agency-grid" }, [
                e("label", { className: "field", key: "create-agency-organization" }, [
                  e("span", { className: "field-label", key: "label" }, "Managing agency"),
                  e(
                    "select",
                    {
                      className: "field-input field-select",
                      value: propertyForm.assigned_agency_organization_id,
                      onChange: function onChange(event) {
                        updateSimpleForm(
                          setPropertyForm,
                          "assigned_agency_organization_id",
                          event.target.value
                        );
                      }
                    },
                    [
                      e("option", { value: "", key: "none" }, "Choose an agency"),
                      state.agencies.map(function renderAgency(organization) {
                        return e(
                          "option",
                          { value: organization.id, key: organization.id },
                          organization.name
                        );
                      })
                    ]
                  )
                ]),
                e("label", { className: "field", key: "create-agency-user" }, [
                  e("span", { className: "field-label", key: "label" }, "Agent email"),
                  e("input", {
                    className: "field-input",
                    type: "email",
                    value: propertyForm.assigned_agency_user_email,
                    onChange: function onChange(event) {
                      updateSimpleForm(setPropertyForm, "assigned_agency_user_email", event.target.value);
                    },
                    placeholder: "agent@agency.com"
                  })
                ])
              ])
            : null,
          e("label", { className: "field", key: "create-tenant-email" }, [
            e("span", { className: "field-label", key: "label" }, "Prospective tenant email"),
            e("input", {
              className: "field-input",
              type: "email",
              value: propertyForm.assigned_tenant_email,
              onChange: function onChange(event) {
                updateSimpleForm(setPropertyForm, "assigned_tenant_email", event.target.value);
              },
              placeholder: "tenant@example.com"
            }),
            e(
              "span",
              { className: "field-help", key: "help" },
              "Optional. Use this if you already know which tenant is expected to take the property."
            )
          ]),
          e(
            "button",
            {
              type: "button",
              className: "button button-secondary",
              disabled: actionState.kind === "property-create",
              onClick: handleCreateProperty
            },
            actionState.kind === "property-create" ? "Saving..." : "Save property"
          )
        ])
          : null,
        effectivePropertyWorkspace === "manage" && state.properties.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              state.properties.map(function renderPropertySummary(propertyRecord) {
                var isOwner = propertyRecord.created_by_user_id === session.user.id;
                var propertyEditForm =
                  propertyEditForms[propertyRecord.id] || buildPropertyEditForm(propertyRecord);
                return e("article", { className: "stack-card", key: propertyRecord.id }, [
                  e("strong", { className: "stack-card-title", key: "label" }, propertyRecord.property_label),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "management",
                      tone:
                        propertyRecord.management_mode === "agency_managed"
                          ? "accent"
                          : "success",
                      label:
                        propertyRecord.management_mode === "agency_managed"
                          ? "Agency managed"
                          : "Owner managed"
                    }),
                    e(StatusBadge, {
                      key: "owner",
                      tone: "neutral",
                      label: "Owner: " + propertyRecord.created_by_user_full_name
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "facts" }, [
                    e(FactPill, {
                      key: "address",
                      label: "Address",
                      value: propertyRecord.address_line1
                    }),
                    e(FactPill, {
                      key: "city",
                      label: "City",
                      value: propertyRecord.city
                    }),
                    e(FactPill, {
                      key: "country",
                      label: "Country",
                      value: propertyRecord.country_code
                    }),
                    e(FactPill, {
                      key: "agency",
                      label: "Agency",
                      value: propertyRecord.assigned_agency_organization_name || "Not assigned"
                    }),
                    e(FactPill, {
                      key: "agent",
                      label: "Agent",
                      value: propertyRecord.assigned_agency_user_full_name || "Not assigned"
                    }),
                    e(FactPill, {
                      key: "tenant",
                      label: "Prospective tenant",
                      value: propertyRecord.assigned_tenant_user_full_name || "Not assigned",
                      tone: "accent"
                    })
                  ]),
                  propertyRecord.custom_tags && propertyRecord.custom_tags.length
                    ? e(
                        "div",
                        { className: "pill-row", key: "tags" },
                        propertyRecord.custom_tags.map(function renderTag(tag) {
                          return e("span", { className: "pill", key: tag }, tag);
                        })
                      )
                    : e(
                        "p",
                        { className: "empty-copy", key: "empty" },
                        "No custom tags have been added to this property yet."
                      ),
                  isOwner
                    ? e("div", { className: "auth-form", key: "property-edit-form" }, [
                        e("div", { className: "form-grid", key: "edit-grid" }, [
                          e("label", { className: "field", key: "edit-label" }, [
                            e("span", { className: "field-label", key: "label" }, "Property label"),
                            e("input", {
                              className: "field-input",
                              value: propertyEditForm.property_label,
                              onChange: function onChange(event) {
                                updateEntityForm(
                                  setPropertyEditForms,
                                  propertyRecord.id,
                                  "property_label",
                                  event.target.value
                                );
                              }
                            })
                          ]),
                          e("label", { className: "field", key: "edit-address" }, [
                            e("span", { className: "field-label", key: "label" }, "Address"),
                            e("input", {
                              className: "field-input",
                              value: propertyEditForm.address_line1,
                              onChange: function onChange(event) {
                                updateEntityForm(
                                  setPropertyEditForms,
                                  propertyRecord.id,
                                  "address_line1",
                                  event.target.value
                                );
                              }
                            })
                          ]),
                          e("label", { className: "field", key: "edit-city" }, [
                            e("span", { className: "field-label", key: "label" }, "City"),
                            e("input", {
                              className: "field-input",
                              value: propertyEditForm.city,
                              onChange: function onChange(event) {
                                updateEntityForm(
                                  setPropertyEditForms,
                                  propertyRecord.id,
                                  "city",
                                  event.target.value
                                );
                              }
                            })
                          ]),
                          e("label", { className: "field", key: "edit-country" }, [
                            e("span", { className: "field-label", key: "label" }, "Country"),
                            e("input", {
                              className: "field-input",
                              value: propertyEditForm.country_code,
                              onChange: function onChange(event) {
                                updateEntityForm(
                                  setPropertyEditForms,
                                  propertyRecord.id,
                                  "country_code",
                                  event.target.value
                                );
                              },
                              minLength: 2,
                              maxLength: 2
                            })
                          ])
                        ]),
                        e("div", { className: "form-grid", key: "assignment-grid" }, [
                          e("label", { className: "field", key: "management-mode" }, [
                            e("span", { className: "field-label", key: "label" }, "Who manages this property?"),
                            e(
                              "select",
                              {
                                className: "field-input field-select",
                                value: propertyEditForm.management_mode,
                                onChange: function onChange(event) {
                                  setPropertyEditForms(function updateManagement(previous) {
                                    var next = Object.assign({}, previous);
                                    next[propertyRecord.id] = applyPropertyManagementMode(
                                      propertyEditForm,
                                      event.target.value
                                    );
                                    return next;
                                  });
                                }
                              },
                              [
                                e("option", { value: "owner_managed", key: "owner_managed" }, "I manage this property myself"),
                                e("option", { value: "agency_managed", key: "agency_managed" }, "An agency manages this property")
                              ]
                            ),
                            e(
                              "span",
                              { className: "field-help", key: "help" },
                              propertyEditForm.management_mode === "agency_managed"
                                ? "Agency management keeps this property inside agency workflows and lets you name the responsible operator."
                                : "Owner-managed keeps all day-to-day control with you while still allowing tenant assignment."
                            )
                          ]),
                          isAgencyManagedProperty(propertyEditForm)
                            ? e("label", { className: "field", key: "agency-organization" }, [
                            e("span", { className: "field-label", key: "label" }, "Assigned agency"),
                            e(
                              "select",
                              {
                                className: "field-input field-select",
                                value: propertyEditForm.assigned_agency_organization_id,
                                onChange: function onChange(event) {
                                  updateEntityForm(
                                    setPropertyEditForms,
                                    propertyRecord.id,
                                    "assigned_agency_organization_id",
                                    event.target.value
                                  );
                                }
                              },
                              [
                                e("option", { value: "", key: "none" }, "No agency assigned"),
                                state.agencies.map(function renderAgency(organization) {
                                  return e(
                                    "option",
                                    { value: organization.id, key: organization.id },
                                    organization.name
                                  );
                                })
                              ]
                            )
                          ])
                            : null,
                          isAgencyManagedProperty(propertyEditForm)
                            ? e("label", { className: "field", key: "agency-user" }, [
                            e("span", { className: "field-label", key: "label" }, "Agent email"),
                            e("input", {
                              className: "field-input",
                              type: "email",
                              value: propertyEditForm.assigned_agency_user_email,
                              onChange: function onChange(event) {
                                updateEntityForm(
                                  setPropertyEditForms,
                                  propertyRecord.id,
                                  "assigned_agency_user_email",
                                  event.target.value
                                );
                              },
                              placeholder: "agent@agency.com"
                            })
                          ])
                            : null,
                          e("label", { className: "field", key: "tenant-email" }, [
                            e("span", { className: "field-label", key: "label" }, "Prospective tenant email"),
                            e("input", {
                              className: "field-input",
                              type: "email",
                              value: propertyEditForm.assigned_tenant_email,
                              onChange: function onChange(event) {
                                updateEntityForm(
                                  setPropertyEditForms,
                                  propertyRecord.id,
                                  "assigned_tenant_email",
                                  event.target.value
                                );
                              },
                              placeholder: "tenant@example.com"
                            })
                          ]),
                          e("label", { className: "field", key: "property-tags" }, [
                            e("span", { className: "field-label", key: "label" }, "Tags"),
                            e("input", {
                              className: "field-input",
                              value: propertyEditForm.custom_tags_text,
                              onChange: function onChange(event) {
                                updateEntityForm(
                                  setPropertyEditForms,
                                  propertyRecord.id,
                                  "custom_tags_text",
                                  event.target.value
                                );
                              },
                              placeholder: "priority, furnished, student"
                            })
                          ])
                        ]),
                        e(
                          "button",
                          {
                            type: "button",
                            className: "button button-secondary button-small",
                            disabled: actionState.kind === "property-save" && actionState.id === propertyRecord.id,
                            onClick: function onClick() {
                              handleSaveProperty(propertyRecord);
                            }
                          },
                          actionState.kind === "property-save" && actionState.id === propertyRecord.id
                            ? "Saving..."
                            : "Save property setup"
                        )
                      ])
                    : e(
                        "p",
                        { className: "empty-copy", key: "read-only-copy" },
                        "This property is linked to your account through an active workflow, but only the creator can change its setup."
                      )
                ]);
              })
            )
          : null,
        effectivePropertyWorkspace === "manage" && !state.properties.length
          ? e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No saved property records are linked to this account yet."
            )
          : null
      ])
        : null
    ]),
    e("section", { className: "split-grid", key: "top", id: "records-section-history" }, [
      e("article", { className: "detail-panel", key: "imports" }, [
        e("h2", { className: "detail-title", key: "title" }, "Past rental history"),
        e("div", { className: "auth-form", key: "form" }, [
          e("label", { className: "field", key: "title" }, [
            e("span", { className: "field-label", key: "label" }, "Import title"),
            e("input", {
              className: "field-input",
              value: historyImportForm.title,
              onChange: function onChange(event) {
                updateSimpleForm(setHistoryImportForm, "title", event.target.value);
              },
              minLength: 2,
              maxLength: 255
            })
          ]),
          e("label", { className: "field", key: "summary" }, [
            e("span", { className: "field-label", key: "label" }, "Summary"),
            e("input", {
              className: "field-input",
              value: historyImportForm.summary,
              onChange: function onChange(event) {
                updateSimpleForm(setHistoryImportForm, "summary", event.target.value);
              },
              maxLength: 1000
            })
          ]),
          e(
            "button",
            {
              type: "button",
              className: "button button-secondary",
              disabled: actionState.kind === "history-import-create",
              onClick: handleCreateHistoryImport
            },
            actionState.kind === "history-import-create" ? "Creating..." : "Create import draft"
          )
        ]),
        state.historyImports.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              state.historyImports.map(function renderHistoryImport(historyImport) {
                var canSubmit =
                  historyImport.status === "draft" &&
                  historyImport.tenancy_count > 0 &&
                  historyImport.evidence_document_count > 0;
                return e("article", { className: "stack-card", key: historyImport.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, historyImport.title),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, {
                      key: "history-status",
                      tone:
                        historyImport.status === "approved" || historyImport.status === "accepted"
                          ? "success"
                          : historyImport.status === "draft"
                            ? "accent"
                            : "warning",
                      label: historyImport.status
                    })
                  ]),
                  e("div", { className: "fact-grid", key: "meta" }, [
                    e(FactPill, { key: "tenancies", label: "Tenancies", value: String(historyImport.tenancy_count) }),
                    e(FactPill, {
                      key: "evidence",
                      label: "Evidence items",
                      value: String(historyImport.evidence_document_count),
                      tone: "accent"
                    })
                  ]),
                  historyImport.summary
                    ? e(NoteBlock, { key: "summary", label: "Import summary", tone: "accent" }, historyImport.summary)
                    : null,
                  historyImport.status === "draft"
                    ? e(
                        "button",
                        {
                          type: "button",
                          className: "button button-small",
                          disabled:
                            !canSubmit ||
                            (actionState.kind === "history-import-submit" && actionState.id === historyImport.id),
                          onClick: function onClick() {
                            handleSimplePost(
                              "history-import-submit",
                              historyImport.id,
                              "/history-imports/" + historyImport.id + "/submit",
                              "History import submitted for review."
                            );
                          }
                        },
                        actionState.kind === "history-import-submit" && actionState.id === historyImport.id
                          ? "Submitting..."
                          : canSubmit
                            ? "Submit for review"
                            : "Needs tenancy and evidence before submit"
                      )
                    : null
                ]);
              })
            )
          : e("p", { className: "empty-copy", key: "empty" }, "No history imports have been created yet.")
      ]),
      e("article", { className: "detail-panel", key: "incoming" }, [
        e("h2", { className: "detail-title", key: "title" }, "References waiting for your reply"),
        pendingIncomingRequests.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              pendingIncomingRequests.map(function renderReferenceRequest(referenceRequest) {
                var fulfillmentForm =
                  fulfillmentForms[referenceRequest.id] || buildReferenceFulfillmentForm();
                return e("article", { className: "stack-card", key: referenceRequest.id }, [
                  e(
                    "strong",
                    { className: "stack-card-title", key: "title" },
                    referenceRequest.subject_user_full_name + " requested your reference"
                  ),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, { key: "pending", tone: "warning", label: "Waiting for your reply" })
                  ]),
                  referenceRequest.message
                    ? e(
                        NoteBlock,
                        { key: "message", label: "Requester note", tone: "accent" },
                        referenceRequest.message
                      )
                    : null,
                  e("label", { className: "field", key: "artifact" }, [
                    e("span", { className: "field-label", key: "label" }, "Artifact name"),
                    e("input", {
                      className: "field-input",
                      value: fulfillmentForm.artifact_name,
                      onChange: function onChange(event) {
                        updateEntityForm(setFulfillmentForms, referenceRequest.id, "artifact_name", event.target.value);
                      },
                      minLength: 2,
                      maxLength: 255
                    })
                  ]),
                  e("label", { className: "field", key: "summary" }, [
                    e("span", { className: "field-label", key: "label" }, "Reference summary"),
                    e("input", {
                      className: "field-input",
                      value: fulfillmentForm.summary,
                      onChange: function onChange(event) {
                        updateEntityForm(setFulfillmentForms, referenceRequest.id, "summary", event.target.value);
                      },
                      minLength: 2,
                      maxLength: 1000
                    })
                  ]),
                  e("label", { className: "field", key: "file" }, [
                    e("span", { className: "field-label", key: "label" }, "Reference artifact file"),
                    e("input", {
                      className: "field-input",
                      type: "file",
                      accept: ".pdf,.png,.jpg,.jpeg,.webp,.txt,application/pdf,image/png,image/jpeg,image/webp,text/plain",
                      onChange: function onChange(event) {
                        updateEntityForm(
                          setFulfillmentForms,
                          referenceRequest.id,
                          "file",
                          event.target.files && event.target.files[0] ? event.target.files[0] : null
                        );
                      }
                    }),
                    fulfillmentForm.file
                      ? e(
                          "span",
                          { className: "field-help", key: "file-name" },
                          "Selected file: " + fulfillmentForm.file.name
                        )
                      : null
                  ]),
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-small",
                      disabled:
                        actionState.kind === "reference-request-fulfill" && actionState.id === referenceRequest.id,
                      onClick: function onClick() {
                        handleFulfillReferenceRequest(referenceRequest);
                      }
                    },
                    actionState.kind === "reference-request-fulfill" && actionState.id === referenceRequest.id
                      ? "Submitting..."
                      : "Submit reference"
                  )
                ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No pending reference requests are waiting for your response."
            )
      ])
    ]),
    state.tenancies.length
      ? e(
          "div",
          { className: "list-stack", key: "tenancies", id: "records-section-artifacts" },
          state.tenancies.map(function renderTenancy(tenancy) {
            var evidenceForm = evidenceForms[tenancy.id] || buildEvidenceForm(session.user.id, tenancy);
            var referenceForm = referenceForms[tenancy.id];
            var canConfirm =
              tenancy.created_by_user_id !== session.user.id && tenancy.verification_status === "self_reported";
            var canRequestReview =
              tenancy.verification_status !== "reviewed" &&
              tenancy.verification_status !== "verified" &&
              !tenancy.review_requested_at;
            var tenancyPartyContext = buildTenancyPartyContext(tenancy, session.user.id);

            return e("section", { className: "detail-panel", key: tenancy.id }, [
              e("h2", { className: "detail-title", key: "title" }, tenancy.property_label),
              e("div", { className: "status-row", key: "status-row" }, [
                e(StatusBadge, {
                  key: "verification",
                  tone:
                    tenancy.verification_status === "verified" || tenancy.verification_status === "reviewed"
                      ? "success"
                      : tenancy.verification_status === "self_reported"
                        ? "warning"
                        : "accent",
                  label: "Verification " + tenancy.verification_status
                }),
                e(StatusBadge, {
                  key: "status",
                  tone: "accent",
                  label: "Tenancy " + tenancy.tenancy_status
                })
              ]),
              e("div", { className: "fact-grid", key: "meta" }, [
                e(FactPill, { key: "city", label: "City", value: tenancy.city }),
                e(FactPill, {
                  key: "role",
                  label: "Your role",
                  value: tenancyPartyContext.role,
                  tone: "accent"
                }),
                e(FactPill, {
                  key: "counterparty",
                  label: tenancyPartyContext.counterpartyLabel,
                  value: tenancyPartyContext.counterpartyName,
                  tone: "accent"
                })
              ]),
              e("div", { className: "action-row", key: "actions" }, [
                canConfirm
                  ? e(
                      "button",
                      {
                        type: "button",
                        className: "button button-secondary button-small",
                        disabled: actionState.kind === "confirm" && actionState.id === tenancy.id,
                        onClick: function onClick() {
                          handleSimplePost(
                            "confirm",
                            tenancy.id,
                            "/tenancies/" + tenancy.id + "/confirm",
                            "Counterparty confirmation recorded."
                          );
                        }
                      },
                      actionState.kind === "confirm" && actionState.id === tenancy.id
                        ? "Saving..."
                        : "Confirm record"
                    )
                  : null,
                canRequestReview
                  ? e(
                      "button",
                      {
                        type: "button",
                        className: "button button-small",
                        disabled: actionState.kind === "review" && actionState.id === tenancy.id,
                        onClick: function onClick() {
                          handleSimplePost(
                            "review",
                            tenancy.id,
                            "/tenancies/" + tenancy.id + "/request-review",
                            "Review requested successfully."
                          );
                        }
                      },
                      actionState.kind === "review" && actionState.id === tenancy.id
                        ? "Saving..."
                        : "Request review"
                    )
                  : null
              ]),
              e(SegmentedTabs, {
                key: "artifact-workspace-tabs",
                tabs: [
                  { id: "create", label: "Create artifact", meta: "Upload a new supporting file" },
                  {
                    id: "library",
                    label: "Artifact library",
                    meta: String((state.evidenceByTenancy[tenancy.id] || []).length) + " files on record"
                  },
                  {
                    id: "references",
                    label: "Reference request",
                    meta: referenceForm ? "Ask the counterparty for a written reference" : "Not available"
                  }
                ],
                activeTab: artifactWorkspace[tenancy.id] || "create",
                onChange: function onChange(nextTab) {
                  updateSelectionMap(setArtifactWorkspace, tenancy.id, nextTab);
                },
                "aria-label": tenancy.property_label + " artifact workspace"
              }),
              (artifactWorkspace[tenancy.id] || "create") === "create"
                ? e("article", { className: "stack-card", key: "evidence-form" }, [
                    e("strong", { className: "stack-card-title", key: "title" }, "Upload a new artifact"),
                    e("label", { className: "field", key: "subject" }, [
                      e("span", { className: "field-label", key: "label" }, "Evidence subject"),
                      e(
                        "select",
                        {
                          className: "field-input field-select",
                          value: evidenceForm.subject_user_id,
                          onChange: function onChange(event) {
                            updateEntityForm(setEvidenceForms, tenancy.id, "subject_user_id", event.target.value);
                          }
                        },
                        [
                          e("option", { value: tenancy.tenant_user_id, key: "tenant" }, tenancy.tenant_full_name),
                          e("option", { value: tenancy.landlord_user_id, key: "landlord" }, tenancy.landlord_full_name)
                        ]
                      )
                    ]),
                    e("label", { className: "field", key: "type" }, [
                      e("span", { className: "field-label", key: "label" }, "Document type"),
                      e(
                        "select",
                        {
                          className: "field-input field-select",
                          value: evidenceForm.document_type,
                          onChange: function onChange(event) {
                            updateEntityForm(setEvidenceForms, tenancy.id, "document_type", event.target.value);
                          }
                        },
                        [
                          e("option", { value: "lease_agreement", key: "lease_agreement" }, "Lease agreement"),
                          e("option", { value: "rent_receipt", key: "rent_receipt" }, "Rent receipt"),
                          e("option", { value: "utility_settlement", key: "utility_settlement" }, "Utility settlement"),
                          e("option", { value: "deposit_return", key: "deposit_return" }, "Deposit return"),
                          e("option", { value: "landlord_reference", key: "landlord_reference" }, "Landlord reference"),
                          e("option", { value: "identity_document", key: "identity_document" }, "Identity document"),
                          e("option", { value: "other", key: "other" }, "Other")
                        ]
                      )
                    ]),
                    e("label", { className: "field", key: "artifact" }, [
                      e("span", { className: "field-label", key: "label" }, "Artifact name"),
                      e("input", {
                        className: "field-input",
                        value: evidenceForm.artifact_name,
                        onChange: function onChange(event) {
                          updateEntityForm(setEvidenceForms, tenancy.id, "artifact_name", event.target.value);
                        },
                        minLength: 2,
                        maxLength: 255
                      })
                    ]),
                    e("label", { className: "field", key: "summary" }, [
                      e("span", { className: "field-label", key: "label" }, "Summary"),
                      e("input", {
                        className: "field-input",
                        value: evidenceForm.summary,
                        onChange: function onChange(event) {
                          updateEntityForm(setEvidenceForms, tenancy.id, "summary", event.target.value);
                        },
                        minLength: 2,
                        maxLength: 1000
                      })
                    ]),
                    e("label", { className: "field", key: "file" }, [
                      e("span", { className: "field-label", key: "label" }, "Artifact file"),
                      e("input", {
                        className: "field-input",
                        type: "file",
                        accept: ".pdf,.png,.jpg,.jpeg,.webp,.txt,application/pdf,image/png,image/jpeg,image/webp,text/plain",
                        onChange: function onChange(event) {
                          updateEntityForm(
                            setEvidenceForms,
                            tenancy.id,
                            "file",
                            event.target.files && event.target.files[0] ? event.target.files[0] : null
                          );
                        }
                      }),
                      evidenceForm.file
                        ? e(
                            "span",
                            { className: "field-help", key: "file-name" },
                            "Selected file: " + evidenceForm.file.name
                          )
                        : null
                    ]),
                    e(
                      "button",
                      {
                        type: "button",
                        className: "button button-secondary",
                        disabled: actionState.kind === "evidence" && actionState.id === tenancy.id,
                        onClick: function onClick() {
                          handleEvidenceSubmit(tenancy.id);
                        }
                      },
                      actionState.kind === "evidence" && actionState.id === tenancy.id
                        ? "Submitting..."
                        : "Submit evidence"
                    )
                  ])
                : null,
              (artifactWorkspace[tenancy.id] || "create") === "library"
                ? e("article", { className: "stack-card", key: "evidence-list" }, [
                    e("strong", { className: "stack-card-title", key: "title" }, "Artifacts already on record"),
                    state.evidenceByTenancy[tenancy.id] && state.evidenceByTenancy[tenancy.id].length
                      ? e(
                          "div",
                          { className: "list-stack", key: "list" },
                          state.evidenceByTenancy[tenancy.id].map(function renderEvidence(evidence) {
                            return e("article", { className: "stack-card", key: evidence.id }, [
                              e("strong", { className: "stack-card-title", key: "title" }, evidence.artifact_name),
                              e("div", { className: "status-row", key: "status" }, [
                                e(StatusBadge, { key: "type", tone: "accent", label: evidence.document_type }),
                                e(StatusBadge, {
                                  key: "review",
                                  tone:
                                    evidence.review_status === "accepted"
                                      ? "success"
                                      : evidence.review_status === "rejected"
                                        ? "danger"
                                        : "warning",
                                  label: evidence.review_status
                                })
                              ]),
                              e("div", { className: "fact-grid", key: "facts" }, [
                                e(FactPill, {
                                  key: "subject",
                                  label: "Subject",
                                  value: evidence.subject_user_full_name || "Unknown user"
                                }),
                                e(FactPill, {
                                  key: "file",
                                  label: "Artifact type",
                                  value: evidence.has_uploaded_artifact
                                    ? evidence.artifact_content_type
                                    : "No file uploaded"
                                }),
                                evidence.has_uploaded_artifact
                                  ? e(FactPill, {
                                      key: "size",
                                      label: "File size",
                                      value: String(evidence.artifact_size_bytes) + " bytes",
                                      tone: "accent"
                                    })
                                  : null
                              ]),
                              e(NoteBlock, { key: "summary", label: "Summary" }, evidence.summary),
                              evidence.has_uploaded_artifact
                                ? e(
                                    "button",
                                    {
                                      type: "button",
                                      className: "button button-secondary button-small",
                                      key: "download",
                                      disabled:
                                        actionState.kind === "evidence-artifact-access" &&
                                        actionState.id === evidence.id,
                                      onClick: function onClick() {
                                        handleEvidenceArtifactAccess(evidence);
                                      }
                                    },
                                    actionState.kind === "evidence-artifact-access" &&
                                      actionState.id === evidence.id
                                      ? "Opening..."
                                      : "Open artifact"
                                  )
                                : null
                            ]);
                          })
                        )
                      : e(
                          "p",
                          { className: "empty-copy", key: "empty" },
                          "No evidence has been attached to this tenancy yet."
                        )
                  ])
                : null,
              (artifactWorkspace[tenancy.id] || "create") === "references"
                ? e("article", { className: "stack-card", key: "reference-request" }, [
                    e("strong", { className: "stack-card-title", key: "title" }, "Counterparty reference"),
                    referenceForm
                      ? [
                          e("p", { className: "empty-copy", key: "copy" }, "Ask the other side to add a written reference without mixing that step into artifact uploads."),
                          e("label", { className: "field", key: "reference-message" }, [
                            e("span", { className: "field-label", key: "label" }, "Request message"),
                            e("input", {
                              className: "field-input",
                              value: referenceForm.message,
                              onChange: function onChange(event) {
                                updateEntityForm(setReferenceForms, tenancy.id, "message", event.target.value);
                              },
                              maxLength: 1000
                            })
                          ]),
                          e(
                            "button",
                            {
                              type: "button",
                              className: "button button-secondary button-small",
                              disabled:
                                actionState.kind === "reference-request-create" && actionState.id === tenancy.id,
                              onClick: function onClick() {
                                handleCreateReferenceRequest(tenancy);
                              }
                            },
                            actionState.kind === "reference-request-create" && actionState.id === tenancy.id
                              ? "Requesting..."
                              : "Request reference"
                          )
                        ]
                      : e(
                          "p",
                          { className: "empty-copy", key: "empty" },
                          "Reference requests are available only when the tenancy connects you with the counterparty directly."
                        )
                  ])
                : null
            ]);
          })
        )
      : e(
          "div",
          { className: "detail-panel", key: "empty" },
          e("p", { className: "empty-copy" }, "No tenancy records are attached to this account yet.")
        )
  ]);
}
