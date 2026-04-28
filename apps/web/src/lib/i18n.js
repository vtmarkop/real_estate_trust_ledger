import React from "react";
import { EL_PATCH_TRANSLATIONS } from "./i18n-extra.js";

var STORAGE_KEY = "trustledger.language";
var SUPPORTED_LANGUAGES = ["en", "el"];
var VISIBLE_PROP_NAMES = new Set(["placeholder", "title", "aria-label", "ariaLabel", "alt"]);
var runtimeLanguage = "en";
var MERGED_EL_TRANSLATIONS = null;

var EL_TRANSLATIONS = {
  "Trust Ledger": "Trust Ledger",
  "Web Workspace": "Χώρος εργασίας Web",
  Home: "Αρχική",
  Workspace: "Χώρος εργασίας",
  "Start here and see what to do next": "Ξεκίνα εδώ και δες τι ακολουθεί",
  "My Trust": "Η Εμπιστοσύνη μου",
  "Scores, sharing, and trust history": "Βαθμολογίες, κοινοποίηση και ιστορικό εμπιστοσύνης",
  Listings: "Αγγελίες",
  "Browse listings and track applications": "Περιήγηση σε αγγελίες και παρακολούθηση αιτήσεων",
  "Rental Records": "Μισθωτικά αρχεία",
  "Leases, evidence, imports, and references": "Μισθώσεις, τεκμήρια, εισαγωγές και συστάσεις",
  "Rent & Issues": "Ενοίκιο & ζητήματα",
  "Payments, deposits, repairs, and disputes": "Πληρωμές, εγγυήσεις, επισκευές και διαφορές",
  "Agency Tools": "Εργαλεία πρακτορείου",
  "Properties, screening, assignments, and applications":
    "Ακίνητα, έλεγχοι, αναθέσεις και αιτήσεις",
  "Review Center": "Κέντρο ελέγχου",
  "Reviews, disputes, automation, audits, and system health":
    "Έλεγχοι, διαφορές, αυτοματισμοί, audit και υγεία συστήματος",
  Account: "Λογαριασμός",
  "Sessions and sign-in activity": "Συνεδρίες και δραστηριότητα σύνδεσης",
  "Access level": "Επίπεδο πρόσβασης",
  "Agency access": "Πρόσβαση πρακτορείου",
  "Workspace mode": "Λειτουργία χώρου",
  "Reviewer tools available": "Διαθέσιμα εργαλεία ελεγκτή",
  "Agency workspace available": "Διαθέσιμος χώρος πρακτορείου",
  "Personal workspace": "Προσωπικός χώρος",
  "Evidence-backed leasing workflows with cleaner operational lanes.":
    "Ροές μίσθωσης με τεκμήρια και καθαρότερους λειτουργικούς διαδρόμους.",
  "internal review": "εσωτερική αξιολόγηση",
  personal: "προσωπικός",
  "personal + agency": "προσωπικός + πρακτορείο",
  "Sign out": "Αποσύνδεση",
  "Signing out...": "Αποσύνδεση...",
  "Evidence-verified rental trust": "Εμπιστοσύνη μίσθωσης με τεκμήρια",
  "A calmer, faster workspace for trust-backed leasing.":
    "Ένας πιο ήρεμος και γρήγορος χώρος εργασίας για μισθώσεις με τεκμηριωμένη εμπιστοσύνη.",
  "Trust Ledger helps tenants, landlords, agencies, and reviewers work from the same evidence-backed rental record instead of scattered messages and guesswork.":
    "Το Trust Ledger βοηθά ενοικιαστές, ιδιοκτήτες, πρακτορεία και ελεγκτές να δουλεύουν πάνω στο ίδιο μισθωτικό ιστορικό με τεκμήρια, αντί για σκόρπια μηνύματα και υποθέσεις.",
  "Sign in": "Σύνδεση",
  "Create an account": "Δημιουργία λογαριασμού",
  Tenant: "Ενοικιαστής",
  "Prove reliability without starting from zero.":
    "Απόδειξε αξιοπιστία χωρίς να ξεκινάς από το μηδέν.",
  "Cold-start trust grows from evidence, references, and verified history.":
    "Η αρχική εμπιστοσύνη χτίζεται από τεκμήρια, συστάσεις και επαληθευμένο ιστορικό.",
  Landlord: "Ιδιοκτήτης",
  "Show operational discipline, not just a listing.":
    "Δείξε συνέπεια στη διαχείριση, όχι μόνο μια αγγελία.",
  "Maintenance, deposits, and response quality are building blocks of trust.":
    "Η συντήρηση, οι εγγυήσεις και η ποιότητα ανταπόκρισης είναι δομικά στοιχεία εμπιστοσύνης.",
  Agency: "Πρακτορείο",
  "Review applicants with shared scores and clear consent.":
    "Αξιολόγησε υποψηφίους με κοινόχρηστες βαθμολογίες και σαφή συγκατάθεση.",
  "Agencies can manage listings, review applications, and run trust checks with an audit trail.":
    "Τα πρακτορεία μπορούν να διαχειρίζονται αγγελίες, να αξιολογούν αιτήσεις και να εκτελούν trust checks με audit trail.",
  Internal: "Εσωτερικό",
  "Keep reviews, automation, and oversight in one place.":
    "Κράτησε ελέγχους, αυτοματισμούς και εποπτεία σε ένα σημείο.",
  "Reviewers and admins can manage queues, audits, and release-readiness from the same workspace.":
    "Οι ελεγκτές και οι διαχειριστές μπορούν να διαχειρίζονται ουρές, audit και ετοιμότητα έκδοσης από τον ίδιο χώρο εργασίας.",
  "Page not found": "Η σελίδα δεν βρέθηκε",
  "The route scaffolding is in place, but this URL is not part of the current web slice.":
    "Η δομή δρομολόγησης υπάρχει, αλλά αυτό το URL δεν ανήκει στο τρέχον κομμάτι της web εφαρμογής.",
  "Return home": "Επιστροφή στην αρχική",
  "Create your Trust Ledger account.": "Δημιούργησε τον λογαριασμό σου στο Trust Ledger.",
  "Welcome back.": "Καλώς ήρθες ξανά.",
  "Create account": "Δημιουργία λογαριασμού",
  "Create a secure account first. After that, you can build your rental record, share your trust profile, and join organizations.":
    "Δημιούργησε πρώτα έναν ασφαλή λογαριασμό. Μετά θα μπορείς να χτίσεις το μισθωτικό σου ιστορικό, να μοιραστείς το προφίλ εμπιστοσύνης σου και να συμμετέχεις σε οργανισμούς.",
  "Sign in to open your workspace, review your records, and continue from where you left off.":
    "Συνδέσου για να ανοίξεις τον χώρο εργασίας σου, να δεις τα αρχεία σου και να συνεχίσεις από εκεί που έμεινες.",
  "Full name": "Ονοματεπώνυμο",
  Email: "Email",
  Password: "Κωδικός",
  "Confirm password": "Επιβεβαίωση κωδικού",
  "Passwords must match before account creation.":
    "Οι κωδικοί πρέπει να ταιριάζουν πριν δημιουργηθεί ο λογαριασμός.",
  "Authentication failed.": "Η ταυτοποίηση απέτυχε.",
  "Creating account...": "Δημιουργία λογαριασμού...",
  "Signing in...": "Σύνδεση...",
  "Already have an account?": "Έχεις ήδη λογαριασμό;",
  "Need an account?": "Χρειάζεσαι λογαριασμό;",
  "Create one": "Δημιούργησε έναν",
  "Loading your trust workspace": "Φόρτωση του χώρου εμπιστοσύνης σου",
  "We are restoring your score snapshot and organization memberships from the rebuilt API.":
    "Επαναφέρουμε το στιγμιότυπο βαθμολογίας σου και τις συμμετοχές σου σε οργανισμούς από το νέο API.",
  "Workspace data unavailable": "Τα δεδομένα του χώρου εργασίας δεν είναι διαθέσιμα",
  "What each menu item does": "Τι κάνει κάθε στοιχείο του μενού",
  "If the menu feels unfamiliar, use this as a quick map. Each area is focused on one part of the rental journey.":
    "Αν το μενού σου φαίνεται άγνωστο, χρησιμοποίησέ το σαν γρήγορο χάρτη. Κάθε ενότητα αντιστοιχεί σε ένα μέρος της μισθωτικής διαδρομής.",
  "This is your starting point. Use the menu on the left to move between your trust profile, rental records, day-to-day tenancy operations, listings, and account tools.":
    "Αυτό είναι το σημείο εκκίνησής σου. Χρησιμοποίησε το μενού αριστερά για να μετακινείσαι ανάμεσα στο προφίλ εμπιστοσύνης, τα μισθωτικά αρχεία, τις καθημερινές λειτουργίες μίσθωσης, τις αγγελίες και τα εργαλεία λογαριασμού.",
  "Open My Trust": "Άνοιγμα της εμπιστοσύνης μου",
  "Browse listings": "Περιήγηση σε αγγελίες",
  "Open rental records": "Άνοιγμα μισθωτικών αρχείων",
  "Installable workspace": "Εγκαταστάσιμος χώρος εργασίας",
  "This device is already running the workspace in installed mode.":
    "Αυτή η συσκευή τρέχει ήδη τον χώρο εργασίας σε εγκατεστημένη μορφή.",
  "The rebuilt web app now exposes a manifest and service worker so supported browsers can offer an install flow for quicker repeat access.":
    "Η νέα web εφαρμογή εκθέτει πλέον manifest και service worker ώστε οι συμβατοί browsers να προσφέρουν εγκατάσταση για ταχύτερη επαναλαμβανόμενη πρόσβαση.",
  Installed: "Εγκαταστάθηκε",
  "Install app shell": "Εγκατάσταση εφαρμογής",
  "Mobile-ready shell": "Κέλυφος έτοιμο για κινητό",
  "Install is available in this browser for faster repeat access.":
    "Η εγκατάσταση είναι διαθέσιμη σε αυτόν τον browser για γρηγορότερη επαναλαμβανόμενη πρόσβαση.",
  "Trust Ledger is now installed on this device.":
    "Το Trust Ledger είναι πλέον εγκατεστημένο σε αυτή τη συσκευή.",
  "This browser is not currently offering an install prompt.":
    "Αυτός ο browser δεν προσφέρει αυτή τη στιγμή προτροπή εγκατάστασης.",
  "Install prompt completed. If the app was not installed, the browser may have dismissed it.":
    "Η διαδικασία προτροπής εγκατάστασης ολοκληρώθηκε. Αν η εφαρμογή δεν εγκαταστάθηκε, ο browser ίσως την απέρριψε.",
  "Opening install...": "Άνοιγμα εγκατάστασης...",
  "Tenant score": "Βαθμολογία ενοικιαστή",
  "Verification strength": "Ισχύς επαλήθευσης",
  Organizations: "Οργανισμοί",
  "Current evidence-backed tenant score from the canonical scoring service.":
    "Η τρέχουσα βαθμολογία ενοικιαστή με βάση τεκμήρια από την κεντρική υπηρεσία scoring.",
  "Confidence level based on accepted evidence, confirmations, and reviewed history.":
    "Επίπεδο εμπιστοσύνης με βάση αποδεκτά τεκμήρια, επιβεβαιώσεις και ελεγμένο ιστορικό.",
  "Active memberships discovered through the new organization lookup endpoint.":
    "Ενεργές συμμετοχές που βρέθηκαν μέσω του νέου endpoint αναζήτησης οργανισμών.",
  "No active organization memberships yet. You can still use your personal trust profile.":
    "Δεν υπάρχουν ακόμη ενεργές συμμετοχές σε οργανισμούς. Μπορείς ακόμη να χρησιμοποιήσεις το προσωπικό σου προφίλ εμπιστοσύνης.",
  "Trust profile snapshot": "Στιγμιότυπο προφίλ εμπιστοσύνης",
  "Primary score agencies and landlords can eventually review with consent.":
    "Η βασική βαθμολογία που μπορούν να δουν πρακτορεία και ιδιοκτήτες με συγκατάθεση.",
  "Landlord score": "Βαθμολογία ιδιοκτήτη",
  "Separate landlord-side signal so a single account can build trust in both directions.":
    "Ξεχωριστό σήμα για την πλευρά του ιδιοκτήτη, ώστε ένας λογαριασμός να χτίζει εμπιστοσύνη και προς τις δύο κατευθύνσεις.",
  "Scoring version": "Έκδοση scoring",
  "Canonical model version currently powering both self-service and agency-facing score reads.":
    "Η τρέχουσα έκδοση του κεντρικού μοντέλου που τροφοδοτεί τόσο την αυτοεξυπηρέτηση όσο και τις αναγνώσεις βαθμολογίας για πρακτορεία.",
  "Your active organizations": "Οι ενεργοί οργανισμοί σου",
  "No active agency or internal memberships are attached to this account yet.":
    "Δεν υπάρχουν ακόμη ενεργές συμμετοχές σε πρακτορεία ή εσωτερικές ομάδες για αυτόν τον λογαριασμό.",
  "Loading live listings": "Φόρτωση ζωντανών αγγελιών",
  "We are loading available listings and your applications.":
    "Φορτώνουμε τις διαθέσιμες αγγελίες και τις αιτήσεις σου.",
  "Marketplace data unavailable": "Τα δεδομένα της αγοράς δεν είναι διαθέσιμα",
  "Submitted from the rebuilt marketplace.": "Υποβλήθηκε από τη νέα αγορά.",
  "Application submitted successfully.": "Η αίτηση υποβλήθηκε με επιτυχία.",
  "Unable to submit the application.": "Δεν ήταν δυνατή η υποβολή της αίτησης.",
  "Available listings": "Διαθέσιμες αγγελίες",
  Applications: "Αιτήσεις",
  "My applications": "Οι αιτήσεις μου",
  "There are no open listings available right now.":
    "Δεν υπάρχουν διαθέσιμες ανοιχτές αγγελίες αυτή τη στιγμή.",
  "You have not submitted any listing applications yet.":
    "Δεν έχεις υποβάλει ακόμη καμία αίτηση σε αγγελία.",
  "Open listings": "Ανοιχτές αγγελίες",
  "Loading trust score profile": "Φόρτωση προφίλ βαθμολογίας εμπιστοσύνης",
  "We are loading your scores, sharing permissions, and trust history.":
    "Φορτώνουμε τις βαθμολογίες σου, τα δικαιώματα κοινοποίησης και το ιστορικό εμπιστοσύνης.",
  "Trust data unavailable": "Τα δεδομένα εμπιστοσύνης δεν είναι διαθέσιμα",
  Scores: "Βαθμολογίες",
  "What affects my score": "Τι επηρεάζει τη βαθμολογία μου",
  "Activity that shaped my record": "Δραστηριότητα που διαμόρφωσε το αρχείο μου",
  "Who opened my shared report": "Ποιος άνοιξε την κοινόχρηστη αναφορά μου",
  "Score updates over time": "Μεταβολές βαθμολογίας στον χρόνο",
  "Share my profile with an agency": "Κοινοποίηση του προφίλ μου σε πρακτορείο",
  "Check a shared trust profile": "Έλεγχος κοινοποιημένου προφίλ εμπιστοσύνης",
  "Use a share token and access code to confirm access, preview a profile, or save a trust check to your agency history.":
    "Χρησιμοποίησε token κοινοποίησης και κωδικό πρόσβασης για να επιβεβαιώσεις πρόσβαση, να δεις προεπισκόπηση προφίλ ή να αποθηκεύσεις trust check στο ιστορικό του πρακτορείου.",
  "Choose an agency, set an access code, and create a revocable share token.":
    "Επίλεξε πρακτορείο, όρισε κωδικό πρόσβασης και δημιούργησε token κοινοποίησης που μπορεί να ανακληθεί.",
  "No trust-report consents have been issued yet.":
    "Δεν έχουν εκδοθεί ακόμη συγκαταθέσεις για trust report.",
  "No agency access events have been recorded against your shared trust report yet.":
    "Δεν έχουν καταγραφεί ακόμη συμβάντα πρόσβασης πρακτορείου στο κοινόχρηστο trust report σου.",
  "Trust profile preview loaded.": "Η προεπισκόπηση του προφίλ εμπιστοσύνης φορτώθηκε.",
  "Agency trust check created successfully.": "Το trust check του πρακτορείου δημιουργήθηκε με επιτυχία.",
  "Consent access validated successfully.": "Η πρόσβαση στη συγκατάθεση επικυρώθηκε με επιτυχία.",
  "This consent is no longer active.": "Αυτή η συγκατάθεση δεν είναι πλέον ενεργή.",
  "Loading records and imports": "Φόρτωση αρχείων και εισαγωγών",
  "We are loading your properties, tenancy records, uploaded evidence, past-history imports, and reference requests.":
    "Φορτώνουμε τα ακίνητά σου, τα αρχεία μισθώσεων, τα ανεβασμένα τεκμήρια, τις εισαγωγές ιστορικού και τα αιτήματα συστάσεων.",
  "Records unavailable": "Τα αρχεία δεν είναι διαθέσιμα",
  "Rent, deposit, and repair tracking": "Παρακολούθηση ενοικίου, εγγύησης και επισκευών",
  "Use a saved property": "Χρήση αποθηκευμένου ακινήτου",
  "Create from a new address": "Δημιουργία από νέα διεύθυνση",
  "Add a tenancy record": "Προσθήκη αρχείου μίσθωσης",
  "Create tenancy record": "Δημιουργία αρχείου μίσθωσης",
  "Tenancy record created successfully.": "Το αρχείο μίσθωσης δημιουργήθηκε με επιτυχία.",
  "Unable to create tenancy record.": "Δεν ήταν δυνατή η δημιουργία του αρχείου μίσθωσης.",
  "Only properties you created can be reused for a new tenancy record.":
    "Μόνο ακίνητα που δημιούργησες εσύ μπορούν να επαναχρησιμοποιηθούν για νέο αρχείο μίσθωσης.",
  "Save property setup": "Αποθήκευση ρύθμισης ακινήτου",
  "Property saved and ready to assign.": "Το ακίνητο αποθηκεύτηκε και είναι έτοιμο για ανάθεση.",
  "Unable to create property.": "Δεν ήταν δυνατή η δημιουργία ακινήτου.",
  "Property created and ready for listing.": "Το ακίνητο δημιουργήθηκε και είναι έτοιμο για αγγελία.",
  "No reusable property records yet. Enter a new address below.":
    "Δεν υπάρχουν ακόμη επαναχρησιμοποιήσιμα αρχεία ακινήτων. Καταχώρισε νέα διεύθυνση παρακάτω.",
  "No saved property records are linked to this account yet.":
    "Δεν υπάρχουν ακόμη αποθηκευμένα αρχεία ακινήτων συνδεδεμένα με αυτόν τον λογαριασμό.",
  "No tenancy records are attached to this account yet.":
    "Δεν υπάρχουν ακόμη αρχεία μίσθωσης συνδεδεμένα με αυτόν τον λογαριασμό.",
  "No evidence has been attached to this tenancy yet.":
    "Δεν έχουν συνδεθεί ακόμη τεκμήρια σε αυτή τη μίσθωση.",
  "History imports": "Εισαγωγές ιστορικού",
  "Past rental history": "Προηγούμενο ιστορικό μίσθωσης",
  "Create import draft": "Δημιουργία πρόχειρης εισαγωγής",
  "History import draft created.": "Το πρόχειρο εισαγωγής ιστορικού δημιουργήθηκε.",
  "History import submitted for review.": "Η εισαγωγή ιστορικού υποβλήθηκε για έλεγχο.",
  "No history imports have been created yet.": "Δεν έχουν δημιουργηθεί ακόμη εισαγωγές ιστορικού.",
  "Counterparty reference": "Σύσταση αντισυμβαλλομένου",
  "Request reference": "Αίτημα σύστασης",
  "Counterparty reference request created.": "Το αίτημα σύστασης αντισυμβαλλομένου δημιουργήθηκε.",
  "Counterparty reference submitted.": "Η σύσταση αντισυμβαλλομένου υποβλήθηκε.",
  "No pending reference requests are waiting for your response.":
    "Δεν υπάρχουν εκκρεμή αιτήματα συστάσεων που να περιμένουν την απάντησή σου.",
  "Evidence submitted successfully.": "Το τεκμήριο υποβλήθηκε με επιτυχία.",
  "Unable to submit evidence.": "Δεν ήταν δυνατή η υποβολή του τεκμηρίου.",
  "Evidence artifact opened in a new tab.": "Το αρχείο τεκμηρίου άνοιξε σε νέα καρτέλα.",
  "Unable to open the evidence artifact.": "Δεν ήταν δυνατό να ανοίξει το αρχείο τεκμηρίου.",
  "Loading operational ledger": "Φόρτωση λειτουργικού καθολικού",
  "We are loading payments, deposit activity, and maintenance updates.":
    "Φορτώνουμε πληρωμές, δραστηριότητα εγγυήσεων και ενημερώσεις συντήρησης.",
  "Operations unavailable": "Οι λειτουργίες δεν είναι διαθέσιμες",
  "Use this page for the day-to-day side of a tenancy: rent records, deposit handling, and maintenance issues.":
    "Χρησιμοποίησε αυτήν τη σελίδα για την καθημερινή πλευρά μιας μίσθωσης: αρχεία ενοικίου, διαχείριση εγγύησης και ζητήματα συντήρησης.",
  Payments: "Πληρωμές",
  Deposit: "Εγγύηση",
  Maintenance: "Συντήρηση",
  "Dispute desk": "Κέντρο διαφορών",
  "There are no open disputes across your current tenancy records.":
    "Δεν υπάρχουν ανοιχτές διαφορές στα τρέχοντα αρχεία μισθώσεών σου.",
  "Create payment record": "Δημιουργία εγγραφής πληρωμής",
  "Payment record created.": "Η εγγραφή πληρωμής δημιουργήθηκε.",
  "Payment proof submitted.": "Το αποδεικτικό πληρωμής υποβλήθηκε.",
  "Payment confirmed.": "Η πληρωμή επιβεβαιώθηκε.",
  "Payment rejected.": "Η πληρωμή απορρίφθηκε.",
  "Payment dispute submitted.": "Η διαφορά πληρωμής υποβλήθηκε.",
  "Payment appeal submitted.": "Η έφεση πληρωμής υποβλήθηκε.",
  "Open payment disputes": "Ανοιχτές διαφορές πληρωμών",
  "Open proof file": "Άνοιγμα αρχείου απόδειξης",
  "Submit proof": "Υποβολή απόδειξης",
  "Dispute payment": "Αμφισβήτηση πληρωμής",
  "Appeal verdict": "Έφεση κατά απόφασης",
  "Open deposit record": "Άνοιγμα αρχείου εγγύησης",
  "Deposit record opened.": "Το αρχείο εγγύησης άνοιξε.",
  "Deposit settlement submitted.": "Ο διακανονισμός εγγύησης υποβλήθηκε.",
  "Deposit dispute submitted.": "Η διαφορά εγγύησης υποβλήθηκε.",
  "Open deposit disputes": "Ανοιχτές διαφορές εγγυήσεων",
  "Submit settlement": "Υποβολή διακανονισμού",
  "Dispute settlement": "Αμφισβήτηση διακανονισμού",
  "Report issue": "Αναφορά ζητήματος",
  "Maintenance issue reported.": "Το ζήτημα συντήρησης αναφέρθηκε.",
  "Maintenance ticket acknowledged.": "Το αίτημα συντήρησης επιβεβαιώθηκε.",
  "Maintenance ticket resolved.": "Το αίτημα συντήρησης επιλύθηκε.",
  "Maintenance dispute submitted.": "Η διαφορά συντήρησης υποβλήθηκε.",
  "Maintenance appeal submitted.": "Η έφεση συντήρησης υποβλήθηκε.",
  "Open maintenance disputes": "Ανοιχτές διαφορές συντήρησης",
  "Dispute maintenance resolution": "Αμφισβήτηση επίλυσης συντήρησης",
  "Loading account security": "Φόρτωση ασφάλειας λογαριασμού",
  "We are loading your active sessions and recent sign-in events.":
    "Φορτώνουμε τις ενεργές συνεδρίες σου και τα πρόσφατα συμβάντα σύνδεσης.",
  "Security data unavailable": "Τα δεδομένα ασφαλείας δεν είναι διαθέσιμα",
  "Account security": "Ασφάλεια λογαριασμού",
  "Your devices and sign-in activity": "Οι συσκευές σου και η δραστηριότητα σύνδεσης",
  "Use this page to review where your account is signed in and to sign out of other devices if needed.":
    "Χρησιμοποίησε αυτήν τη σελίδα για να δεις πού είναι συνδεδεμένος ο λογαριασμός σου και να αποσυνδέσεις άλλες συσκευές αν χρειάζεται.",
  "Current session": "Τρέχουσα συνεδρία",
  "Known sessions": "Γνωστές συνεδρίες",
  "Recent sign-in events": "Πρόσφατα συμβάντα σύνδεσης",
  "Sign out this device": "Αποσύνδεση αυτής της συσκευής",
  "Sign out of other devices": "Αποσύνδεση άλλων συσκευών",
  "Selected session signed out.": "Η επιλεγμένη συνεδρία αποσυνδέθηκε.",
  "Other devices were signed out.": "Οι άλλες συσκευές αποσυνδέθηκαν.",
  "Unable to sign out this session.": "Δεν ήταν δυνατή η αποσύνδεση αυτής της συνεδρίας.",
  "Agency tools unavailable": "Τα εργαλεία πρακτορείου δεν είναι διαθέσιμα",
  "Agency data unavailable": "Τα δεδομένα του πρακτορείου δεν είναι διαθέσιμα",
  "The agency dashboard is initializing.": "Ο πίνακας πρακτορείου αρχικοποιείται.",
  "This account is not attached to an active agency organization, so agency tools are not available yet.":
    "Αυτός ο λογαριασμός δεν είναι συνδεδεμένος με ενεργό οργανισμό πρακτορείου, οπότε τα εργαλεία πρακτορείου δεν είναι ακόμη διαθέσιμα.",
  "Use this page to add properties, publish listings, review applicants, run trust checks, and keep an eye on agency activity.":
    "Χρησιμοποίησε αυτήν τη σελίδα για να προσθέτεις ακίνητα, να δημοσιεύεις αγγελίες, να αξιολογείς υποψηφίους, να εκτελείς trust checks και να παρακολουθείς τη δραστηριότητα του πρακτορείου.",
  "Business snapshot": "Επιχειρησιακό στιγμιότυπο",
  "Recent screening": "Πρόσφατος έλεγχος",
  "Estate portfolio": "Χαρτοφυλάκιο ακινήτων",
  "Browse your saved properties, search them quickly, and keep custom tags up to date so you can find estates faster.":
    "Περιηγήσου στα αποθηκευμένα σου ακίνητα, βρες τα γρήγορα και κράτα τις προσαρμοσμένες ετικέτες ενημερωμένες ώστε να εντοπίζεις ακίνητα πιο εύκολα.",
  "Find by label, city, or tag": "Αναζήτηση με ετικέτα, πόλη ή tag",
  "No properties match the current filter.": "Κανένα ακίνητο δεν ταιριάζει με το τρέχον φίλτρο.",
  "No custom tags have been added to this property yet.":
    "Δεν έχουν προστεθεί ακόμη προσαρμοσμένα tags σε αυτό το ακίνητο.",
  "Edit custom tags": "Επεξεργασία προσαρμοσμένων tags",
  "Save tags": "Αποθήκευση tags",
  "Property tags saved.": "Τα tags του ακινήτου αποθηκεύτηκαν.",
  "Unable to save property tags.": "Δεν ήταν δυνατή η αποθήκευση των tags του ακινήτου.",
  "Team access": "Πρόσβαση ομάδας",
  "Invite agency teammates by email and keep roles up to date without leaving this workspace.":
    "Προσκάλεσε μέλη της ομάδας του πρακτορείου με email και κράτα τους ρόλους ενημερωμένους χωρίς να φύγεις από αυτόν τον χώρο εργασίας.",
  "You can see who belongs to this agency here. Owners and managers can update access.":
    "Εδώ μπορείς να δεις ποιος ανήκει σε αυτό το πρακτορείο. Οι owners και managers μπορούν να ενημερώνουν την πρόσβαση.",
  "Add team member": "Προσθήκη μέλους ομάδας",
  "Adding member...": "Προσθήκη μέλους...",
  "Team member added.": "Το μέλος ομάδας προστέθηκε.",
  "Unable to add this team member.": "Δεν ήταν δυνατή η προσθήκη αυτού του μέλους.",
  "No team memberships are attached to this agency yet.":
    "Δεν υπάρχουν ακόμη συμμετοχές ομάδας σε αυτό το πρακτορείο.",
  "Loading live operational state": "Φόρτωση ζωντανής λειτουργικής κατάστασης",
  "We are loading review queues, automation tasks, audits, and release-readiness data.":
    "Φορτώνουμε ουρές ελέγχου, εργασίες αυτοματισμού, audit και δεδομένα ετοιμότητας έκδοσης.",
  "Overview unavailable": "Η επισκόπηση δεν είναι διαθέσιμη",
  "Use this page to review pending work, monitor automation, inspect audits, and check whether the platform is ready for release.":
    "Χρησιμοποίησε αυτήν τη σελίδα για να ελέγχεις εκκρεμείς εργασίες, να παρακολουθείς αυτοματισμούς, να επιθεωρείς audit και να βλέπεις αν η πλατφόρμα είναι έτοιμη για έκδοση.",
  "Review queues and system health": "Ουρές ελέγχου και υγεία συστήματος",
  "Release readiness": "Ετοιμότητα έκδοσης",
  Automation: "Αυτοματισμός",
  Workers: "Workers",
  Notifications: "Ειδοποιήσεις",
  "Recent audit activity": "Πρόσφατη δραστηριότητα audit",
  "Score controls": "Έλεγχοι scoring",
  "Follow-up controls": "Έλεγχοι follow-up",
  "Claim due tasks": "Ανάληψη ληξιπρόθεσμων εργασιών",
  "Clean stale follow-ups": "Καθαρισμός παλιών follow-up",
  "Clean expired consent reminders": "Καθαρισμός ληγμένων υπενθυμίσεων συγκατάθεσης",
  "Due score recalculation requests": "Ληξιπρόθεσμα αιτήματα επαναϋπολογισμού score",
  "No score refresh requests are waiting right now.":
    "Δεν υπάρχουν αυτή τη στιγμή αιτήματα ανανέωσης score σε αναμονή.",
  "No score batches have been queued yet.": "Δεν έχουν μπει ακόμη παρτίδες score στην ουρά.",
  "No notification deliveries have been queued yet.":
    "Δεν έχουν μπει ακόμη αποστολές ειδοποιήσεων στην ουρά.",
  "No worker runs have been recorded yet.": "Δεν έχουν καταγραφεί ακόμη εκτελέσεις worker.",
  "No audit events match the current filter.": "Κανένα συμβάν audit δεν ταιριάζει με το τρέχον φίλτρο.",
  "No evidence reviews are waiting right now.":
    "Δεν υπάρχουν έλεγχοι τεκμηρίων σε αναμονή αυτή τη στιγμή.",
  "No history-import reviews are waiting right now.":
    "Δεν υπάρχουν έλεγχοι εισαγωγών ιστορικού σε αναμονή αυτή τη στιγμή.",
  "No tenancy reviews are waiting right now.":
    "Δεν υπάρχουν έλεγχοι μισθώσεων σε αναμονή αυτή τη στιγμή.",
  "No payment disputes are waiting for review right now.":
    "Δεν υπάρχουν διαφορές πληρωμών που να περιμένουν έλεγχο αυτή τη στιγμή.",
  "No maintenance disputes are waiting for review right now.":
    "Δεν υπάρχουν διαφορές συντήρησης που να περιμένουν έλεγχο αυτή τη στιγμή.",
  "Queue refresh": "Καταχώριση ανανέωσης",
  "Recalculate now": "Επαναϋπολογισμός τώρα",
  "Queue organization batch": "Ουρά παρτίδας οργανισμού",
  "Score refresh request queued.": "Το αίτημα ανανέωσης score μπήκε στην ουρά.",
  "Score recalculated immediately.": "Το score επανυπολογίστηκε άμεσα.",
  "Organization score batch queued.": "Η παρτίδα score του οργανισμού μπήκε στην ουρά.",
  "Unable to queue the score refresh request.": "Δεν ήταν δυνατή η καταχώριση του αιτήματος ανανέωσης score.",
  "Unable to process this score request.": "Δεν ήταν δυνατή η επεξεργασία αυτού του αιτήματος score.",
  "Unable to create the score batch.": "Δεν ήταν δυνατή η δημιουργία της παρτίδας score.",
  "Create follow-up task": "Δημιουργία follow-up εργασίας",
  "Create manual follow-up tasks when a reviewer needs to chase missing evidence, contact a user, or track an operational edge case.":
    "Δημιούργησε χειροκίνητες follow-up εργασίες όταν ένας ελεγκτής πρέπει να αναζητήσει ελλιπή τεκμήρια, να επικοινωνήσει με χρήστη ή να παρακολουθήσει μια λειτουργική ιδιαιτερότητα.",
  "Follow-up task created.": "Η follow-up εργασία δημιουργήθηκε.",
  "Unable to create the follow-up task.": "Δεν ήταν δυνατή η δημιουργία της follow-up εργασίας.",
  "Unable to claim automation tasks.": "Δεν ήταν δυνατή η ανάληψη των εργασιών αυτοματισμού.",
  "Unable to execute this automation task.": "Δεν ήταν δυνατή η εκτέλεση αυτής της εργασίας αυτοματισμού.",
  "Unable to run the cleanup right now.": "Δεν ήταν δυνατή η εκτέλεση του καθαρισμού αυτή τη στιγμή.",
  "Request failed.": "Το αίτημα απέτυχε.",
  "Unable to sign in.": "Δεν ήταν δυνατή η σύνδεση.",
  "Unable to restore the current session.": "Δεν ήταν δυνατή η επαναφορά της τρέχουσας συνεδρίας.",
  "Unable to load workspace data.": "Δεν ήταν δυνατή η φόρτωση των δεδομένων του χώρου εργασίας.",
  "Unable to load your trust profile.": "Δεν ήταν δυνατή η φόρτωση του προφίλ εμπιστοσύνης σου.",
  "Unable to load marketplace data.": "Δεν ήταν δυνατή η φόρτωση των δεδομένων της αγοράς.",
  "Unable to load record-management surfaces.": "Δεν ήταν δυνατή η φόρτωση των επιφανειών διαχείρισης αρχείων.",
  "Unable to load operational ledger data.": "Δεν ήταν δυνατή η φόρτωση των δεδομένων λειτουργικού καθολικού.",
  "Unable to load the agency dashboard.": "Δεν ήταν δυνατή η φόρτωση του πίνακα πρακτορείου.",
  "Unable to load the operations overview.": "Δεν ήταν δυνατή η φόρτωση της επισκόπησης λειτουργιών.",
  "Unable to load security details.": "Δεν ήταν δυνατή η φόρτωση των στοιχείων ασφαλείας.",
  "Unable to load organization memberships.": "Δεν ήταν δυνατή η φόρτωση των συμμετοχών οργανισμών.",
  "value is not a valid email address": "η τιμή δεν είναι έγκυρη διεύθυνση email",
  "The part after the @-sign is a special-use or reserved name that cannot be used with email.":
    "Το τμήμα μετά το @ είναι ειδικής χρήσης ή δεσμευμένο όνομα και δεν μπορεί να χρησιμοποιηθεί σε email.",
  "Field required": "Το πεδίο είναι υποχρεωτικό",
  body: "σώμα",
  query: "ερώτημα",
  path: "διαδρομή",
  email: "email",
  password: "κωδικός",
  "No active agencies are currently available in the directory.":
    "Δεν υπάρχουν αυτή τη στιγμή ενεργά πρακτορεία στον κατάλογο.",
  Accept: "Αποδοχή",
  Reject: "Απόρριψη",
  Pause: "Παύση",
  Close: "Κλείσιμο",
  Reopen: "Επαναφορά",
  Cancel: "Ακύρωση",
  Confirm: "Επιβεβαίωση",
  Save: "Αποθήκευση",
  "Save property": "Αποθήκευση ακινήτου",
  "Save access": "Αποθήκευση πρόσβασης",
  "Save screening settings": "Αποθήκευση ρυθμίσεων ελέγχου",
  "Save trust check": "Αποθήκευση trust check",
  "Open artifact": "Άνοιγμα αρχείου",
  "Open counterparty evidence": "Άνοιγμα τεκμηρίου αντισυμβαλλομένου",
  "Open reported evidence": "Άνοιγμα αναφερθέντος τεκμηρίου",
  "Open resolution file": "Άνοιγμα αρχείου επίλυσης",
  "Open settlement proof": "Άνοιγμα απόδειξης διακανονισμού",
  Evidence: "Τεκμήριο",
  "Artifact file": "Αρχείο τεκμηρίου",
  "Artifact name": "Όνομα αρχείου",
  "Document type": "Τύπος εγγράφου",
  Description: "Περιγραφή",
  Address: "Διεύθυνση",
  City: "Πόλη",
  Country: "Χώρα",
  "Property label": "Ετικέτα ακινήτου",
  "Custom tags": "Προσαρμοσμένα tags",
  "Agent email": "Email agent",
  "Prospective tenant email": "Email υποψήφιου ενοικιαστή",
  "Landlord email": "Email ιδιοκτήτη",
  "Tenant email": "Email ενοικιαστή",
  "Lease start date": "Ημερομηνία έναρξης μίσθωσης",
  "Lease end date": "Ημερομηνία λήξης μίσθωσης",
  "Monthly rent": "Μηνιαίο ενοίκιο",
  Currency: "Νόμισμα",
  "Access code": "Κωδικός πρόσβασης",
  "Share token": "Token κοινοποίησης",
  "Team member email": "Email μέλους ομάδας",
  Role: "Ρόλος",
  Owner: "Ιδιοκτήτης",
  Manager: "Manager",
  Member: "Μέλος",
  Reviewer: "Ελεγκτής",
  Admin: "Διαχειριστής",
  User: "Χρήστης",
  "Under review": "Υπό αξιολόγηση",
  Accepted: "Εγκρίθηκε",
  Rejected: "Απορρίφθηκε",
  Submitted: "Υποβλήθηκε",
  Pending: "Σε εκκρεμότητα",
  Active: "Ενεργό",
  Inactive: "Ανενεργό",
  Completed: "Ολοκληρώθηκε",
  Closed: "Κλειστό",
  Open: "Ανοιχτό",
  open: "ανοιχτό",
  paused: "σε παύση",
  closed: "κλειστό",
  Normal: "Κανονικό",
  Low: "Χαμηλό",
  High: "Υψηλό",
  Urgent: "Επείγον",
  "Favors tenant": "Υπέρ ενοικιαστή",
  "Favors landlord": "Υπέρ ιδιοκτήτη",
  "Shared fault": "Κοινή υπαιτιότητα",
  Inconclusive: "Ασαφές",
  Amount: "Ποσό",
  Status: "Κατάσταση",
  Reason: "Λόγος",
  Outcome: "Αποτέλεσμα",
  Scope: "Εμβέλεια",
  Target: "Στόχος",
  Subject: "Θέμα",
  "Your role": "Ο ρόλος σου",
  "Current status": "Τρέχουσα κατάσταση",
  "Applications in last 30 days": "Αιτήσεις τις τελευταίες 30 ημέρες",
  "Trust checks in last 30 days": "Trust checks τις τελευταίες 30 ημέρες",
  "Tracked properties": "Παρακολουθούμενα ακίνητα",
  "Active members": "Ενεργά μέλη",
  "Sent notifications": "Σταλμένες ειδοποιήσεις",
  "Denied logins": "Απορριφθείσες συνδέσεις",
  "Failed access attempts": "Αποτυχημένες προσπάθειες πρόσβασης",
  "Average verification strength": "Μέση ισχύς επαλήθευσης",
  "Average applicant score": "Μέση βαθμολογία υποψηφίων",
  "Open listings without applicants": "Ανοιχτές αγγελίες χωρίς υποψηφίους",
  "total applications across the agency pipeline.": "συνολικές αιτήσεις στη ροή του πρακτορείου.",
  "total listings under this agency organization.": "συνολικές αγγελίες σε αυτόν τον οργανισμό πρακτορείου.",
  "total trust checks on record.": "συνολικά trust checks στο αρχείο."
};

