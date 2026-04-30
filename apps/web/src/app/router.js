import React from "react";
import {
  Navigate,
  Outlet,
  createBrowserRouter,
  useLocation
} from "react-router-dom";

import { e } from "../lib/i18n.js";
import { AppShell } from "./AppShell.js";
import { isPersonalWorkspaceRole, useSession } from "./session.js";
import { AuthPage } from "../pages/AuthPage.js";
import { LandingPage } from "../pages/LandingPage.js";
import { NotFoundPage } from "../pages/NotFoundPage.js";
import { SecurityPage } from "../pages/SecurityPage.js";

var WorkspaceHomePage = React.lazy(function loadWorkspaceHomePage() {
  return import("../pages/WorkspaceHomePage.js").then(function resolveModule(module) {
    return { default: module.WorkspaceHomePage };
  });
});
var TrustProfilePage = React.lazy(function loadTrustProfilePage() {
  return import("../pages/TrustProfilePage.js").then(function resolveModule(module) {
    return { default: module.TrustProfilePage };
  });
});
var MarketplacePage = React.lazy(function loadMarketplacePage() {
  return import("../pages/MarketplacePage.js").then(function resolveModule(module) {
    return { default: module.MarketplacePage };
  });
});
var RecordsPage = React.lazy(function loadRecordsPage() {
  return import("../pages/RecordsPage.js").then(function resolveModule(module) {
    return { default: module.RecordsPage };
  });
});
var OperationsPage = React.lazy(function loadOperationsPage() {
  return import("../pages/OperationsPage.js").then(function resolveModule(module) {
    return { default: module.OperationsPage };
  });
});
var AgencyWorkbenchPage = React.lazy(function loadAgencyWorkbenchPage() {
  return import("../pages/AgencyWorkbenchPage.js").then(function resolveModule(module) {
    return { default: module.AgencyWorkbenchPage };
  });
});
var InternalOperationsPage = React.lazy(function loadInternalOperationsPage() {
  return import("../pages/InternalOperationsPage.js").then(function resolveModule(module) {
    return { default: module.InternalOperationsPage };
  });
});

function LoadingScreen() {
  return e("div", { className: "state-panel" }, [
    e("p", { className: "eyebrow", key: "eyebrow" }, "Trust Ledger"),
    e("h2", { className: "state-title", key: "title" }, "Restoring session"),
    e(
      "p",
      { className: "state-copy", key: "copy" },
      "We are checking your sign-in status before opening the workspace."
    )
  ]);
}

function LazyRoute(props) {
  return React.createElement(
    React.Suspense,
    { fallback: e(LoadingScreen) },
    e(props.component, props.componentProps)
  );
}

function RequireAuth() {
  var session = useSession();
  var location = useLocation();

  if (session.status === "loading" || session.status === "refreshing") {
    return e(LoadingScreen);
  }

  if (!session.capabilities.isAuthenticated) {
    return e(Navigate, {
      to: "/login",
      replace: true,
      state: { from: location.pathname }
    });
  }

  return e(Outlet);
}

function RequireInternalAccess() {
  var session = useSession();

  if (!session.capabilities.canAccessInternal || session.activeWorkspaceRole !== "internal") {
    return e(Navigate, {
      to: "/app",
      replace: true
    });
  }

  return e(Outlet);
}

function RequireAgencyAccess() {
  var session = useSession();

  if (!session.capabilities.canOperateAgency || session.activeWorkspaceRole !== "agency") {
    return e(Navigate, {
      to: "/app",
      replace: true
    });
  }

  return e(Outlet);
}

function RequirePersonalWorkspace() {
  var session = useSession();

  if (!session.capabilities.canUsePersonalWorkspace || !isPersonalWorkspaceRole(session.activeWorkspaceRole)) {
    return e(Navigate, {
      to: "/app",
      replace: true
    });
  }

  return e(Outlet);
}

function TenantMarketplaceRoute() {
  var session = useSession();

  if (!session.capabilities.canUsePersonalWorkspace || session.activeWorkspaceRole !== "tenant") {
    return e(Navigate, {
      to: "/app",
      replace: true
    });
  }

  return e(LazyRoute, { component: MarketplacePage });
}

function RedirectAuthenticatedHome() {
  var session = useSession();

  if (session.status === "loading" || session.status === "refreshing") {
    return e(LoadingScreen);
  }

  if (session.capabilities.isAuthenticated) {
    return e(Navigate, {
      to: "/app",
      replace: true
    });
  }

  return e(Outlet);
}

export function createAppRouter() {
  return createBrowserRouter([
    {
      path: "/",
      element: e(RedirectAuthenticatedHome),
      children: [
        {
          index: true,
          element: e(LandingPage)
        },
        {
          path: "login",
          element: e(AuthPage, { mode: "login" })
        },
        {
          path: "register",
          element: e(AuthPage, { mode: "register" })
        }
      ]
    },
    {
      path: "/app",
      element: e(RequireAuth),
      children: [
        {
          element: e(AppShell),
          children: [
            {
              index: true,
              element: e(LazyRoute, { component: WorkspaceHomePage })
            },
            {
              element: e(RequirePersonalWorkspace),
              children: [
                {
                  path: "trust",
                  element: e(LazyRoute, { component: TrustProfilePage })
                },
                {
                  path: "marketplace",
                  element: e(TenantMarketplaceRoute)
                },
                {
                  path: "records",
                  element: e(LazyRoute, { component: RecordsPage })
                },
                {
                  path: "operations",
                  element: e(LazyRoute, { component: OperationsPage })
                }
              ]
            },
            {
              path: "security",
              element: e(SecurityPage)
            },
            {
              element: e(RequireAgencyAccess),
              children: [
                {
                  path: "agency",
                  element: e(LazyRoute, { component: AgencyWorkbenchPage })
                }
              ]
            },
            {
              element: e(RequireInternalAccess),
              children: [
                {
                  path: "internal",
                  element: e(LazyRoute, { component: InternalOperationsPage })
                }
              ]
            }
          ]
        }
      ]
    },
    {
      path: "*",
      element: e(NotFoundPage)
    }
  ]);
}
