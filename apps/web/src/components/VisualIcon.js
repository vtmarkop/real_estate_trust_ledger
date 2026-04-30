import React from "react";

var ICON_PATHS = {
  agency: [
    "M5 20V7l7-3 7 3v13",
    "M8 20v-4h8v4",
    "M9 10h.01M12 10h.01M15 10h.01M9 13h.01M12 13h.01M15 13h.01"
  ],
  applications: [
    "M7 4h7l3 3v13H7z",
    "M14 4v4h4",
    "M9 11h6M9 14h6M9 17h4"
  ],
  calendar: [
    "M7 4v3M17 4v3",
    "M5 8h14",
    "M6 6h12v14H6z",
    "M9 12h.01M12 12h.01M15 12h.01M9 16h.01M12 16h.01"
  ],
  city: [
    "M4 20V9l5-3v14",
    "M9 20V4l6 3v13",
    "M15 20v-8l5 2v6",
    "M7 11h.01M7 14h.01M12 9h.01M12 12h.01M12 15h.01M18 16h.01"
  ],
  controls: [
    "M4 7h16M4 12h16M4 17h16",
    "M8 5v4M14 10v4M11 15v4"
  ],
  country: [
    "M12 21a9 9 0 100-18 9 9 0 000 18z",
    "M3.6 9h16.8M3.6 15h16.8",
    "M12 3a14 14 0 010 18M12 3a14 14 0 000 18"
  ],
  currency: [
    "M17 7a5 5 0 00-4-2 5 5 0 000 10 5 5 0 004-2",
    "M6 10h7M6 14h7"
  ],
  deposit: [
    "M4 8h16v10H4z",
    "M7 8V6h10v2",
    "M16 13h2"
  ],
  email: [
    "M4 6h16v12H4z",
    "M4 8l8 6 8-6"
  ],
  disputes: [
    "M12 4l8 8-8 8-8-8z",
    "M12 8v5M12 16h.01"
  ],
  evidence: [
    "M8 12l5-5a3 3 0 014 4l-6 6a5 5 0 01-7-7l6-6",
    "M10 14l6-6"
  ],
  file: [
    "M7 4h7l3 3v13H7z",
    "M14 4v4h4",
    "M9 13h6M9 16h4"
  ],
  history: [
    "M4 12a8 8 0 108-8",
    "M4 6v6h6",
    "M12 8v5l3 2"
  ],
  home: [
    "M4 11l8-7 8 7",
    "M6 10v10h5v-6h2v6h5V10"
  ],
  internal: [
    "M12 4l7 3v5c0 4-3 7-7 8-4-1-7-4-7-8V7z",
    "M9 12l2 2 4-4"
  ],
  key: [
    "M14 14a4 4 0 11-2.8-6.8A4 4 0 0114 14z",
    "M14 14l6 6",
    "M17 17l-2 2M19 19l-2 2"
  ],
  maintenance: [
    "M14 6l4 4",
    "M6 18l7-7",
    "M15 5a4 4 0 015 5l-3-3-3 3 3 3a4 4 0 01-5-5"
  ],
  marketplace: [
    "M5 10l1-5h12l1 5",
    "M6 10v9h12v-9",
    "M9 19v-5h6v5",
    "M4 10h16"
  ],
  money: [
    "M4 7h16v10H4z",
    "M8 12h.01M16 12h.01",
    "M12 9a3 3 0 110 6 3 3 0 010-6z"
  ],
  note: [
    "M6 5h12v14H6z",
    "M9 9h6M9 12h6M9 15h4"
  ],
  operations: [
    "M5 7h14v10H5z",
    "M8 10h5",
    "M16 14h.01",
    "M9 17v3M15 17v3"
  ],
  payment: [
    "M4 7h16v10H4z",
    "M4 10h16",
    "M7 14h4"
  ],
  property: [
    "M5 20V6h14v14",
    "M8 9h2M14 9h2M8 13h2M14 13h2",
    "M10 20v-4h4v4"
  ],
  records: [
    "M7 4h7l3 3v13H7z",
    "M14 4v4h4",
    "M9 12h6M9 15h6M9 18h4"
  ],
  review: [
    "M8 5h8l1 3v12H7V8z",
    "M9 5a3 3 0 016 0",
    "M9 13l2 2 4-4"
  ],
  roles: [
    "M8 11a3 3 0 100-6 3 3 0 000 6z",
    "M4 20a4 4 0 018 0",
    "M17 10a2.5 2.5 0 100-5 2.5 2.5 0 000 5z",
    "M14 19a3.5 3.5 0 017 0"
  ],
  runtime: [
    "M12 8a4 4 0 100 8 4 4 0 000-8z",
    "M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1"
  ],
  security: [
    "M7 10V8a5 5 0 0110 0v2",
    "M6 10h12v10H6z",
    "M12 14v3"
  ],
  search: [
    "M11 18a7 7 0 100-14 7 7 0 000 14z",
    "M16 16l4 4"
  ],
  score: [
    "M5 19h14",
    "M7 16l3-4 3 2 4-7",
    "M17 7h-4V3"
  ],
  sharing: [
    "M8 12l8-5M8 12l8 5",
    "M6 14a2 2 0 100-4 2 2 0 000 4z",
    "M18 9a2 2 0 100-4 2 2 0 000 4z",
    "M18 19a2 2 0 100-4 2 2 0 000 4z"
  ],
  status: [
    "M5 12l4 4L19 6",
    "M4 20h16"
  ],
  tag: [
    "M4 5h7l9 9-6 6-9-9z",
    "M8 8h.01"
  ],
  title: [
    "M5 6h14",
    "M12 6v12",
    "M8 18h8"
  ],
  trust: [
    "M12 4l7 3v5c0 4-3 7-7 8-4-1-7-4-7-8V7z",
    "M9.5 12.5l1.7 1.7 3.8-4.2"
  ]
};