function normalizeLanguage(language) {
  return SUPPORTED_LANGUAGES.indexOf(language) >= 0 ? language : "en";
}

function detectDefaultLanguage() {
  if (typeof window === "undefined") {
    return "en";
  }

  try {
    var storedLanguage = window.localStorage.getItem(STORAGE_KEY);
    if (storedLanguage) {
      return normalizeLanguage(storedLanguage);
    }
  } catch (error) {}

  var browserLanguage =
    (window.navigator && (window.navigator.language || window.navigator.userLanguage)) || "en";
  return String(browserLanguage).toLowerCase().indexOf("el") === 0 ? "el" : "en";
}

runtimeLanguage = detectDefaultLanguage();

function getDictionary(language) {
  if (language === "el") {
    if (!MERGED_EL_TRANSLATIONS) {
      MERGED_EL_TRANSLATIONS = Object.assign({}, EL_TRANSLATIONS, EL_PATCH_TRANSLATIONS);
    }
    return MERGED_EL_TRANSLATIONS;
  }
  return {};
}

function toTitleCaseWords(value) {
  return String(value).replace(/\b\w/g, function capitalize(character) {
    return character.toUpperCase();
  });
}

function translateCore(value, language) {
  var dictionary = getDictionary(language);
  if (Object.prototype.hasOwnProperty.call(dictionary, value)) {
    return dictionary[value];
  }

  if (/^[a-z0-9_]+$/.test(value)) {
    var spacedToken = value.replace(/_/g, " ");
    var titledToken = toTitleCaseWords(spacedToken);
    if (Object.prototype.hasOwnProperty.call(dictionary, spacedToken)) {
      return dictionary[spacedToken];
    }
    if (Object.prototype.hasOwnProperty.call(dictionary, titledToken)) {
      return dictionary[titledToken];
    }
  }

  if (/^[a-z][a-z0-9 ]+$/.test(value)) {
    var titleCandidate = toTitleCaseWords(value);
    if (Object.prototype.hasOwnProperty.call(dictionary, titleCandidate)) {
      return dictionary[titleCandidate];
    }
  }

  if (value.indexOf("|") !== -1) {
    var translatedPipeValue = value
      .split("|")
      .map(function translatePipeSegment(segment) {
        var leadingWhitespaceMatch = segment.match(/^\s*/);
        var trailingWhitespaceMatch = segment.match(/\s*$/);
        var leadingWhitespace = leadingWhitespaceMatch ? leadingWhitespaceMatch[0] : "";
        var trailingWhitespace = trailingWhitespaceMatch ? trailingWhitespaceMatch[0] : "";
        var coreSegment = segment.trim();

        if (!coreSegment) {
          return segment;
        }

        return (
          leadingWhitespace + translateCore(coreSegment, language) + trailingWhitespace
        );
      })
      .join("|");

    if (translatedPipeValue !== value) {
      return translatedPipeValue;
    }
  }

  var alreadyAppliedEarlyMatch = value.match(/^You already applied to this listing\. Current status: (.+)$/);
  if (alreadyAppliedEarlyMatch) {
    return "Έχεις ήδη κάνει αίτηση σε αυτή την αγγελία. Τρέχουσα κατάσταση: " + translateCore(alreadyAppliedEarlyMatch[1], language);
  }

  if (value.indexOf(" to ") !== -1) {
    var relationshipSegments = value.split(" to ");
    if (relationshipSegments.length === 2) {
      var translatedFrom = translateCore(relationshipSegments[0], language);
      var translatedTo = translateCore(relationshipSegments[1], language);
      if (
        translatedFrom !== relationshipSegments[0] ||
        translatedTo !== relationshipSegments[1]
      ) {
        return translatedFrom + " προς " + translatedTo;
      }
    }
  }

  if (value.indexOf(": ") !== -1) {
    var delimiterIndex = value.indexOf(": ");
    var prefix = value.slice(0, delimiterIndex);
    var suffix = value.slice(delimiterIndex + 2);
    var translatedPrefix = translateCore(prefix, language);
    var translatedSuffix = translateCore(suffix, language);
    if (translatedPrefix !== prefix || translatedSuffix !== suffix) {
      return translatedPrefix + ": " + translatedSuffix;
    }
  }

  if (value.endsWith(":")) {
    var colonCore = value.slice(0, -1);
    var translatedColonCore = translateCore(colonCore, language);
    if (translatedColonCore !== colonCore) {
      return translatedColonCore + ":";
    }
  }

  if (value.endsWith(" |")) {
    var pipeCore = value.slice(0, -2);
    var translatedPipeCore = translateCore(pipeCore, language);
    if (translatedPipeCore !== pipeCore) {
      return translatedPipeCore + " |";
    }
  }

  var trailingNumberMatch = value.match(
    /^(.+?)(\s+[-+]?[0-9]+(?:[.,][0-9]+)?(?:%|€| B| KB| MB)?)$/
  );
  if (trailingNumberMatch) {
    var translatedPrefixValue = translateCore(trailingNumberMatch[1], language);
    if (translatedPrefixValue !== trailingNumberMatch[1]) {
      return translatedPrefixValue + trailingNumberMatch[2];
    }
  }

  if (value.endsWith(" organization")) {
    return translateCore(value.slice(0, -" organization".length), language) + " οργανισμός";
  }

  var welcomeMatch = value.match(/^Welcome back, (.+)\.$/);
  if (welcomeMatch) {
    return "Καλώς ήρθες ξανά, " + welcomeMatch[1] + ".";
  }

  var welcomeShortMatch = value.match(/^Welcome back, (.+)$/);
  if (welcomeShortMatch) {
    return "Καλώς ήρθες ξανά, " + welcomeShortMatch[1];
  }

  var numericPrefixMatch = value.match(/^([0-9]+(?:[.,][0-9]+)?)(?:\s+)(.+)$/);
  if (numericPrefixMatch) {
    var translatedNumericSuffix = translateCore(numericPrefixMatch[2], language);
    if (translatedNumericSuffix !== numericPrefixMatch[2]) {
      return numericPrefixMatch[1] + " " + translatedNumericSuffix;
    }
  }

  var shareTokenMatch = value.match(/^Share token created for (.+)$/);
  if (shareTokenMatch) {
    return "Το token κοινοποίησης δημιουργήθηκε για " + shareTokenMatch[1];
  }

  var selectedFileMatch = value.match(/^Selected file: (.+)$/);
  if (selectedFileMatch) {
    return "Επιλεγμένο αρχείο: " + selectedFileMatch[1];
  }

  var requestedByMatch = value.match(/^Requested by (.+)$/);
  if (requestedByMatch) {
    return "Ζητήθηκε από " + requestedByMatch[1];
  }

  var rolesUpdatedMatch = value.match(/^Roles updated for (.+)$/);
  if (rolesUpdatedMatch) {
    return "Οι ρόλοι ενημερώθηκαν για " + rolesUpdatedMatch[1];
  }

  var roleInfoOnlyMatch = value.match(/^(.+) info only$/);
  if (roleInfoOnlyMatch) {
    return translateCore(roleInfoOnlyMatch[1], language) + " μόνο για ενημέρωση";
  }

  var loadedMatch = value.match(/^Loaded (.+)$/);
  if (loadedMatch) {
    return "Φορτώθηκαν " + translateCore(loadedMatch[1], language);
  }

  var showingMatch = value.match(/^Showing (.+)$/);
  if (showingMatch) {
    return "Εμφάνιση " + translateCore(showingMatch[1], language);
  }

  var versionMatch = value.match(/^Version (.+)$/);
  if (versionMatch) {
    return "Έκδοση " + versionMatch[1];
  }

  var homeForMatch = value.match(/^(.+) home for (.+)$/);
  if (homeForMatch) {
    return translateCore(homeForMatch[1], language) + " αρχική για " + homeForMatch[2];
  }

  var scoreContributionBreakdownMatch = value.match(/^(.+) score contribution breakdown$/);
  if (scoreContributionBreakdownMatch) {
    return "Ανάλυση συνεισφοράς βαθμολογίας " + translateCore(scoreContributionBreakdownMatch[1], language).toLowerCase();
  }

  var tenancyStatusMatch = value.match(/^Tenancy (.+)$/);
  if (tenancyStatusMatch) {
    return "Μίσθωση " + translateCore(tenancyStatusMatch[1], language).toLowerCase();
  }

  var contributionRuleMatch = value.match(/^([0-9]+(?:[.,][0-9]+)?) x ([-+]?[0-9]+(?:[.,][0-9]+)?) pts$/);
  if (contributionRuleMatch) {
    return contributionRuleMatch[1] + " x " + contributionRuleMatch[2] + " πόντοι";
  }

  var movedCaseMatch = value.match(/^(.+) moved this case into reviewer flow\.$/);
  if (movedCaseMatch) {
    return movedCaseMatch[1] + " μετέφερε αυτή την υπόθεση στη ροή ελέγχου.";
  }

  var movedIssueMatch = value.match(/^(.+) moved this issue into reviewer flow\.$/);
  if (movedIssueMatch) {
    return movedIssueMatch[1] + " μετέφερε αυτό το ζήτημα στη ροή ελέγχου.";
  }

  var sentDepositMatch = value.match(/^(.+) sent this deposit case to review\.$/);
  if (sentDepositMatch) {
    return sentDepositMatch[1] + " έστειλε την υπόθεση εγγύησης για έλεγχο.";
  }

  var requestedReferenceMatch = value.match(/^(.+) requested your reference$/);
  if (requestedReferenceMatch) {
    return requestedReferenceMatch[1] + " ζήτησε τη σύστασή σου";
  }

  var historyTimelineMatch = value.match(/^(.+) history timeline$/);
  if (historyTimelineMatch) {
    return "Χρονολόγιο ιστορικού " + translateCore(historyTimelineMatch[1], language).toLowerCase();
  }

  var readOnlyHistoryMatch = value.match(
    /^Read-only (.+) handoffs for this selected property in time order\.$/
  );
  if (readOnlyHistoryMatch) {
    return (
      "Χρονολογημένες, μόνο για ανάγνωση, μεταβιβάσεις για " +
      translateCore(readOnlyHistoryMatch[1], language).toLowerCase() +
      " στο επιλεγμένο ακίνητο."
    );
  }

  var noHistoryMatch = value.match(
    /^No (.+) history has been recorded for this property yet\.$/
  );
  if (noHistoryMatch) {
    return (
      "Δεν έχει καταγραφεί ακόμη ιστορικό " +
      translateCore(noHistoryMatch[1], language).toLowerCase() +
      " για αυτό το ακίνητο."
    );
  }

  var issueReportedMatch = value.match(/^Issue reported: (.+)$/);
  if (issueReportedMatch) {
    return "Αναφέρθηκε ζήτημα: " + issueReportedMatch[1];
  }

  return value;
}

