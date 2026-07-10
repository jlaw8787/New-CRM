# HCA CRM PHASE 2 BRIEF
# Run AFTER all stages of UPGRADE-BRIEF.md are complete and confirmed.
# Same standing rules: straight quotes only, node --check after every
# edit, one feature at a time with sign-off between, SQL before frontend,
# never rewrite working code.

---

## GATE ITEM, READ FIRST: REAL CANDIDATE DATA

Feature 3 below imports real candidates. Before ANY real nurse data
enters this system, authentication must be real. Right now the anon key
plus open RLS policies means anyone with the URL and key can read and
write everything, and the login screen is cosmetic. That is fine for
synthetic demo data and completely unacceptable for real PII under
Australian privacy obligations.

Prerequisite work before real data:
1. Enable Supabase Auth (email + password), link users.supabase_auth_id
2. Replace the anon_all RLS policies with authenticated-role policies
3. Login screen becomes a real email/password sign-in
Until this is done, the import feature must only be used with dummy data.

---

## FEATURE 1: SEARCH ACROSS NOTES AND ACTIVITY

Extend the global quick search (Stage 5) so it also searches activity
content and candidate notes, not just names.

- Search input matches: candidate name, email, phone, facility name,
  submission facility, AND activity.content AND candidates.notes
- Results dropdown groups by type: Candidates, Facilities, Notes
- A note match shows: candidate name, first 80 chars of the note with
  the match highlighted, and the date. Clicking opens the candidate
  full page on the History tab with that entry flashed (reuse
  flashElement).
- Search is debounced 250ms and case-insensitive. All in-memory, the
  data is already loaded client-side. No new queries needed.

## FEATURE 2: TASKS

New table. Run this SQL first, confirm, then build UI:

```sql
CREATE TABLE IF NOT EXISTS tasks (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title text NOT NULL,
  notes text,
  candidate_id bigint REFERENCES candidates(id) ON DELETE CASCADE,
  facility_id bigint REFERENCES facilities(id) ON DELETE SET NULL,
  assigned_to bigint REFERENCES users(id),
  created_by bigint REFERENCES users(id),
  due_date date,
  priority text DEFAULT 'med',
  status text DEFAULT 'Open',
  completed_at timestamptz,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename='tasks'
    AND policyname='anon_all') THEN
    CREATE POLICY "anon_all" ON tasks FOR ALL TO anon
      USING (true) WITH CHECK (true);
  END IF;
END $$;
```

UI:
- "+ Task" button in the top bar and on candidate/facility pages
  (pre-links the task to that record)
- Create form: title, optional notes, assign to (dropdown of active
  users), due date, priority, linked candidate autocomplete
- Dashboard gains "My Tasks" as the first widget: open tasks assigned
  to the logged-in user, overdue in red, due today amber. One click
  marks complete (writes completed_at, logs activity on the linked
  candidate if there is one).
- Sidebar Tasks badge = open tasks assigned to current user
- Admins and ops can see and reassign tasks across their teams;
  consultants see their own plus ones they created
- Assigning a task to someone else logs an activity entry on the
  linked candidate: "Task assigned to {name}: {title}"

## FEATURE 3: CANDIDATE IMPORT (CSV)

Import real spreadsheets to create candidates in bulk. CSV only, tell
the user to save Excel files as CSV. Do not add an xlsx library.

Flow (a modal wizard, 3 steps):
1. UPLOAD: file input reads the CSV client-side. Parse with a small
   robust hand-rolled parser handling quoted fields and commas. Show
   detected headers and first 3 rows.
2. MAP: two-column mapping UI, our fields on the left (name, email,
   phone, classification, state, nurse_type, ahpra_number,
   ahpra_expiry, available_from, min_rate, notes, consultant), their
   headers in dropdowns on the right. Auto-match by fuzzy header name
   (e.g. "Mobile" matches phone). Unmapped fields skipped. Consultant
   maps by name to a user id, unmatched defaults to current user.
3. PREVIEW + DEDUPE: show the rows to be created. Flag duplicates
   where email OR phone matches an existing candidate, default those
   rows to Skip with an option to Import Anyway. Import button inserts
   in batches of 50 via the existing insert path so activity and
   defaults behave, shows progress, reports created/skipped/failed
   counts. Every imported candidate gets an activity entry "Imported
   from {filename}".

## FEATURE 4: EXPORT AND REPORTING

- Every list view (Candidates, Submissions, Contracts, Alerts) gets an
  Export CSV button that exports the CURRENT filtered view, not the
  whole table, with human column headers
- Client-side generation, no server: build the CSV string, trigger a
  download with a Blob link, filename like
  candidates-export-2026-07-04.csv
- Management dashboard gets a Reports card with three canned exports:
  Compliance Gaps (every non-verified required item with candidate,
  consultant, item, status, expiry), Pipeline Snapshot (all open
  submissions with days-in-stage and SLA state), Contracts Ending
  (contracts ending in the next 60 days with facility and consultant)

## FEATURE 5: JOB BOARD ENHANCEMENTS

- CLONE: every role card gets a Clone action that opens the role form
  pre-filled with everything except dates. One save creates the copy.
- MULTI-WARD CREATE: in the role form, allow selecting several wards
  at once, creates one role per ward on save
- STATUS ACTIONS on each card: Open, On Hold, Filled, Closed as a
  one-click chip. Filled prompts to link the winning submission.
- ROLE AGEING: each open role shows days-open, amber past 14, red
  past 30
- MATCH COUNT: each role shows how many current candidates match on
  nurse_type and state with compliance above 80%, clicking it opens
  the candidates list pre-filtered to those people

## SUGGESTED ORDER

Tasks (2) first, it changes daily behaviour the most. Then export (4),
cheap and instantly useful. Then notes search (1), job board (5), and
import (3) last because of the auth gate above.
