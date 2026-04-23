import React from "react";

import { e } from "../lib/i18n.js";

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
      return e(
        "button",
        {
          type: "button",
          key: tab.id,
          className: "segmented-tab" + (isActive ? " is-active" : ""),
          role: "tab",
          "aria-selected": isActive ? "true" : "false",
          onClick: function onClick() {
            onChange(tab.id);
          }
        },
        [
          e("span", { className: "segmented-tab-label", key: "label" }, tab.label),
          typeof tab.meta === "string" && tab.meta
            ? e("span", { className: "segmented-tab-meta", key: "meta" }, tab.meta)
            : null
        ]
      );
    })
  );
}
