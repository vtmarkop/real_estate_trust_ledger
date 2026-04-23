import React from "react";

import { SegmentedTabs } from "../components/SegmentedTabs.js";
import {
  FactPill,
  HeroStat,
  NoteBlock,
  PageHero,
  SectionHeading,
  StatusBadge,
  TimelineEntry
} from "../components/PageChrome.js";
import { apiRequest } from "../lib/api.js";
import { e } from "../lib/i18n.js";

function DataPanel(props) {
  return e("section", { className: "detail-panel" }, [
    e("h2", { className: "detail-title", key: "title" }, props.title),
    props.children
  ]);
}

function inferStatusTone(value) {
  var normalized = String(value || "").toLowerCase();
  if (
    normalized.indexOf("success") >= 0 ||
    normalized.indexOf("active") >= 0 ||
    normalized.indexOf("current") >= 0
  ) {
    return "success";
  }
  if (
    normalized.indexOf("fail") >= 0 ||
    normalized.indexOf("revoked") >= 0 ||
    normalized.indexOf("signed_out") >= 0 ||
    normalized.indexOf("inactive") >= 0
  ) {
    return "danger";
  }
  return "accent";
}

export function SecurityPage() {
  var stateTuple = React.useState({
    status: "loading",
    sessions: [],
    events: [],
    error: null
  });
  var state = stateTuple[0];
  var setState = stateTuple[1];
  var actionTuple = React.useState(false);
  var isRevokingOthers = actionTuple[0];
  var setIsRevokingOthers = actionTuple[1];
  var sessionActionTuple = React.useState({
    id: "",
    message: null
  });
  var sessionAction = sessionActionTuple[0];
  var setSessionAction = sessionActionTuple[1];
  var securitySectionTuple = React.useState("sessions");
  var securitySection = securitySectionTuple[0];
  var setSecuritySection = securitySectionTuple[1];

  var loadSecurityState = React.useCallback(async function loadSecurityState() {
    setState(function setLoading(previous) {
      return {
        status: previous.sessions.length || previous.events.length ? "refreshing" : "loading",
        sessions: previous.sessions,
        events: previous.events,
        error: null
      };
    });

    try {
      var results = await Promise.all([
        apiRequest("/auth/sessions"),
        apiRequest("/auth/security-events")
      ]);
      setState({
        status: "ready",
        sessions: results[0],
        events: results[1],
        error: null
      });
    } catch (error) {
      setState({
        status: "error",
        sessions: [],
        events: [],
        error: error.message || "Unable to load security details."
      });
    }
  }, []);

  React.useEffect(function bootstrapSecurityState() {
    loadSecurityState();
  }, [loadSecurityState]);

  async function handleRevokeOthers() {
    setIsRevokingOthers(true);
    try {
      await apiRequest("/auth/sessions/revoke-others", {
        method: "POST"
      });
      await loadSecurityState();
      setSessionAction({
        id: "",
        message: "Other devices were signed out."
      });
    } finally {
      setIsRevokingOthers(false);
    }
  }

  async function handleRevokeSession(sessionId) {
    setSessionAction({
      id: sessionId,
      message: null
    });
    try {
      await apiRequest("/auth/sessions/" + sessionId + "/revoke", {
        method: "POST"
      });
      await loadSecurityState();
      setSessionAction({
        id: "",
        message: "Selected session signed out."
      });
    } catch (error) {
      setSessionAction({
        id: "",
        message: error.message || "Unable to sign out this session."
      });
    }
  }

  if (state.status === "loading") {
    return e("div", { className: "state-panel" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Account"),
      e("h1", { className: "state-title", key: "title" }, "Loading account security"),
      e(
        "p",
        { className: "state-copy", key: "copy" },
        "We are loading your active sessions and recent sign-in events."
      )
    ]);
  }

  if (state.status === "error") {
    return e("div", { className: "state-panel is-error" }, [
      e("p", { className: "eyebrow", key: "eyebrow" }, "Account"),
      e("h1", { className: "state-title", key: "title" }, "Security data unavailable"),
      e("p", { className: "state-copy", key: "copy" }, state.error)
    ]);
  }

  var activeSessions = state.sessions.filter(function filterActive(session) {
    return session.is_active;
  });
  var currentSessionCount = state.sessions.filter(function filterCurrent(session) {
    return session.is_current;
  }).length;
  var securityTabs = [
    {
      id: "sessions",
      label: "Sessions",
      meta: String(activeSessions.length) + " active"
    },
    {
      id: "events",
      label: "Sign-in activity",
      meta: String(state.events.length) + " events"
    }
  ];

  return e("div", { className: "workspace-page" }, [
    e(PageHero, {
      key: "hero",
      eyebrow: "Account security",
      title: "Your devices and sign-in activity",
      copy:
        "Use this page to review where your account is signed in and to sign out of other devices if needed.",
      actions: [
        e(
          "button",
          {
            type: "button",
            className: "button button-secondary",
            disabled: isRevokingOthers,
            onClick: handleRevokeOthers,
            key: "revoke"
          },
          isRevokingOthers ? "Signing out..." : "Sign out of other devices"
        )
      ],
      stats: [
        e(HeroStat, {
          label: "Known sessions",
          value: String(state.sessions.length),
          copy: String(activeSessions.length) + " still active."
        }),
        e(HeroStat, {
          label: "Current device",
          value: String(currentSessionCount),
          copy: "The current browser session stays protected from self-revoke."
        }),
        e(HeroStat, {
          label: "Recent security events",
          value: String(state.events.length),
          copy: "Recent sign-in outcomes and session-related events."
        })
      ]
    }),
    sessionAction.message
      ? e("div", { className: "form-alert", key: "message" }, sessionAction.message)
      : null,
    e("section", { className: "detail-panel section-switcher", key: "security-switcher" }, [
      e(SectionHeading, {
        title: "Focus on one account-safety lane",
        copy:
          securitySection === "sessions"
            ? "Stay on sessions when you want to remove device access without the noise of historical event logs."
            : "Switch to sign-in activity when you want to investigate how the account has been used recently.",
        key: "heading"
      }),
      e(SegmentedTabs, {
        key: "tabs",
        tabs: securityTabs,
        activeTab: securitySection,
        onChange: setSecuritySection,
        "aria-label": "Security sections"
      })
    ]),
    securitySection === "sessions"
      ? e(DataPanel, {
      title: "Known sessions",
      key: "sessions",
      children: e(
        "div",
        { className: "list-stack" },
        state.sessions.map(function renderSession(session) {
          return e("article", { className: "stack-card", key: session.id }, [
            e("strong", { className: "stack-card-title", key: "title" }, session.is_current ? "Current session" : "Known session"),
            e("div", { className: "status-row", key: "status" }, [
              e(StatusBadge, {
                key: "active",
                tone: session.is_active ? "success" : "danger",
                label: session.is_active ? "Active" : "Inactive"
              }),
              session.is_current
                ? e(StatusBadge, { key: "current", tone: "accent", label: "Current device" })
                : null
            ]),
            e("div", { className: "fact-grid", key: "facts" }, [
              e(FactPill, { key: "expires", label: "Expires", value: session.expires_at }),
              e(FactPill, { key: "ip", label: "IP", value: session.ip_address || "Unknown IP" })
            ]),
            e(
              NoteBlock,
              { key: "agent", label: "Browser or device", tone: "accent" },
              session.user_agent || "Unknown user agent"
            ),
            !session.is_current && session.is_active
              ? e(
                  "button",
                  {
                    type: "button",
                    className: "button button-small",
                    disabled: sessionAction.id === session.id,
                    onClick: function onClick() {
                      handleRevokeSession(session.id);
                    },
                    key: "revoke"
                  },
                  sessionAction.id === session.id ? "Signing out..." : "Sign out this device"
                )
              : null
          ]);
        })
      )
    })
      : null,
    securitySection === "events"
      ? e(DataPanel, {
      title: "Recent sign-in events",
      key: "events",
      children: e(
        "div",
        { className: "timeline-list" },
        state.events.map(function renderEvent(event) {
          return e(TimelineEntry, {
            key: event.id,
            eyebrow: event.created_at,
            title: event.action_type,
            badges: [
              e(StatusBadge, {
                key: "outcome",
                tone: inferStatusTone(event.outcome_status),
                label: event.outcome_status
              })
            ],
            summary: event.details || "No extra details captured."
          });
        })
      )
    })
      : null
  ]);
}
