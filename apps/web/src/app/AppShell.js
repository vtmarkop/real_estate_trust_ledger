import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { e } from "../lib/i18n.js";
import {
  getWorkspaceRoleCopy,
  getWorkspaceRoleLabel,
  isPersonalWorkspaceRole,
  useSession
} from "./session.js";

var DENSITY_STORAGE_KEY = "trustledger.workspace-density";

function formatRoleLabel(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/_/g, " ")
    .replace(/\b\w/g, function capitalize(character) {
      return character.toUpperCase();
    });
}

export function normalizeDensity(value) {
  return value === "compact" ? "compact" : "comfortable";
}

export function resolveInitialDensity() {
  if (typeof window === "undefined") {
    return "comfortable";
  }

  return normalizeDensity(window.localStorage.getItem(DENSITY_STORAGE_KEY));
}

export function buildNavigation(session) {
  var activeWorkspaceRole = session.activeWorkspaceRole || "tenant";
  var items = [
    {
      to: "/app",
      label: "Home",
      copy: "Start here and see what to do next"
    }
  ];

  if (session.capabilities.canUsePersonalWorkspace && isPersonalWorkspaceRole(activeWorkspaceRole)) {
    items.push(
      {
        to: "/app/trust",
        label: activeWorkspaceRole === "landlord" ? "Landlord Trust" : "Tenant Trust",
        copy:
          activeWorkspaceRole === "landlord"
            ? "Your property-owner score, inputs, and sharing"
            : "Your renter score, sharing, and trust history"
      },
      {
        to: "/app/records",
        label: "Rental Records",
        copy:
          activeWorkspaceRole === "landlord"
            ? "Properties, tenant records, evidence, and references"
            : "Tenancy records, evidence, imports, and references"
      },
      {
        to: "/app/operations",
        label: "Rent & Issues",
        copy:
          activeWorkspaceRole === "landlord"
            ? "Rent collection, deposits, repairs, and disputes"
            : "Payments, deposits, repairs, and disputes"
      }
    );
  }

  if (session.capabilities.canUsePersonalWorkspace && activeWorkspaceRole === "tenant") {
    items.splice(2, 0, {
      to: "/app/marketplace",
      label: "Listings",
      copy: "Browse listings and track applications"
    });
  }

  if (session.capabilities.canOperateAgency && activeWorkspaceRole === "agency") {
    items.push({
      to: "/app/agency",
      label: "Agency Tools",
      copy: "Properties, screening, assignments, and applications"
    });
  }

  if (session.capabilities.canAccessInternal && activeWorkspaceRole === "internal") {
    items.push({
      to: "/app/internal",
      label: "Review Center",
      copy: "Reviews, disputes, automation, audits, and system health"
    });
  }

  items.push({
    to: "/app/security",
    label: "Account",
    copy: "Sessions and sign-in activity"
  });

  return items;
}

function NavigationLink(item) {
  return e(
    NavLink,
    {
      key: item.to,
      to: item.to,
      className: function classNameResolver(navState) {
        return navState.isActive ? "shell-nav is-active" : "shell-nav";
      }
    },
    [
      e("span", { className: "shell-nav-label", key: item.to + "-label" }, item.label),
      e("span", { className: "shell-nav-copy", key: item.to + "-copy" }, item.copy)
    ]
  );
}

