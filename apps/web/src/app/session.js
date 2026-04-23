import React from "react";

import { apiRequest } from "../lib/api.js";

var SessionContext = React.createContext(null);

export function buildCapabilities(user, organizations) {
  if (!user) {
    return {
      isAuthenticated: false,
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

  var agencyMemberships = (organizations || []).filter(function filterOrganizations(organization) {
    return organization.organization_type === "agency";
  });
  var canManageAgency = agencyMemberships.some(function canManage(organization) {
    return (
      organization.current_user_membership_role === "owner" ||
      organization.current_user_membership_role === "admin"
    );
  });
  var canOperateAgency = agencyMemberships.some(function canOperate(organization) {
    return ["owner", "admin", "agent"].indexOf(organization.current_user_membership_role) !== -1;
  });
  var isInternalUser =
    user.system_role === "reviewer" || user.system_role === "admin";

  return {
    isAuthenticated: true,
    hasAgencyWorkspace: agencyMemberships.length > 0,
    canOperateAgency: canOperateAgency,
    canManageAgency: canManageAgency,
    canCreateAgencyWorkspace: user.system_role === "user" && agencyMemberships.length === 0,
    canAccessInternal: isInternalUser,
    canManagePlatform: user.system_role === "admin",
    canUsePersonalWorkspace: user.system_role === "user",
    organizations: organizations || []
  };
}

export function SessionProvider(props) {
  var children = props.children;
  var stateTuple = React.useState({
    status: "loading",
    user: null,
    organizations: [],
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
      setSessionState({
        status: "authenticated",
        user: user,
        organizations: organizations,
        error: null
      });
      return user;
    } catch (error) {
      if (error && error.status === 401) {
        setSessionState({
          status: "anonymous",
          user: null,
          organizations: [],
          error: null
        });
        return null;
      }

      setSessionState({
        status: "anonymous",
        user: null,
        organizations: [],
        error: error.message || "Unable to restore the current session."
      });
      return null;
    }
  }, []);

  React.useEffect(function bootstrapSession() {
    refreshSession();
  }, [refreshSession]);

  var login = React.useCallback(async function login(payload) {
    setSessionState(function updatePrevious(previous) {
      return {
        status: previous.user ? "refreshing" : "loading",
        user: previous.user,
        organizations: previous.organizations,
        error: null
      };
    });

    try {
      var user = await apiRequest("/auth/login", {
        method: "POST",
        body: payload
      });
      var organizations = await apiRequest("/organizations/mine");
      setSessionState({
        status: "authenticated",
        user: user,
        organizations: organizations,
        error: null
      });
      return user;
    } catch (error) {
      setSessionState({
        status: "anonymous",
        user: null,
        organizations: [],
        error: error.message || "Unable to sign in."
      });
      throw error;
    }
  }, []);

  var register = React.useCallback(async function register(payload) {
    await apiRequest("/auth/register", {
      method: "POST",
      body: payload
    });
    return login({
      email: payload.email,
      password: payload.password
    });
  }, [login]);

  var logout = React.useCallback(async function logout() {
    await apiRequest("/auth/logout", {
      method: "POST"
    });
    setSessionState({
      status: "anonymous",
      user: null,
      organizations: [],
      error: null
    });
  }, []);

  var value = React.useMemo(function buildValue() {
    return {
      status: sessionState.status,
      user: sessionState.user,
      organizations: sessionState.organizations,
      error: sessionState.error,
      capabilities: buildCapabilities(sessionState.user, sessionState.organizations),
      refreshSession: refreshSession,
      login: login,
      register: register,
      logout: logout
    };
  }, [sessionState, refreshSession, login, register, logout]);

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
