import test from "node:test";
import assert from "node:assert/strict";

import { buildCapabilities } from "../src/app/session.js";
import { buildNavigation, normalizeDensity } from "../src/app/AppShell.js";

test("buildCapabilities exposes agency and internal access separately", function () {
  const user = {
    system_role: "reviewer"
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
    system_role: "user"
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

test("buildNavigation shows agency and review spaces only when capabilities allow them", function () {
  const session = {
    capabilities: {
      canUsePersonalWorkspace: false,
      canOperateAgency: true,
      canAccessInternal: true
    }
  };

  const labels = buildNavigation(session).map(function pickLabel(item) {
    return item.label;
  });

  assert.deepEqual(labels, ["Home", "Agency Tools", "Review Center", "Account"]);
});

test("normalizeDensity keeps the compact toggle strict and safe", function () {
  assert.equal(normalizeDensity("compact"), "compact");
  assert.equal(normalizeDensity("comfortable"), "comfortable");
  assert.equal(normalizeDensity("dense"), "comfortable");
  assert.equal(normalizeDensity(null), "comfortable");
});
