import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { e } from "../lib/i18n.js";
import { useSession } from "./session.js";

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
  var items = [
    {
      to: "/app",
      label: "Home",
      copy: "Start here and see what to do next"
    }
  ];

  if (session.capabilities.canUsePersonalWorkspace) {
    items.push(
      {
        to: "/app/trust",
        label: "My Trust",
        copy: "Scores, sharing, and trust history"
      },
      {
        to: "/app/marketplace",
        label: "Listings",
        copy: "Browse listings and track applications"
      },
      {
        to: "/app/records",
        label: "Rental Records",
        copy: "Leases, evidence, imports, and references"
      },
      {
        to: "/app/operations",
        label: "Rent & Issues",
        copy: "Payments, deposits, repairs, and disputes"
      }
    );
  }

  if (session.capabilities.canOperateAgency) {
    items.push({
      to: "/app/agency",
      label: "Agency Tools",
      copy: "Properties, screening, assignments, and applications"
    });
  }

  if (session.capabilities.canAccessInternal) {
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
          session.capabilities.canAccessInternal
            ? "Workspace mode: internal review"
            : session.capabilities.canOperateAgency
              ? "Workspace mode: personal + agency"
              : "Workspace mode: personal"
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
          e("h2", { className: "topbar-title", key: "title" }, "Trust Ledger"),
          e(
            "p",
            { className: "topbar-copy-line", key: "copy" },
            "Evidence-backed leasing workflows with cleaner operational lanes."
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
            session.capabilities.canAccessInternal
              ? "Reviewer tools available"
              : session.capabilities.canOperateAgency
                ? "Agency workspace available"
                : "Personal workspace"
          )
        ])
      ]),
      e("section", { className: "app-content", key: "content" }, e(Outlet))
    ])
  ]);
}
