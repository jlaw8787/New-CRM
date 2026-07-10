# HCA CRM REGRESSION PASS — WRAP-UP REPORT
Full pass against TEST-PLAN.md, groups W1–W9. Run 2026-07-09 to
2026-07-10. This report covers which groups passed clean and every
issue the pass found, cross-referenced to its KNOWN-ISSUES.md number.

====================================================================
## RESULT BY GROUP
====================================================================

| Group | Area | Result | Issues found (KNOWN-ISSUES #) |
|---|---|---|---|
| W1 | Login and role visibility | 4/4 PASS, clean | none |
| W2 | Candidate lifecycle | 7/8 PASS | 2 findings, neither given a KNOWN-ISSUES number — see note below |
| W3 | Submission flow end to end | 6/6 PASS, clean | none |
| W4 | Alerts work queue | 6/6 PASS (after same-day fixes) | #7 — FIXED |
| W5 | Facilities and Job Board | PASS with findings | #8, #9 — both Open |
| W6 | Contracts and travel | PASS with findings | #10 — FIXED; #11 — Open |
| W7 | Cross-role integrity | PASS with findings | #12 — Open |
| W8 | Guard rails | PASS with findings/notes | #14 — Open; #15 — test-plan note (not pass/fail) |
| W9 | Visual QA sweep | PASS, clean (light sweep) | none |

Also surfaced during the pass, not tied to a single W-group: **#13**
(Open, minor) — found while building the W6/#10 fix (CONTRACT-EDIT-BRIEF
Stage 2), not an independent regression-pass finding.

====================================================================
## GROUP DETAIL
====================================================================

**W1 — Login and role visibility.** All 4 checks passed cleanly: login
screen lists all 7 users, Sarah Keating's candidate count correctly
scoped, sidebar badges non-zero and matching, switch-user works. No
console errors, no issues logged.

**W2 — Candidate lifecycle.** 7 of 8 checks passed, including the
thorough edit-save-hard-refresh persistence check that exercises the
exact save path rebuilt earlier that session (submissions, contracts,
follow-ups all confirmed stable across saves). Two findings:
- Phase-dropdown control does not exist anywhere in the app — this
  re-confirms WORKFLOW-AUDIT.md's own headline finding rather than
  being a new discovery, so it was not given its own KNOWN-ISSUES
  number.
- Hot-flag toggle exists (`toggleHot()`) but is only wired up on the
  Candidates list page, not on the candidate's own profile page —
  flagged in the W2 report as a new minor finding. **Not confirmed as
  ever written to KNOWN-ISSUES.md as a numbered item** — flagging this
  gap now so it can be logged properly rather than silently dropped.

**W3 — Submission flow end to end.** All 6 checks passed clean: 5-step
submit flow (both role-linked and ad-hoc paths), Pipeline/Submissions
list visibility, inline status colour + persistence, pipeline board
Next Stage and kebab-menu Decline, activity logging per status change,
SLA chips on stale seeded submissions. No new issues — only a
previously-logged CLEANUP-LIST item (duplicate candidate 230) resurfaced.

**W4 — Alerts work queue.** The largest chunk of work in the pass. The
page crashed on first load for any candidate list containing specific
alert types (missing `id` fields caused an uncaught exception that
silently froze the whole page). Investigating and fixing this surfaced
four more problems in the same page, all fixed same-day: two group-
membership overlaps (four alert types never rendered anywhere; AHPRA
alerts double-counted), a day-boundary collision between two alert
types, and sidebar-badge/header staleness across all three alert-
clearing actions (Snooze, Mark Done, Mark Verified). All five write-ups
live under **KNOWN-ISSUES #7**, now marked FIXED with full verification
detail. Final state: 6/6 PASS.

**W5 — Facilities and Job Board.** Facility list, facility profile
page, and per-row counts (Active/Subs/Conv. Rate) all verified correct
against live-recomputed values — no count-vs-display mismatches found
here, despite that being the specific thing screened for given W4.
Two real findings, both Open:
- **#8** — facility contact info lives in two places (`facilities`
  table vs. `facility_contacts` table) and drifts apart; editing via
  the modal updates one, the page displays the other.
- **#9** — Job Board role cards have no clickable link back to their
  facility, on the card or in the slide-out panel.

**W6 — Contracts and travel.** Two real findings:
- **#10** — no UI path existed to edit an existing contract (only
  create). **This is now FIXED** — built and verified across
  CONTRACT-EDIT-BRIEF.md Stages 0–4 later in the session: an Edit
  Contract form reachable from both the Contracts page and the
  candidate Pipeline tab, saving through the confirmed per-row update
  pattern, with a new `contract_audit` table logging one row per
  changed field (including status changes via the existing dropdown).
- **#11** — Open. No UI path exists to create flight, accommodation,
  car hire, or expense records anywhere — read-side only, matching
  WORKFLOW-AUDIT.md's original finding for these four entities.

**W7 — Cross-role integrity.** (Completed in a prior session; task
tracking marked complete now.) One finding:
- **#12** — Open. Management Dashboard's consultant-row click
  (labelled "Click a row to filter to their pipeline") instead
  navigates away to the unfiltered Candidates list — wrong behavior on
  two counts, not just one.

**W8 — Guard rails.** Two notes, both Open:
- **#14** — minor. No email format validation anywhere in the app; a
  clearly invalid address saves silently and renders as a live mailto
  link. Doesn't fail the guard-rail test (no crash), but matters once
  the app is actually emailing facilities.
- **#15** — test-plan note, not a pass/fail. W8.3 ("kill the server,
  confirm a visible save error") doesn't map to this app's
  architecture — the dev server only serves the page; saves go
  straight from the browser to Supabase. Killing the server prevents
  the page from loading at all, so the "attempt a save while the
  server is down" state is unreachable. Flagged for a TEST-PLAN.md
  revision (target Supabase reachability instead) plus a genuine
  future offline/unreachable-Supabase error-handling check.

**W9 — Visual QA sweep.** Light pass across pages: no emoji icons, no
obviously broken spacing, consistent headers. Passed clean, no new
issues.

====================================================================
## OPEN ITEM NEEDING A DECISION
====================================================================

The W2 hot-flag-toggle finding (candidate profile page missing the
toggle that the Candidates list page has) does not appear in
KNOWN-ISSUES.md under any number. Every other finding from this pass
was walked through an explicit "add this to KNOWN-ISSUES.md" step;
this one was reported in the W2 group summary but — as best this
report can confirm — never formally logged. Recommend logging it as
its own numbered item (would be **#16**) if you want it tracked
alongside everything else, rather than leaving it as a comment
resolved by memory only.

====================================================================
## SUMMARY
====================================================================

9 of 9 groups run. 3 groups (W1, W3, W9) passed with zero findings.
6 groups produced findings, all logged to KNOWN-ISSUES.md except the
one flagged above. Of the 9 numbered items this pass produced (#7–#15):
**2 fixed same-day** (#7 Alerts crash, #10 contract editing), **6 still
open** (#8, #9, #11, #12, #14, #15 — the last a test-plan note rather
than a bug), **1 open and minor** (#13, contract-edit follow-on gap).

No app code was changed to produce this report.
