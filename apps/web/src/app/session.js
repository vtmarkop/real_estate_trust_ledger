import React from "react";

import { apiRequest } from "../lib/api.js";

var SessionContext = React.createContext(null);
var WORKSPACE_ROLE_STORAGE_KEY = "trustledger.workspace-role";

export var WORKSPACE_ROLE_OPTIONS = [
  {
    id: "tenant",
    label: "Tenant",
    copy: "Renting, applications, payments, maintenance, and tenant-side trust."
  },
  {
    id: "landlord",
    label: "Landlord",
    copy: "Property setup, tenant records, rent collection, deposits, and repairs."
  },
  {
    id: "agency",
    label: "Agent",
    copy: "Agency listings, screening, portfolio work, and trust checks."
  },
  {
    id: "internal",
    label: "Admin",
    copy: "Internal review queues, disputes, runtime controls, and audit work."
  }
];

function readStoredWorkspaceRole() {
  if (typeof window === "undefined") {
    return "tenant";
  }
  return window.localStorage.getItem(WORKSPACE_ROLE_STORAGE_KEY) || "tenant";
}

function persistWorkspaceRole(role) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(WORKSPACE_ROLE_STORAGE_KEY, role);
  }
}

function getWorkspaceRoleOption(role) {
  return (
    WORKSPACE_ROLE_OPTIONS.find(function findRole(option) {
      return option.id === role;
    }) || WORKSPACE_ROLE_OPTIONS[0]
  );
}

export function getWorkspaceRoleLabel(role) {
  return getWorkspaceRoleOption(role).label;
}

export function getWorkspaceRoleCopy(role) {
  return getWorkspaceRoleOption(role).copy;
}

export function isPersonalWorkspaceRole(role) {
  return role === "tenant" || role === "landlord";
}

function getAgencyMemberships(organizations) {
  return (organizations || []).filter(function filterOrganizations(organization) {
    return organization.organization_type === "agency";
  });
}

export function getAvailableWorkspaceRoles(user, organizations) {
  if (!user) {
    return [];
  }

  var assignedRoles = Array.isArray(user.workspace_roles) ? user.workspace_roles.slice() : [];
  if (!assignedRoles.length) {
    if (user.system_role === "reviewer" || user.system_role === "admin") {
      assignedRoles.push("internal");
    } else if (user.system_role === "user") {
      assignedRoles.push("tenant");
    }
  }

  var roles = [];
  var isInternalUser = user.system_role === "reviewer" || user.system_role === "admin";

  ["tenant", "landlord"].forEach(function appendPersonalRole(role) {
    if (assignedRoles.indexOf(role) !== -1) {
      roles.push(role);
    }
  });
  if (assignedRoles.indexOf("agency") !== -1) {
    roles.push("agency");
  }
  if (assignedRoles.indexOf("internal") !== -1 && isInternalUser) {
    roles.push("internal");
  }

  return roles;
}

export function normalizeWorkspaceRole(role, user, organizations) {
  var availableRoles = getAvailableWorkspaceRoles(user, organizations);
  if (!availableRoles.length) {
    return "tenant";
  }
  if (availableRoles.indexOf(role) !== -1) {
    return role;
  }
  return availableRoles[0];
}

export function buildCapabilities(user, organizations, activeWorkspaceRole) {
  if (!user) {
    return {
      isAuthenticated: false,
      activeWorkspaceRole: "tenant",
      availableWorkspaceRoles: [],
      hasAgencyWorkspace: false,
      canOperateAgency: false,
      canManageAgency: false,
      canCreateAgencyWorkspace: false,
      canAccessInternal: false,
      canManagePlatform: false,
      canUsePersonalWorkspace: false,
      organizations: []
    };
  }

  var agencyMemberships = getAgencyMemberships(organizations);
  var canManageAgency = agencyMemberships.some(function canManage(organization) {
    return (
      organization.current_user_membership_role === "owner" ||
      organization.current_user_membership_role === "admin"
    );
  });
  var isInternalUser =
    user.system_role === "reviewer" || user.system_role === "admin";
  var normalizedWorkspaceRole = normalizeWorkspaceRole(activeWorkspaceRole || "tenant", user, organizations);
  var availableWorkspaceRoles = getAvailableWorkspaceRoles(user, organizations);

  return {
    isAuthenticated: true,
    activeWorkspaceRole: normalizedWorkspaceRole,
    availableWorkspaceRoles: availableWorkspaceRoles,
    hasAgencyWorkspace: agencyMemberships.length > 0,
    canOperateAgency: availableWorkspaceRoles.indexOf("agency") !== -1,
    canManageAgency: canManageAgency,
    canCreateAgencyWorkspace:
      availableWorkspaceRoles.indexOf("landlord") !== -1 &&
      agencyMemberships.length === 0,
    canAccessInternal: availableWorkspaceRoles.indexOf("internal") !== -1,
    canManagePlatform:
      user.system_role === "admin" &&
      availableWorkspaceRoles.indexOf("internal") !== -1,
    canUsePersonalWorkspace:
      availableWorkspaceRoles.indexOf("tenant") !== -1 ||
      availableWorkspaceRoles.indexOf("landlord") !== -1,
    organizations: organizations || []
  };
}

