# HCA CRM PHASE 3 BRIEF: INTELLIGENCE LAYER
# Read HCA-CRM-MASTER-BRIEF.txt first for architecture, then this.
# Standing rules unchanged: straight quotes only, node --check after
# every edit, one feature at a time with sign-off, SQL before frontend,
# never rewrite working code, verify your own work in the browser.

---

## PROJECT STATUS (for a fresh session picking this up cold)

Everything in UPGRADE-BRIEF.md and FILES-NOTIFY-BRIEF.md is COMPLETE
and verified: stabilised codebase, schema aligned to the live DB,
~227 seeded candidates across 4 consultants + 2 admins + 1 ops user,
actionable alerts with deep links, 5-status submission model
(Promoting, Submitted, Accepted, Withdrawn, Declined) with list +
pipeline views and SLA chips, professional visual pass (SVG icons,
spacing/type scale, interaction states, skeletons, empty states),
tabbed candidate pages (Overview, Profile, Work Preferences,
Compliance, Pipeline, History, Files), unified required-items-only
compliance percentage with CP_STD as the single checklist scheme,
document upload (compliance docs to candidate-docs bucket, general
files to documents bucket), Supabase Realtime live notifications for
new roles (all users) and submission stage changes (admin/ops only),
optimistic UI on all routine actions, full-row click targets, back
preserves scroll and filters, keyboard-driveable modals, in-app
confirm dialogs (no window.confirm anywhere), paginated fetchAll on
all loads.

Still pending from earlier plans (do NOT rebuild, just be aware):
TEST-PLAN.md full regression run, DAY-IN-THE-LIFE.md persona run,
and PHASE2-BRIEF.md (tasks, CSV import/export, notes search, job
board cloning). This Phase 3 brief may be run before or after those
at the user's discretion.

DO NOT run any uploaded schema.sql from older projects. The live
database schema is the source of truth. Discover it by querying, or
ask for a fresh schema dump if needed.

---

## PHILOSOPHY FOR THIS PHASE

Everything below serves one shift: from a system that stores what
happened to one that tells the consultant what to do next. Every
screen should help answer "what am I trying to fill today?" Jobs in
this market fill in under 30 minutes or are lost; a consultant runs
20+ submissions per placement. Speed to submit and never-missed
follow-ups are the two levers that move revenue.

Build order below is by value density. One feature per sign-off.

---

## FEATURE 1: MORNING BRIEF

Replace the current dashboard top section with a Morning Brief: the
consultant's day, not a data readout.

On login (consultant role), the dashboard leads with:
- Greeting with name and date
- TODAY'S PRIORITIES, an ordered action list generated from data:
  1. Hot open roles matching their candidates (role, facility,
     matches count, one click to the match list)
  2. Nurses becoming available within 7 days (count, expandable)
  3. Compliance items expiring within 14 days for their candidates
  4. Overdue check-ins (no contact 14+ days)
  5. Submissions awaiting follow-up (from Feature 2 below)
- Each priority row: icon, one-line description, count badge, and a
  single action button that takes them straight to the work
- ESTIMATED WORKLOAD line: "N actions today" (sum of the above)
- START MY DAY button: opens the highest-priority item directly
- Admin/ops variant: same structure but aggregated across their
  consultants, with a per-consultant breakdown row

Data comes from what is already loaded client-side; no new tables.
Priorities with zero items hide entirely. The brief collapses to a
slim summary bar after the consultant starts working (first
navigation away), expandable again from the header.

## FEATURE 2: AUTOMATED 24H/48H SUBMISSION FOLLOW-UPS

The market standard this desk runs on: every submission gets chased
at 24h and 48h, no exceptions, no memory required.

SQL first (run in Supabase, confirm before frontend):

```sql
CREATE TABLE IF NOT EXISTS submission_followups (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  submission_id bigint REFERENCES submissions(id) ON DELETE CASCADE,
  candidate_id bigint REFERENCES candidates(id) ON DELETE CASCADE,
  due_at timestamptz NOT NULL,
  label text DEFAULT '24h chase',
  status text DEFAULT 'Pending',
  completed_at timestamptz,
  completed_by text,
  notes text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE submission_followups ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE
    tablename='submission_followups' AND policyname='anon_all') THEN
    CREATE POLICY "anon_all" ON submission_followups FOR ALL TO anon
      USING (true) WITH CHECK (true);
  END IF;
END $$;
```

