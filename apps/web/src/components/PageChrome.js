import React from "react";

import { e } from "../lib/i18n.js";

function buildToneClass(baseClassName, tone) {
  return tone ? baseClassName + " is-" + tone : baseClassName;
}

export function HeroStat(props) {
  return e("article", { className: "hero-stat-card" }, [
    e("p", { className: "hero-stat-label", key: "label" }, props.label),
    e("strong", { className: "hero-stat-value", key: "value" }, props.value),
    props.copy ? e("p", { className: "hero-stat-copy", key: "copy" }, props.copy) : null
  ]);
}

export function PageHero(props) {
  var actions = Array.isArray(props.actions) ? props.actions.filter(Boolean) : [];
  var stats = Array.isArray(props.stats) ? props.stats.filter(Boolean) : [];
  var details = Array.isArray(props.details) ? props.details.filter(Boolean) : [];

  return e("section", { className: "workspace-hero workspace-hero-rich" }, [
    e("div", { className: "workspace-hero-main", key: "main" }, [
      props.eyebrow ? e("p", { className: "eyebrow", key: "eyebrow" }, props.eyebrow) : null,
      e("h1", { className: "page-title", key: "title" }, props.title),
      props.copy ? e("p", { className: "page-copy", key: "copy" }, props.copy) : null,
      details.length
        ? e(
            "div",
            { className: "hero-detail-stack", key: "details" },
            details.map(function renderDetail(detail, index) {
              return e("p", { className: "workspace-hero-note", key: index }, detail);
            })
          )
        : null,
      actions.length ? e("div", { className: "hero-actions", key: "actions" }, actions) : null,
      props.extra ? e("div", { className: "hero-extra", key: "extra" }, props.extra) : null
    ]),
    stats.length
      ? e(
          "div",
          { className: "workspace-hero-aside", key: "aside" },
          e(
            "div",
            { className: "hero-stat-grid" },
            stats.map(function renderStat(stat, index) {
              return React.cloneElement(stat, { key: stat.key || index });
            })
          )
        )
      : null
  ]);
}

export function SectionHeading(props) {
  var actions = Array.isArray(props.actions) ? props.actions.filter(Boolean) : [];

  return e("div", { className: "section-heading" }, [
    e("div", { className: "section-heading-copy", key: "copy" }, [
      props.eyebrow ? e("p", { className: "eyebrow", key: "eyebrow" }, props.eyebrow) : null,
      e("h2", { className: "detail-title", key: "title" }, props.title),
      props.copy ? e("p", { className: "empty-copy", key: "body" }, props.copy) : null
    ]),
    actions.length
      ? e("div", { className: "section-heading-actions", key: "actions" }, actions)
      : null
  ]);
}

export function StatusBadge(props) {
  var className = buildToneClass("status-badge", props.tone || "neutral");
  return e(
    props.as || "span",
    { className: className },
    props.children || props.label
  );
}

export function FactPill(props) {
  return e("div", { className: buildToneClass("fact-pill", props.tone) }, [
    props.label
      ? e("span", { className: "fact-pill-label", key: "label" }, props.label)
      : null,
    e("strong", { className: "fact-pill-value", key: "value" }, props.value || props.children)
  ]);
}

export function NoteBlock(props) {
  var body = props.children || props.body || props.copy;
  return e("section", { className: buildToneClass("note-block", props.tone) }, [
    props.label
      ? e("p", { className: "note-block-label", key: "label" }, props.label)
      : null,
    body ? e("p", { className: "note-block-copy", key: "body" }, body) : null
  ]);
}

export function TimelineEntry(props) {
  var badges = Array.isArray(props.badges) ? props.badges.filter(Boolean) : [];
  var details = Array.isArray(props.details) ? props.details.filter(Boolean) : [];

  return e("article", { className: "timeline-entry" }, [
    e("div", { className: "timeline-entry-rail", key: "rail" }, [
      e("span", { className: "timeline-entry-dot", key: "dot" })
    ]),
    e("div", { className: "timeline-entry-main", key: "main" }, [
      props.eyebrow
        ? e("p", { className: "timeline-entry-eyebrow", key: "eyebrow" }, props.eyebrow)
        : null,
      e("div", { className: "timeline-entry-head", key: "head" }, [
        e("strong", { className: "stack-card-title", key: "title" }, props.title),
        badges.length
          ? e(
              "div",
              { className: "status-row", key: "badges" },
              badges.map(function renderBadge(badge, index) {
                return React.isValidElement(badge)
                  ? React.cloneElement(badge, { key: badge.key || index })
                  : e(StatusBadge, { key: index, label: badge });
              })
            )
          : null
      ]),
      props.meta
        ? e("p", { className: "timeline-entry-meta", key: "meta" }, props.meta)
        : null,
      props.summary
        ? e("p", { className: "timeline-entry-summary", key: "summary" }, props.summary)
        : null,
      details.length
        ? e("div", { className: "timeline-entry-details", key: "details" }, details)
        : null,
      props.children
        ? e("div", { className: "timeline-entry-extra", key: "extra" }, props.children)
        : null
    ])
  ]);
}