export function SessionProvider(props) {
  var children = props.children;
  var stateTuple = React.useState({
    status: "loading",
    user: null,
    organizations: [],
    activeWorkspaceRole: readStoredWorkspaceRole(),
    error: null
  });
  var sessionState = stateTuple[0];
  var setSessionState = stateTuple[1];

  var refreshSession = React.useCallback(async function refreshSession() {
    setSessionState(function updatePrevious(previous) {
      return {
        status: previous.user ? "refreshing" : "loading",
        user: previous.user,
        organizations: previous.organizations,
        activeWorkspaceRole: previous.activeWorkspaceRole,
        error: null
      };
    });

    try {
      var user = await apiRequest("/auth/me");
      var organizations = [];
      try {
        organizations = await apiRequest("/organizations/mine");
      } catch (organizationError) {
        organizations = [];
      }
      var nextWorkspaceRole = normalizeWorkspaceRole(
        readStoredWorkspaceRole(),
        user,
        organizations
      );
      persistWorkspaceRole(nextWorkspaceRole);
      setSessionState({
        status: "authenticated",
        user: user,
        organizations: organizations,
        activeWorkspaceRole: nextWorkspaceRole,
        error: null
      });
      return user;
    } catch (error) {
      if (error && error.status === 401) {
        setSessionState({
          status: "anonymous",
          user: null,
          organizations: [],
          activeWorkspaceRole: readStoredWorkspaceRole(),
          error: null
        });
        return null;
      }

      setSessionState({
        status: "anonymous",
        user: null,
        organizations: [],
        activeWorkspaceRole: readStoredWorkspaceRole(),
        error: error.message || "Unable to restore the current session."
      });
      return null;
    }
  }, []);

  React.useEffect(function bootstrapSession() {
    refreshSession();
  }, [refreshSession]);

  var login = React.useCallback(async function login(payload, options) {
    setSessionState(function updatePrevious(previous) {
      return {
        status: previous.user ? "refreshing" : "loading",
        user: previous.user,
        organizations: previous.organizations,
        activeWorkspaceRole: previous.activeWorkspaceRole,
        error: null
      };
    });

    try {
      var user = await apiRequest("/auth/login", {
        method: "POST",
        body: payload
      });
      var organizations = await apiRequest("/organizations/mine");
      var nextWorkspaceRole = normalizeWorkspaceRole(
        (options && options.workspaceRole) || readStoredWorkspaceRole(),
        user,
        organizations
      );
      persistWorkspaceRole(nextWorkspaceRole);
      setSessionState({
        status: "authenticated",
        user: user,
        organizations: organizations,
        activeWorkspaceRole: nextWorkspaceRole,
        error: null
      });
      return user;
    } catch (error) {
      setSessionState({
        status: "anonymous",
        user: null,
        organizations: [],
        activeWorkspaceRole: readStoredWorkspaceRole(),
        error: error.message || "Unable to sign in."
      });
      throw error;
    }
  }, []);

  var register = React.useCallback(async function register(payload, options) {
    await apiRequest("/auth/register", {
      method: "POST",
      body: payload
    });
    return login({
      email: payload.email,
      password: payload.password
    }, options);
  }, [login]);

  var logout = React.useCallback(async function logout() {
    await apiRequest("/auth/logout", {
      method: "POST"
    });
    setSessionState({
      status: "anonymous",
      user: null,
      organizations: [],
      activeWorkspaceRole: readStoredWorkspaceRole(),
      error: null
    });
  }, []);

  var setActiveWorkspaceRole = React.useCallback(function setWorkspaceRole(role) {
    setSessionState(function updateRole(previous) {
      var nextWorkspaceRole = normalizeWorkspaceRole(role, previous.user, previous.organizations);
      persistWorkspaceRole(nextWorkspaceRole);
      return Object.assign({}, previous, {
        activeWorkspaceRole: nextWorkspaceRole
      });
    });
  }, []);

  var value = React.useMemo(function buildValue() {
    return {
      status: sessionState.status,
      user: sessionState.user,
      organizations: sessionState.organizations,
      activeWorkspaceRole: sessionState.activeWorkspaceRole,
      availableWorkspaceRoles: getAvailableWorkspaceRoles(sessionState.user, sessionState.organizations),
      error: sessionState.error,
      capabilities: buildCapabilities(
        sessionState.user,
        sessionState.organizations,
        sessionState.activeWorkspaceRole
      ),
      refreshSession: refreshSession,
      login: login,
      register: register,
      logout: logout,
      setActiveWorkspaceRole: setActiveWorkspaceRole
    };
  }, [sessionState, refreshSession, login, register, logout, setActiveWorkspaceRole]);

  return React.createElement(
    SessionContext.Provider,
    { value: value },
    children
  );
}

export function useSession() {
  var session = React.useContext(SessionContext);
  if (!session) {
    throw new Error("useSession must be used inside a SessionProvider.");
  }
  return session;
}
