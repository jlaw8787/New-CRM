# HCA CRM KNOWN ISSUES
Minor findings logged for tracking, not yet fixed. Larger structural gaps
(contract creation, candidate phase advancement, submission date capture)
are tracked in WORKFLOW-AUDIT.md instead — this file is for small,
contained inconsistencies that don't block a workflow, just cause a
display disagreement or an extra manual step.

Do not fix anything in this file without explicit go-ahead — logged here
specifically to be dealt with later, in priority order, once the bigger
structural gaps in WORKFLOW-AUDIT.md are resolved.

====================================================================
## 1. Compliance items show "Verified" past their expiry date
====================================================================

STATUS: Open. Logged 2026-07-09 during the full workflow audit.

WHAT HAPPENS
A compliance item's expiry is computed dynamically wherever alerts are
generated (getAutos(), via ddiff() against the stored expiry date) —
that part is correct, and the Alerts page does flag it appropriately
(EXPIRED / expiring-soon banners work as intended).

What does NOT happen: the item's own `status` field is never written
back to 'Expired' when the date passes. It stays whatever a human last
set it to (typically 'Verified') until someone manually opens the
candidate's Compliance tab and changes the dropdown themselves.

RESULT
A document that has actually expired shows a green "Verified" badge on
the Compliance tab itself, while the Alerts page correctly shows it as
expired at the same time. The two views disagree until someone
manually reconciles the status field.

WHY NOT FIXED YET
Not a dead-end — the fix path (attach a new document, set a new expiry,
mark Verified) is one click away from the alert via openCandAtComp().
Purely a display inconsistency between two screens showing the same
underlying date.

LIKELY FIX (not yet agreed, not yet built)
Either (a) compute displayed status the same way everywhere — derive
"Expired" for display from the date whenever expiry has passed,
regardless of stored status, so the Compliance tab and Alerts page
never disagree, or (b) a scheduled/on-load reconciliation pass similar
to the existing reconcileCompliance() function that already fixes a
different checked/status mismatch on load.

====================================================================
## 2. Standard compliance checklist creation is manual, not automatic
====================================================================

STATUS: Open. Originally specced in HCA-CRM-MASTER-BRIEF.txt Part 8,
Gap #1. Confirmed still unimplemented during the 2026-07-09 workflow
audit.

WHAT HAPPENS
When a new candidate is saved for the first time, nothing creates their
compliance checklist automatically. A consultant has to separately open
the candidate's Compliance tab and click "Create Standard Checklist (13
items)" (cpAutoCreateCompliance()) before any compliance tracking exists
for that candidate at all.

WHY NOT FIXED YET
Not a dead-end — the button exists and is one click away, so nothing is
unreachable, it's just an extra manual step every single time a
candidate is created. Master brief explicitly asked for this to be
automatic on first save.

LIKELY FIX (not yet agreed, not yet built)
Call the same logic cpAutoCreateCompliance() already runs, from inside
saveCand()'s "new candidate" branch, immediately after the candidate
insert succeeds and its real id is known.

====================================================================
## 3. Submissions list/pipeline board have no visible date range
====================================================================

STATUS: Open. Logged 2026-07-09, deferred out of the Accepted->Contract
build by explicit decision — this is the "split recommendation" the
user approved: capture submission dates now, display them later.

WHAT HAPPENS
Submissions now capture start_date/end_date (added this build — see
WORKFLOW-AUDIT.md for the history of why). They're auto-copied from the
linked role when one exists, or entered manually for ad-hoc submissions,
in Step 1 of the submission flow. But nothing displays them on the
Submissions list view or the pipeline board — the only place they're
currently visible is inside the Accepted -> Contract modal, which
prefills from them.

WHY NOT FIXED YET
Explicitly scoped out of this build to keep it reviewable as "one
feature, one sign-off." No dependency risk — this is a pure display
addition with nothing else waiting on it.

LIKELY FIX (not yet agreed, not yet built)
Add a "Dates" column to the Submissions list view and a small date-range
line to the pipeline board cards, reading submission.startDate/endDate
directly (mapSubmissionRow already exposes them).