export function AppShell() {
  var session = useSession();
  var navigate = useNavigate();
  var logoutState = React.useState(false);
  var isLoggingOut = logoutState[0];
  var setIsLoggingOut = logoutState[1];
  var densityTuple = React.useState(resolveInitialDensity);
  var density = densityTuple[0];
  var setDensity = densityTuple[1];
  var navigation = buildNavigation(session);
  var activeWorkspaceRole = session.activeWorkspaceRole || "tenant";
  var activeWorkspaceLabel = getWorkspaceRoleLabel(activeWorkspaceRole);
  var activeWorkspaceCopy = getWorkspaceRoleCopy(activeWorkspaceRole);

  React.useEffect(function syncDensityPreference() {
    if (typeof window === "undefined" || typeof document === "undefined") {
      return undefined;
    }

    var normalizedDensity = normalizeDensity(density);
    window.localStorage.setItem(DENSITY_STORAGE_KEY, normalizedDensity);
    document.documentElement.setAttribute("data-density", normalizedDensity);

    return function cleanupDensityPreference() {
      if (document.documentElement.getAttribute("data-density") === normalizedDensity) {
        document.documentElement.removeAttribute("data-density");
      }
    };
  }, [density]);

  async function handleLogout() {
    setIsLoggingOut(true);
    try {
      await session.logout();
      navigate("/");
    } finally {
      setIsLoggingOut(false);
    }
  }

  function handleWorkspaceRoleChange(event) {
    session.setActiveWorkspaceRole(event.target.value);
    navigate("/app");
  }

  return e("div", { className: "app-shell", "data-density": density }, [
    e("aside", { className: "app-sidebar", key: "sidebar" }, [
      e("div", { className: "brand-lockup", key: "brand" }, [
        e("div", { className: "brand-mark", key: "mark" }, "TL"),
        e("div", { className: "brand-copy", key: "copy" }, [
          e("p", { className: "eyebrow", key: "eyebrow" }, "Trust Ledger"),
          e("h1", { className: "brand-title", key: "title" }, "Web Workspace")
        ])
      ]),
      e("nav", { className: "shell-nav-list", key: "nav" }, navigation.map(NavigationLink)),
      e("div", { className: "sidebar-foot", key: "foot" }, [
        e("p", { className: "sidebar-user-name", key: "name" }, session.user.full_name),
        session.availableWorkspaceRoles.length > 1
          ? e("label", { className: "workspace-role-switch", key: "role-switch" }, [
              e("span", { className: "sidebar-user-role", key: "label" }, "Active role"),
              e(
                "select",
                {
                  className: "workspace-role-select",
                  value: activeWorkspaceRole,
                  onChange: handleWorkspaceRoleChange
                },
                session.availableWorkspaceRoles.map(function renderRole(role) {
                  return e(
                    "option",
                    { value: role, key: role },
                    getWorkspaceRoleLabel(role)
                  );
                })
              )
            ])
          : e(
              "p",
              { className: "sidebar-user-role", key: "single-role" },
              "Active role: " + activeWorkspaceLabel
            ),
        e(
          "p",
          { className: "sidebar-user-role", key: "role" },
          "Access level: " + formatRoleLabel(session.user.system_role)
        ),
        session.capabilities.canOperateAgency
          ? e(
              "p",
              { className: "sidebar-user-role", key: "agency-role" },
              "Agency access: " +
                String(session.organizations.filter(function onlyAgencies(organization) {
                  return organization.organization_type === "agency";
                }).length)
            )
          : null,
        e(
          "p",
          { className: "sidebar-user-role", key: "workspace-kind" },
          "Workspace mode: " + activeWorkspaceLabel
        ),
        e(
          "button",
          {
            type: "button",
            className: "button button-secondary",
            disabled: isLoggingOut,
            onClick: handleLogout,
            key: "logout"
          },
          isLoggingOut ? "Signing out..." : "Sign out"
        )
      ])
    ]),
    e("main", { className: "app-main", key: "main" }, [
      e("header", { className: "app-topbar", key: "topbar" }, [
        e("div", { className: "topbar-copy", key: "topbar-copy" }, [
          e("p", { className: "eyebrow", key: "eyebrow" }, "Workspace"),
          e("h2", { className: "topbar-title", key: "title" }, activeWorkspaceLabel + " workspace"),
          e(
            "p",
            { className: "topbar-copy-line", key: "copy" },
            activeWorkspaceCopy
          )
        ]),
        e("div", { className: "topbar-controls", key: "controls" }, [
          e("div", { className: "density-switch", key: "density" }, [
            e("span", { className: "density-label", key: "label" }, "Density"),
            e(
              "button",
              {
                type: "button",
                className:
                  density === "comfortable"
                    ? "density-button is-active"
                    : "density-button",
                onClick: function onClick() {
                  setDensity("comfortable");
                },
                key: "comfortable"
              },
              "Comfort"
            ),
            e(
              "button",
              {
                type: "button",
                className:
                  density === "compact" ? "density-button is-active" : "density-button",
                onClick: function onClick() {
                  setDensity("compact");
                },
                key: "compact"
              },
              "Compact"
            )
          ]),
          e(
            "div",
            { className: "status-chip", key: "status" },
            "Showing " + activeWorkspaceLabel.toLowerCase() + " info only"
          )
        ])
      ]),
      e("section", { className: "app-content", key: "content" }, e(Outlet))
    ])
  ]);
}
