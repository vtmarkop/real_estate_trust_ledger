import React from "react";

import { VisualIcon, resolveIconName } from "./VisualIcon.js";
import { e } from "../lib/i18n.js";

function buildTabToken(value) {
  return String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function SegmentedTabs(props) {
  var tabs = props.tabs || [];
  var activeTab = props.activeTab;
  var onChange = props.onChange;
  var className = props.className || "";

  return e(
    "div",
    {
      className: "segmented-tabs" + (className ? " " + className : ""),
      role: "tablist",
      "aria-label": props["aria-label"] || "Workspace sections"
    },
    tabs.map(function renderTab(tab) {
      var isActive = tab.id === activeTab;
      var tabToken = buildTabToken(tab.id || tab.label);
      var iconName = tab.icon || resolveIconName(tabToken || tab.label);
      return e(
        "button",
        {
          type: "button",
          key: tab.id,
          className:
            "segmented-tab" +
            (tabToken ? " segmented-tab-" + tabToken : "") +
            (isActive ? " is-active" : ""),
          role: "tab",
          "aria-selected": isActive ? "true" : "false",
          onClick: function onClick() {
            onChange(tab.id);
          }
        },
        [
          e("span", { className: "segmented-tab-head", key: "head" }, [
            e(VisualIcon, { className: "segmented-tab-icon", key: "icon", name: iconName }),
            e("span", { className: "segmented-tab-label text-static", key: "label" }, tab.label)
          ]),
          typeof tab.meta === "string" && tab.meta
            ? e("span", { className: "segmented-tab-meta", key: "meta" }, tab.meta)
            : null
        ]
      );
    })
  );
}
