import React from "react";

import { SegmentedTabs } from "../components/SegmentedTabs.js";
import {
  FactPill,
  HeroStat,
  NoteBlock,
  PageHero,
  SectionHeading,
  StatusBadge
} from "../components/PageChrome.js";
import { apiRequest } from "../lib/api.js";
import { e, getLanguageLocale } from "../lib/i18n.js";

function formatMinorAmount(minorAmount, currencyCode) {
  return new Intl.NumberFormat(getLanguageLocale(), {
    style: "currency",
    currency: currencyCode || "EUR",
    maximumFractionDigits: 2
  }).format((minorAmount || 0) / 100);
}

function inferStatusTone(value) {
  var normalized = String(value || "").toLowerCase();
  if (
    normalized.indexOf("accept") >= 0 ||
    normalized.indexOf("active") >= 0 ||
    normalized.indexOf("open") >= 0
  ) {
    return "success";
  }
  if (
    normalized.indexOf("review") >= 0 ||
    normalized.indexOf("pending") >= 0 ||
    normalized.indexOf("submitted") >= 0
  ) {
    return "warning";
  }
  if (
    normalized.indexOf("reject") >= 0 ||
    normalized.indexOf("closed") >= 0 ||
    normalized.indexOf("withdraw") >= 0
  ) {
    return "danger";
  }
  return "accent";
}