export function translateText(value, languageOverride) {
  if (typeof value !== "string") {
    return value;
  }

  var language = normalizeLanguage(languageOverride || runtimeLanguage);
  if (language === "en") {
    return value;
  }

  var leadingWhitespaceMatch = value.match(/^\s*/);
  var trailingWhitespaceMatch = value.match(/\s*$/);
  var leadingWhitespace = leadingWhitespaceMatch ? leadingWhitespaceMatch[0] : "";
  var trailingWhitespace = trailingWhitespaceMatch ? trailingWhitespaceMatch[0] : "";
  var coreValue = value.trim();

  if (!coreValue) {
    return value;
  }

  return leadingWhitespace + translateCore(coreValue, language) + trailingWhitespace;
}

function translateProps(props) {
  if (!props) {
    return props;
  }

  var next = props;
  VISIBLE_PROP_NAMES.forEach(function translateVisibleProp(name) {
    if (typeof props[name] === "string") {
      var translatedValue = translateText(props[name]);
      if (translatedValue !== props[name]) {
        if (next === props) {
          next = Object.assign({}, props);
        }
        next[name] = translatedValue;
      }
    }
  });

  return next;
}

function translateNode(node) {
  if (typeof node === "string") {
    return translateText(node);
  }

  if (Array.isArray(node)) {
    return node.map(translateNode);
  }

  return node;
}

