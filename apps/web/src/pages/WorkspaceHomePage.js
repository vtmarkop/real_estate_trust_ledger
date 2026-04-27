import React from "react";
import { Link } from "react-router-dom";

import { apiRequest } from "../lib/api.js";
import { e } from "../lib/i18n.js";
import { useSession } from "../app/session.js";
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
  var organizations = state.organizations;
  var menuGuide = [
    {
      title: "Home",
      copy: "Start here for a quick summary and shortcuts into the rest of the workspace."
    },
    {
      title: "My Trust",
      copy: "See your scores, understand what affects them, and control who can view your shared report."
    },
    {
      title: "Listings",
      copy: "Browse available homes and keep track of the applications you already submitted."
    },
    {
      title: "Rental Records",
      copy: "Manage tenancy history, upload supporting evidence, submit past rental history, and handle references."
    },
    {
      title: "Rent & Issues",
      copy: "Record payments, deposit steps, and maintenance updates for active tenancies."
    },
    {
      title: "Agency Tools",
      copy: "Use this area only if you belong to an agency and need listings, screening, or trust checks."
    },
    {
      title: "Account",
      copy: "Review the devices signed into your account and your recent sign-in activity."
    }
  ];

  if (session.capabilities.canAccessInternal) {
    menuGuide.push({
      title: "Review Center",
      copy: "Internal reviewers and admins use this area for queues, audits, automation, and release checks."
    });
  }

  var workspaceStats = [
    e(HeroStat, {
      key: "tenant-score",
      label: "Tenant score",
      value: String(scoreSummary.tenant_score),
      copy: "Current evidence-backed tenant score."
    }),
    e(HeroStat, {
      key: "verification-strength",
      label: "Verification strength",
      value: String(scoreSummary.verification_strength) + "%",
      copy: "Confidence built from accepted evidence and reviewed history."
    }),
    e(HeroStat, {
      key: "active-memberships",
      label: "Active memberships",
      value: String(organizations.length),
      copy: organizations.length
        ? "Organizations currently connected to this account."
        : "You are currently operating only in the personal workspace."
    })
  ];

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Home",
      title: "Welcome back, " + session.user.full_name + ".",
      copy:
        "This is your starting point. Use the menu on the left to move between your trust profile, rental records, day-to-day tenancy operations, listings, and account tools.",
      details: [
        "The home page is now meant to answer two questions quickly: where am I working, and what should I open next?"
      ],
      actions: [
        session.capabilities.canUsePersonalWorkspace
          ? e(Link, { className: "button", to: "/app/trust", key: "trust" }, "Open My Trust")
          : null,
        session.capabilities.canUsePersonalWorkspace
          ? e(Link, { className: "button button-secondary", to: "/app/marketplace", key: "marketplace" }, "Browse listings")
          : null,
        session.capabilities.canUsePersonalWorkspace
          ? e(Link, { className: "button button-secondary", to: "/app/records", key: "records" }, "Open rental records")
          : null,
        session.capabilities.canOperateAgency
          ? e(Link, { className: "button button-secondary", to: "/app/agency", key: "agency" }, "Open agency tools")
          : null,
        session.capabilities.canAccessInternal
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
      e("article", { className: "detail-panel", key: "trust" }, [
      e(SectionHeading, {
        title: "Trust profile snapshot",
        copy:
          "These are the core personal trust signals that power sharing, screening, and score-aware workflows across the app.",
        key: "heading"
      }),
      e("div", { className: "metric-grid", key: "metrics" }, [
        e("article", { className: "metric-card", key: "tenant" }, [
          e("p", { className: "metric-kicker", key: "kicker" }, "Tenant score"),
          e("strong", { className: "metric-value", key: "value" }, String(scoreSummary.tenant_score)),
          e("p", { className: "metric-copy", key: "copy" }, "Primary score agencies and landlords can eventually review with consent.")
        ]),
        e("article", { className: "metric-card", key: "landlord" }, [
          e("p", { className: "metric-kicker", key: "kicker" }, "Landlord score"),
          e("strong", { className: "metric-value", key: "value" }, String(scoreSummary.landlord_score)),
          e("p", { className: "metric-copy", key: "copy" }, "Separate landlord-side signal so a single account can build trust in both directions.")
        ]),
        e("article", { className: "metric-card", key: "version" }, [
          e("p", { className: "metric-kicker", key: "kicker" }, "Scoring version"),
          e("strong", { className: "metric-value", key: "value" }, scoreSummary.scoring_version.toUpperCase()),
          e("p", { className: "metric-copy", key: "copy" }, "Canonical model version currently powering both self-service and agency-facing score reads.")
        ])
      ])
    ]),
      e("article", { className: "detail-panel", key: "organizations" }, [
      e(SectionHeading, {
        title: "Your active organizations",
        copy:
          "This area shows where your account can act beyond the personal workspace, including agency and internal memberships.",
        key: "heading"
      }),
      organizations.length
        ? e("div", { className: "list-stack", key: "list" }, organizations.map(OrganizationCard))
        : e(
            "p",
            { className: "empty-copy", key: "empty" },
            "No active agency or internal memberships are attached to this account yet."
          )
    ])]),
    session.capabilities.canCreateAgencyWorkspace
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
