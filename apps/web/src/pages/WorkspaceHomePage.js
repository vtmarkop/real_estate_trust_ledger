import React from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "../lib/api.js";
import { e } from "../lib/i18n.js";
import { getWorkspaceRoleLabel, isPersonalWorkspaceRole, useSession } from "../app/session.js";
import {
  FactPill,
  HeroStat,
  NoteBlock,
  PageHero,
  SectionHeading,
  StatusBadge
} from "../components/PageChrome.js";

function formatLabel(value) {
  return String(value || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, function capitalize(character) {
      return character.toUpperCase();
    });
}

function buildAgencySlug(value) {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 120);
}

function MenuGuideCard(props) {
  return e("article", { className: "stack-card" }, [
    e("strong", { className: "stack-card-title", key: "title" }, props.title),
    e(NoteBlock, { key: "copy", label: "What this area is for", tone: "accent" }, props.copy)
  ]);
}

function OrganizationCard(organization) {
  return e("article", { className: "stack-card", key: organization.id }, [
    e("strong", { className: "stack-card-title", key: "name" }, organization.name),
    e("div", { className: "status-row", key: "badges" }, [
      e(StatusBadge, {
        key: "type",
        tone: "accent",
        label: formatLabel(organization.organization_type) + " organization"
      }),
      e(StatusBadge, {
        key: "role",
        tone: "success",
        label: "Role: " + formatLabel(organization.current_user_membership_role || "member")
      })
    ]),
    e("div", { className: "fact-grid", key: "facts" }, [
      e(FactPill, { key: "name", label: "Workspace", value: organization.name }),
      e(FactPill, {
        key: "membership",
        label: "Membership",
        value: formatLabel(organization.current_user_membership_role || "member")
      })
    ])
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

function isStandaloneDisplayMode() {
  if (typeof window === "undefined") {
    return false;
  }

  if (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) {
    return true;
  }

  return Boolean(window.navigator && window.navigator.standalone);
}

export function WorkspaceHomePage() {
  var session = useSession();
  var stateTuple = React.useState({
    status: "loading",
    scoreSummary: null,
    organizations: [],
    error: null
  });
  var state = stateTuple[0];
  var setState = stateTuple[1];
  var installTuple = React.useState({
    available: Boolean(typeof window !== "undefined" && window.__trustLedgerInstallPrompt),
    installed: isStandaloneDisplayMode(),
    prompting: false,
    message: null
  });
  var installState = installTuple[0];
  var setInstallState = installTuple[1];
  var agencyFormTuple = React.useState({
    name: "",
    slug: ""
  });
  var agencyForm = agencyFormTuple[0];
  var setAgencyForm = agencyFormTuple[1];
  var agencyActionTuple = React.useState({
    isSubmitting: false,
    message: null
  });
  var agencyAction = agencyActionTuple[0];
  var setAgencyAction = agencyActionTuple[1];

  var loadWorkspaceState = React.useCallback(async function loadWorkspaceState() {
    setState(function setLoading(previous) {
      return {
        status: previous.scoreSummary || previous.organizations.length ? "refreshing" : "loading",
        scoreSummary: previous.scoreSummary,
        organizations: previous.organizations,
        error: null
      };
    });

    try {
      var results = await Promise.all([
        apiRequest("/trust-scores/mine"),
        apiRequest("/organizations/mine")
      ]);
      setState({
        status: "ready",
        scoreSummary: results[0],
        organizations: results[1],
        error: null
      });
    } catch (error) {
      setState({
        status: "error",
        scoreSummary: null,
        organizations: [],
        error: error.message || "Unable to load workspace data."
      });
    }
  }, []);

  React.useEffect(function bootstrapWorkspaceState() {
    loadWorkspaceState();
  }, [loadWorkspaceState]);

  React.useEffect(function bindInstallEvents() {
    if (typeof window === "undefined") {
      return undefined;
    }

    function markAvailable() {
      setInstallState(function updateState(previous) {
        return Object.assign({}, previous, {
          available: true,
          message: "Install is available in this browser for faster repeat access."
        });
      });
    }

    function markInstalled() {
      setInstallState({
        available: false,
        installed: true,
        prompting: false,
        message: "Trust Ledger is now installed on this device."
      });
    }

    window.addEventListener("trustledger:install-available", markAvailable);
    window.addEventListener("trustledger:installed", markInstalled);

    return function cleanupInstallEvents() {
      window.removeEventListener("trustledger:install-available", markAvailable);
      window.removeEventListener("trustledger:installed", markInstalled);
    };
  }, []);

  async function handleInstall() {
    if (typeof window === "undefined" || !window.__trustLedgerInstallPrompt) {
      setInstallState(function updateUnavailable(previous) {
        return Object.assign({}, previous, {
          available: false,
          message: "This browser is not currently offering an install prompt."
        });
      });
      return;
    }

    setInstallState(function updatePrompting(previous) {
      return Object.assign({}, previous, { prompting: true, message: null });
    });

    try {
      window.__trustLedgerInstallPrompt.prompt();
      if (window.__trustLedgerInstallPrompt.userChoice) {
        await window.__trustLedgerInstallPrompt.userChoice;
      }
      setInstallState(function afterPrompt(previous) {
        return Object.assign({}, previous, {
          available: Boolean(window.__trustLedgerInstallPrompt),
          prompting: false,
          message: previous.installed
            ? previous.message
            : "Install prompt completed. If the app was not installed, the browser may have dismissed it."
        });
      });
    } catch (error) {
      setInstallState(function updateError(previous) {
        return Object.assign({}, previous, {
          prompting: false,
          message: error.message || "Unable to trigger the install prompt."
        });
      });
    }
  }

  async function handleAgencyCreate(event) {
    event.preventDefault();
    setAgencyAction({
      isSubmitting: true,
      message: null
    });

    try {
      await apiRequest("/organizations", {
        method: "POST",
        body: {
          name: agencyForm.name,
          slug: agencyForm.slug,
          organization_type: "agency"
        }
      });
      setAgencyForm({
        name: "",
        slug: ""
      });
      await session.refreshSession();
      await loadWorkspaceState();
      setAgencyAction({
        isSubmitting: false,
        message: "Agency workspace created. The agency tools tab is now available."
      });
    } catch (error) {
      setAgencyAction({
        isSubmitting: false,
        message: error.message || "Unable to create the agency workspace."
      });
    }
  }

  if (state.status === "loading") {
    return e("div", { className: "state-panel" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Home"),
      e("h1", { className: "state-title", key: "title" }, "Loading your trust workspace"),
      e(
        "p",
        { className: "state-copy", key: "copy" },
        "We are restoring your score snapshot and organization memberships from the rebuilt API."
      )
    ]);
  }

  if (state.status === "error") {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Home"),
      e("h1", { className: "state-title", key: "title" }, "Workspace data unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  var scoreSummary = state.scoreSummary;
  var activeWorkspaceRole = session.activeWorkspaceRole || "tenant";
  var activeWorkspaceLabel = getWorkspaceRoleLabel(activeWorkspaceRole);
  var isLandlordWorkspace = activeWorkspaceRole === "landlord";
  var isTenantWorkspace = activeWorkspaceRole === "tenant";
  var isAgencyWorkspace = activeWorkspaceRole === "agency";
  var isInternalWorkspace = activeWorkspaceRole === "internal";
  var isPersonalWorkspace = isPersonalWorkspaceRole(activeWorkspaceRole);
  var landlordSideActive = hasLandlordSideSignals(scoreSummary);
  var organizations = state.organizations;
  var menuGuide = [
    {
      title: "Home",
      copy: "Start here for a quick summary and shortcuts into the rest of the workspace."
    }
  ];

  if (isTenantWorkspace || isLandlordWorkspace) {
    menuGuide.push(
      {
        title: isLandlordWorkspace ? "Landlord Trust" : "Tenant Trust",
        copy: isLandlordWorkspace
          ? "See your landlord-side score, inputs, sharing, and score history."
          : "See your tenant-side score, sharing controls, and trust history."
      },
      isTenantWorkspace
        ? {
            title: "Listings",
            copy: "Browse available homes and keep track of the applications you already submitted."
          }
        : null,
      {
        title: "Rental Records",
        copy: isLandlordWorkspace
          ? "Manage properties, tenant records, landlord evidence, and references."
          : "Manage tenancy records, tenant evidence, imports, and references."
      },
      {
        title: "Rent & Issues",
        copy: isLandlordWorkspace
          ? "Handle rent collection, deposits, repair responses, and disputes."
          : "Handle rent payments, deposits, maintenance requests, and disputes."
      }
    );
  }

  if (isAgencyWorkspace) {
    menuGuide.push({
      title: "Agency Tools",
      copy: "Use this area for listings, screening, portfolio work, and agency trust checks."
    });
  }

  if (isInternalWorkspace) {
    menuGuide.push({
      title: "Review Center",
      copy: "Internal reviewers and admins use this area for queues, audits, automation, and release checks."
    });
  }

  menuGuide.push({
    title: "Account",
    copy: "Review the devices signed into your account and your recent sign-in activity."
  });

  menuGuide = menuGuide.filter(Boolean);

  var workspaceStats = isPersonalWorkspace
    ? [
        e(HeroStat, {
          key: "role-score",
          label: isLandlordWorkspace ? "Landlord score" : "Tenant score",
          value: String(isLandlordWorkspace ? scoreSummary.landlord_score : scoreSummary.tenant_score),
          copy: isLandlordWorkspace
            ? "Current property-owner trust score."
            : "Current evidence-backed renter score."
        }),
        e(HeroStat, {
          key: "verification-strength",
          label: "Verification strength",
          value: String(scoreSummary.verification_strength) + "%",
          copy: "Confidence built from accepted evidence and reviewed history."
        }),
        e(HeroStat, {
          key: "active-mode",
          label: "Active role",
          value: activeWorkspaceLabel,
          copy: "Menus and records are filtered for this role."
        })
      ]
    : [
        e(HeroStat, {
          key: "active-mode",
          label: "Active role",
          value: activeWorkspaceLabel,
          copy: "Menus and records are filtered for this role."
        }),
        e(HeroStat, {
          key: "active-memberships",
          label: isAgencyWorkspace ? "Agency memberships" : "Internal access",
          value: isAgencyWorkspace ? String(organizations.length) : "Enabled",
          copy: isAgencyWorkspace
            ? "Agency organizations connected to this account."
            : "Reviewer/admin tools are available in this workspace mode."
        })
      ];

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Home",
      title: activeWorkspaceLabel + " home for " + session.user.full_name + ".",
      copy:
        isLandlordWorkspace
          ? "This view is scoped to landlord-side property, tenant, rent, deposit, repair, and score work."
          : isTenantWorkspace
            ? "This view is scoped to tenant-side applications, records, rent, maintenance, and score work."
            : isAgencyWorkspace
              ? "This view is scoped to agency portfolio, listing, screening, and application work."
              : "This view is scoped to internal review, disputes, automation, runtime, and audit work.",
      details: [
        "The home page is now meant to answer two questions quickly: where am I working, and what should I open next?"
      ],
      actions: [
        isPersonalWorkspace
          ? e(Link, { className: "button", to: "/app/trust", key: "trust" }, isLandlordWorkspace ? "Open landlord trust" : "Open tenant trust")
          : null,
        isTenantWorkspace
          ? e(Link, { className: "button button-secondary", to: "/app/marketplace", key: "marketplace" }, "Browse listings")
          : null,
        isPersonalWorkspace
          ? e(Link, { className: "button button-secondary", to: "/app/records", key: "records" }, "Open rental records")
          : null,
        isAgencyWorkspace
          ? e(Link, { className: "button button-secondary", to: "/app/agency", key: "agency" }, "Open agency tools")
          : null,
        isInternalWorkspace
          ? e(Link, { className: "button button-secondary", to: "/app/internal", key: "internal" }, "Open review center")
          : null
      ],
      stats: workspaceStats
    }),
    e("section", { className: "split-grid", key: "home-start" }, [
      e("article", { className: "detail-panel install-panel", key: "install" }, [
      e(SectionHeading, {
        title: "Installable workspace",
        copy:
          "Keep this workspace available like an app shell on supported browsers so repeat access feels faster and more focused.",
        key: "heading"
      }),
      e(
        "p",
        { className: "empty-copy", key: "copy" },
        installState.installed
          ? "This device is already running the workspace in installed mode."
          : "The rebuilt web app now exposes a manifest and service worker so supported browsers can offer an install flow for quicker repeat access."
      ),
      e("div", { className: "action-row", key: "actions" }, [
        installState.installed
          ? e(StatusBadge, { tone: "success", label: "Installed", key: "installed" })
          : e(
              "button",
              {
                type: "button",
                className: "button button-secondary",
                disabled: installState.prompting || !installState.available,
                onClick: handleInstall,
                key: "install-button"
              },
              installState.prompting ? "Opening install..." : "Install app shell"
            ),
        e(StatusBadge, { tone: "accent", label: "Mobile-ready shell", key: "mobile" })
      ]),
      installState.message
        ? e(NoteBlock, { key: "message", label: "Install status", tone: "accent" }, installState.message)
        : null
    ]),
      e("article", { className: "detail-panel", key: "menu-guide" }, [
      e(SectionHeading, {
        title: "What each menu item does",
        copy:
          "If the menu feels unfamiliar, use this as a quick map. Each area is focused on one part of the rental journey.",
        key: "heading"
      }),
      e(
        "div",
        { className: "summary-grid", key: "items" },
        menuGuide.map(function renderMenuGuide(item) {
          return e(MenuGuideCard, {
            title: item.title,
            copy: item.copy,
            key: item.title
          });
        })
      )
    ])]),
    e("section", { className: "split-grid", key: "trust-and-orgs" }, [
      isPersonalWorkspace
        ? e("article", { className: "detail-panel", key: "trust" }, [
      e(SectionHeading, {
        title: isLandlordWorkspace ? "Landlord trust snapshot" : "Tenant trust snapshot",
        copy:
          isLandlordWorkspace
            ? "This panel only shows the score dimension for your landlord/property-owner role."
            : "This panel only shows the score dimension for your renter role.",
        key: "heading"
      }),
      e("div", { className: "metric-grid", key: "metrics" }, [
        e("article", { className: "metric-card", key: "role-score" }, [
          e(
            "p",
            { className: "metric-kicker", key: "kicker" },
            isLandlordWorkspace
              ? landlordSideActive
                ? "Your landlord-side score"
                : "Landlord-side score inactive"
              : "Tenant score"
          ),
          e("strong", { className: "metric-value", key: "value" }, String(isLandlordWorkspace ? scoreSummary.landlord_score : scoreSummary.tenant_score)),
          e(
            "p",
            { className: "metric-copy", key: "copy" },
            isLandlordWorkspace
              ? landlordSideActive
                ? "Your score for records where you act as a landlord or property owner."
                : "This landlord-side score stays neutral until you rent out property."
              : "Your score for records where you act as a renter."
          )
        ]),
        e("article", { className: "metric-card", key: "version" }, [
          e("p", { className: "metric-kicker", key: "kicker" }, "Scoring version"),
          e("strong", { className: "metric-value", key: "value" }, scoreSummary.scoring_version.toUpperCase()),
          e("p", { className: "metric-copy", key: "copy" }, "Canonical model version currently powering both self-service and agency-facing score reads.")
        ])
      ])
    ])
        : null,
      isAgencyWorkspace || isInternalWorkspace
        ? e("article", { className: "detail-panel", key: "organizations" }, [
      e(SectionHeading, {
        title: isAgencyWorkspace ? "Your agency organizations" : "Internal workspace context",
        copy:
          isAgencyWorkspace
            ? "This area shows the agencies where this account can operate."
            : "This area stays away from personal rental info while you are in reviewer mode.",
        key: "heading"
      }),
      organizations.length
        ? e("div", { className: "list-stack", key: "list" }, organizations.map(OrganizationCard))
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No active agency or internal memberships are attached to this account yet."
          )
    ])
        : null
    ].filter(Boolean)),
    session.capabilities.canCreateAgencyWorkspace && isLandlordWorkspace
      ? e("section", { className: "detail-panel", key: "agency-create" }, [
          e(SectionHeading, {
            title: "Create an agency workspace",
            copy:
              "If you also work as a real estate operator, create an agency workspace here so you can manage properties, listings, applicants, and trust checks from the same account.",
            key: "heading"
          }),
          e(
            "form",
            { className: "auth-form", onSubmit: handleAgencyCreate, key: "form" },
            [
              e("div", { className: "form-grid", key: "grid" }, [
                e("label", { className: "field", key: "name" }, [
                  e("span", { className: "field-label", key: "label" }, "Agency name"),
                  e("input", {
                    className: "field-input",
                    value: agencyForm.name,
                    onChange: function onChange(event) {
                      var nextName = event.target.value;
                      setAgencyForm(function update(previous) {
                        return {
                          name: nextName,
                          slug: previous.slug || !previous.name ? buildAgencySlug(nextName) : previous.slug
                        };
                      });
                    },
                    placeholder: "Blue Key Realty",
                    required: true
                  })
                ]),
                e("label", { className: "field", key: "slug" }, [
                  e("span", { className: "field-label", key: "label" }, "Workspace slug"),
                  e("input", {
                    className: "field-input",
                    value: agencyForm.slug,
                    onChange: function onChange(event) {
                      setAgencyForm(function update(previous) {
                        return Object.assign({}, previous, {
                          slug: buildAgencySlug(event.target.value)
                        });
                      });
                    },
                    placeholder: "blue-key-realty",
                    required: true
                  })
                ])
              ]),
              agencyAction.message
                ? e("div", { className: "form-alert", key: "message" }, agencyAction.message)
                : null,
              e(
                "button",
                {
                  type: "submit",
                  className: "button",
                  disabled: agencyAction.isSubmitting,
                  key: "submit"
                },
                agencyAction.isSubmitting ? "Creating workspace..." : "Create agency workspace"
              )
            ]
          )
        ])
      : null
  ]);
}
