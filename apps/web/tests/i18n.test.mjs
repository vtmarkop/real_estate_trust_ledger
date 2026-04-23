import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { LanguageProvider, e, getLanguageLocale, translateText } from "../src/lib/i18n.js";

test("translateText returns Greek labels for key workspace strings", function () {
  assert.equal(translateText("Home", "el"), "Αρχική");
  assert.equal(translateText("My Trust", "el"), "Η Εμπιστοσύνη μου");
  assert.equal(translateText("Rent & Issues", "el"), "Ενοίκιο & ζητήματα");
});

test("translateText preserves composite phrases and whitespace", function () {
  assert.equal(
    translateText("Access level: Reviewer", "el"),
    "Επίπεδο πρόσβασης: Ελεγκτής"
  );
  assert.equal(
    translateText("Already have an account? ", "el"),
    "Έχεις ήδη λογαριασμό; "
  );
});

test("getLanguageLocale reflects the selected UI language", function () {
  assert.equal(getLanguageLocale("en"), "en-US");
  assert.equal(getLanguageLocale("el"), "el-GR");
});

test("translateText covers Sprint 20 workflow copy in Greek", function () {
  assert.equal(
    translateText("Focus on one operational lane", "el"),
    "Εστίασε σε μία λειτουργική ενότητα τη φορά"
  );
  assert.equal(
    translateText("Agency workspace sections", "el"),
    "Ενότητες χώρου πρακτορείου"
  );
  assert.equal(
    translateText("Restoring session", "el"),
    "Επαναφορά συνεδρίας"
  );
});

test("LanguageProvider applies the selected language during render", function () {
  function Sample() {
    return e("div", null, "Home");
  }

  var html = renderToStaticMarkup(
    React.createElement(
      LanguageProvider,
      { initialLanguage: "el" },
      React.createElement(Sample)
    )
  );

  assert.match(html, /Αρχική/);
  assert.match(html, /Γλώσσα/);
});

test("LanguageProvider forces the child tree to receive the active language", function () {
  function Probe(props) {
    return e("div", null, props.__trustLedgerLanguage || "missing");
  }

  var html = renderToStaticMarkup(
    React.createElement(
      LanguageProvider,
      { initialLanguage: "el" },
      React.createElement(Probe)
    )
  );

  assert.match(html, /el/);
});

test("translateText covers dynamic workflow strings from operational records", function () {
  assert.equal(
    translateText("rent | under_review | 880,00 €", "el"),
    "ενοίκιο | υπό εξέταση | 880,00 €"
  );
  assert.equal(
    translateText("Tenant to Landlord", "el"),
    "Ενοικιαστής προς Ιδιοκτήτη"
  );
  assert.equal(
    translateText("Minimum tenant score 650 | Verification 72%", "el"),
    "Ελάχιστη βαθμολογία ενοικιαστή 650 | Επαλήθευση 72%"
  );
  assert.equal(
    translateText("Tenant uploaded transfer proof and bank note for the March payment.", "el"),
    "Ο ενοικιαστής ανέβασε αποδεικτικό μεταφοράς και τραπεζική σημείωση για την πληρωμή Μαρτίου."
  );
});
