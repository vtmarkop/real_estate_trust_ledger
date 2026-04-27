import React from "react";

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
import { e, getLanguageLocale } from "../lib/i18n.js";

function MetricCard(props) {
  return e("article", { className: "metric-card" }, [
    e("p", { className: "metric-kicker", key: "kicker" }, props.kicker),
    e("strong", { className: "metric-value", key: "value" }, props.value),
    e("p", { className: "metric-copy", key: "copy" }, props.copy)
  ]);
}

function buildEmptyState(message) {
  return e("div", { className: "state-panel" }, [
    e("p", { className: "eyebrow", key: "eyebrow" }, "Agency tools"),
    e("h1", { className: "state-title", key: "title" }, "Agency tools unavailable"),
    e("p", { className: "state-copy", key: "copy" }, message)
  ]);
}

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

function formatPercent(value) {
  if (value == null) {
    return "N/A";
  }
  return String(value) + "%";
}

function formatHours(value) {
  if (value == null) {
    return "N/A";
  }
  return String(value) + "h";
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

function inferStatusTone(value) {
  var normalized = String(value || "").toLowerCase();
  if (
    normalized.indexOf("open") >= 0 ||
    normalized.indexOf("accept") >= 0 ||
    normalized.indexOf("active") >= 0
  ) {
    return "success";
  }
  if (
    normalized.indexOf("reject") >= 0 ||
    normalized.indexOf("close") >= 0 ||
    normalized.indexOf("inactive") >= 0
  ) {
    return "danger";
  }
  if (normalized.indexOf("review") >= 0 || normalized.indexOf("pause") >= 0) {
    return "warning";
  }
  return "accent";
}

function buildApplicationActions(application) {
  if (application.application_status === "submitted") {
    return [
      {
        status: "under_review",
        label: "Mark under review"
      },
      {
        status: "accepted",
        label: "Accept"
      },
      {
        status: "rejected",
        label: "Reject"
      }
    ];
  }

  if (application.application_status === "under_review") {
    return [
      {
        status: "accepted",
        label: "Accept"
      },
      {
        status: "rejected",
        label: "Reject"
      }
    ];
  }

  return [];
}

function buildListingActions(listing) {
  if (listing.listing_status === "open") {
    return [
      {
        status: "paused",
        label: "Pause"
      },
      {
        status: "closed",
        label: "Close"
      }
    ];
  }

  if (listing.listing_status === "paused") {
    return [
      {
        status: "open",
        label: "Reopen"
      },
      {
        status: "closed",
        label: "Close"
      }
    ];
  }

  if (listing.listing_status === "closed") {
    return [
      {
        status: "open",
        label: "Reopen"
      }
    ];
  }

  return [];
}

function buildInitialPropertyForm() {
  return {
    property_label: "",
    address_line1: "",
    city: "",
    country_code: "GR",
    custom_tags_text: ""
  };
}

function buildInitialListingForm() {
  return {
    property_id: "",
    title: "",
    description: "",
    monthly_rent: "",
    deposit: "",
    currency_code: "EUR",
    minimum_tenant_score: "0",
    minimum_verification_strength: "0"
  };
}

function buildListingEditForm(listing) {
  return {
    description: listing.description || "",
    minimum_tenant_score: String(listing.minimum_tenant_score),
    minimum_verification_strength: String(listing.minimum_verification_strength)
  };
}

function buildInitialTrustCheckForm() {
  return {
    share_token: "",
    access_code: ""
  };
}

function buildInitialMembershipForm() {
  return {
    user_email: "",
    role: "member"
  };
}

function buildMembershipEditForm(membership) {
  return {
    role: membership.role,
    is_active: membership.is_active
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

function updateEntityForm(setter, entityId, name, value) {
  setter(function mergeForms(previous) {
    var next = Object.assign({}, previous);
    var existing = Object.assign({}, next[entityId] || {});
    existing[name] = value;
    next[entityId] = existing;
    return next;
  });
}

var applicationStatusOptions = [
  { value: "", label: "All application statuses" },
  { value: "submitted", label: "Submitted" },
  { value: "under_review", label: "Under review" },
  { value: "accepted", label: "Accepted" },
  { value: "rejected", label: "Rejected" },
  { value: "withdrawn", label: "Withdrawn" }
];

export function AgencyWorkbenchPage() {
  var stateTuple = React.useState({
    status: "loading",
    organizations: [],
    selectedOrganizationId: "",
    dashboard: null,
    commercialOverview: null,
    properties: [],
    memberships: [],
    listings: [],
    applications: [],
    trustChecks: [],
    error: null
  });
  var state = stateTuple[0];
  var setState = stateTuple[1];
  var propertyFormTuple = React.useState(buildInitialPropertyForm());
  var propertyForm = propertyFormTuple[0];
  var setPropertyForm = propertyFormTuple[1];
  var listingFormTuple = React.useState(buildInitialListingForm());
  var listingForm = listingFormTuple[0];
  var setListingForm = listingFormTuple[1];
  var trustCheckFormTuple = React.useState(buildInitialTrustCheckForm());
  var trustCheckForm = trustCheckFormTuple[0];
  var setTrustCheckForm = trustCheckFormTuple[1];
  var membershipFormTuple = React.useState(buildInitialMembershipForm());
  var membershipForm = membershipFormTuple[0];
  var setMembershipForm = membershipFormTuple[1];
  var propertySubmissionTuple = React.useState({
    isSubmitting: false,
    message: null
  });
  var propertySubmission = propertySubmissionTuple[0];
  var setPropertySubmission = propertySubmissionTuple[1];
  var propertyTagFormsTuple = React.useState({});
  var propertyTagForms = propertyTagFormsTuple[0];
  var setPropertyTagForms = propertyTagFormsTuple[1];
  var propertyTagActionTuple = React.useState({
    propertyId: "",
    message: null
  });
  var propertyTagAction = propertyTagActionTuple[0];
  var setPropertyTagAction = propertyTagActionTuple[1];
  var listingSubmissionTuple = React.useState({
    isSubmitting: false,
    message: null
  });
  var listingSubmission = listingSubmissionTuple[0];
  var setListingSubmission = listingSubmissionTuple[1];
  var trustCheckSubmissionTuple = React.useState({
    isSubmitting: false,
    action: "",
    message: null,
    result: null
  });
  var trustCheckSubmission = trustCheckSubmissionTuple[0];
  var setTrustCheckSubmission = trustCheckSubmissionTuple[1];
  var membershipSubmissionTuple = React.useState({
    isSubmitting: false,
    message: null
  });
  var membershipSubmission = membershipSubmissionTuple[0];
  var setMembershipSubmission = membershipSubmissionTuple[1];
  var actionTuple = React.useState({
    applicationId: "",
    nextStatus: ""
  });
  var applicationAction = actionTuple[0];
  var setApplicationAction = actionTuple[1];
  var listingActionTuple = React.useState({
    listingId: "",
    nextStatus: ""
  });
  var listingAction = listingActionTuple[0];
  var setListingAction = listingActionTuple[1];
  var listingEditFormsTuple = React.useState({});
  var listingEditForms = listingEditFormsTuple[0];
  var setListingEditForms = listingEditFormsTuple[1];
  var listingEditActionTuple = React.useState({
    listingId: "",
    messageListingId: "",
    message: null
  });
  var listingEditAction = listingEditActionTuple[0];
  var setListingEditAction = listingEditActionTuple[1];
  var applicationFilterTuple = React.useState("");
  var applicationFilter = applicationFilterTuple[0];
  var setApplicationFilter = applicationFilterTuple[1];
  var propertyTagFilterTuple = React.useState("");
  var propertyTagFilter = propertyTagFilterTuple[0];
  var setPropertyTagFilter = propertyTagFilterTuple[1];
  var membershipEditFormsTuple = React.useState({});
  var membershipEditForms = membershipEditFormsTuple[0];
  var setMembershipEditForms = membershipEditFormsTuple[1];
  var membershipActionTuple = React.useState({
    membershipId: "",
    messageMembershipId: "",
    message: null
  });
  var membershipAction = membershipActionTuple[0];
  var setMembershipAction = membershipActionTuple[1];
  var agencySectionTuple = React.useState("overview");
  var agencySection = agencySectionTuple[0];
  var setAgencySection = agencySectionTuple[1];

  var updatePropertyField = React.useMemo(function buildPropertyFieldUpdater() {
    return updateNamedField(setPropertyForm);
  }, []);
  var updateListingField = React.useMemo(function buildListingFieldUpdater() {
    return updateNamedField(setListingForm);
  }, []);
  var updateTrustCheckField = React.useMemo(function buildTrustCheckFieldUpdater() {
    return updateNamedField(setTrustCheckForm);
  }, []);
  var updateMembershipField = React.useMemo(function buildMembershipFieldUpdater() {
    return updateNamedField(setMembershipForm);
  }, []);

  var loadOrganizationData = React.useCallback(async function loadOrganizationData(organizationId) {
    setState(function setRefreshing(previous) {
      return {
        status: previous.dashboard || previous.listings.length || previous.applications.length
          ? "refreshing"
          : "loading",
        organizations: previous.organizations,
        selectedOrganizationId: organizationId,
        dashboard: previous.dashboard,
        commercialOverview: previous.commercialOverview,
        properties: previous.properties,
        memberships: previous.memberships,
        listings: previous.listings,
        applications: previous.applications,
        trustChecks: previous.trustChecks,
        error: null
      };
    });

    try {
      var results = await Promise.all([
        apiRequest("/organizations/" + organizationId + "/screening-dashboard"),
        apiRequest("/organizations/" + organizationId + "/commercial-overview"),
        apiRequest("/organizations/" + organizationId + "/memberships"),
        apiRequest("/organizations/" + organizationId + "/listings"),
        apiRequest("/organizations/" + organizationId + "/applications"),
        apiRequest("/properties/mine"),
        apiRequest("/organizations/" + organizationId + "/trust-checks")
      ]);
      setState(function setReady(previous) {
        return {
          status: "ready",
          organizations: previous.organizations,
          selectedOrganizationId: organizationId,
          dashboard: results[0],
          commercialOverview: results[1],
          memberships: results[2],
          listings: results[3],
          applications: results[4],
          properties: results[5],
          trustChecks: results[6],
          error: null
        };
      });
      setListingEditForms(function syncListingEditForms(previous) {
        var next = Object.assign({}, previous);
        results[3].forEach(function ensureListingEditForm(listing) {
          next[listing.id] = buildListingEditForm(listing);
        });
        return next;
      });
      setListingForm(function syncPropertySelection(previous) {
        if (previous.property_id) {
          return previous;
        }
        if (!results[5].length) {
          return previous;
        }
        return Object.assign({}, previous, { property_id: results[5][0].id });
      });
      setPropertyTagForms(function syncPropertyTagForms(previous) {
        var next = Object.assign({}, previous);
        results[5].forEach(function ensurePropertyTagForm(propertyRecord) {
          next[propertyRecord.id] = formatTagText(propertyRecord.custom_tags);
        });
        return next;
      });
      setMembershipEditForms(function syncMembershipEditForms(previous) {
        var next = Object.assign({}, previous);
        results[2].forEach(function ensureMembershipEditForm(membership) {
          next[membership.id] = buildMembershipEditForm(membership);
        });
        return next;
      });
    } catch (error) {
      setState(function setError(previous) {
        return {
          status: "error",
          organizations: previous.organizations,
          selectedOrganizationId: organizationId,
          dashboard: null,
          commercialOverview: null,
          memberships: [],
          properties: [],
          listings: [],
          applications: [],
          trustChecks: [],
          error: error.message || "Unable to load the agency dashboard."
        };
      });
    }
  }, []);

  var loadOrganizations = React.useCallback(async function loadOrganizations() {
    setState(function setLoading(previous) {
      return {
        status: previous.organizations.length ? "refreshing" : "loading",
        organizations: previous.organizations,
        selectedOrganizationId: previous.selectedOrganizationId,
        dashboard: previous.dashboard,
        memberships: previous.memberships,
        properties: previous.properties,
        listings: previous.listings,
        applications: previous.applications,
        trustChecks: previous.trustChecks,
        error: null
      };
    });

    try {
      var organizations = await apiRequest("/organizations/mine");
      var agencyOrganizations = organizations.filter(function filterAgencies(organization) {
        return organization.organization_type === "agency";
      });

      if (!agencyOrganizations.length) {
        setState({
          status: "ready",
          organizations: [],
          selectedOrganizationId: "",
          dashboard: null,
          commercialOverview: null,
          memberships: [],
          properties: [],
          listings: [],
          applications: [],
          trustChecks: [],
          error: null
        });
        return;
      }

      var selectedOrganizationId = agencyOrganizations[0].id;
      setState({
        status: "loading",
        organizations: agencyOrganizations,
        selectedOrganizationId: selectedOrganizationId,
        dashboard: null,
        commercialOverview: null,
        memberships: [],
        properties: [],
        listings: [],
        applications: [],
        trustChecks: [],
        error: null
      });
      await loadOrganizationData(selectedOrganizationId);
    } catch (error) {
      setState({
        status: "error",
        organizations: [],
        selectedOrganizationId: "",
        dashboard: null,
        commercialOverview: null,
        properties: [],
        listings: [],
        applications: [],
        trustChecks: [],
        error: error.message || "Unable to load organization memberships."
      });
    }
  }, [loadOrganizationData]);

  React.useEffect(function bootstrapAgencyWorkbench() {
    loadOrganizations();
  }, [loadOrganizations]);

  async function handleOrganizationChange(event) {
    var nextOrganizationId = event.target.value;
    await loadOrganizationData(nextOrganizationId);
  }

  async function handlePropertySubmit(event) {
    event.preventDefault();
    setPropertySubmission({
      isSubmitting: true,
      message: null
    });

    try {
      var createdProperty = await apiRequest("/properties", {
        method: "POST",
        body: {
          property_label: propertyForm.property_label,
          address_line1: propertyForm.address_line1,
          city: propertyForm.city,
          country_code: propertyForm.country_code,
          custom_tags: parseTagText(propertyForm.custom_tags_text)
        }
      });
      setPropertyForm(buildInitialPropertyForm());
      setListingForm(function attachCreatedProperty(previous) {
        return Object.assign({}, previous, { property_id: createdProperty.id });
      });
      await loadOrganizationData(state.selectedOrganizationId);
      setPropertySubmission({
        isSubmitting: false,
        message: "Property created and ready for listing."
      });
    } catch (error) {
      setPropertySubmission({
        isSubmitting: false,
        message: error.message || "Unable to create property."
      });
    }
  }

  async function handlePropertyTagSave(propertyRecord) {
    setPropertyTagAction({
      propertyId: propertyRecord.id,
      message: null
    });

    try {
      await apiRequest("/properties/" + propertyRecord.id, {
        method: "PATCH",
        body: {
          custom_tags: parseTagText(propertyTagForms[propertyRecord.id] || "")
        }
      });
      await loadOrganizationData(state.selectedOrganizationId);
      setPropertyTagAction({
        propertyId: "",
        message: "Property tags saved."
      });
    } catch (error) {
      setPropertyTagAction({
        propertyId: "",
        message: error.message || "Unable to save property tags."
      });
    }
  }

  async function handleMembershipSubmit(event) {
    event.preventDefault();
    setMembershipSubmission({
      isSubmitting: true,
      message: null
    });

    try {
      await apiRequest(
        "/organizations/" + state.selectedOrganizationId + "/memberships",
        {
          method: "POST",
          body: {
            user_email: membershipForm.user_email,
            role: membershipForm.role
          }
        }
      );
      setMembershipForm(buildInitialMembershipForm());
      await loadOrganizationData(state.selectedOrganizationId);
      setMembershipSubmission({
        isSubmitting: false,
        message: "Team member added."
      });
    } catch (error) {
      setMembershipSubmission({
        isSubmitting: false,
        message: error.message || "Unable to add this team member."
      });
    }
  }

  async function handleMembershipSave(membership) {
    var payload = membershipEditForms[membership.id];
    if (!payload) {
      return;
    }

    setMembershipAction({
      membershipId: membership.id,
      messageMembershipId: "",
      message: null
    });

    try {
      await apiRequest(
        "/organizations/" +
          state.selectedOrganizationId +
          "/memberships/" +
          membership.id,
        {
          method: "PATCH",
          body: {
            role: payload.role,
            is_active: payload.is_active
          }
        }
      );
      await loadOrganizationData(state.selectedOrganizationId);
      setMembershipAction({
        membershipId: "",
        messageMembershipId: membership.id,
        message: "Member access updated."
      });
    } catch (error) {
      setMembershipAction({
        membershipId: "",
        messageMembershipId: membership.id,
        message: error.message || "Unable to update this membership."
      });
    }
  }

  async function handleListingSubmit(event) {
    event.preventDefault();
    setListingSubmission({
      isSubmitting: true,
      message: null
    });

    try {
      await apiRequest(
        "/organizations/" + state.selectedOrganizationId + "/listings",
        {
          method: "POST",
          body: {
            property_id: listingForm.property_id,
            title: listingForm.title,
            description: listingForm.description,
            monthly_rent_minor: parseMinorAmount(listingForm.monthly_rent),
            deposit_minor: parseMinorAmount(listingForm.deposit),
            currency_code: listingForm.currency_code,
            minimum_tenant_score: Number(listingForm.minimum_tenant_score),
            minimum_verification_strength: Number(listingForm.minimum_verification_strength)
          }
        }
      );
      setListingForm(function keepPropertySelection(previous) {
        return Object.assign(buildInitialListingForm(), {
          property_id: previous.property_id || ""
        });
      });
      await loadOrganizationData(state.selectedOrganizationId);
      setListingSubmission({
        isSubmitting: false,
        message: "Listing published successfully."
      });
    } catch (error) {
      setListingSubmission({
        isSubmitting: false,
        message: error.message || "Unable to publish listing."
      });
    }
  }

  async function handleTrustCheckAction(action) {
    setTrustCheckSubmission({
      isSubmitting: true,
      action: action,
      message: null,
      result: null
    });

    try {
      var path = "/organizations/" + state.selectedOrganizationId + "/trust-checks";
      if (action === "validate") {
        path += "/validate";
      } else if (action === "preview") {
        path += "/profile";
      }

      var result = await apiRequest(path, {
        method: "POST",
        body: trustCheckForm
      });

      if (action === "create") {
        await loadOrganizationData(state.selectedOrganizationId);
      }

      setTrustCheckSubmission({
        isSubmitting: false,
        action: "",
        message:
          action === "validate"
            ? "Consent access validated successfully."
            : action === "preview"
              ? "Trust profile preview loaded."
              : "Agency trust check created successfully.",
        result: result
      });
    } catch (error) {
      setTrustCheckSubmission({
        isSubmitting: false,
        action: "",
        message: error.message || "Unable to complete the trust-check action.",
        result: null
      });
    }
  }

  async function handleApplicationAction(application, nextStatus) {
    setApplicationAction({
      applicationId: application.id,
      nextStatus: nextStatus
    });

    try {
      await apiRequest(
        "/organizations/" +
          state.selectedOrganizationId +
          "/applications/" +
          application.id,
        {
          method: "PATCH",
          body: {
            application_status: nextStatus,
            status_notes: "Updated from the rebuilt agency workbench."
          }
        }
      );
      await loadOrganizationData(state.selectedOrganizationId);
    } finally {
      setApplicationAction({
        applicationId: "",
        nextStatus: ""
      });
    }
  }

  async function handleListingAction(listing, nextStatus) {
    setListingAction({
      listingId: listing.id,
      nextStatus: nextStatus
    });

    try {
      await apiRequest(
        "/organizations/" +
          state.selectedOrganizationId +
          "/listings/" +
          listing.id,
        {
          method: "PATCH",
          body: {
            listing_status: nextStatus
          }
        }
      );
      await loadOrganizationData(state.selectedOrganizationId);
    } finally {
      setListingAction({
        listingId: "",
        nextStatus: ""
      });
    }
  }

  async function handleListingEditSave(listing) {
    var payload = listingEditForms[listing.id];
    if (!payload) {
      return;
    }

    setListingEditAction({
      listingId: listing.id,
      messageListingId: "",
      message: null
    });

    try {
      await apiRequest(
        "/organizations/" +
          state.selectedOrganizationId +
          "/listings/" +
          listing.id,
        {
          method: "PATCH",
          body: {
            description: payload.description,
            minimum_tenant_score: Number(payload.minimum_tenant_score),
            minimum_verification_strength: Number(payload.minimum_verification_strength)
          }
        }
      );
      await loadOrganizationData(state.selectedOrganizationId);
      setListingEditAction({
        listingId: "",
        messageListingId: listing.id,
        message: "Listing screening settings updated."
      });
    } catch (error) {
      setListingEditAction({
        listingId: "",
        messageListingId: listing.id,
        message: error.message || "Unable to update listing screening settings."
      });
    }
  }

  if (state.status === "loading" && !state.organizations.length && !state.dashboard) {
    return buildEmptyState(
      "We are loading your agency memberships, listings, and applicant screening data."
    );
  }

  if (state.status === "error" && !state.dashboard) {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Agency tools"),
      e("h1", { className: "state-title", key: "title" }, "Agency data unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  if (!state.organizations.length) {
    return buildEmptyState(
      "This account is not attached to an active agency organization, so agency tools are not available yet."
    );
  }

  var dashboard = state.dashboard;
  if (!dashboard) {
    return buildEmptyState("The agency dashboard is initializing.");
  }
  var selectedOrganization = state.organizations.find(function findOrganization(organization) {
    return organization.id === state.selectedOrganizationId;
  }) || null;
  var canManageMemberships = Boolean(
    selectedOrganization &&
      ["owner", "admin"].indexOf(selectedOrganization.current_user_membership_role) !== -1
  );
  var filteredApplications = state.applications.filter(function filterApplications(application) {
    return !applicationFilter || application.application_status === applicationFilter;
  });
  var normalizedPropertyTagFilter = propertyTagFilter.trim().toLowerCase();
  var filteredProperties = state.properties.filter(function filterProperties(propertyRecord) {
    if (!normalizedPropertyTagFilter) {
      return true;
    }
    var haystacks = [propertyRecord.property_label, propertyRecord.city].concat(
      propertyRecord.custom_tags || []
    );
    return haystacks.some(function matches(value) {
      return String(value || "").toLowerCase().indexOf(normalizedPropertyTagFilter) !== -1;
    });
  });
  var commercialOverview = state.commercialOverview;
  var agencySectionTabs = [
    {
      id: "overview",
      label: "Overview",
      meta: "Snapshot, metrics, and business signals"
    },
    {
      id: "publishing",
      label: "Publishing",
      meta: "Create properties and publish listings"
    },
    {
      id: "portfolio",
      label: "Portfolio",
      meta: String(state.properties.length) + " tracked properties"
    },
    {
      id: "screening",
      label: "Screening",
      meta: "Trust checks and shared profile access"
    },
    {
      id: "screening-history",
      label: "Screening history",
      meta: String(state.trustChecks.length) + " saved checks"
    },
    {
      id: "team",
      label: "Team access",
      meta: String(state.memberships.length) + " memberships"
    },
    {
      id: "pipeline",
      label: "Pipeline",
      meta: String(filteredApplications.length) + " filtered applications"
    }
  ];
  var agencySectionCopyByTab = {
    overview: "Start here for the agency-wide picture before changing anything.",
    publishing: "Keep property creation and listing publication together so publishing work stays separate from review work.",
    portfolio: "Use this lane only for estate search, tagging, and portfolio maintenance.",
    screening: "Run trust checks here without mixing screening into team or publishing flows.",
    "screening-history": "Use this lane only for saved trust-check history and audit context.",
    team: "Manage teammates and permissions here without touching listings or applicants.",
    pipeline: "Use the pipeline lane when you want to process listings and applications together."
  };

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Agency tools",
      title: dashboard.organization_name + " workspace",
      copy:
        "Use this page to add properties, publish listings, review applicants, run trust checks, and keep an eye on agency activity.",
      details: [
        "The agency workspace is now structured like an operating console: publishing, portfolio management, screening, team access, and pipeline work each have their own lane."
      ],
      extra: e("label", { className: "field toolbar-row", key: "selector" }, [
        e("span", { className: "field-label", key: "label" }, "Agency"),
        e(
          "select",
          {
            className: "field-input field-select",
            value: state.selectedOrganizationId,
            onChange: handleOrganizationChange,
            key: "select"
          },
          state.organizations.map(function renderOrganization(organization) {
            return e(
              "option",
              { value: organization.id, key: organization.id },
              organization.name + " (" + organization.current_user_membership_role + ")"
            );
          })
        )
      ]),
      stats: [
        e(HeroStat, {
          label: "Open listings",
          value: String(dashboard.open_listings),
          copy: String(dashboard.closed_listings) + " closed listings also on record."
        }),
        e(HeroStat, {
          label: "Applications",
          value: String(dashboard.total_applications),
          copy:
            String(dashboard.submitted_applications) +
            " submitted and " +
            String(dashboard.under_review_applications) +
            " under review."
        }),
        e(HeroStat, {
          label: "Trust checks",
          value: commercialOverview ? String(commercialOverview.total_trust_checks) : "0",
          copy: commercialOverview
            ? String(commercialOverview.trust_checks_last_30_days) + " run in the last 30 days."
            : "Commercial overview is not available yet."
        })
      ]
    }),
    e("section", { className: "detail-panel section-switcher", key: "agency-switcher" }, [
      e(SectionHeading, {
        title: "Focus on one agency lane",
        copy: agencySectionCopyByTab[agencySection],
        key: "heading"
      }),
      e(SegmentedTabs, {
        key: "tabs",
        tabs: agencySectionTabs,
        activeTab: agencySection,
        onChange: setAgencySection,
        "aria-label": "Agency workspace sections"
      })
    ]),
    agencySection === "publishing" ? e("section", { className: "split-grid", key: "publisher" }, [
      e("article", { className: "detail-panel", key: "property-form" }, [
        e("h2", { className: "detail-title", key: "title" }, "Add a property"),
        e(
          "p",
          { className: "empty-copy", key: "copy" },
          "Create a property record first. You can use it right away when you create a listing."
        ),
        e(
          "form",
          { className: "auth-form", onSubmit: handlePropertySubmit, key: "form" },
          [
            e("label", { className: "field", key: "property_label" }, [
              e("span", { className: "field-label", key: "label" }, "Property label"),
              e("input", {
                className: "field-input",
                name: "property_label",
                value: propertyForm.property_label,
                onChange: updatePropertyField,
                minLength: 2,
                maxLength: 255,
                required: true
              })
            ]),
            e("label", { className: "field", key: "address_line1" }, [
              e("span", { className: "field-label", key: "label" }, "Address"),
              e("input", {
                className: "field-input",
                name: "address_line1",
                value: propertyForm.address_line1,
                onChange: updatePropertyField,
                minLength: 2,
                maxLength: 255,
                required: true
              })
            ]),
            e("div", { className: "form-grid", key: "row" }, [
              e("label", { className: "field", key: "city" }, [
                e("span", { className: "field-label", key: "label" }, "City"),
                e("input", {
                  className: "field-input",
                  name: "city",
                  value: propertyForm.city,
                  onChange: updatePropertyField,
                  minLength: 2,
                  maxLength: 120,
                  required: true
                })
              ]),
              e("label", { className: "field", key: "country_code" }, [
                e("span", { className: "field-label", key: "label" }, "Country"),
                e("input", {
                  className: "field-input",
                  name: "country_code",
                  value: propertyForm.country_code,
                  onChange: updatePropertyField,
                  minLength: 2,
                  maxLength: 2,
                  required: true
                })
              ])
            ]),
            e("label", { className: "field", key: "custom_tags_text" }, [
              e("span", { className: "field-label", key: "label" }, "Custom tags"),
              e("input", {
                className: "field-input",
                name: "custom_tags_text",
                value: propertyForm.custom_tags_text,
                onChange: updatePropertyField,
                maxLength: 500,
                placeholder: "priority, waterfront, renovation"
              }),
              e(
                "span",
                { className: "field-help", key: "help" },
                "Use comma-separated tags to organize and search your estate portfolio more quickly."
              )
            ]),
            propertySubmission.message
              ? e("div", { className: "form-alert", key: "message" }, propertySubmission.message)
              : null,
            e(
              "button",
              {
                type: "submit",
                className: "button",
                disabled: propertySubmission.isSubmitting,
                key: "submit"
              },
              propertySubmission.isSubmitting ? "Creating property..." : "Create property"
            )
          ]
        )
      ]),
      e("article", { className: "detail-panel", key: "listing-form" }, [
        e("h2", { className: "detail-title", key: "title" }, "Create a listing"),
        e(
          "p",
          { className: "empty-copy", key: "copy" },
          state.properties.length
            ? "Select a property, define the commercial terms, and publish the listing into this agency workspace."
            : "Create at least one property first so the listing form has a property to attach."
        ),
        e(
          "form",
          { className: "auth-form", onSubmit: handleListingSubmit, key: "form" },
          [
            e("label", { className: "field", key: "property_id" }, [
              e("span", { className: "field-label", key: "label" }, "Property"),
              e(
                "select",
                {
                  className: "field-input field-select",
                  name: "property_id",
                  value: listingForm.property_id,
                  onChange: updateListingField,
                  required: true,
                  disabled: !state.properties.length
                },
                [
                  e("option", { value: "", key: "blank" }, "Select a property"),
                  state.properties.map(function renderProperty(propertyRecord) {
                    return e(
                      "option",
                      { value: propertyRecord.id, key: propertyRecord.id },
                      propertyRecord.property_label + " | " + propertyRecord.city
                    );
                  })
                ]
              )
            ]),
            e("label", { className: "field", key: "title" }, [
              e("span", { className: "field-label", key: "label" }, "Listing title"),
              e("input", {
                className: "field-input",
                name: "title",
                value: listingForm.title,
                onChange: updateListingField,
                minLength: 2,
                maxLength: 255,
                required: true
              })
            ]),
            e("label", { className: "field", key: "description" }, [
              e("span", { className: "field-label", key: "label" }, "Description"),
              e("input", {
                className: "field-input",
                name: "description",
                value: listingForm.description,
                onChange: updateListingField,
                maxLength: 1000
              })
            ]),
            e("div", { className: "form-grid", key: "money-row" }, [
              e("label", { className: "field", key: "monthly_rent" }, [
                e("span", { className: "field-label", key: "label" }, "Monthly rent"),
                e("input", {
                  className: "field-input",
                  name: "monthly_rent",
                  type: "number",
                  min: "0",
                  step: "0.01",
                  value: listingForm.monthly_rent,
                  onChange: updateListingField,
                  required: true
                })
              ]),
              e("label", { className: "field", key: "deposit" }, [
                e("span", { className: "field-label", key: "label" }, "Deposit"),
                e("input", {
                  className: "field-input",
                  name: "deposit",
                  type: "number",
                  min: "0",
                  step: "0.01",
                  value: listingForm.deposit,
                  onChange: updateListingField,
                  required: true
                })
              ])
            ]),
            e("div", { className: "form-grid", key: "threshold-row" }, [
              e("label", { className: "field", key: "minimum_tenant_score" }, [
                e("span", { className: "field-label", key: "label" }, "Minimum tenant score"),
                e("input", {
                  className: "field-input",
                  name: "minimum_tenant_score",
                  type: "number",
                  min: "0",
                  max: "1000",
                  value: listingForm.minimum_tenant_score,
                  onChange: updateListingField,
                  required: true
                })
              ]),
              e("label", { className: "field", key: "minimum_verification_strength" }, [
                e("span", { className: "field-label", key: "label" }, "Minimum verification strength"),
                e("input", {
                  className: "field-input",
                  name: "minimum_verification_strength",
                  type: "number",
                  min: "0",
                  max: "100",
                  value: listingForm.minimum_verification_strength,
                  onChange: updateListingField,
                  required: true
                })
              ])
            ]),
            listingSubmission.message
              ? e("div", { className: "form-alert", key: "message" }, listingSubmission.message)
              : null,
            e(
              "button",
              {
                type: "submit",
                className: "button",
                disabled: listingSubmission.isSubmitting || !state.properties.length,
                key: "submit"
              },
              listingSubmission.isSubmitting ? "Publishing listing..." : "Publish listing"
            )
          ]
        )
      ])
    ]) : null,
    agencySection === "portfolio" ? e("section", { className: "detail-panel", key: "property-portfolio" }, [
      e("h2", { className: "detail-title", key: "title" }, "Estate portfolio"),
      e(
        "p",
        { className: "empty-copy", key: "copy" },
        "Browse your saved properties, search them quickly, and keep custom tags up to date so you can find estates faster."
      ),
      e("label", { className: "field toolbar-row", key: "filter" }, [
        e("span", { className: "field-label", key: "label" }, "Find by label, city, or tag"),
        e("input", {
          className: "field-input",
          value: propertyTagFilter,
          onChange: function onChange(event) {
            setPropertyTagFilter(event.target.value);
          },
          placeholder: "search by estate label or tag"
        })
      ]),
      propertyTagAction.message
        ? e("div", { className: "form-alert", key: "message" }, propertyTagAction.message)
        : null,
      filteredProperties.length
        ? e(
            "div",
            { className: "list-stack", key: "list" },
            filteredProperties.map(function renderPropertyCard(propertyRecord) {
              var tagValue =
                Object.prototype.hasOwnProperty.call(propertyTagForms, propertyRecord.id)
                  ? propertyTagForms[propertyRecord.id]
                  : formatTagText(propertyRecord.custom_tags);
              return e("article", { className: "stack-card", key: propertyRecord.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, propertyRecord.property_label),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "management",
                    tone: propertyRecord.management_mode === "agency_managed" ? "accent" : "success",
                    label: propertyRecord.management_mode === "agency_managed" ? "Agency managed" : "Owner managed"
                  })
                ]),
                e("div", { className: "fact-grid", key: "meta" }, [
                  e(FactPill, {
                    key: "location",
                    label: "Location",
                    value: propertyRecord.address_line1 + " | " + propertyRecord.city + " | " + propertyRecord.country_code
                  }),
                  e(FactPill, {
                    key: "agent",
                    label: "Assigned agent",
                    value: propertyRecord.assigned_agency_user_full_name || "Not yet assigned",
                    tone: "accent"
                  }),
                  e(FactPill, {
                    key: "tenant",
                    label: "Prospective tenant",
                    value: propertyRecord.assigned_tenant_user_full_name || "Not yet assigned"
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
                      "No tags added yet."
                    ),
                e("label", { className: "field", key: "tag-edit" }, [
                  e("span", { className: "field-label", key: "label" }, "Edit custom tags"),
                  e("input", {
                    className: "field-input",
                    value: tagValue,
                    onChange: function onChange(event) {
                      setPropertyTagForms(function updatePropertyTags(previous) {
                        var next = Object.assign({}, previous);
                        next[propertyRecord.id] = event.target.value;
                        return next;
                      });
                    }
                  })
                ]),
                e(
                  "button",
                  {
                    type: "button",
                    className: "button button-secondary button-small",
                    disabled: propertyTagAction.propertyId === propertyRecord.id,
                    onClick: function onClick() {
                      handlePropertyTagSave(propertyRecord);
                    }
                  },
                  propertyTagAction.propertyId === propertyRecord.id ? "Saving..." : "Save tags"
                )
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No properties match the current filter."
          )
    ]) : null,
    agencySection === "screening" ? e("section", { className: "split-grid", key: "trust-checks" }, [
      e("article", { className: "detail-panel", key: "trust-check-form" }, [
        e("h2", { className: "detail-title", key: "title" }, "Check a shared trust profile"),
        e(
          "p",
          { className: "empty-copy", key: "copy" },
          "Use a share token and access code to confirm access, preview a profile, or save a trust check. Saved checks live in Screening history."
        ),
        e("div", { className: "auth-form", key: "form" }, [
          e("label", { className: "field", key: "share_token" }, [
            e("span", { className: "field-label", key: "label" }, "Share token"),
            e("input", {
              className: "field-input",
              name: "share_token",
              value: trustCheckForm.share_token,
              onChange: updateTrustCheckField,
              minLength: 20,
              maxLength: 255,
              required: true
            })
          ]),
          e("label", { className: "field", key: "access_code" }, [
            e("span", { className: "field-label", key: "label" }, "Access code"),
            e("input", {
              className: "field-input",
              name: "access_code",
              type: "password",
              value: trustCheckForm.access_code,
              onChange: updateTrustCheckField,
              minLength: 4,
              maxLength: 64,
              required: true
            })
          ]),
          trustCheckSubmission.message
            ? e("div", { className: "form-alert", key: "message" }, trustCheckSubmission.message)
            : null,
          e("div", { className: "action-row", key: "actions" }, [
            e(
              "button",
              {
                type: "button",
                className: "button button-secondary button-small",
                disabled: trustCheckSubmission.isSubmitting,
                onClick: function onClick() {
                  handleTrustCheckAction("validate");
                },
                key: "validate"
              },
              trustCheckSubmission.isSubmitting && trustCheckSubmission.action === "validate"
                ? "Validating..."
                : "Check access"
            ),
            e(
              "button",
              {
                type: "button",
                className: "button button-secondary button-small",
                disabled: trustCheckSubmission.isSubmitting,
                onClick: function onClick() {
                  handleTrustCheckAction("preview");
                },
                key: "preview"
              },
              trustCheckSubmission.isSubmitting && trustCheckSubmission.action === "preview"
                ? "Loading..."
                : "Preview profile"
            ),
            e(
              "button",
              {
                type: "button",
                className: "button button-small",
                disabled: trustCheckSubmission.isSubmitting,
                onClick: function onClick() {
                  handleTrustCheckAction("create");
                },
                key: "create"
              },
              trustCheckSubmission.isSubmitting && trustCheckSubmission.action === "create"
                ? "Creating..."
                : "Save trust check"
            )
          ]),
          trustCheckSubmission.result
            ? e("div", { className: "list-stack", key: "result" }, [
                trustCheckSubmission.result.subject_full_name
                  ? e(NoteBlock, { key: "subject", label: "Subject", tone: "accent" }, trustCheckSubmission.result.subject_full_name)
                  : null,
                trustCheckSubmission.result.profile
                  ? e("div", { className: "fact-grid", key: "profile" }, [
                      e(FactPill, { key: "tenant", label: "Tenant score", value: String(trustCheckSubmission.result.profile.tenant_score), tone: "accent" }),
                      e(FactPill, { key: "landlord", label: "Landlord score", value: String(trustCheckSubmission.result.profile.landlord_score), tone: "accent" }),
                      e(FactPill, { key: "verification", label: "Verification strength", value: String(trustCheckSubmission.result.profile.verification_strength) + "%", tone: "success" }),
                      e(FactPill, { key: "tenancies", label: "Verified tenancies", value: String(trustCheckSubmission.result.profile.verified_tenancies) })
                    ])
                  : trustCheckSubmission.result.tenant_score != null
                    ? e("div", { className: "fact-grid", key: "preview-profile" }, [
                        e(FactPill, { key: "tenant", label: "Tenant score", value: String(trustCheckSubmission.result.tenant_score), tone: "accent" }),
                        e(FactPill, { key: "landlord", label: "Landlord score", value: String(trustCheckSubmission.result.landlord_score), tone: "accent" }),
                        e(FactPill, { key: "verification", label: "Verification strength", value: String(trustCheckSubmission.result.verification_strength) + "%", tone: "success" }),
                        e(FactPill, { key: "events", label: "Trust events", value: String(trustCheckSubmission.result.trust_event_count) })
                      ])
                    : null
              ])
            : null
        ])
      ])
    ]) : null,
    agencySection === "screening-history" ? e("section", { className: "detail-panel", key: "recent-trust-checks" }, [
        e("h2", { className: "detail-title", key: "title" }, "Recent trust checks"),
        state.trustChecks.length
          ? e(
              "div",
              { className: "list-stack", key: "list" },
              state.trustChecks.map(function renderTrustCheck(trustCheck) {
                return e("article", { className: "stack-card", key: trustCheck.id }, [
                  e("strong", { className: "stack-card-title", key: "title" }, trustCheck.subject_full_name),
                  e("div", { className: "status-row", key: "status" }, [
                    e(StatusBadge, { key: "scope", tone: "accent", label: trustCheck.scope }),
                    e(StatusBadge, { key: "created", tone: "neutral", label: trustCheck.created_at })
                  ]),
                  e(NoteBlock, { key: "meta", label: "Requested by" }, trustCheck.requested_by_user_full_name)
                ]);
              })
            )
          : e(
              "p",
              { className: "empty-copy", key: "empty" },
              "No agency trust checks have been created for this organization yet."
            )
    ]) : null,
    agencySection === "overview"
      ? e("section", { className: "metric-grid", key: "metrics" }, [
      e(MetricCard, {
        kicker: "Listings",
        value: String(dashboard.open_listings) + " open",
        copy: String(dashboard.closed_listings) + " closed listings on record."
      }),
      e(MetricCard, {
        kicker: "Applications",
        value: String(dashboard.total_applications),
        copy: String(dashboard.submitted_applications) + " submitted and " + String(dashboard.under_review_applications) + " under review."
      }),
      e(MetricCard, {
        kicker: "Average applicant score",
        value: dashboard.average_applicant_tenant_score == null
          ? "N/A"
          : String(dashboard.average_applicant_tenant_score),
        copy: "Average applicant verification " + (dashboard.average_applicant_verification_strength == null
          ? "N/A"
          : String(dashboard.average_applicant_verification_strength) + "%") + "."
      }),
      e(MetricCard, {
        kicker: "Acceptance rate",
        value: commercialOverview ? formatPercent(commercialOverview.acceptance_rate_percent) : "N/A",
        copy: commercialOverview
          ? String(commercialOverview.total_applications) + " total applications across the agency pipeline."
          : "Commercial overview is loading."
      }),
      e(MetricCard, {
        kicker: "Decision speed",
        value: commercialOverview ? formatHours(commercialOverview.average_time_to_decision_hours) : "N/A",
        copy: commercialOverview
          ? String(commercialOverview.applications_last_30_days) + " applications in the last 30 days."
          : "Commercial overview is loading."
      }),
      e(MetricCard, {
        kicker: "Recent screening",
        value: commercialOverview ? String(commercialOverview.trust_checks_last_30_days) : "0",
        copy: commercialOverview
          ? String(commercialOverview.total_trust_checks) + " total trust checks on record."
          : "Commercial overview is loading."
      })
    ]) : null,
    agencySection === "overview" && commercialOverview
      ? e("section", { className: "detail-panel", key: "commercial-overview" }, [
        e("h2", { className: "detail-title", key: "title" }, "Business snapshot"),
          e("div", { className: "pill-row", key: "pills" }, [
            e("span", { className: "pill", key: "members" }, "Active members: " + String(commercialOverview.active_member_count)),
            e("span", { className: "pill", key: "properties" }, "Tracked properties: " + String(commercialOverview.tracked_property_count)),
            e("span", { className: "pill", key: "open" }, "Open listings: " + String(commercialOverview.open_listing_count)),
            e("span", { className: "pill", key: "no-applicants" }, "Open listings without applicants: " + String(commercialOverview.listings_without_applicants_count)),
            e("span", { className: "pill", key: "recent-applications" }, "Applications in last 30 days: " + String(commercialOverview.applications_last_30_days)),
            e("span", { className: "pill", key: "recent-checks" }, "Trust checks in last 30 days: " + String(commercialOverview.trust_checks_last_30_days))
          ])
        ])
      : null,
    agencySection === "team" ? e("section", { className: "detail-panel", key: "team-access" }, [
      e("h2", { className: "detail-title", key: "title" }, "Team access"),
      e(
        "p",
        { className: "empty-copy", key: "copy" },
        canManageMemberships
          ? "Invite agency teammates by email and keep roles up to date without leaving this workspace."
          : "You can see who belongs to this agency here. Owners and admins can update access."
      ),
      canManageMemberships
        ? e(
            "form",
            { className: "auth-form", onSubmit: handleMembershipSubmit, key: "form" },
            [
              e("div", { className: "form-grid", key: "row" }, [
                e("label", { className: "field", key: "email" }, [
                  e("span", { className: "field-label", key: "label" }, "Team member email"),
                  e("input", {
                    className: "field-input",
                    type: "email",
                    name: "user_email",
                    value: membershipForm.user_email,
                    onChange: updateMembershipField,
                    placeholder: "agent@company.com",
                    required: true
                  })
                ]),
                e("label", { className: "field", key: "role" }, [
                  e("span", { className: "field-label", key: "label" }, "Role"),
                  e(
                    "select",
                    {
                      className: "field-input field-select",
                      name: "role",
                      value: membershipForm.role,
                      onChange: updateMembershipField
                    },
                    [
                      e("option", { value: "member", key: "member" }, "Member"),
                      e("option", { value: "agent", key: "agent" }, "Agent"),
                      e("option", { value: "admin", key: "admin" }, "Admin"),
                      e("option", { value: "owner", key: "owner" }, "Owner")
                    ]
                  )
                ])
              ]),
              membershipSubmission.message
                ? e("div", { className: "form-alert", key: "message" }, membershipSubmission.message)
                : null,
              e(
                "button",
                {
                  type: "submit",
                  className: "button button-secondary",
                  disabled: membershipSubmission.isSubmitting,
                  key: "submit"
                },
                membershipSubmission.isSubmitting ? "Adding member..." : "Add team member"
              )
            ]
          )
        : null,
      state.memberships.length
        ? e(
            "div",
            { className: "list-stack", key: "memberships" },
            state.memberships.map(function renderMembership(membership) {
              var membershipFormState =
                membershipEditForms[membership.id] || buildMembershipEditForm(membership);
              var isSavingMembership = membershipAction.membershipId === membership.id;
              return e("article", { className: "stack-card", key: membership.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, membership.user_full_name + " | " + membership.user_email),
                e("div", { className: "status-row", key: "meta" }, [
                  e(StatusBadge, { key: "role", tone: "accent", label: membership.role }),
                  e(StatusBadge, {
                    key: "access",
                    tone: membership.is_active ? "success" : "danger",
                    label: membership.is_active ? "Active" : "Inactive"
                  })
                ]),
                canManageMemberships
                  ? e("div", { className: "form-grid", key: "controls" }, [
                      e("label", { className: "field", key: "role" }, [
                        e("span", { className: "field-label", key: "label" }, "Role"),
                        e(
                          "select",
                          {
                            className: "field-input field-select",
                            value: membershipFormState.role,
                            onChange: function onChange(event) {
                              updateEntityForm(
                                setMembershipEditForms,
                                membership.id,
                                "role",
                                event.target.value
                              );
                            }
                          },
                          [
                            e("option", { value: "member", key: "member" }, "Member"),
                            e("option", { value: "agent", key: "agent" }, "Agent"),
                            e("option", { value: "admin", key: "admin" }, "Admin"),
                            e("option", { value: "owner", key: "owner" }, "Owner")
                          ]
                        )
                      ]),
                      e("label", { className: "field", key: "active" }, [
                        e("span", { className: "field-label", key: "label" }, "Access"),
                        e(
                          "select",
                          {
                            className: "field-input field-select",
                            value: membershipFormState.is_active ? "active" : "inactive",
                            onChange: function onChange(event) {
                              updateEntityForm(
                                setMembershipEditForms,
                                membership.id,
                                "is_active",
                                event.target.value === "active"
                              );
                            }
                          },
                          [
                            e("option", { value: "active", key: "active" }, "Active"),
                            e("option", { value: "inactive", key: "inactive" }, "Inactive")
                          ]
                        )
                      ])
                    ])
                  : null,
                canManageMemberships
                  ? e("div", { className: "action-row", key: "actions" }, [
                      e(
                        "button",
                        {
                          type: "button",
                          className: "button button-secondary button-small",
                          disabled: isSavingMembership,
                          onClick: function onClick() {
                            handleMembershipSave(membership);
                          },
                          key: "save"
                        },
                        isSavingMembership ? "Saving..." : "Save access"
                      ),
                      membershipAction.message &&
                      membershipAction.messageMembershipId === membership.id &&
                      !membershipAction.membershipId
                        ? e("span", { className: "empty-copy", key: "message" }, membershipAction.message)
                        : null
                    ])
                  : null
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No team memberships are attached to this agency yet."
          )
    ]) : null,
    agencySection === "pipeline" ? e("section", { className: "detail-panel", key: "pipeline" }, [
        e("h2", { className: "detail-title", key: "title" }, "Application pipeline"),
      e("div", { className: "pill-row", key: "pills" }, [
        e("span", { className: "pill", key: "submitted" }, "Submitted: " + String(dashboard.submitted_applications)),
        e("span", { className: "pill", key: "review" }, "Under review: " + String(dashboard.under_review_applications)),
        e("span", { className: "pill", key: "accepted" }, "Accepted: " + String(dashboard.accepted_applications)),
        e("span", { className: "pill", key: "rejected" }, "Rejected: " + String(dashboard.rejected_applications)),
        e("span", { className: "pill", key: "withdrawn" }, "Withdrawn: " + String(dashboard.withdrawn_applications))
      ])
    ]) : null,
    agencySection === "pipeline" ? e("section", { className: "detail-panel", key: "listings" }, [
      e("h2", { className: "detail-title", key: "title" }, "Listings"),
      state.listings.length
        ? e(
            "div",
            { className: "list-stack", key: "list" },
          state.listings.map(function renderListing(listing) {
            var listingActions = buildListingActions(listing);
            var listingEditForm = listingEditForms[listing.id] || buildListingEditForm(listing);
            var isSavingListingSettings = listingEditAction.listingId === listing.id;
              return e("article", { className: "stack-card", key: listing.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, listing.title),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "listing-status",
                    tone: inferStatusTone(listing.listing_status),
                    label: listing.listing_status
                  }),
                  e(StatusBadge, { key: "property", tone: "accent", label: listing.property_label }),
                  e(StatusBadge, { key: "city", tone: "neutral", label: listing.city })
                ]),
                e("div", { className: "fact-grid", key: "facts" }, [
                  e(FactPill, {
                    key: "rent",
                    label: "Monthly rent",
                    value: formatMinorAmount(listing.monthly_rent_minor, listing.currency_code),
                    tone: "accent"
                  }),
                  e(FactPill, {
                    key: "deposit",
                    label: "Deposit",
                    value: formatMinorAmount(listing.deposit_minor, listing.currency_code),
                    tone: "warning"
                  }),
                  e(FactPill, {
                    key: "score",
                    label: "Minimum tenant score",
                    value: String(listing.minimum_tenant_score)
                  }),
                  e(FactPill, {
                    key: "verification",
                    label: "Verification threshold",
                    value: String(listing.minimum_verification_strength) + "%",
                    tone: "success"
                  })
                ]),
                e("div", { className: "form-grid", key: "settings-grid" }, [
                  e("label", { className: "field", key: "edit-description" }, [
                    e("span", { className: "field-label", key: "label" }, "Screening note"),
                    e("input", {
                      className: "field-input",
                      value: listingEditForm.description,
                      onChange: function onChange(event) {
                        updateEntityForm(setListingEditForms, listing.id, "description", event.target.value);
                      },
                      maxLength: 1000
                    })
                  ]),
                  e("label", { className: "field", key: "edit-score" }, [
                    e("span", { className: "field-label", key: "label" }, "Minimum tenant score"),
                    e("input", {
                      className: "field-input",
                      type: "number",
                      min: "0",
                      max: "1000",
                      value: listingEditForm.minimum_tenant_score,
                      onChange: function onChange(event) {
                        updateEntityForm(
                          setListingEditForms,
                          listing.id,
                          "minimum_tenant_score",
                          event.target.value
                        );
                      }
                    })
                  ]),
                  e("label", { className: "field", key: "edit-verification" }, [
                    e("span", { className: "field-label", key: "label" }, "Minimum verification"),
                    e("input", {
                      className: "field-input",
                      type: "number",
                      min: "0",
                      max: "100",
                      value: listingEditForm.minimum_verification_strength,
                      onChange: function onChange(event) {
                        updateEntityForm(
                          setListingEditForms,
                          listing.id,
                          "minimum_verification_strength",
                          event.target.value
                        );
                      }
                    })
                  ])
                ]),
                e("div", { className: "action-row", key: "settings-actions" }, [
                  e(
                    "button",
                    {
                      type: "button",
                      className: "button button-secondary button-small",
                      disabled: isSavingListingSettings || Boolean(listingAction.listingId),
                      onClick: function onClick() {
                        handleListingEditSave(listing);
                      },
                      key: "save"
                    },
                    isSavingListingSettings ? "Saving..." : "Save screening settings"
                  ),
                  listingEditAction.message &&
                  listingEditAction.messageListingId === listing.id &&
                  !listingEditAction.listingId
                    ? e("span", { className: "empty-copy", key: "message" }, listingEditAction.message)
                    : null
                ]),
                listingActions.length
                  ? e(
                      "div",
                      { className: "action-row", key: "actions" },
                      listingActions.map(function renderAction(action) {
                        var isSubmitting =
                          listingAction.listingId === listing.id &&
                          listingAction.nextStatus === action.status;
                        return e(
                          "button",
                          {
                            type: "button",
                            className: "button button-secondary button-small",
                            disabled: Boolean(listingAction.listingId),
                            onClick: function onClick() {
                              handleListingAction(listing, action.status);
                            },
                            key: action.status
                          },
                          isSubmitting ? "Saving..." : action.label
                        );
                      })
                    )
                  : null
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No listings have been published for this agency organization yet."
          )
    ]) : null,
    agencySection === "pipeline" ? e("section", { className: "detail-panel", key: "applications" }, [
      e("div", { className: "action-row", key: "header" }, [
        e("h2", { className: "detail-title", key: "title" }, "Applications"),
        e(
          "select",
          {
            className: "field-input field-select",
            value: applicationFilter,
            onChange: function onChange(event) {
              setApplicationFilter(event.target.value);
            },
            key: "filter"
          },
          applicationStatusOptions.map(function renderOption(option) {
            return e("option", { value: option.value, key: option.value || "all" }, option.label);
          })
        )
      ]),
      filteredApplications.length
        ? e(
            "div",
            { className: "list-stack", key: "applications" },
            filteredApplications.map(function renderApplication(application) {
              var actions = buildApplicationActions(application);
              return e("article", { className: "stack-card", key: application.id }, [
                e(
                  "strong",
                  { className: "stack-card-title", key: "title" },
                  application.applicant_full_name + " applied for " + application.listing_title
                ),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "application-status",
                    tone: inferStatusTone(application.application_status),
                    label: application.application_status
                  })
                ]),
                e("div", { className: "fact-grid", key: "facts" }, [
                  e(FactPill, {
                    key: "score",
                    label: "Tenant score",
                    value:
                      application.applicant_tenant_score == null
                        ? "N/A"
                        : String(application.applicant_tenant_score),
                    tone: "accent"
                  }),
                  e(FactPill, {
                    key: "verification",
                    label: "Verification strength",
                    value:
                      application.applicant_verification_strength == null
                        ? "N/A"
                        : String(application.applicant_verification_strength) + "%",
                    tone: "success"
                  })
                ]),
                e(
                  NoteBlock,
                  { key: "note", label: "Application note", tone: "accent" },
                  application.status_notes ||
                    application.applicant_note ||
                    "No extra notes captured yet."
                ),
                actions.length
                  ? e(
                      "div",
                      { className: "action-row", key: "actions" },
                      actions.map(function renderAction(action) {
                        var isSubmitting =
                          applicationAction.applicationId === application.id &&
                          applicationAction.nextStatus === action.status;
                        return e(
                          "button",
                          {
                            type: "button",
                            className: "button button-secondary button-small",
                            disabled: Boolean(applicationAction.applicationId),
                            onClick: function onClick() {
                              handleApplicationAction(application, action.status);
                            },
                            key: action.status
                          },
                          isSubmitting ? "Saving..." : action.label
                        );
                      })
                    )
                  : e(
                      "p",
                      { className: "empty-copy", key: "final" },
                      "This application is already in a final state."
                    )
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            applicationFilter
              ? "No applications match the current status filter."
              : "No applications have reached this dashboard yet."
          )
    ]) : null
  ]);
}
