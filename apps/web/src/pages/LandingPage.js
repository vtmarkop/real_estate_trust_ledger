import React from "react";
import { Link } from "react-router-dom";
import { e } from "../lib/i18n.js";

function PersonaCard(props) {
  return e("article", { className: "persona-card" }, [
    e("p", { className: "persona-kicker", key: "kicker" }, props.kicker),
    e("h3", { className: "persona-title", key: "title" }, props.title),
    e("p", { className: "persona-copy", key: "copy" }, props.copy)
  ]);
}

export function LandingPage() {
  return e("div", { className: "public-page" }, [
    e("section", { className: "hero-panel", key: "hero" }, [
      e("div", { className: "hero-copy", key: "copy" }, [
        e("p", { className: "eyebrow", key: "eyebrow" }, "Evidence-verified rental trust"),
        e(
          "h1",
          { className: "hero-title", key: "title" },
          "A calmer, faster workspace for trust-backed leasing."
        ),
        e(
          "p",
          { className: "hero-text", key: "text" },
          "Trust Ledger helps tenants, landlords, agencies, and reviewers work from the same evidence-backed rental record instead of scattered messages and guesswork."
        ),
        e("div", { className: "hero-actions", key: "actions" }, [
          e(Link, { className: "button", to: "/login", key: "login" }, "Sign in"),
          e(
            Link,
            { className: "button button-secondary", to: "/register", key: "register" },
            "Create an account"
          )
        ])
      ]),
      e("div", { className: "hero-grid", key: "grid" }, [
        e(PersonaCard, {
          kicker: "Tenant",
          title: "Prove reliability without starting from zero.",
          copy: "Cold-start trust grows from evidence, references, and verified history."
        }),
        e(PersonaCard, {
          kicker: "Landlord",
          title: "Show operational discipline, not just a listing.",
          copy: "Maintenance, deposits, and response quality are building blocks of trust."
        }),
        e(PersonaCard, {
          kicker: "Agency",
          title: "Review applicants with shared scores and clear consent.",
          copy: "Agencies can manage listings, review applications, and run trust checks with an audit trail."
        }),
        e(PersonaCard, {
          kicker: "Internal",
          title: "Keep reviews, automation, and oversight in one place.",
          copy: "Reviewers and admins can manage queues, audits, and release-readiness from the same workspace."
        })
      ])
    ])
  ]);
}
