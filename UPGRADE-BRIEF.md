# HCA CRM PROFESSIONAL UPGRADE BRIEF

Read this whole file before writing any code. Work through stages in order.
Stop after each stage, tell me to test, wait for my confirmation.

Standing rules, unchanged: straight quotes only, verify script parses with
node --check after every edit, never rewrite working code, one stage at a
time, all writes go to Supabase.

Design target: the benchmark is Bullhorn, Vincere and JobAdder. Their shared
principle: a consultant never hunts and never double-handles. The system
surfaces the next action, and every list row can be actioned inline without
opening the record. Every stage below serves that principle.

---

## STAGE 0: STABILISE (do this before anything visual)

The file contains duplicate definitions of these functions: saveCand,
savePanelFull, toggleHot, submitNote, saveUser, saveFac, markFU, delUser,
delFac, delCand, closePanel. In each pair the earlier definition is the old
in-memory version and the later one is the Supabase-synced version that
actually runs.

1. For each name, find both definitions. Confirm the later one contains the
   DB sync call. Delete the EARLIER one only. One function at a time,
   node --check after each deletion.
2. Audit every Supabase write in the file. Every .insert/.update/.delete
   must either show a success toast after the DB confirms, or a red error
   toast with the message. No console-only failures. List every call site
   you changed.
3. Finish the 5 gaps from your own audit, with one change: gap 4 (Hot List
   row click) must open the candidate FULL PAGE via openCandPage, not the
   old panel. Apply the same to every other candidate row click in the app:
   Dashboard, Alerts, Submissions, Job Board matches. The panel is no
   longer a navigation destination.

## STAGE 1: ACTIONABLE ALERTS (turn the alerts page into a work queue)

Current alerts are a read-only list. Rebuild each alert row so it can be
resolved in place without navigating anywhere.

Row layout: severity icon | alert text with candidate name as a link |
age ("3d") | inline action buttons right-aligned.

Actions per alert type:
- No check-in 14+ days: [Log Check-in] opens a small inline composer
  (textarea + save) that writes an activity entry of type check-in,
  updates last_checkin to today, resolves the alert. [Snooze 7d] hides it
  for 7 days (store snoozed_until on the alert source or a snooze map
  keyed by alert id in a new alerts_snooze table or users JSONB).
- Compliance expiring within 60 days: [View Item] deep-links to the
  candidate page compliance tab with that item highlighted. [Mark
  Verified] sets the item status to Verified inline.
- Overdue submission follow-up: [Mark Done] existing markFU behaviour.
  [Open Submission] deep-links to the submission.
- AHPRA expired or expiring: same as compliance but pinned to top with
  red severity regardless of date order.

Grouping: sections in this order: Critical (AHPRA, expired items),
Follow-ups due, Check-ins overdue, Expiring soon. Each section header shows
a count. Resolved alerts animate out (150ms fade) rather than the whole
page re-rendering.

Add auto-generation: on data load, scan compliance items and create alert
entries for anything expiring within 60 days. No manual step.

## STAGE 2: SUBMISSIONS PIPELINE (the Vincere treatment)

Add a view toggle to the Submissions page: List | Pipeline. Persist choice
per user.

Pipeline view: kanban columns for Promoting, Submitted, Shortlisted,
Interview, Offered, Accepted. Declined collapses into a count chip at top
right that expands on click. Each card shows: candidate name, facility,
ward, rate, days in current stage, and an SLA chip that turns amber at 3
business days in Submitted with no facility response and red at 5. Card
click opens the submission detail. Advancing stage: a next-stage button on
the card (no drag and drop, keep it dependency-free), which updates
Supabase and logs an activity entry automatically.

List view refinements: the existing table gains inline stage-change (the
select already exists), plus a Follow-up column showing the due date with
overdue in red, and the same SLA chip. Filter bar state persists per user.

Both views must read from the same data and stay in sync. No duplicated
render logic beyond the two layouts: extract shared card/row data prep
into one function.

## STAGE 3: PROFESSIONAL VISUAL PASS

The current build reads as low-end because of four things: emoji icons,
inconsistent spacing, inline style drift, and missing interaction states.
Fix in this order.

1. Icons: replace every emoji used as UI (phone, envelope, fire, clipboard,
   warning) with a small inline SVG icon set. Define each icon once as a JS
   function returning an SVG string, 16px, stroke currentColor, 1.5px
   stroke width, consistent rounded caps. Roughly 12 icons needed: phone,
   mail, flame, alert-triangle, check, clock, calendar, file, plane,
   building, user, chevron-right.
2. Spacing and type scale: define and enforce a scale. Spacing: 4, 8, 12,
   16, 24, 32. Font sizes: 11 (meta), 12 (body), 13 (emphasis), 15
   (section titles), 18 (page titles). Sweep each page and snap every
   inline padding/margin/font-size to the scale by moving it into a class.
   Do this one page per confirmation cycle, starting with Candidates list
   and the Candidate page.
3. Interaction states: every clickable row gets a hover background
   (var(--purple-pale) at low opacity) and cursor pointer. Every button
   gets hover and active states and a visible focus ring. All transitions
   120ms ease.
4. Loading and empty states: a skeleton loader (grey shimmer bars) shown
   while the initial Supabase load runs, replacing any blank flash. Every
   empty table gets a designed empty state: icon, one line of copy, one
   primary action button.
5. Header polish: page header area gets a consistent pattern across all
   pages: title, subtitle, right-aligned action buttons, and a subtle
   1px bottom border. No page-to-page drift.

## STAGE 4: CANDIDATE PAGE TABS

Convert the stacked sections on the candidate page into tabs under a
persistent identity header.

Tabs: Overview | Profile | Work Preferences | Compliance (with live %
in the label) | Pipeline | History.

Mapping: Profile = personal + professional + clinical. Work Preferences =
availability + regions + rates and increments. Pipeline = submissions +
contracts. History = travel, activity, and admin flags (admin/ops roles
only). Keep every existing section renderer, they become content blocks
inside tabs, do not rewrite their internals. Active tab persists in the
URL hash (e.g. #candidate/12/compliance) so deep links from Alerts work.
The left identity column stays exactly as it is.

## STAGE 5: NO DOUBLE HANDLING SWEEP

1. Global quick search: a search input in the top bar (keyboard shortcut
   press /) searching candidates, facilities and submissions by name,
   showing a dropdown of results, enter opens the top result's full page.
2. Auto-logging: any status change, submission stage change, compliance
   update, or check-in writes its own activity entry. A consultant should
   never type a note that says what a click already said.
3. Next Action field on candidates: action text + due date, editable from
   the candidate header and the candidates list (inline). Dashboard gains
   a "Today" widget at top: next actions due today or overdue, each with
   a done button that clears it and logs activity.
4. The slide-out panel becomes read-only quick view: remove its edit
   forms, keep the summary tabs, add one primary button: Open Full
   Profile. Delete the now-dead edit code paths after confirming nothing
   references them.

## ACCEPTANCE BAR FOR THE WHOLE BRIEF

A consultant can: see today's work on login without clicking anything,
resolve any alert in two clicks without leaving the alerts page, move a
submission through the pipeline with one click per stage, find any record
in under two seconds with keyboard search, and never enter the same
information twice. Visually: no emoji in the UI, no off-scale spacing, no
unstyled state anywhere, every action gives visible feedback.
