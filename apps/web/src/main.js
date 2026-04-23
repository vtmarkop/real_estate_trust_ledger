import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "react-router-dom";

import { createAppRouter } from "./app/router.js";
import { SessionProvider } from "./app/session.js";
import { LanguageProvider, useLanguage } from "./lib/i18n.js";
import "./styles/index.css";

function registerInstallLifecycle() {
  if (typeof window === "undefined") {
    return;
  }

  if (!window.__trustLedgerInstallPrompt) {
    window.__trustLedgerInstallPrompt = null;
  }

  window.addEventListener("beforeinstallprompt", function handleBeforeInstallPrompt(event) {
    event.preventDefault();
    window.__trustLedgerInstallPrompt = event;
    window.dispatchEvent(new CustomEvent("trustledger:install-available"));
  });

  window.addEventListener("appinstalled", function handleAppInstalled() {
    window.__trustLedgerInstallPrompt = null;
    window.dispatchEvent(new CustomEvent("trustledger:installed"));
  });
}

function registerServiceWorker() {
  if (typeof window === "undefined") {
    return;
  }
  if (!("serviceWorker" in navigator) || !import.meta.env.PROD) {
    return;
  }
  window.addEventListener("load", function onWindowLoad() {
    navigator.serviceWorker.register("/sw.js").catch(function ignoreServiceWorkerError() {});
  });
}

registerInstallLifecycle();
registerServiceWorker();

var root = ReactDOM.createRoot(document.getElementById("root"));

function ApplicationRoot() {
  var language = useLanguage().language;
  var router = React.useMemo(function createLanguageAwareRouter() {
    return createAppRouter();
  }, [language]);

  return React.createElement(
    SessionProvider,
    null,
    React.createElement(RouterProvider, {
      router: router,
      key: "router-" + language
    })
  );
}

root.render(
  React.createElement(
    React.StrictMode,
    null,
    React.createElement(
      LanguageProvider,
      null,
      React.createElement(ApplicationRoot)
    )
  )
);