export function e(type, props) {
  var children = Array.prototype.slice.call(arguments, 2).map(translateNode);
  return React.createElement.apply(React, [type, translateProps(props)].concat(children));
}

export function getLanguageLocale(languageOverride) {
  return normalizeLanguage(languageOverride || runtimeLanguage) === "el" ? "el-GR" : "en-US";
}

var LanguageContext = React.createContext(null);

function decorateChildrenWithLanguage(children, language) {
  return React.Children.map(children, function decorateChild(child) {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, {
        __trustLedgerLanguage: language
      });
    }
    return child;
  });
}

function LanguageDock() {
  var languageState = useLanguage();
  var language = languageState.language;
  var setLanguage = languageState.setLanguage;

  return e("div", { className: "language-dock" }, [
    e(
      "span",
      { className: "language-dock-label", key: "label" },
      language === "el" ? "Γλώσσα" : "Language"
    ),
    e(
      "button",
      {
        type: "button",
        className: language === "en" ? "language-button is-active" : "language-button",
        onClick: function onClickEnglish() {
          setLanguage("en");
        },
        "aria-label": language === "el" ? "Αλλαγή στα αγγλικά" : "Switch to English",
        key: "english"
      },
      "EN"
    ),
    e(
      "button",
      {
        type: "button",
        className: language === "el" ? "language-button is-active" : "language-button",
        onClick: function onClickGreek() {
          setLanguage("el");
        },
        "aria-label": language === "el" ? "Διατήρηση στα ελληνικά" : "Switch to Greek",
        key: "greek"
      },
      "ΕΛ"
    )
  ]);
}

