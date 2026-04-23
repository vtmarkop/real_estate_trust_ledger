import React from "react";
import { Link } from "react-router-dom";
import { e } from "../lib/i18n.js";

export function NotFoundPage() {
  return e("div", { className: "state-panel" }, [
    e("p", { className: "eyebrow", key: "eyebrow" }, "Trust Ledger"),
    e("h1", { className: "state-title", key: "title" }, "Page not found"),
    e(
      "p",
      { className: "state-copy", key: "copy" },
      "The route scaffolding is in place, but this URL is not part of the current web slice."
    ),
    e(Link, { className: "button", to: "/", key: "home" }, "Return home")
  ]);
}