var TOKEN_ICON_MAP = {
  "access": "security",
  "access-log": "history",
  "account": "security",
  "application": "applications",
  "applications": "applications",
  "artifacts": "evidence",
  "audit": "history",
  "controls": "controls",
  "daily": "operations",
  "daily-work": "operations",
  "deposit": "deposit",
  "deposits": "deposit",
  "discovery": "marketplace",
  "disputes": "disputes",
  "evidence": "evidence",
  "history": "history",
  "issues": "maintenance",
  "listings": "marketplace",
  "maintenance": "maintenance",
  "overview": "trust",
  "payments": "payment",
  "payment": "payment",
  "pipeline": "applications",
  "portfolio": "property",
  "properties": "property",
  "publishing": "marketplace",
  "records": "records",
  "references": "sharing",
  "review": "review",
  "review-center": "internal",
  "review-queues": "review",
  "roles": "roles",
  "runtime": "runtime",
  "screening": "agency",
  "screening-history": "history",
  "sessions": "security",
  "sharing": "sharing",
  "summary": "trust",
  "team-access": "roles",
  "tenancies": "records",
  "tenancy-records": "records"
};

export function resolveIconName(token) {
  var normalized = String(token || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return TOKEN_ICON_MAP[normalized] || (ICON_PATHS[normalized] ? normalized : "records");
}

export function resolveFieldIconName(label) {
  var normalized = String(label || "").toLowerCase();

  if (/\b(city|town)\b/.test(normalized)) {
    return "city";
  }
  if (/\b(country)\b/.test(normalized)) {
    return "country";
  }
  if (/\b(agency|organization)\b/.test(normalized)) {
    return "agency";
  }
  if (/\b(address|property)\b/.test(normalized)) {
    return normalized.indexOf("agency") >= 0 ? "agency" : "property";
  }
  if (/\b(email|e-mail)\b/.test(normalized)) {
    return "email";
  }
  if (/\b(password|access code|share token|token)\b/.test(normalized)) {
    return "key";
  }
  if (/\b(start|end|due|expires|schedule|date|days)\b/.test(normalized)) {
    return "calendar";
  }
  if (/\b(rent|amount|price|currency)\b/.test(normalized)) {
    return "currency";
  }
  if (/\b(deposit)\b/.test(normalized)) {
    return "deposit";
  }
  if (/\b(score|delta|verification strength|minimum verification)\b/.test(normalized)) {
    return "score";
  }
  if (/\b(file|document|artifact|proof|receipt|evidence)\b/.test(normalized)) {
    return "file";
  }
  if (/\b(note|notes|message|summary|description)\b/.test(normalized)) {
    return "note";
  }
  if (/\b(tag|tags)\b/.test(normalized)) {
    return "tag";
  }
  if (/\b(status|outcome|verdict|access)\b/.test(normalized)) {
    return "status";
  }
  if (/\b(role|payer|tenant|landlord|member|user|name|who manages)\b/.test(normalized)) {
    return "roles";
  }
  if (/\b(find|search|filter)\b/.test(normalized)) {
    return "search";
  }
  if (/\b(title|label|subject|type)\b/.test(normalized)) {
    return "title";
  }
  if (/\b(menu|choose|select)\b/.test(normalized)) {
    return "controls";
  }
  return "records";
}

export function VisualIcon(props) {
  var iconName = resolveIconName(props.name);
  var paths = ICON_PATHS[iconName] || ICON_PATHS.records;
  var className = "visual-icon" + (props.className ? " " + props.className : "");

  return React.createElement(
    "svg",
    {
      "aria-hidden": "true",
      className: className,
      fill: "none",
      focusable: "false",
      stroke: "currentColor",
      strokeLinecap: "round",
      strokeLinejoin: "round",
      strokeWidth: "1.8",
      viewBox: "0 0 24 24"
    },
    paths.map(function renderPath(path, index) {
      return React.createElement("path", { d: path, key: index });
    })
  );
}