export function MarketplacePage() {
  var stateTuple = React.useState({
    status: "loading",
    listings: [],
    applications: [],
    error: null
  });
  var state = stateTuple[0];
  var setState = stateTuple[1];
  var notesTuple = React.useState({});
  var listingNotes = notesTuple[0];
  var setListingNotes = notesTuple[1];
  var submitTuple = React.useState({
    listingId: "",
    message: null
  });
  var submitState = submitTuple[0];
  var setSubmitState = submitTuple[1];
  var marketSectionTuple = React.useState("available");
  var marketSection = marketSectionTuple[0];
  var setMarketSection = marketSectionTuple[1];

  var loadMarketplace = React.useCallback(async function loadMarketplace() {
    setState(function setLoading(previous) {
      return {
        status: previous.listings.length || previous.applications.length ? "refreshing" : "loading",
        listings: previous.listings,
        applications: previous.applications,
        error: null
      };
    });

    try {
      var results = await Promise.all([
        apiRequest("/listings/open"),
        apiRequest("/applications/mine")
      ]);
      setState({
        status: "ready",
        listings: results[0],
        applications: results[1],
        error: null
      });
    } catch (error) {
      setState({
        status: "error",
        listings: [],
        applications: [],
        error: error.message || "Unable to load marketplace data."
      });
    }
  }, []);

  React.useEffect(function bootstrapMarketplace() {
    loadMarketplace();
  }, [loadMarketplace]);

  function updateListingNote(listingId, value) {
    setListingNotes(function mergeNotes(previous) {
      var next = Object.assign({}, previous);
      next[listingId] = value;
      return next;
    });
  }

  async function handleApply(listing) {
    setSubmitState({
      listingId: listing.id,
      message: null
    });

    try {
      await apiRequest("/listings/" + listing.id + "/applications", {
        method: "POST",
        body: {
          applicant_note:
            listingNotes[listing.id] || "Submitted from the rebuilt marketplace."
        }
      });
      await loadMarketplace();
      setSubmitState({
        listingId: "",
        message: "Application submitted successfully."
      });
    } catch (error) {
      setSubmitState({
        listingId: listing.id,
        message: error.message || "Unable to submit the application."
      });
    }
  }

  if (state.status === "loading") {
    return e("div", { className: "state-panel" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Listings"),
      e("h1", { className: "state-title", key: "title" }, "Loading live listings"),
      e(
        "p",
        { className: "state-copy", key: "copy" },
        "We are loading available listings and your applications."
      )
    ]);
  }

  if (state.status === "error") {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Listings"),
      e("h1", { className: "state-title", key: "title" }, "Marketplace data unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  var appliedListingIds = {};
  state.applications.forEach(function mapApplication(application) {
    appliedListingIds[application.listing_id] = application.application_status;
  });
  var underReviewCount = state.applications.filter(function filterUnderReview(application) {
    return application.application_status === "under_review";
  }).length;
  var acceptedCount = state.applications.filter(function filterAccepted(application) {
    return application.application_status === "accepted";
  }).length;
  var marketplaceTabs = [
    {
      id: "available",
      label: "Available listings",
      meta: String(state.listings.length) + " open homes"
    },
    {
      id: "applications",
      label: "My applications",
      meta: String(state.applications.length) + " submitted"
    }
  ];

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Listings",
      title: "Browse listings and track applications",
      copy:
        "Use this page to look for available homes, submit applications, and follow the status of the ones you already sent.",
      details: [
        "This workspace now separates discovery from tracking, so searching for homes does not compete visually with reviewing your own application pipeline."
      ],
      stats: [
        e(HeroStat, {
          label: "Open listings",
          value: String(state.listings.length),
          copy: "Listings currently open to applicants."
        }),
        e(HeroStat, {
          label: "Applications",
          value: String(state.applications.length),
          copy: String(underReviewCount) + " under review right now."
        }),
        e(HeroStat, {
          label: "Accepted",
          value: String(acceptedCount),
          copy: "Applications already moved into acceptance."
        })
      ]
    }),
    submitState.message
      ? e("div", { className: "form-alert", key: "message" }, submitState.message)
      : null,
    e("section", { className: "detail-panel section-switcher", key: "market-switcher" }, [
      e(SectionHeading, {
        title: "Focus on one marketplace lane",
        copy:
          marketSection === "available"
            ? "Stay in discovery mode when you want to compare active homes and submit new applications."
            : "Switch here when you only want to review what you have already submitted.",
        key: "heading"
      }),
      e(SegmentedTabs, {
        key: "tabs",
        tabs: marketplaceTabs,
        activeTab: marketSection,
        onChange: setMarketSection,
        "aria-label": "Marketplace sections"
      })
    ]),
    marketSection === "available"
      ? e("section", { className: "detail-panel", key: "open-listings" }, [
      e(SectionHeading, {
        title: "Available listings",
        copy: "Each listing shows the rent, deposit, and trust thresholds before you apply.",
        key: "heading"
      }),
      state.listings.length
        ? e(
            "div",
            { className: "list-stack", key: "listings" },
            state.listings.map(function renderListing(listing) {
              var existingStatus = appliedListingIds[listing.id];
              var isSubmitting = submitState.listingId === listing.id;
              return e("article", { className: "stack-card", key: listing.id }, [
                e("strong", { className: "stack-card-title", key: "title" }, listing.title),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, { key: "lane", tone: "accent", label: "Open listing" }),
                  existingStatus
                    ? e(StatusBadge, {
                        key: "application",
                        tone: inferStatusTone(existingStatus),
                        label: existingStatus
                      })
                    : null
                ]),
                e("div", { className: "fact-grid", key: "meta" }, [
                  e(FactPill, {
                    key: "organization",
                    label: "Agency",
                    value: listing.organization_name
                  }),
                  e(FactPill, {
                    key: "property",
                    label: "Property",
                    value: listing.property_label
                  }),
                  e(FactPill, {
                    key: "city",
                    label: "City",
                    value: listing.city
                  }),
                  e(FactPill, {
                    key: "rent",
                    label: "Rent",
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
                    key: "minimum-score",
                    label: "Minimum tenant score",
                    value: String(listing.minimum_tenant_score)
                  }),
                  e(FactPill, {
                    key: "verification",
                    label: "Verification strength",
                    value: String(listing.minimum_verification_strength) + "%",
                    tone: "success"
                  })
                ]),
                e("label", { className: "field", key: "note" }, [
                  e("span", { className: "field-label", key: "label" }, "Application note"),
                  e("input", {
                    className: "field-input",
                    value: listingNotes[listing.id] || "",
                    onChange: function onChange(event) {
                      updateListingNote(listing.id, event.target.value);
                    },
                    maxLength: 1000,
                    disabled: Boolean(existingStatus)
                  })
                ]),
                existingStatus
                  ? e(
                      NoteBlock,
                      {
                        key: "existing",
                        tone: "accent",
                        label: "Current application"
                      },
                      "You already applied to this listing. Current status: " + existingStatus + "."
                    )
                  : e(
                      "button",
                      {
                        type: "button",
                        className: "button button-secondary",
                        disabled: Boolean(submitState.listingId),
                        onClick: function onClick() {
                          handleApply(listing);
                        },
                        key: "apply"
                      },
                      isSubmitting ? "Submitting..." : "Send application"
                    )
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "There are no open listings available right now."
          )
    ])
      : null,
    marketSection === "applications"
      ? e("section", { className: "detail-panel", key: "applications" }, [
      e(SectionHeading, {
        title: "My applications",
        copy: "Track application status, captured score snapshots, and any notes returned by the agency.",
        key: "heading"
      }),
      state.applications.length
        ? e(
            "div",
            { className: "list-stack", key: "applications" },
            state.applications.map(function renderApplication(application) {
              return e("article", { className: "stack-card", key: application.id }, [
                e(
                  "strong",
                  { className: "stack-card-title", key: "title" },
                  application.listing_title + " | " + application.organization_name
                ),
                e("div", { className: "status-row", key: "status" }, [
                  e(StatusBadge, {
                    key: "application-status",
                    tone: inferStatusTone(application.application_status),
                    label: application.application_status
                  })
                ]),
                e("div", { className: "fact-grid", key: "score" }, [
                  e(FactPill, {
                    key: "tenant-score",
                    label: "Captured tenant score",
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
                  { key: "note", label: "Agency or applicant notes", tone: "accent" },
                  application.status_notes ||
                    application.applicant_note ||
                    "No notes captured."
                )
              ]);
            })
          )
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "You have not submitted any listing applications yet."
          )
    ])
      : null
  ]);
}
