# HCA CRM WORKFLOW AUDIT
Full-system audit of where work dead-ends or can't be actioned from where
the user is standing. Requested mid-Phase-3 (before Feature 4) to establish
the target flow before further feature work. Change reference only — see
KNOWN-ISSUES.md for the two minor findings logged separately, and the
Phase 3 briefs for feature work this audit informs.

Audited against the live codebase as of 2026-07-09 (post Feature 3,
Explainable Match Scores). Every claim below was verified by reading the
relevant function or grepping for every write site of the field in
question — not inferred from the master brief's original spec.

====================================================================
## HOW TO READ THIS
====================================================================

For each entity: where it's created and what fields are captured, what
states it can move through, whether the next action is one click from
where the item is shown, and where it dead-ends (shown but not
actionable, or has no path forward at all).

"Dead-end" here means: an operation the app's own specs (master brief,
TEST-PLAN.md) describe as something a user should be able to do, that
currently has no UI path — not a UX nitpick.

====================================================================
## THE HEADLINE FINDING
====================================================================

Everything upstream of a submission being marked **Accepted** works, and
in every case the next action is reachable in one click from wherever
the item is shown (dropdowns in place, no navigating away to hunt).

Everything from **Accepted onward — contract creation, contract
confirmation flags, candidate phase advancement past "Submission" — has
no UI path at all.** Not a few clicks away: no button, modal, or field
exists to do it. This is a structural gap, not a polish gap, and it sits
directly underneath the Phase 3 Feature 5 (Revenue at Risk) and Feature 6
(Redeployment Engine) specs, both of which key off contract start/end
dates and status transitions that nothing in the app can currently
produce. Today those features would only ever compute against frozen
seed data, never against anything a consultant does inside the app.

====================================================================
## ENTITY 1 — CANDIDATE
====================================================================

STATES (10 phases, in order):
New Lead -> Screening -> Compliance -> Submission -> Offer -> Contract ->
Travel & Onboarding -> On Assignment -> Redeployment -> Extension/Exit

1. CREATED WHERE / FIELDS CAPTURED
   "Add Candidate" opens the full edit modal (openNewCand -> openCandModal).
   This is the same modal used for editing, so every field in the 67-column
   schema is available at creation time, not deferred. Name is required and
   dupe-checked against existing name + email/phone before saving
   (saveCand()). phase defaults to "New Lead".