Bundle in with this, since they're the same piece of work:
- Label the field as "Expected" dates on the submission (vs. the
  contract's dates, which become authoritative once one exists) so the
  two don't read as contradictory once both are visible at once.
- Submission dates currently have no edit UI after creation — same gap
  rate has always had. If a facility shifts a start date during
  negotiation, there's no way to update it on the submission record
  before a contract exists. Not a blocker (the contract modal lets you
  enter the correct dates at Accept time regardless of what the
  submission says), but worth an inline edit affordance once the Dates
  column exists to look at.

====================================================================
## 4. Submissions have the same rate-format bug as contracts had
====================================================================

STATUS: Open. Found 2026-07-09 while verifying the Accepted -> Contract
build, NOT fixed — out of the scope that was approved (contract rate
code specifically).

WHAT HAPPENS
Some seeded submissions store rate with a unit suffix baked in (e.g.
"59/hr" instead of "59"), same as the contracts bug that was fixed this
build. The submission card's rate display (renderCpSubmissions) and the
pipeline board card both append their own "/hr", so affected rows show
"$59/hr/hr". Confirmed live on at least one seeded row (submission id
10, Max Williams -> Tennant Creek Hospital).

WHY NOT FIXED YET
The approved scope for this build was "contract rate code" specifically
(cleanRate() in renderCpContracts). This is the same bug class on a
different table's display code — flagging rather than silently
expanding scope.

LIKELY FIX (not yet agreed, not yet built)
Same technique as the contract fix: a cleanRate()-style parseFloat
strip on display, applied to renderCpSubmissions and the pipeline board
card's rate line. Don't touch the stored seed values, same as the
contract fix didn't.

====================================================================
## 5. Contracts used delete-then-reinsert on general candidate save — FIXED
====================================================================

STATUS: Fixed 2026-07-09. Originally logged the same day as an open item;
closing the loop here rather than leaving a stale "not yet built" note.

WHAT WAS WRONG (two bugs, not one)
(a) syncCandidateToDb()'s contracts block still used delete-then-reinsert,
same as submissions did before the Phase 3 Feature 2 fix. Now that this
phase's Accepted -> Contract flow populates contracts.submission_id and
contracts.role_id for the first time, regenerating contract ids on every
unrelated profile save would silently break that linkage, and would
orphan documents.contract_id (ON DELETE SET NULL) the moment a
document-to-contract upload feature gets built.

(b) The Feature 2 "fix" for submissions — believed shipped and working —
was ALSO broken, and had been the whole time. Both submissions.id and
contracts.id are `bigint GENERATED ALWAYS AS IDENTITY`. A batch
`.upsert()` that includes an explicit id value against a GENERATED ALWAYS
identity column fails outright with Postgres error 428C9 ("cannot insert
a non-DEFAULT value into column id... Use OVERRIDING SYSTEM VALUE to
override"), which supabase-js's upsert() does not set. The failure was
silently swallowed by dbErr() (logs, doesn't throw), so every general
profile save silently failed to persist submission field changes (status,
notes, dates) made outside the direct-write paths (setSubStatus,
sfConfirm), with no visible symptom until this session's testing surfaced
it via console errors.

THE FIX
Replaced the batch `.upsert()` on both submissions and contracts with a
loop of per-row `.update(payload).eq('id', x.id)` calls (Promise.all'd
for parallelism). UPDATE never touches the identity column, so it
sidesteps 428C9 entirely — and is arguably a more literal match for
"upsert by id" than a batch upsert ever was. The insert-for-new-rows
branch (rows with no local id yet) was already correct and untouched.

CORRECTION TO THE ORIGINAL FLIGHTS/ACCOM/CAR-HIRE ASSESSMENT
When this item was first logged, flights/accommodation/car_hire were
assessed as safe to leave on delete-then-reinsert because nothing
references *their* ids via foreign key. That check was backwards: the
real dependency runs the other way — flights.contract_id,
accommodation.contract_id, and car_hire.contract_id all reference
contracts.id. Confirmed live: while contracts were churning ids during
debugging, every flights/accommodation/car_hire reinsert failed with
Postgres error 23503 ("insert or update on table flights violates
foreign key constraint flights_contract_id_fkey — Key is not present in
table contracts"), because their local contractId still pointed at a
contract id that had just been deleted out from under them. With
contract ids now stable, this is resolved as a side effect — no change
needed to flights/accommodation/car_hire's own sync code, since they
were never the source of the problem, only collateral damage from it.

VERIFIED — contracts side
Candidate id 115 (Ethan Hall), contract id 115 (facility Longreach
Hospital, submission_id 153, role_id 26). Edited an unrelated field
(phone number) via the UI and saved, twice in a row:
  - Before: contract id 115, submission_id 153, role_id 26
  - After save 1: contract id 115, submission_id 153, role_id 26 (phone
    updated 0400000115 -> 0411222333)
  - After save 2: contract id 115, submission_id 153, role_id 26 (phone
    updated -> 0422333444)
No console errors on either save. Contract id and both linkage columns
held steady across both.

VERIFIED — submissions side (2026-07-09, separate re-check)
This was requested specifically because the contracts test above never
actually exercised a candidate with multiple submissions or any
submission_followups rows, and the original Feature 2 "verification"
never caught the 428C9 bug in the first place — a repeat of the same
shallow test wouldn't have proven anything stronger. Used candidate id 1
(Marco Thompson): 4 submissions, 6 submission_followups rows spread
across 3 of them. Edited phone via the UI, saved twice in a row, with
console.error patched to capture every dbErr() call plus an independent
check via the browser's own console reader.

  Submission ids — before/after save 1/after save 2 (identical all three
  times): 147, 148, 149, 150

  Follow-up ids and their submission_id link — before/after save 1/after
  save 2 (identical all three times):
    id 2  -> submission 147 (24h chase)
    id 4  -> submission 148 (24h chase)
    id 5  -> submission 147 (48h chase)
    id 7  -> submission 148 (48h chase)
    id 26 -> submission 149 (24h chase)
    id 27 -> submission 149 (48h chase)

  Phone: 0496074728 -> 0400111001 (save 1) -> 0400222002 (save 2)

Zero `[DB]` console messages on either save, confirmed by two independent
methods. Every submission id and every follow-up row's id and
submission_id link held exactly steady across both saves.

====================================================================
## 6. Test-data loss on candidate 115 (Ethan Hall) while diagnosing #5
====================================================================

STATUS: Disclosed and repaired 2026-07-09 (records restored on request).
Seed/test data only — no real candidate data was involved.

WHAT HAPPENED
Before the 428C9 root cause (see #5) was understood, reproducing the bug
involved repeatedly triggering syncCandidateToDb() with contract ids that
no longer matched the live database. Each cycle's delete-stale step
removed the current contract rows (since the stale local ids weren't in
the keep-list), and the batch upsert that should have reinserted them
failed silently (428C9) — so contract rows kept reappearing under new
auto-generated ids instead of being restored under their real ones. One
of those cycles also deleted candidate 115's flights (Rex, 1 row),
accommodation (Hospital Quarters, 1 row), and car_hire (1 row) records,
which then failed to reinsert with a 23503 foreign-key error because
their local contractId pointed at a contract id that no longer existed
in the database (see #5's flights/accom/car-hire correction).

REPAIRED
- Contract data itself: intact throughout — the contract rows kept
  getting recreated with fresh ids and correct field values, just not
  stable ones. Final state after the fix landed: contract id 115
  (Longreach Hospital) and id 114 (Mersey Community Hospital), both
  correct.
- Submission 153's status (Accepted) and start/end dates (07 Aug 2026 -
  28 Nov 2026), which were also collateral casualties of the same
  debugging cycles, were manually restored via direct REST calls after
  the fix was confirmed working.

RESTORED (2026-07-09, on request)
Recreated via direct API insert, since there is no UI to create these
records at all (see WORKFLOW-AUDIT.md — travel/accommodation/car-hire
have no create path). Correctly linked to contract id 114 (Mersey
Community Hospital), the current id for the contract they were
originally attached to (contract id 55 pre-churn).

IMPORTANT CAVEAT: only partial field values were available to restore.
The browser's in-memory copy of the deleted records had already been
overwritten by later page reloads by the time restoration happened, so
recreation relied solely on the fields captured earlier in conversation
context — not a full original record:
  - flights id 34: airline "Rex" only. flight_no, from/to, dates, cost,
    booking_ref all null (unknown, not fabricated).
  - accommodation id 34: name "Hospital Quarters" only. address, dates,
    cost all null (unknown, not fabricated).
  - car_hire id 19: no identifying field was ever captured for this one
    — provider, vehicle, dates, cost are all null. This record is
    effectively a placeholder confirming a car hire existed and was
    linked to this contract, not a reconstruction of its actual details.
All three: approval_status defaulted to 'Pending' (the schema default;
their real prior value is unknown).

====================================================================
## 7. Alerts page silently failed to render for any candidate list
## containing a "still promoting", contract-expiry, extension, no-travel,
## or redeployment alert — FIXED
====================================================================

STATUS: Fixed 2026-07-09. Found and fixed same-day, during the W4 (Alerts
work queue) section of the TEST-PLAN.md regression pass.

WHAT WAS WRONG
alertRowHtml() unconditionally called `a.id.replace(/:/g,'_')` to build a
DOM element id for every alert row. Only 4 of the 9 alert-push sites in
getAutos() actually set an `id` field (followup, checkin, comp, ahpra).
The other 5 never did: "Still promoting" (sub type, submission stuck in
Promoting 7+ days), "Contract expires", "Discuss extension", "No travel
arranged", "Redeployment window" — all four contract-derived alert types
plus the stale-promoting submission alert.

The first alert of any of those 5 types anywhere in a user's candidate
list threw `TypeError: Cannot read properties of undefined (reading
'replace')` inside a `.map()` in renderAlerts(). The exception was
uncaught, so it propagated out of renderAlerts() entirely — the line
that writes the new HTML into `#page` never ran. Result: clicking
"Alerts" changed the URL hash and highlighted the sidebar item, but the
visible page silently stayed frozen on whatever had been on screen
before, with no error toast and nothing in the UI to suggest a failure.
Only the browser console showed anything wrong.

This was not a Feature 2/3 regression from this session's work — the
follow-up alerts (Feature 2) correctly set an id from day one. It was a
latent gap in older alert-generation code that had apparently never been
exercised against live seed data by an actual click into the Alerts
page before this regression pass. Confirmed on Sarah Keating's own
roster: 7 seeded (non-TEST-) candidates have "Still promoting"
submissions 7+ days old, so the crash fired on first load, every time.
WORKFLOW-AUDIT.md's read-only review of this entity ("None found, fully
wired end to end") didn't catch it because it was a code-read, not a
runtime click-through.

THE FIX (two parts)
1. Added a stable, unique `id` to all 5 previously id-less alert push
   sites in getAutos(), following the existing scheme (type prefix +
   colon + the underlying row's real id): `promoting:<submission.id>`,
   `contract:<contract.id>`, `extend:<contract.id>`, `travel:<contract.id>`,
   `redeploy:<contract.id>`. Stable across renders, so snooze/dismiss
   behavior for these types now works the same way it already did for
   followup/checkin/comp/ahpra alerts.
2. Hardened alertRowHtml() so a missing or malformed id can never again
   take down the whole page: it now falls back to a deterministic
   `noid:<type>:<cid>:<key-or-subId-or-followupId-or-si>` id if `a.id` is
   null/undefined, and every `.map(alertRowHtml)` call in renderAlerts()
   is wrapped so one row throwing (from any future unforeseen cause,
   not just this one) is caught, logged to console as
   `[alerts] row render failed, skipping row`, and skipped — the rest of
   the page still renders. One bad record can now only ever cost one row,
   never the whole page.

No SQL/schema change — this bug and its fix are entirely client-side
alert construction in getAutos()/alertRowHtml(); nothing is persisted or
read from a new column.

VERIFIED
Reloaded, re-logged in as Sarah Keating. Console: zero TypeErrors, zero
`[alerts] row render failed` messages (the safety net wasn't even
needed — the real fix covered every live case). Alerts page rendered
fully: 114 alerts generated across all 8 types (`sub`:23, `travel`:25,
`comp`:34, `checkin`:17, `ahpra`:2, `redeploy`:7, `extend`:2,
`contract`:4), every one with a non-null id. All four visible TEST-PLAN
groups confirmed on screen: Critical (4), Follow-ups Due (23), Check-ins
Overdue (16), Expiring Soon. Header read "113 alerts — 30 urgent (1
snoozed)" (114 raw minus 1 already-snoozed).

Action persistence re-confirmed live in Supabase, not just the UI:
- "Mark Done" on a follow-up alert (submission_followups id 2): before
  status Pending/completed_at null, after status "Completed",
  completed_by "Sarah Keating", completed_at timestamped. Alert
  correctly stopped being generated on the next getAutos() call (raw
  count 114 -> 113).
- "Mark Verified" on a compliance alert (compliance_items id 30,
  National Police Check, Mason Johnson): before verified_by "Lisa
  Bennett" / verified_at 27 May 2026, after verified_by "Sarah Keating" /
  verified_at 09 Jul 2026, current timestamp.

NOTE ON KNOWN-ISSUES #1 (compliance Verified-past-expiry display gap)
Checked whether it reproduces here: Sarah Keating's current roster has
no compliance item that is actually past its expiry date and still
showing "Verified" today, so the specific live inconsistency wasn't
observable in this session's data. The underlying code path described
in #1 (status field never auto-flips to Expired) is unchanged by this
fix and remains open.

FOLLOW-ON FIX, SAME DAY: contract/extend/travel/redeploy never rendered
The four contract-derived alert types (`contract`, `extend`, `travel`,
`redeploy`) were generated by getAutos() and counted in the page's
top-line "N alerts" total, but renderAlerts()'s `groups` array only
bucketed `ahpra`/`comp`/`sub`/`checkin` into a visible section — these
four types were never rendered as rows anywhere on the Alerts page,
including the highest-value ones (contract-expiry, redeployment
window). Initially logged as a lower-severity "adjacent" note; on review
this was correctly identified as the same class of bug as the crash
above (page silently disagrees with what it claims), not a separate
lesser issue, and fixed the same day.

Added two new render groups and expanded Critical:
- **Critical** (expanded): now also includes `contract` alerts at
  level=red (expires in <=7 days) — a contract ending within a week is
  treated the same as an expiring compliance document.
- **Travel Not Arranged** (new): `travel` type alone. Kept separate from
  the group below because it's an operational gap on a contract that
  may already be Signed/Active, not a countdown — different action
  ("arrange travel") and severity shape than the planning alerts.
- **Contract Actions** (new): `contract` at level=amber (8-14d) +
  `extend` (discuss extension) + `redeploy` (redeployment window) — all
  three are "plan the next move on this contract" alerts at different
  lead times on the same underlying entity, bundled under one heading.

BOUNDARY BUG FOUND AND FIXED DURING THE SAME REVIEW
The four day-range conditions in getAutos() that decide `contract`
(red/amber) vs `extend` vs `redeploy` had a genuine overlap, not just a
grouping gap. `extend`'s condition was hardcoded `d>=14`, while
`contract`'s amber range extends to `d<=(k.alertDays||14)` — with
`alertDays` defaulting to (and, confirmed live, 100% of the time
currently equal to) 14. On day d=14 exactly, a contract satisfied BOTH
conditions, generating two separate alert objects (`contract:<id>` and
`extend:<id>`) for the same contract on the same day.

Fixed by tying extend's lower bound to the same variable rather than a
second hardcoded constant: `d>(k.alertDays||14)&&d<=21` (was
`d>=14&&d<=21`). Correct for any per-contract `alertDays`, not just the
default. The `extend`/`redeploy` boundary (21/22) was already clean and
untouched. Reconciled boundary table (days-to-end, default alertDays=14):

| d range | Alert | Level | Group |
|---|---|---|---|
| d<0 | none (pre-existing gap, not part of this fix) | — | — |
| 0-7 | contract | red | Critical |
| 8-14 | contract | amber | Contract Actions |
| 15-21 | extend | blue | Contract Actions |
| 22-45 | redeploy | blue | Contract Actions |
| d>45 | none, by design | — | — |

Flagged, not fixed: (a) d<0 (a contract already past its end date but
still marked Active generates zero contract-type alert at all — separate
gap, outside the four ranges reconciled here); (b) if a contract's
`alertDays` were ever configured >21, `extend`'s range would invert to
empty and `redeploy` could overlap `contract`-amber for d 22 through
that custom alertDays value. Theoretical only — confirmed live that all
109 seeded contracts use the default alertDays=14, so this does not
currently occur.

SECOND OVERLAP FOUND BY THE VERIFICATION ITSELF: AHPRA double-counted
Verifying the new groups produced two required assertions (header total
== sum of rendered rows; no alert id in more than one rendered group).
The second assertion immediately caught a third, independent, pre­
existing bug: Critical's filter was `a.type==='ahpra'` (unconditional,
no level check — present before any of this session's changes), while
Expiring Soon was `(comp||ahpra)&&level!=='red'`. Any non-red AHPRA
alert matched both, rendering twice — inflating the visible row count
above the header total (114 rendered vs. 112 in the header, the mirror
image of the original crash: too many rows shown, not too few).

Fixed by making AHPRA match the same red/non-red split already applied
to `comp` and `contract`: Critical now requires
`a.type==='ahpra'&&a.level==='red'`; Expiring Soon is unchanged
(`(comp||ahpra)&&level!=='red'`). One consistent rule across all three
compliance-adjacent types instead of AHPRA being a special case.

FINAL VERIFICATION (both required assertions, re-run after the AHPRA fix)
Reloaded, re-logged in as Sarah Keating, zero console errors.
  headerTotal: 112, sumRendered: 112, matches: true
  dupIds: [] (no alert id in more than one group)
  everyAlertInSomeGroup: true
  byGroupCounts: {Critical:3, Follow-ups Due:22, Check-ins Overdue:16,
    Travel Not Arranged:25, Contract Actions:12, Expiring Soon:34}
  header text: "112 alerts — 30 urgent (1 snoozed)"
3+22+16+25+12+34 = 112, matches the header exactly.

THIRD OVERLAP FOUND WHILE VERIFYING AHPRA FIX: Critical's own filter
Re-running the review turned up Critical was written as
`a.type==='ahpra'` unconditionally (no level check — pre-existing, not
from this session), while Expiring Soon was `(comp||ahpra)&&level!=='red'`.
Any non-red AHPRA alert matched both — a third instance of the same
count-vs-page disagreement, this time inflating rendered rows above the
header total. Fixed by giving AHPRA the same red/non-red split already
used for `comp` and `contract`: Critical now requires
`a.type==='ahpra'&&a.level==='red'`, matching how the desk wants
Critical to mean "act today" as a single consistent rule instead of
AHPRA being a special case. Expiring Soon unchanged. Re-verified: both
required assertions (header total = sum of rendered rows; no alert id
in more than one group) pass exactly — 112 = 112, zero duplicate ids,
byGroupCounts sum to 112.

FOURTH ISSUE, FOUND VERIFYING SNOOZE (W4.3/W4.6): sidebar badge and
header text both went stale independently of the grouping fix above —
same failure family, different code path
1. `updateBadges()` (drives the sidebar "Alerts" nav badge) computed its
   red-alert count from raw `getAutos()` output with no snooze filter —
   it never applied the `!snzOk(a.id||'')` filter `renderAlerts()`'s
   header already used. Confirmed live: sidebar badge read 31 while the
   header correctly read "29 urgent" — the gap was exactly the two
   alerts already snoozed. A snoozed alert kept lighting the badge,
   which defeats the purpose of snoozing. Fixed: `updateBadges()` now
   filters through the same `!snzOk(...)` set before counting reds.
2. Verifying that fix surfaced a second, related gap: `alertSnooze(id,
   days)` only called `snzSet()` + `alertDismiss()` (a lightweight
   DOM-only row fade-out) — it never called `updateBadges()`, so even
   with fix #1 the sidebar badge stayed stale until the next full page
   navigation, not "real time." Fixed by adding `updateBadges()` to
   `alertSnooze()`.
3. With the badge now live, the header subtitle text ("N alerts — N
   urgent") was the odd one out — it's only written by a full
   `renderAlerts()` call, which `alertSnooze()` still never triggers
   (deliberately avoids a full row re-render/flicker for a single
   dismiss). Added a small `refreshAlertsHeader()` helper that
   recomputes just the header text using the same formula
   `renderAlerts()` uses, called from `alertSnooze()` alongside
   `updateBadges()`.

VERIFIED: snoozed a live red alert (`checkin:15`, Ella Smith) and read
all three numbers in the same synchronous check, no navigation between
before/after:
  Before: badge 27, header "27 urgent", rendered red rows 27
  After (immediately, same tick): badge 26, header "26 urgent"
  After (post fade-out animation): rendered red rows 26, element fully
    removed from DOM
All three numbers matched at every point checked. Zero console errors.

FOLLOW-ON FIX, SAME DAY: applied identically to Mark Done / Mark Verified
`alertMarkVerified`, `alertMarkFU`, and `alertCompleteFollowup` shared
the exact same `alertDismiss()`-only pattern as `alertSnooze()` did
before its fix above — confirmed the same 3-way staleness applied to
them too, since they're the primary way alerts get cleared day to day
(more visible than snooze). Fixed identically: all three now call
`updateBadges();refreshAlertsHeader();` immediately after
`alertDismiss(id)`. `alertMarkVerified`'s async-failure revert branch
(which reverts local state and calls `renderPage()` if the Supabase
update fails) was also given the same two calls, closing the same gap
on the error path, not just the success path.

VERIFIED: marked a live red follow-up alert done (`followup:5`, Marco
Thompson, 48h overdue) and read all three numbers in the same
synchronous check:
  Before: badge 26, header "26 urgent", rendered red rows 26
  After (same tick): badge 25, header "25 urgent", rendered red rows 25,
    element fully removed from DOM immediately (alertCompleteFollowup's
    call to completeFollowup() already triggers a full renderPage(),
    so the row removal here was immediate rather than the fade-out
    animation used by snooze/dismiss elsewhere)
All three numbers dropped by exactly 1, matched at every point checked.
Zero console errors. Confirmed live in Supabase, not just the UI:
submission_followups id 5 — status "Completed", completed_by
"Sarah Keating".

====================================================================
## 8. Facility contact info is stored in two places and they drift apart
====================================================================

STATUS: Open. Found 2026-07-09 during the W5 (Facilities and Job Board)
regression pass. Not fixed — decision needed first.

WHAT HAPPENS
The Edit Facility modal (saveFac()) saves contact_name, contact_email,
contact_phone onto the facilities table's own row. But the Contacts
section on the facility page reads from the separate facility_contacts
table instead. Editing contact details in the modal updates the
facilities row only — the on-page Contacts cards still show whatever
is in facility_contacts, untouched.

CONFIRMED LIVE
Changed phone to 07 11111111 via the Edit Facility modal. Saved
correctly to facilities.contact_phone in Supabase. The page's Primary
Contact card still showed the old contact (Peter Harris) sourced from
facility_contacts.

DECISION NEEDED IN PHASE 2
Pick one source of truth for facility contacts — either the modal
should write to facility_contacts instead of (or as well as)
facilities.contact_*, or the Contacts section should read from
facilities.contact_* instead of facility_contacts, or the two need an
explicit reconciliation step. Not fixed.

====================================================================
## 9. Job Board role cards have no link back to their facility
====================================================================

STATUS: Open. Found 2026-07-09 during W5 item 4 (Facilities and Job
Board) of the regression pass. Navigation gap, not a data bug.

WHAT WAS TESTED
On the Job Board, clicked a role card, then tried clicking the
hospital/facility name both on the card itself and in the role's
right-hand slide-out detail panel (role detail, checklist, matches),
expecting either to navigate to that facility's full profile page.

WHAT HAPPENS
The role card correctly opens the slide-out panel — that part works as
intended. But the hospital/facility name is plain text, not a link,
anywhere it appears: not on the card, not in the panel. There is no way
to get from a role to its facility page from the Job Board. The deep
link is missing.

WHY THIS MATTERS
Not a data problem — the role's facility_id/link to the facility record
itself is presumably intact (unverified whether the underlying data
association exists; the gap found here is purely the absence of a
clickable UI path, not a check of the data). A consultant looking at a
role on the Job Board who wants to see the full facility (contacts,
other open roles, submission history) currently has no route there
except leaving the Job Board and searching/browsing for the facility by
name separately.

LIKELY FIX (not yet agreed, not yet built)
Make the facility name on the role card and/or in the slide-out panel a
clickable link that calls the existing facility-page navigation (the
same function role rows elsewhere in the app already use to open a
facility profile).

====================================================================
## 10. No UI path to edit an existing contract — missing core action — FIXED
====================================================================

STATUS: Fixed 2026-07-10. Found 2026-07-09 during W6 item 2 (Contracts
and travel) of the regression pass. Was HIGHER PRIORITY than items 8
and 9 — a missing core action, not a cosmetic or navigation gap.
Built per CONTRACT-EDIT-BRIEF.md across four signed-off stages
(0: audit, 1: audit table, 2: form, 3: save + audit logging, 4: status
dropdown audit logging).

WHAT WAS TESTED
On Max Kelly, an On Assignment candidate, tried to edit an existing
contract's dates from two places: the candidate's Pipeline tab, and the
Contracts page in the sidebar.

WHAT HAPPENS
No edit control for a contract exists anywhere.
- Candidate Pipeline tab: the contract renders read-only, no edit
  affordance on the card.
- Contracts page: clicking a contract row navigates to the candidate's
  profile Overview tab, not to an editable contract — there is no
  contract edit view at all.

You can CREATE a new contract (via the Accepted -> Contract flow built
earlier this session), but there is no way to EDIT one afterward — not
dates, not rate, not hours, not status via a dedicated form (the
inline status dropdown on contract cards is the one exception; it is
not being described as broken here).

WHY THIS IS LIKELY A UI GAP, NOT A DATA-LAYER PROBLEM
The contracts save path (syncCandidateToDb's contracts block) was fixed
earlier today — see item 5 — converted from delete-then-reinsert to
per-row .update().eq('id',...), and verified live with a real edit-save
round trip. That plumbing writes contract field changes correctly when
something calls it. The gap here is that nothing in the UI currently
lets a user open a contract in an editable state and trigger that save
path — no "Edit Contract" button, modal, or inline form exists for any
field beyond status.

THE FIX
Built exactly the affordance described above: an "Edit Contract" modal
(openContractEditModal(), reusing the shared #mo/#m-body/#m-foot shell
and styling already established by the New Contract flow), with an
Edit button added to both the candidate Pipeline tab's contract card
(renderCpContracts) and the Contracts page (renderContracts), both
opening the same form. Every editable field (all contract columns
already loaded into local state, except status — which stays owned by
the existing inline dropdown — and rate, excluded because payroll owns
it) saves through saveContractEdit() via the confirmed per-row
.update().eq('id',...) pattern, id never in the payload, also setting
last_edited_by/last_edited_at. A new contract_audit table (id, contract_id,
field_name, old_value, new_value, changed_by, changed_at — id GENERATED
ALWAYS AS IDENTITY, never written explicitly) records one row per field
that actually changed on every save, comparing old vs. new per field so
untouched fields write nothing. The existing status dropdown
(cpUpdateContractStatus) was extended to write to the same table with
the same pattern, so status changes are captured in the audit trail too
without moving status into the new form.

VERIFIED
Edits and status changes confirmed persisting live in Supabase (not
just on screen), and contract_audit confirmed writing exactly one row
per changed field per save — multi-field edits produced multiple rows
in the same save, untouched fields produced none.

====================================================================
## 11. No UI path to create flight/accommodation/car hire/expense
## records — same class as item 10, read side built, write side missing
## — FIXED (Manage Placement)
====================================================================

STATUS: Fixed 2026-07-11, via PLACEMENT-SETUP-BRIEF.md, Stages 0-5 all
done and verified. Found 2026-07-09 during W6 items 3 and 4 (Contracts
and travel) of the regression pass.

WHAT WAS TESTED
On Max Kelly, an On Assignment candidate, tried to add a flight entry
and an accommodation entry from the candidate's History tab / Travel &
Expenses section, checking all four sub-tabs (Flights, Accommodation,
Car Hire, Expenses). Also checked the Travel & Expenses page in the
sidebar for a way to create entries there instead.

WHAT HAPPENS
No add control exists anywhere. All four travel sub-tabs on the
candidate page display counts and existing records (all currently 0
for this candidate) but have no button to add a new entry. The Travel &
Expenses sidebar page also provides no way to create entries — it can
only display whatever already exists. Travel/expense records can be
viewed but not created from the UI, on any candidate.

CONSEQUENCE FOR THIS REGRESSION PASS
W6 item 4 (Travel & Expenses page reflects newly added entries) could
not be tested as a result — there is nothing to add, so nothing to
confirm reflects on that page.

SAME PATTERN AS ITEM 10
Display/read side is built (sub-tabs render counts and records
correctly when they exist); the create/write UI is missing entirely.
Consistent with WORKFLOW-AUDIT.md's original finding that flights,
accommodation, car hire, and expenses are read-only, seed-data-only
entities with no creation path anywhere in the app — this regression
pass confirms that gap is still present and unchanged.

LIKELY FIX (not yet agreed, not yet built)
An "Add Flight" / "Add Accommodation" / "Add Car Hire" / "Add Expense"
affordance on each respective sub-tab, following the pattern of other
add-record modals already built elsewhere in the app.

THE FIX (Manage Placement)
The above per-sub-tab "Add" approach was superseded before being built
— see PLACEMENT-SETUP-BRIEF.md "Why this changed." Travel and
accommodation records belong to a contract, not to the candidate in
the abstract, so the fix is a single contract-scoped "Manage
Placement" screen instead of four scattered add buttons. Built in
stages:
- Stage 0: schema — status column (text) added to flights,
  accommodation, car_hire; subsidy_type and subsidy_amount added to
  accommodation. All nullable, no identity-id columns touched.
- Stage 1: Manage Placement screen shell, reachable from a "Manage
  Placement" button on the Contracts page and the candidate Pipeline
  tab, next to the existing Edit Contract button.
- Stage 2: three-way arrangement status (Not required / Booked /
  Self-booked) built and verified on Flights as the template.
- Stage 3: pattern cloned to Accommodation (plus subsidy tracking:
  None/Partial/Full + amount, shown when Self-booked) and Car Hire
  (same three-way status, no subsidy). Expenses kept as a simple
  add/list with no status, per the brief (expenses are real spend,
  always concrete).
- Stage 4: edit and delete added for all four record types. Edit
  reuses the create form pre-filled, saves via
  .update(payload).eq('id', <id>) with no id in the payload. Delete
  confirms via showConfirm() then .delete().eq('id', <id>). Both
  re-render the section and the at-a-glance duty-of-care line.
- Throughout: an at-a-glance line at the top of the screen (e.g.
  "Flight: Booked · Accom: Self-booked (partial subsidy $200) · Car:
  Not required") summarises the whole arrangement without opening each
  section. All new records use plain .insert() with id left to
  default (GENERATED ALWAYS AS IDENTITY) — no .upsert() with an
  explicit id anywhere, consistent with the guard rail carried over
  from the items 10/13 fixes.
- Stage 4B: one attached document per record, all four types. Reuses
  the existing uploadToStorage() helper (candidate-docs bucket) rather
  than the generic documents-table pipeline, since doc_url/
  doc_added_by/doc_added_at live directly on each record's own row.
  Each saved row shows an "Attach document" control, or once attached,
  a "View document" link plus who/when added and a "Replace" control.
  Verified: files persist to Supabase and survive a hard refresh for
  all four types, including car_hire. Fixed a pre-existing data-loss
  trap surfaced by this stage: car_hire's doc_url/doc_added_by/
  doc_added_at were carried through by neither mapCandidate() (so an
  attached file would vanish on reload) nor the old candidate-level
  delete-then-reinsert save path (so it could later be silently wiped
  by an unrelated save) — both fixed as part of Stage 4B.
- Stage 5: the sidebar Travel page's dead "Add Booking" button
  (qMod/goQ stub — picked a candidate, opened their profile, created
  nothing) removed outright rather than wired up, since Manage
  Placement is contract-scoped and already reachable from the
  Contracts page and candidate Pipeline tab, both better-contextualized
  entry points than a page-level picker would be. Separately, each
  travel row on that page (Flights, Accommodation, Expenses) now links
  through to its own contract's Manage Placement screen
  (openManagePlacement(item.contractId)) instead of the candidate's
  general profile, falling back to the old behaviour only when a row's
  contract_id is null. Car Hire remains absent from this page — a
  pre-existing asymmetry, unchanged.

SUMMARY OF THE FEATURE
One "Manage Placement" screen per contract (reachable from the
Contracts page and the candidate Pipeline tab) replaces the four
scattered add buttons originally planned. It provides: a three-way
arrangement status (Not required / Booked / Self-booked) for flights,
accommodation, and car hire, with full booking-detail forms only when
Booked; accommodation subsidy tracking (None/Partial/Full + amount)
when Self-booked; a simple always-available add/list for expenses (no
status — real spend is always concrete); an at-a-glance duty-of-care
line summarising all three arrangement statuses without opening each
section; full edit and delete on all four record types
(.update()/.delete().eq('id',...), id never sent in any payload); and
one attached document per record across all four types, reusing the
existing uploadToStorage() helper rather than a new upload path. The
sidebar Travel page's dead "Add Booking" stub is gone, and its rows
now link straight to the relevant contract's placement screen.

SUPERSEDED
The standalone "Add Flight" display-only stub built as an early,
since-abandoned attempt at this item (flights-only, no save, no
status model) is fully superseded by Manage Placement and can be
removed.

====================================================================
## 12. Management Dashboard consultant row click navigates away instead
## of filtering, and lands on an unfiltered list — FIXED
====================================================================

STATUS: Fixed 2026-07-10. Found 2026-07-10 during W7 item 4 (Cross-role
integrity) of the regression pass. Was a misfiring read-side feature —
wrong click handler / wrong navigation target — not the missing-write-UI
pattern seen in item 11 (item 10 was the same pattern but is now fixed).

WHAT WAS TESTED
On the Management Dashboard, clicked a consultant's row in the
Consultant Performance table. The table's own on-screen instruction
says "Click a row to filter to their pipeline." Clicked Sarah Keating's
row.

WHAT SHOULD HAVE HAPPENED
Per the table's own stated behavior, the dashboard should stay on the
Management Dashboard and re-filter its cards and tables to show only
Sarah's data.

WHAT ACTUALLY HAPPENED
Two things wrong at once:
1. The click navigated away from the Management Dashboard entirely, to
   the main Candidates list — it should not have left the dashboard.
2. The Candidates list it landed on was not filtered to Sarah either —
   other consultants' candidates (Marcus's and Priya's) were visible.

So the row click both leaves the page it should stay on, and fails to
apply the one filter it claims to apply.

THE FIX
Root cause turned out to be two separate gaps, not one:
1. `vc()`'s `ops` role branch ignored `VCon` entirely — it always
   returned every candidate regardless of the filter, unlike the
   `admin` branch, which already respected `VCon` correctly. One-line
   fix: `if(CU.role==="ops")return VCon?candidates.filter(function(c){
   return c.consultantId===VCon;}):candidates;` — same shape as the
   admin branch. This alone explains why the row click (which does
   correctly set `VCon` via `setVC()`) still landed on an unfiltered
   list for an ops user (Josh Dermody), since the Candidates page's
   `vc()` call silently dropped the filter.
2. `VCon` was never cleared by ordinary navigation — once set by a
   drill-in, it stayed set through any later, unrelated visit to
   Candidates. Fixed by resetting `VCon=null` at every ordinary
   navigation-to-candidates entry point, while deliberately leaving the
   drill-in paths untouched:
   - Sidebar Candidates button — `onclick="nav('candidates')"` ->
     `onclick="VCon=null;nav('candidates')"`.
   - `routeFromHash()`'s generic page dispatch — covers both the
     browser back/forward button (via `popstate`) and a direct or
     bookmarked `#candidates` URL, since both funnel through this one
     function: `if(known.indexOf(h)>=0){nav(h);return;}` ->
     `if(known.indexOf(h)>=0){if(h==='candidates')VCon=null;nav(h);
     return;}`.
   - CSV-import-candidates flow — `nav('candidates');` ->
     `VCon=null;nav('candidates');`.
   - `jobToastMatches()` (view job-toast matches) —
     `nav('candidates');` -> `VCon=null;nav('candidates');`.
   `nav()`, `setVC()`, and `drillCon()` themselves were deliberately
   never touched, so the two intentional drill-in paths (Management
   Dashboard row click via `setVC()`+`nav()`, and `drillCon()`) keep
   setting `VCon` and filtering exactly as designed. A single passive
   check inside `nav()` couldn't distinguish "just set on purpose" from
   "stale from an earlier click" — both look identical to `nav()` by
   the time it runs — so the reset had to live at each ordinary entry
   point instead of in the shared function.

ALSO FIXED AS A SIDE EFFECT
The Home page's "View: All / [consultant]" toggle-pill switcher
(`setVC()`, no `nav()` call) had the exact same latent `vc()` gap for
ops users — it would set `VCon` but silently have no effect once
rendered through the broken `ops` branch. Fixed by the same one-line
`vc()` change; no separate code needed for this surface.

VERIFIED
Confirmed live: drilling into a consultant (dashboard row click) now
correctly filters the Candidates list to just that person. Both the
sidebar Candidates button and the browser back button correctly clear
back to the full, unfiltered candidate list afterward.

====================================================================
## 13. contract_number, extension_count, and total_contract_value are
## not editable — mapCandidate doesn't load them into local state
====================================================================

STATUS: Open. Minor, future gap. Found 2026-07-10 while building the
contract edit form (CONTRACT-EDIT-BRIEF.md Stage 2).

WHAT HAPPENS
These three contracts columns (plus weekly_hours, a separate numeric
column duplicating what the canonical `hours` text field already
covers) exist in the database but mapCandidate() never reads them into
the local candidate/contract objects the app works with in-session.
The Edit Contract form (see item 10, now fixed) deliberately left them
out rather than showing a fake blank value that doesn't reflect what's
actually stored in Supabase.

WHY NOT FIXED YET
Out of scope for the contract-edit build, which was scoped to fields
already available client-side. Fixing requires extending
mapCandidate()'s contract mapping to also load these columns (and the
corresponding camelCase fields) before they can be honestly exposed
anywhere, including in this edit form.

LIKELY FIX (not yet agreed, not yet built)
Add contract_number, extension_count, and total_contract_value to
mapCandidate()'s contracts mapping, then add them to the Edit Contract
form's field list and CONTRACT_EDIT_FIELDS audit-diff array the same
way the other fields were added in Stage 2/3.

====================================================================
## 14. No email format validation anywhere in the app
====================================================================

STATUS: Open, minor. Found 2026-07-10 during W8 item 2 (Guard rails) of
the regression pass. Not a crash — passes the guard-rail test as-is —
but a soft gap worth tracking.

WHAT HAPPENS
A clearly invalid email ("notanemail") saves without warning anywhere
it's entered, and renders as a clickable mailto link same as a real
address would.

WHY THIS MATTERS
Low priority today, but the app already sends submission emails to
facility contacts (the 5-step submission flow's email step). Without
format validation, junk or mistyped addresses will save silently and
accumulate over time, surfacing later as bounced/undeliverable
submissions with no earlier signal that the address was ever wrong.

LIKELY FIX (not yet agreed, not yet built)
Basic client-side email format check (e.g. a simple regex) on the
relevant input fields (candidate email, facility contact email, etc.),
surfaced as a validation message rather than a silent accept.

====================================================================
## 15. W8 item 3 (server-down save test) cannot be run as written —
## architecture mismatch, test-plan revision needed
====================================================================

STATUS: Open / test-plan note. Not an app bug. Found 2026-07-10 during
W8 item 3 (Guard rails) of the regression pass.

WHAT THE TEST ASSUMES
TEST-PLAN.md W8.3 assumes killing the dev server stops saves from
reaching the database, and expects that to surface as a visible red
error toast (not a silent failure) when something is saved while the
server is down.

WHY IT DOESN'T MAP TO THIS APP'S ARCHITECTURE
The dev server (port 8080, server.js) only serves the static page.
Saves write directly from the browser to Supabase in the cloud — the
two are independent. With the server up, saves reach Supabase
regardless of the server's own health. With the server down, the page
won't load at all, so there's no way to trigger a save in the first
place — "server down + attempt save" is not a reachable state in this
app. The failure happens one step earlier than the test anticipates,
before any save is ever attempted.

RESULT
Could not be executed as designed — not logged as a pass or a fail,
since the test's premise doesn't hold for this app's client-writes-
directly-to-Supabase architecture.

STILL WORTH TESTING, DIFFERENTLY
The underlying question W8.3 was really after — does a FAILED save
show a clear, visible error rather than silently succeeding — is still
a real and worthwhile check. It just has to be reached by simulating
Supabase itself being unreachable (network failure / Supabase outage)
while the page is already loaded, not by killing the local dev server.

FOLLOW-UP NEEDED
1. Revise TEST-PLAN.md W8.3 to target Supabase reachability instead of
   the local dev server.
2. Add a future offline/unreachable-Supabase error-handling check using
   that revised approach.

====================================================================
## 16. No way to delete or archive a candidate — create only, same
## pattern as items 10 and 11
====================================================================

STATUS: Open. Found 2026-07-10 during post-W8 demo cleanup, trying to
remove a test candidate ("sarah") from the UI.

WHAT HAPPENS
There is no delete or archive option anywhere on a candidate — not in
the edit form, not on the profile page. Candidates can be created but
never removed or hidden from the UI once they exist.

WHY THIS MATTERS
Mistaken, duplicate, or stale candidates (including ordinary test
records) accumulate permanently with no way to clear them out. Same
read-heavy/write-light pattern already logged for contracts (item 10,
now fixed) and travel/expense records (item 11) before this: create
exists, remove does not.

LIKELY FIX (not yet agreed, not yet built)
A delete or, better, archive/soft-delete affordance on the candidate
profile — soft-delete preferred over hard delete so records aren't
lost permanently, consistent with how the rest of the app treats data
(e.g. contracts stay in the database with a status rather than being
removed).

====================================================================
## 17. Contracts page "Add Contract" button is a dead qMod/goQ stub —
## same class as the now-removed Travel page "Add Booking" stub
====================================================================

STATUS: Open. Found 2026-07-11 during the PLACEMENT-SETUP-BRIEF Stage 5
audit/build (item 11), while removing the sidebar Travel page's dead
"Add Booking" button.

WHAT HAPPENS
The Contracts page header button "Add Contract" calls the same shared
qMod('Contracts')/goQ('Contracts') helper the Travel page's "Add
Booking" button used. qMod opens a "Select Candidate" picker modal;
its Continue handler, goQ, ignores the tab argument entirely and just
calls openCandPage(id) — it does not open a contract form, does not
land on the candidate's Contracts tab specifically, and does not
create anything. Picking a candidate and clicking Continue simply
opens that candidate's profile page.

WHY THIS MATTERS
Same dead-button pattern already found and removed on the Travel page
(item 11, Stage 5): a button that implies an action ("Add Contract")
but performs a different, unrelated one. Not fixed now because
qMod/goQ is shared — Travel's call site was removed outright since
Manage Placement already covers that need from better-contextualized
entry points, but Contracts has no equivalent replacement entry point
yet, so this one needs its own decision rather than a copy-paste
removal.

LIKELY FIX (not yet agreed, not yet built)
Either build a real "Add Contract" flow (likely reusing/adapting the
new-contract modal that already exists elsewhere in the app, if one
does), or remove the button the same way Travel's was removed if
contract creation already has a better home elsewhere. Do not remove
the shared qMod/goQ helper itself — no other change needed there.

====================================================================
## CLEANUP LIST — test-data artifacts to remove before real data goes in
====================================================================

Running list, updated as the TEST-PLAN.md regression pass creates or
finds test-data artifacts. Nothing in this section has been deleted —
logged only, per explicit instruction not to touch it mid-run. Clear
each item once it's actually removed, right before the system goes
live with real data.

- **Candidate id 230, duplicate "TEST-Nurse Alpha"** — pre-existing,
  predates the 2026-07-09 regression pass (not created by it). Has a
  stale Declined submission attached. Discovered during W2 (Candidate
  lifecycle) when creating this pass's own TEST-Nurse Alpha (id 232)
  and finding the name already taken by a different phone/email.
  Remove candidate 230 and its submission(s) before go-live.
- **Candidate id 231, "TEST-Guardrail Candidate"** — INTENTIONAL KEEP,
  not for removal. Per TEST-PLAN.md W8.2, this is the persisted fixture
  for the malformed-email guard-rail check (email "not-an-email"). Keep
  it permanently as a live regression fixture; do not delete or "fix"
  its email even after go-live.
