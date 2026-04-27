import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { e } from "../lib/i18n.js";
import { useSession } from "../app/session.js";

function buildInitialState(mode) {
  return {
    email: "",
    fullName: "",
    password: "",
    confirmPassword: "",
    mode: mode || "login"
  };
}

export function AuthPage(props) {
  var mode = props.mode || "login";
  var session = useSession();
  var navigate = useNavigate();
  var location = useLocation();
  var formState = React.useState(buildInitialState(mode));
  var fields = formState[0];
  var setFields = formState[1];
  var submissionState = React.useState({
    isSubmitting: false,
    message: null
  });
  var submission = submissionState[0];
  var setSubmission = submissionState[1];

  React.useEffect(
    function syncMode() {
      setFields(buildInitialState(mode));
      setSubmission({
        isSubmitting: false,
        message: null
      });
    },
    [mode]
  );

  function updateField(event) {
    var target = event.target;
    setFields(function mergeFields(previous) {
      var next = Object.assign({}, previous);
      next[target.name] = target.value;
      return next;
    });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmission({
      isSubmitting: true,
      message: null
    });

    try {
      if (mode === "register") {
        if (fields.password !== fields.confirmPassword) {
          throw new Error("Passwords must match before account creation.");
        }
        await session.register({
          email: fields.email,
          full_name: fields.fullName,
          password: fields.password
        });
      } else {
        await session.login({
          email: fields.email,
          password: fields.password
        });
      }

      var redirectTarget =
        location.state && location.state.from ? location.state.from : "/app";
      navigate(redirectTarget, { replace: true });
    } catch (error) {
      setSubmission({
        isSubmitting: false,
        message: error.message || "Authentication failed."
      });
      return;
    }

    setSubmission({
      isSubmitting: false,
      message: null
    });
  }

  return e("div", { className: "public-page auth-page" }, [
    e("section", { className: "auth-panel", key: "panel" }, [
      e("div", { className: "auth-intro", key: "intro" }, [
        e("p", { className: "eyebrow", key: "eyebrow" }, mode === "register" ? "Create account" : "Sign in"),
        e(
          "h1",
          { className: "auth-title", key: "title" },
          mode === "register" ? "Create your Trust Ledger account." : "Welcome back."
        ),
        e(
          "p",
          { className: "auth-copy", key: "copy" },
          mode === "register"
            ? "Create a secure account first. After that, you can build your rental record, share your trust profile, and join organizations."
            : "Sign in securely. The app will open the last valid workspace role for this browser, and you can switch assigned roles from the sidebar."
        )
      ]),
      e(
        "form",
        {
          className: "auth-form",
          onSubmit: handleSubmit,
          key: "form"
        },
        [
          mode === "register"
            ? e("label", { className: "field", key: "fullName" }, [
                e("span", { className: "field-label", key: "label" }, "Full name"),
                e("input", {
                  className: "field-input",
                  name: "fullName",
                  value: fields.fullName,
                  onChange: updateField,
                  minLength: 2,
                  maxLength: 255,
                  required: true
                })
              ])
            : null,
          e("label", { className: "field", key: "email" }, [
            e("span", { className: "field-label", key: "label" }, "Email"),
            e("input", {
              className: "field-input",
              name: "email",
              type: "email",
              value: fields.email,
              onChange: updateField,
              autoComplete: "email",
              required: true
            })
          ]),
          e("label", { className: "field", key: "password" }, [
            e("span", { className: "field-label", key: "label" }, "Password"),
            e("input", {
              className: "field-input",
              name: "password",
              type: "password",
              value: fields.password,
              onChange: updateField,
              minLength: 12,
              maxLength: 128,
              autoComplete: mode === "register" ? "new-password" : "current-password",
              required: true
            })
          ]),
          mode === "register"
            ? e("label", { className: "field", key: "confirmPassword" }, [
                e("span", { className: "field-label", key: "label" }, "Confirm password"),
                e("input", {
                  className: "field-input",
                  name: "confirmPassword",
                  type: "password",
                  value: fields.confirmPassword,
                  onChange: updateField,
                  minLength: 12,
                  maxLength: 128,
                  autoComplete: "new-password",
                  required: true
                })
              ])
            : null,
          submission.message || session.error
            ? e(
                "div",
                { className: "form-alert", key: "alert" },
                submission.message || session.error
              )
            : null,
          e(
            "button",
            {
              type: "submit",
              className: "button",
              disabled: submission.isSubmitting,
              key: "submit"
            },
            submission.isSubmitting
              ? mode === "register"
                ? "Creating account..."
                : "Signing in..."
              : mode === "register"
                ? "Create account"
                : "Sign in"
          ),
          e(
            "p",
            { className: "auth-switch", key: "switch" },
            mode === "register"
              ? [
                  "Already have an account? ",
                  e(Link, { to: "/login", key: "link" }, "Sign in")
                ]
              : [
                  "Need an account? ",
                  e(Link, { to: "/register", key: "link" }, "Create one")
                ]
          )
        ]
      )
    ])
  ]);
}