export function LanguageProvider(props) {
  var languageTuple = React.useState(function resolveInitialLanguage() {
    return normalizeLanguage(props.initialLanguage || detectDefaultLanguage());
  });
  var language = languageTuple[0];
  var setLanguageState = languageTuple[1];
  var normalizedLanguage = normalizeLanguage(language || props.initialLanguage);

  runtimeLanguage = normalizedLanguage;

  React.useEffect(
    function syncLanguageState() {
      if (typeof document !== "undefined") {
        document.documentElement.lang = normalizedLanguage;
      }
      if (typeof window !== "undefined") {
        try {
          window.localStorage.setItem(STORAGE_KEY, normalizedLanguage);
        } catch (error) {}
      }
    },
    [normalizedLanguage]
  );

  var value = React.useMemo(
    function buildLanguageContextValue() {
      return {
        language: normalizedLanguage,
        setLanguage: function setLanguage(nextLanguage) {
          setLanguageState(normalizeLanguage(nextLanguage));
        },
        locale: getLanguageLocale(normalizedLanguage),
        t: function translate(valueToTranslate) {
          return translateText(valueToTranslate, normalizedLanguage);
        }
      };
    },
    [normalizedLanguage]
  );

  return React.createElement(
    LanguageContext.Provider,
    { value: value },
    [
      React.createElement(
        React.Fragment,
        { key: "language-content" },
        decorateChildrenWithLanguage(props.children, normalizedLanguage)
      ),
      React.createElement(LanguageDock, { key: "language-dock" })
    ]
  );
}

export function useLanguage() {
  var context = React.useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used inside a LanguageProvider.");
  }
  return context;
}
