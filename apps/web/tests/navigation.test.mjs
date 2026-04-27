import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCapabilities,
  getAvailableWorkspaceRoles,
  normalizeWorkspaceRole
} from "../src/app/session.js";
import { buildNavigation, normalizeDensity } from "../src/app/AppShell.js";

test("buildCapabilities exposes agency and internal access separately", function () {
  const user = {
    system_role: "reviewer",
    workspace_roles: ["agency", "internal"]
  };
  const organizations = [
    {
      organization_type: "agency",
      current_user_membership_role: "agent"
    }
  ];

  const capabilities = buildCapabilities(user, organizations);
  assert.equal(capabilities.canAccessInternal, true);
  assert.equal(capabilities.canOperateAgency, true);
  assert.equal(capabilities.canManageAgency, false);
});

test("buildCapabilities keeps personal workspace tabs for users who also belong to an agency", function () {
  const user = {
    system_role: "user",
    workspace_roles: ["tenant", "agency"]
  };
  const organizations = [
    {
      organization_type: "agency",
      current_user_membership_role: "owner"
    }
  ];

  const capabilities = buildCapabilities(user, organizations);
  assert.equal(capabilities.canUsePersonalWorkspace, true);
  assert.equal(capabilities.canOperateAgency, true);
});

test("buildNavigation hides agency tools when the user cannot operate an agency", function () {
  const session = {
    activeWorkspaceRole: "tenant",
    capabilities: {
      canUsePersonalWorkspace: true,
      canOperateAgency: false,
      canAccessInternal: false
    }
  };

  const labels = buildNavigation(session).map(function pickLabel(item) {
    return item.label;
  });

  assert.equal(labels.includes("Agency Tools"), false);
  assert.equal(labels.includes("Review Center"), false);
  assert.equal(labels.includes("Rent & Issues"), true);
});

test("buildNavigation scopes agency mode to agency tools", function () {
  const session = {
    activeWorkspaceRole: "agency",
    capabilities: {
      canUsePersonalWorkspace: false,
      canOperateAgency: true,
      canAccessInternal: true
    }
  };

  const labels = buildNavigation(session).map(function pickLabel(item) {
    return item.label;
  });

  assert.deepEqual(labels, ["Home", "Agency Tools", "Account"]);
});

test("buildNavigation scopes internal mode to review center", function () {
  const session = {
    activeWorkspaceRole: "internal",
    capabilities: {
      canUsePersonalWorkspace: false,
      canOperateAgency: true,
      canAccessInternal: true
    }
  };

  const labels = buildNavigation(session).map(function pickLabel(item) {
    return item.label;
  });

  assert.deepEqual(labels, ["Home", "Review Center", "Account"]);
});

test("buildNavigation keeps listings tenant-only", function () {
  const tenantSession = {
    activeWorkspaceRole: "tenant",
    capabilities: {
      canUsePersonalWorkspace: true,
      canOperateAgency: false,
      canAccessInternal: false
    }
  };
  const landlordSession = {
    activeWorkspaceRole: "landlord",
    capabilities: {
      canUsePersonalWorkspace: true,
      canOperateAgency: false,
      canAccessInternal: false
    }
  };

  assert.equal(
    buildNavigation(tenantSession).some(function hasListings(item) {
      return item.label === "Listings";
    }),
    true
  );
  assert.equal(
    buildNavigation(landlordSession).some(function hasListings(item) {
      return item.label === "Listings";
    }),
    false
  );
});

test("workspace role normalization only returns available roles", function () {
  const user = {
    system_role: "user",
    workspace_roles: ["tenant", "agency"]
  };
  const organizations = [
    {
      organization_type: "agency",
      current_user_membership_role: "agent"
    }
  ];

  assert.deepEqual(getAvailableWorkspaceRoles(user, organizations), ["tenant", "agency"]);
  assert.equal(normalizeWorkspaceRole("agency", user, organizations), "agency");
  assert.equal(normalizeWorkspaceRole("internal", user, organizations), "tenant");
});

test("workspace roles are account entitlements, not inferred personas", function () {
  const tenantOnlyUser = {
    system_role: "user",
    workspace_roles: ["tenant"]
  };
  const mixedUser = {
    system_role: "user",
    workspace_roles: ["tenant", "landlord"]
  };

  assert.deepEqual(getAvailableWorkspaceRoles(tenantOnlyUser, []), ["tenant"]);
  assert.deepEqual(getAvailableWorkspaceRoles(mixedUser, []), ["tenant", "landlord"]);
  assert.equal(normalizeWorkspaceRole("landlord", tenantOnlyUser, []), "tenant");
});

test("normalizeDensity keeps the compact toggle strict and safe", function () {
  assert.equal(normalizeDensity("compact"), "compact");
  assert.equal(normalizeDensity("comfortable"), "comfortable");
  assert.equal(normalizeDensity("dense"), "comfortable");
  assert.equal(normalizeDensity(null), "comfortable");
});