2. STATES IT CAN MOVE THROUGH FROM WHICH SCREENS
   Grepped every `.phase=` assignment in the file. There is exactly ONE:
   inside sfConfirm() (the submission flow's "Confirm Sent" step), which
   auto-advances New Lead / Screening / Compliance -> Submission the first
   time a candidate is submitted. That is the only phase transition that
   exists anywhere in the app.

3. ONE CLICK FROM WHERE SHOWN?
   N/A past "Submission" — see below.

4. DEAD-ENDS
   - No manual phase control exists anywhere. The candidate edit modal
     object (EC) never references `.phase` in any input — it cannot be
     hand-set even by an admin/ops user. The pipeline strip on the
     Candidates list only FILTERS by phase (setPF), it does not SET it.
   - Everything past "Submission" is permanently unreachable through the
     app. A candidate who gets Accepted, contracted, deployed, redeployed,
     or exits never has phase touched by anything — it stays on
     "Submission" forever unless the database is edited directly.
   - TEST-PLAN.md W2.7 explicitly expects "Advance phase through the
     dropdown: each change persists and logs an activity entry
     automatically" — that dropdown does not exist in the current build.
     Either this regressed at some point or the test plan was written
     ahead of the build; either way it's a live mismatch between the test
     plan and the app.
   - Related, not a phase issue: compliance items are not auto-created on
     first candidate save (master brief Part 8 Gap #1). Logged as a minor
     finding in KNOWN-ISSUES.md — not a dead-end, since the "Create
     Standard Checklist" button is one click away on the Compliance tab.

====================================================================
## ENTITY 2 — SUBMISSION
====================================================================

STATES (5-status model):
Promoting -> Submitted -> Accepted / Withdrawn / Declined

1. CREATED WHERE / FIELDS CAPTURED
   5-step submission flow, written to the database on the final
   "Confirm Sent" step (sfConfirm()). Captures candidate_id, facility_id,
   ward, nurse_type, role_id (nullable — "Ad-hoc (no role)" is a valid
   choice in the Step 1 role picker), submitted_by, status, submitted_date,
   follow_up_date, checklist_snapshot, submission_package_text.

   GAP CALLED OUT BY NAME: submissions has NO start_date / end_date
   column. Confirmed against mapSubmissionRow() and the insert payload in
   sfConfirm() — neither reads nor writes a date range. Dates only exist
   on the linked role (role.startDate / role.endDate), and nothing in the
   app ever copies them onto the submission or carries them forward from
   there. For an ad-hoc submission (no role_id), the intended start/end
   date is never captured anywhere, at any point in the lifecycle.

2. STATES / SCREENS
   Status dropdown is inline and identical in behavior on: the Submissions
   list row, the pipeline board card, the candidate-page submission card,
   and a kebab "Set Status" menu. All four call setSubStatus() directly.

3. ONE CLICK FROM WHERE SHOWN?
   Yes, well covered. No navigation required to change status from any of
   the four surfaces it appears on.

4. DEAD-ENDS
   "Accepted" doesn't cascade to anything. setSubStatus() updates the
   status, logs activity, and (as of Feature 2) resolves pending
   submission_followups — but it never touches candidate.phase and never
   creates a contract. Master brief Part 6 explicitly specs "If Accepted:
   prompt to create contract" — that prompt does not exist. An Accepted
   submission is a visual dead end: the status badge turns green and
   nothing else happens.

====================================================================
## ENTITY 3 — CONTRACT
====================================================================

STATES (values exist, nothing writes them):
Draft / Signed / Active / Expiring / Completed / Cancelled

1. CREATED WHERE / FIELDS CAPTURED
   NOWHERE. Grepped for openContractModal, "New Contract", contracts.push,
   and every write-oriented variant of contract creation — zero matches
   anywhere in the file. renderCpContracts() (candidate page) is pure
   read/display of whatever rows already exist in the database.

   Confirmation flags (flightConfirmed, accomConfirmed, shiftConfirmed)
   are read INTO the DB-sync payload (so they can be written back
   unchanged) but are never SET to true by any UI action — grepped every
   assignment site, only the sync-out mapping exists.

2. STATES / SCREENS
   Status values exist in the data model and are displayed with color
   coding, but nothing in the app ever writes them. They are seed-only,
   display-only values.

3. ONE CLICK FROM WHERE SHOWN?
   N/A — there is no path to advance a contract from any screen. Master
   brief Part 4 Page 4 specs "Extend / Edit / View" buttons on each
   contract card; none of the three exist.

4. DEAD-ENDS
   The entire entity is a dead end. Contracts only exist in this system
   because they were seeded directly into Supabase. submission_id and
   role_id columns exist on the contracts table (added in the July 2026
   migration, intended to link a contract back to the submission and role
   that produced it) but are not even read into the front-end object
   (mapCandidate's contracts mapping omits both) — so even a seeded link
   between a submission and its resulting contract is invisible to the
   app today.

   THIS IS THE MOST CONSEQUENTIAL GAP IN THE SYSTEM. Feature 5 (Revenue
   at Risk) and Feature 6 (Redeployment Engine) both key off contract
   start/end dates and status transitions that nothing currently
   produces. Building either feature today means it can only ever
   compute against frozen seed data, never against anything a
   consultant does inside the app.

   Same read-only pattern extends to flights, accommodation, car hire,
   and expenses (grepped for Add Flight / addFlight / openFlightModal /
   equivalents for accommodation — zero matches). All four are display
   -only, same as contracts. Not one of the five Phase 3 feature specs
   depends on these directly, but they're part of the same structural
   gap and worth fixing in the same pass as contracts, since travel/
   accommodation records are meant to link to a contract's confirmation
   flags.

====================================================================
## ENTITY 4 — COMPLIANCE ITEM
====================================================================

STATES:
Not Started -> Requested -> Received -> Verified, plus Expired and
Waived as manually-settable values.

1. CREATED WHERE / FIELDS CAPTURED
   Manual "Create Standard Checklist (13 items)" button on a candidate's
   Compliance tab (cpAutoCreateCompliance), inserting the fixed CP_STD set
   (AHPRA Certificate, Photo ID/Passport, Work Rights/Visa, National
   Police Check, WWC Check, NDIS Worker Screening, COVID-19, Influenza,
   Hepatitis B, ALS Certificate, Resume/CV, Reference 1, Reference 2).
   A "+ Add Item" path also exists for custom/non-standard items.

2. STATES / SCREENS
   Inline status dropdown per item, on the Compliance tab.

3. ONE CLICK FROM WHERE SHOWN?
   Yes. Inline dropdown on the Compliance tab itself, and from the Alerts
   page alertMarkVerified() advances an item to Verified in one click
   without navigating to the candidate at all.

4. DEAD-ENDS
   None that block work, one inconsistency logged as a minor finding in
   KNOWN-ISSUES.md: expiry is computed dynamically by the alert engine
   (ddiff against the stored expiry date) rather than written back to the
   row, so an item past its expiry date still displays a green "Verified"
   badge on the Compliance tab itself until someone manually changes the
   dropdown — even though the Alerts page correctly flags it as expired
   in the meantime.

====================================================================
## ENTITY 5 — SUBMISSION FOLLOW-UP (submission_followups)
====================================================================

Built this phase (Feature 2). Included for completeness since it's one
of the five entities named in the audit request.

STATES:
Pending -> Completed

1. CREATED WHERE / FIELDS CAPTURED
   Auto-created (two rows, 24h chase + 48h chase) whenever a submission
   enters Submitted status — via either the submission flow (sfConfirm())
   or a status change (setSubStatus()). No manual creation path, by
   design — this entity exists specifically so no submission goes
   unchased without a human having to remember to set a reminder.

2. STATES / SCREENS
   Alerts page (Follow-ups Due section), the Morning Brief priority list,
   and a chip on the submission card/row everywhere a submission appears.

3. ONE CLICK FROM WHERE SHOWN?
   Yes on all three surfaces — "Mark Done" calls completeFollowup()
   directly in place, no navigation needed.

4. DEAD-ENDS
   None found. This is currently the one entity in the system where
   creation, state, and action are all fully wired end to end, including
   auto-complete when the parent submission's status changes away from
   Submitted (Accepted/Declined/Withdrawn all resolve pending follow-ups
   automatically with a "Resolved by outcome" note).

====================================================================
## WHAT THIS MEANS FOR PHASE 3 FEATURES 5 AND 6
====================================================================

Feature 5 (Revenue at Risk + Pipeline Value) needs contract rate, hours,
and weeks-remaining. Feature 6 (Redeployment Engine) needs contract
end_date to trigger the 21-day alert and role.startDate to pre-filter
matches. Both are fully specced against data that currently has no path
into the system except direct database seeding.

Recommendation raised at audit time, not yet agreed or built: a
lightweight contract-creation flow triggered from setSubStatus() when a
submission's status becomes Accepted, pre-filled from the linked role's
dates when role_id is present, with a manual date-entry fallback for
ad-hoc submissions. This is the fork in the road for whether Features 5
and 6 land on real, consultant-generated data or only ever exercise the
seed set.

No code has been changed as a result of this audit. This document is the
map the next fix pass should be planned against.
