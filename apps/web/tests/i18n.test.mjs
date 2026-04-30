import test from "node:test";
import assert from "node:assert/strict";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { LanguageProvider, e, getLanguageLocale, translateText } from "../src/lib/i18n.js";

test("translateText returns Greek labels for key workspace strings", function () {
  assert.equal(translateText("Home", "el"), "Αρχική");
  assert.equal(translateText("My Trust", "el"), "Η αξιοπιστία μου");
  assert.equal(translateText("Rent & Issues", "el"), "Ενοίκια & Θέματα");
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

test("button actions receive hover help bubbles", function () {
  var acceptHtml = renderToStaticMarkup(e("button", { type: "button" }, "Accept"));
  assert.match(acceptHtml, /has-action-tooltip/);
  assert.match(acceptHtml, /data-tooltip="Accept this application so the next step can create the tenancy\."/);

  var directTenancyHtml = renderToStaticMarkup(
    e("button", { type: "button" }, "Create tenancy record")
  );
  assert.match(
    directTenancyHtml,
    /data-tooltip="Create a new tenancy record from the entered property, lease, and counterparty details\."/
  );
  assert.doesNotMatch(directTenancyHtml, /accepted application/);

  var publishHtml = renderToStaticMarkup(
    e("button", { type: "button" }, "Publish to tenant Listings")
  );
  assert.match(
    publishHtml,
    /data-tooltip="Publish this owner-managed home so tenants can find and apply to it\."/
  );

  var confirmHtml = renderToStaticMarkup(e("button", { type: "button" }, "Confirm record"));
  assert.match(
    confirmHtml,
    /data-tooltip="Confirm that this tenancy record matches your side of the agreement\."/
  );

  var tabHtml = renderToStaticMarkup(
    e(
      "button",
      {
        type: "button",
        className: "segmented-tab",
        role: "tab"
      },
      "Sessions"
    )
  );
  assert.doesNotMatch(tabHtml, /has-action-tooltip/);
  assert.doesNotMatch(tabHtml, /data-tooltip=/);

  var languageHtml = renderToStaticMarkup(
    e(
      "button",
      {
        type: "button",
        className: "language-button",
        "aria-label": "Switch language to Greek"
      },
      "EL"
    )
  );
  assert.match(languageHtml, /data-tooltip="Use this button to run the Switch language to Greek action\."/);
});

test("translated nested child arrays do not trigger React key warnings", function () {
  var errors = [];
  var originalError = console.error;
  console.error = function captureError() {
    errors.push(Array.prototype.slice.call(arguments).join(" "));
  };

  try {
    renderToStaticMarkup(
      e("div", null, [
        e("span", null, "One"),
        e("span", null, "Two")
      ])
    );
  } finally {
    console.error = originalError;
  }

  assert.equal(
    errors.some(function includesKeyWarning(message) {
      return message.indexOf('unique "key" prop') !== -1;
    }),
    false
  );
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

test("translateText covers current UX reset and score transparency copy in Greek", function () {
  assert.equal(
    translateText(
      "Sign in securely. The app will open the last valid workspace role for this browser, and you can switch assigned roles from the sidebar.",
      "el"
    ),
    "Συνδέσου με ασφάλεια. Η εφαρμογή θα ανοίξει τον τελευταίο έγκυρο ρόλο αυτού του προγράμματος περιήγησης και μπορείς να αλλάξεις τους ανατεθειμένους ρόλους από την πλευρική μπάρα."
  );
  assert.equal(
    translateText("End this browser session.", "el"),
    "Τερμάτισε αυτή τη συνεδρία του προγράμματος περιήγησης."
  );
  assert.equal(
    translateText("Landlord home for lila tsoutsoura.", "el"),
    "Αρχική ιδιοκτήτη για lila tsoutsoura."
  );
  assert.equal(translateText("Daily work", "el"), "Καθημερινή εργασία");
  assert.equal(translateText("History", "el"), "Ιστορικό");
  assert.equal(
    translateText(
      "History is read-only. Use it when you want to understand what already happened before taking the next action.",
      "el"
    ),
    "Το ιστορικό είναι μόνο για ανάγνωση. Χρησιμοποίησέ το όταν θέλεις να καταλάβεις τι έχει ήδη συμβεί πριν την επόμενη ενέργεια."
  );
  assert.equal(
    translateText("Tenant score contribution preview", "el"),
    "Προεπισκόπηση συνεισφοράς βαθμολογίας ενοικιαστή"
  );
  assert.equal(
    translateText(
      "Use this lane for first verdicts and appealed re-reviews. If a case comes back through an appeal, replace the earlier verdict with a fresh one here.",
      "el"
    ),
    "Χρησιμοποίησε αυτή την ενότητα για πρώτες αποφάσεις και επανελέγχους μετά από έφεση. Αν μια υπόθεση επιστρέψει με έφεση, αντικατάστησε εδώ την προηγούμενη απόφαση με νέα."
  );
  assert.equal(
    translateText("Agency-managed setup unavailable", "el"),
    "Η διαχείριση από πρακτορείο δεν είναι ακόμη διαθέσιμη"
  );
  assert.equal(
    translateText(
      "No agency workspace exists yet. Save this property as owner-managed now; you can assign an agency later.",
      "el"
    ),
    "Δεν υπάρχει ακόμη χώρος πρακτορείου. Αποθήκευσε τώρα το ακίνητο ως διαχειριζόμενο από εσένα και μπορείς να αναθέσεις πρακτορείο αργότερα."
  );
  assert.equal(
    translateText(
      "Create the agency workspace this agent account will operate. After creation, this account becomes the agency owner and can add teammates from Agency Tools.",
      "el"
    ),
    "Δημιούργησε τον χώρο πρακτορείου που θα χειρίζεται αυτός ο λογαριασμός agent. Μετά τη δημιουργία, ο λογαριασμός γίνεται ιδιοκτήτης του πρακτορείου και μπορεί να προσθέσει συνεργάτες από τα Εργαλεία Πρακτορείου."
  );
  assert.equal(
    translateText(
      "Your agent role is active, but this account is not attached to an agency organization yet. Create an agency workspace from Home, or ask an agency owner to invite this account.",
      "el"
    ),
    "Ο ρόλος agent είναι ενεργός, αλλά αυτός ο λογαριασμός δεν είναι ακόμη συνδεδεμένος με οργανισμό πρακτορείου. Δημιούργησε χώρο πρακτορείου από την Αρχική ή ζήτησε από ιδιοκτήτη πρακτορείου να προσκαλέσει αυτόν τον λογαριασμό."
  );
  assert.equal(
    translateText("Open Home to create agency workspace", "el"),
    "Άνοιγμα Αρχικής για δημιουργία χώρου πρακτορείου"
  );
  assert.equal(translateText("Managing agent", "el"), "Υπεύθυνος agent");
  assert.equal(
    translateText("Selected agent email: agent@example.com", "el"),
    "Email επιλεγμένου agent: agent@example.com"
  );
  assert.equal(
    translateText("Property created as agency inventory and ready for listing.", "el"),
    "Το ακίνητο δημιουργήθηκε ως απόθεμα πρακτορείου και είναι έτοιμο για αγγελία."
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
  assert.equal(
    translateText("Showing tenant info only", "el"),
    "Εμφάνιση μόνο πληροφοριών ενοικιαστή"
  );
  assert.equal(
    translateText("Tenant-side score contribution breakdown", "el"),
    "Ανάλυση συνεισφοράς βαθμολογίας ενοικιαστή"
  );
  assert.equal(translateText("5 x +25 pts", "el"), "5 x +25 πόντοι");
  assert.equal(translateText("Tenancy active", "el"), "Ενεργή μίσθωση");
  assert.equal(
    translateText("You already applied to this listing. Current status: Accepted", "el"),
    "Έχεις ήδη κάνει αίτηση σε αυτή την αγγελία. Τρέχουσα κατάσταση: Εγκρίθηκε"
  );
});
