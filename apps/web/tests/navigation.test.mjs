import test from "node:test";
import assert from "node:assert/strict";

import {
  buildCapabilities,
  getAvailableWorkspaceRoles,
  normalizeWorkspaceRole
} from "../src/app/session.js";
import { buildNavigation, WORKSPACE_DENSITY } from "../src/app/AppShell.js";
import { resolveFieldIconName, resolveIconName } from "../src/components/VisualIcon.js";
import {
  applyAgencyOrganizationSelection,
  getEffectivePropertyManagementMode,
  getAgencyOperatorsForOrganization,
  hasAgencyDirectoryOptions
} from "../src/pages/RecordsPage.js";

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
  assert.equal(capabilities.canReviewCases, true);
  assert.equal(capabilities.canManagePlatform, false);
  assert.equal(capabilities.canOperateAgency, true);
  assert.equal(capabilities.canManageAgency, false);
});

test("admin and reviewer capabilities stay separate inside internal access", function () {
  const reviewerCapabilities = buildCapabilities({
    system_role: "reviewer",
    workspace_roles: ["internal"]
  }, []);
  const adminCapabilities = buildCapabilities({
    system_role: "admin",
    workspace_roles: ["internal"]
  }, []);

  assert.equal(reviewerCapabilities.canAccessInternal, true);
  assert.equal(reviewerCapabilities.canReviewCases, true);
  assert.equal(reviewerCapabilities.canManagePlatform, false);
  assert.equal(adminCapabilities.canAccessInternal, true);
  assert.equal(adminCapabilities.canReviewCases, false);
  assert.equal(adminCapabilities.canManagePlatform, true);
});

test("buildCapabilities lets an unassigned agent bootstrap an agency workspace", function () {
  const agentUser = {
    system_role: "user",
    workspace_roles: ["agency"]
  };
  const landlordUser = {
    system_role: "user",
    workspace_roles: ["landlord"]
  };

  assert.equal(buildCapabilities(agentUser, []).canCreateAgencyWorkspace, true);
  assert.equal(buildCapabilities(landlordUser, []).canCreateAgencyWorkspace, false);
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
      canAccessInternal: true,
      canManagePlatform: false
    }
  };

  const labels = buildNavigation(session).map(function pickLabel(item) {
    return item.label;
  });

  assert.deepEqual(labels, ["Home", "Review Center", "Account"]);
});

test("buildNavigation labels admin internal mode as admin center", function () {
  const session = {
    activeWorkspaceRole: "internal",
    capabilities: {
      canUsePersonalWorkspace: false,
      canOperateAgency: false,
      canAccessInternal: true,
      canManagePlatform: true
    }
  };

  const labels = buildNavigation(session).map(function pickLabel(item) {
    return item.label;
  });

  assert.deepEqual(labels, ["Home", "Admin Center", "Account"]);
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

test("buildNavigation assigns stable visual tones to workspace lanes", function () {
  const session = {
    activeWorkspaceRole: "tenant",
    capabilities: {
      canUsePersonalWorkspace: true,
      canOperateAgency: false,
      canAccessInternal: false
    }
  };

  const tonesByLabel = Object.fromEntries(
    buildNavigation(session).map(function mapItem(item) {
      return [item.label, item.tone];
    })
  );

  assert.equal(tonesByLabel.Home, "home");
  assert.equal(tonesByLabel["Tenant Trust"], "trust");
  assert.equal(tonesByLabel.Listings, "marketplace");
  assert.equal(tonesByLabel["Rental Records"], "records");
  assert.equal(tonesByLabel["Rent & Issues"], "operations");
  assert.equal(tonesByLabel.Account, "security");
});

test("buildNavigation assigns stable icons to workspace lanes", function () {
  const session = {
    activeWorkspaceRole: "tenant",
    capabilities: {
      canUsePersonalWorkspace: true,
      canOperateAgency: false,
      canAccessInternal: false
    }
  };

  const iconsByLabel = Object.fromEntries(
    buildNavigation(session).map(function mapItem(item) {
      return [item.label, item.icon];
    })
  );

  assert.equal(iconsByLabel.Home, "home");
  assert.equal(iconsByLabel["Tenant Trust"], "trust");
  assert.equal(iconsByLabel.Listings, "marketplace");
  assert.equal(iconsByLabel["Rental Records"], "records");
  assert.equal(iconsByLabel["Rent & Issues"], "operations");
  assert.equal(iconsByLabel.Account, "security");
});

test("resolveIconName maps workflow tab ids to stable icons", function () {
  assert.equal(resolveIconName("daily-work"), "operations");
  assert.equal(resolveIconName("screening-history"), "history");
  assert.equal(resolveIconName("team-access"), "roles");
  assert.equal(resolveIconName("payment"), "payment");
});

test("resolveFieldIconName maps submit-field labels to stable icons", function () {
  assert.equal(resolveFieldIconName("City"), "city");
  assert.equal(resolveFieldIconName("Property label"), "property");
  assert.equal(resolveFieldIconName("Tenant email"), "email");
  assert.equal(resolveFieldIconName("Lease start date"), "calendar");
  assert.equal(resolveFieldIconName("Monthly rent"), "currency");
  assert.equal(resolveFieldIconName("Reference artifact file"), "file");
  assert.equal(resolveFieldIconName("Review notes"), "note");
  assert.equal(resolveFieldIconName("Minimum tenant score"), "score");
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

test("workspace shell uses compact density as the fixed layout", function () {
  assert.equal(WORKSPACE_DENSITY, "compact");
});

test("landlord property setup does not require an agency when none exist", function () {
  assert.equal(hasAgencyDirectoryOptions([]), false);
  assert.equal(
    getEffectivePropertyManagementMode({ management_mode: "agency_managed" }, []),
    "owner_managed"
  );
  assert.equal(
    getEffectivePropertyManagementMode(
      { management_mode: "agency_managed" },
      [{ id: "agency-1", name: "Demo Agency" }]
    ),
    "agency_managed"
  );
});

test("landlord agency selection fills a single operator email automatically", function () {
  const operatorsByAgency = {
    "agency-1": [
      {
        email: "agent@example.com",
        full_name: "Agency Agent",
        role: "agent"
      }
    ],
    "agency-2": [
      {
        email: "owner@example.com",
        full_name: "Agency Owner",
        role: "owner"
      },
      {
        email: "agent-two@example.com",
        full_name: "Second Agent",
        role: "agent"
      }
    ]
  };

  assert.equal(getAgencyOperatorsForOrganization(operatorsByAgency, "agency-1").length, 1);
  assert.equal(
    applyAgencyOrganizationSelection(
      { assigned_agency_organization_id: "", assigned_agency_user_email: "" },
      "agency-1",
      operatorsByAgency
    ).assigned_agency_user_email,
    "agent@example.com"
  );
  assert.equal(
    applyAgencyOrganizationSelection(
      { assigned_agency_organization_id: "", assigned_agency_user_email: "" },
      "agency-2",
      operatorsByAgency
    ).assigned_agency_user_email,
    ""
  );
});