Behaviour:
- When a submission enters Submitted status, auto-create two rows:
  due_at +24h ('24h chase') and +48h ('48h chase'). Client-side on
  the status write, same transaction flow as the activity log.
- If status leaves Submitted (Accepted/Declined/Withdrawn), pending
  follow-ups for it auto-complete with notes 'Resolved by outcome'.
- Overdue = due_at past and status Pending. These feed: the Alerts
  page (Follow-ups section, replacing/merging the current follow-up
  logic), the Morning Brief priority list, and a chase-list count on
  the submission card/row (chip shows '24h due' or '48h overdue').
- Completing one: single click, optional note, logs activity.
- Backfill on load: existing Submitted submissions older than 24h
  with no follow-up rows get them created retroactively.

## FEATURE 3: EXPLAINABLE MATCH SCORES

Upgrade the existing matched-roles logic from a binary filter to a
ranked, explainable fit score. Pure client-side computation.

Score per candidate-role pair out of 100:
- Nurse type matches role: 30
- Home state matches or candidate regions include role region: 20
- Compliance >= 90%: 25 (>=80%: 15)
- Available within 14 days of role start: 15
- Has prior Accepted submission or contract at that facility: 10

Display:
- Role cards and the Matches view rank by score, showing the number
  in a small ring/badge
- Clicking the score expands a breakdown: each factor with its
  points, met factors green, missed grey ("Compliance 92% +25",
  "Not available until 3 weeks after start +0")
- The Morning Brief hot-roles priority uses score >= 70 as "strong
  match"

No black box: a consultant must always be able to see WHY someone
ranks where they do, because they own the submission decision.

## FEATURE 4: FACILITY SELLING INTELLIGENCE

Facilities win or lose candidates on the pitch. Give consultants the
sell at the point of need.

SQL first:

```sql
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS selling_points jsonb DEFAULT '[]'::jsonb;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS nurse_feedback jsonb DEFAULT '[]'::jsonb;
```

- Facility page gains a SELLING POINTS card: editable list of short
  bullets (accommodation quality, travel paid, friendly NUM, meal
  allowance, 4WD provided). Add/edit/remove inline.
- NURSE FEEDBACK card: short quotes with nurse name + date, added
  manually after placements ("Loved the team, would return").
- THE PAYOFF: in the submission flow and on match cards, when a
  facility is selected, its top 3 selling points appear right there,
  so the consultant pitches while dialling. One click copies a
  formatted pitch snippet to clipboard.
- Placement history strip on the facility page: past contracts with
  outcome, so "we have placed 6 nurses here, 5 completed" is visible
  at a glance. Computed from existing contracts data.

## FEATURE 5: REVENUE AT RISK + PIPELINE VALUE

Money makes priorities honest. Compute client-side from existing
data, no new tables:

- Contract value estimate: rate x hours x weeks remaining
- REVENUE AT RISK on the Morning Brief and management dashboard:
  sum of (a) active contracts ending within 30 days with no
  extension/redeployment submission in flight, and (b) submissions
  stuck in Submitted past 48h SLA
- Management dashboard: pipeline value by consultant (Submitted +
  Accepted awaiting contract), displayed alongside the existing
  consultant table
- Each at-risk item is clickable to the record; the number is a door,
  not a decoration

## FEATURE 6: REDEPLOYMENT ENGINE

The cheapest placement is a nurse already working.
- 21 days before any active contract ends, generate a Redeployment
  alert: "Contract ending {date}: {name} at {facility}. Redeploy?"
- The alert's action opens the matched-roles view for that candidate
  (Feature 3 scores), pre-filtered to roles starting within 30 days
  of contract end
- One click from there into the submission flow with candidate and
  role pre-selected
- Track it: candidates redeployed without a gap get a 'redeployed'
  tag automatically for later reporting

## EXPLICITLY OUT OF SCOPE THIS PHASE

E-signatures, contract document generation with merge fields, AHPRA
API verification, AI-generated summaries or outreach drafts, PWA/
mobile packaging, revenue forecasting models. All good ideas, all
later, all after real auth.

## ACCEPTANCE BAR

A consultant logs in and the first screen tells them their day in
priority order with one-click paths into each piece of work. No
submission ever goes unchased past 24h without appearing in an alert.
Every match ranking can explain itself. Every facility pitch is one
glance away during a submission. Every dollar at risk is visible and
clickable. Speed check: job arrives, consultant finds strong matches,
and completes a submission in under 3 minutes without leaving the
happy path.
