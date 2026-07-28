# Notes panel, what I found before building

Read only. No code changed, no SQL written or run yet. Read of index.html
(facility page, ward rendering, facility save path, panel patterns, activity
logging, Supabase load path) on 28 July 2026.

Task as given: right side pop out notes panel on facilities and wards, quick
notes typed during a call, six fixed reasons (Rate, Complaint or issue,
Extension, Staffing request, Accommodation, General), everyone sees every note,
ward notes also show on the facility labelled with the ward. New table, so SQL
first, written out and reviewed before it runs.

---

## 1. There is no notes table, and no notes feature to extend

Nothing in the app reads or writes a facility_notes, ward_notes or notes table.
Confirmed by search. So this is a genuinely new table, as expected.

---

## 2. The overlap you need to decide on

The facility profile already has an Activity section that does almost exactly
this job.

At the bottom of every facility page there is a box with four type buttons
(Note, Call, Email, Meeting), a text area, and an Add button. It writes to the
shared `activity` table with `entity_type='facility'` and `entity_id` set to the
facility, and reads back in date order. Contract, submission and file events
also land in the same feed.

So the new panel is the same act as the existing Activity box, with six reasons
instead of four types and a pop out instead of a section at the bottom of the
page.

Two honest ways forward:

**A. New table, `facility_notes`.** Clean separation, ward notes get a proper
home, filtering by reason stays simple, and the Activity feed stays a system
audit trail. Cost: two places on the same screen where a person can type a note
about a facility, and they will not see each other's entries. That will confuse
people unless the old Activity note button is retired at the same time.

**B. Reuse `activity`.** Add a `reason` column and a ward column, and make the
panel a nicer front end on what is already there. Nothing is duplicated, old
facility notes stay visible. Cost: the notes panel then shows system rows
(submissions, file uploads, contract changes) unless it filters them out, and
`activity` is already a busy shared table.

My recommendation is A with the Activity note buttons removed from the facility
page in the same change, so there is exactly one place to type a note about a
facility. The Activity section stays, read only, as the system trail. That is a
real decision though, not mine to make, and it changes the SQL.

---

## 3. Ward identity is not stable, and this is the biggest problem

This one matters more than anything else in the task.

Every time anyone hits Save in the facility editor, the app **deletes every ward
row for that facility and inserts them all again from scratch**. New rows, new
ids. Ward records have no stable identity across a single save of the facility.

On top of that, the app never loads ward ids into memory at all. The client side
ward object is only a name and a list of nurse types.

Consequences for this task:

- A ward note keyed on `ward_id` would be orphaned the first time anyone edits
  that facility and saves. Silently. The note would still exist, pointing at a
  ward row that no longer exists.
- Keying ward notes on the ward **name** plus facility id matches how everything
  else in the app already refers to wards (roles, submissions and contracts all
  hold a plain ward text string, per FACILITY-DATA-CHECK.md section 4). It is
  consistent, and it survives a facility save.
- Renaming a ward would strand its notes under the old name. There is already a
  routine that handles exactly this for roles and contracts (`checkWardOrphans`,
  it detects the rename and offers to rewrite the strings), so notes can be
  folded into that same routine rather than a second mechanism.

So: ward notes keyed on facility id plus ward name, and wired into the existing
ward rename handler. The alternative, fixing the save path to keep ward ids
stable first, is the correct long term answer and is a prerequisite for open
item 3 on the list anyway (giving roles, submissions and contracts a real ward
id). It is a separate job and it writes real data.

---

## 4. There is no working right side panel to reuse

The HTML still contains an old slide panel (`#panel`, 430px, slides in from the
right, has a header, a tab strip and a note box). It is dead. Its close button
calls `closePanel()` and its Add button calls `submitNote()`, and neither of
those functions exists in the file any more. Nothing fills it in. It is a husk
left behind by an earlier rebuild.

The only right side panel that actually works today is the AI assistant panel,
370px wide, fixed to the right, slides in on a transform, toggled by one
function. That is the pattern to copy.

Two choices: revive `#panel` and its CSS, or build the notes panel on the AI
panel's pattern. Reviving `#panel` sounds like reuse but its markup is built
around candidate tabs and a note form that no longer matches anything, so most
of it would be thrown away. I would leave it alone and build the notes panel on
the AI panel's pattern, then delete the dead `#panel` markup in a separate tidy
up.

---

## 5. Most facilities have no wards, so the ward half of this is thin

From FACILITY-DATA-CHECK.md, re-checked against the code: only 17 of 49
facilities have any ward records. 62 ward rows, 25 distinct names, and most are
never referenced by a role, submission or contract.

The panel needs to open cleanly on a facility with no wards at all, which is
two thirds of them. That is an empty state, not an edge case.

---

## 6. Visibility, everyone seeing every note is already how facilities work

Consultants are restricted to their own candidates through `vc()`, but that
function only touches candidates. The facility list and facility profile are not
filtered by role at all. Only the edit buttons are gated to admin and ops.

So "everyone can see every note" is consistent with how facilities already
behave. Nothing to build for it, and nothing to work around.

---

## 7. Where the panel gets opened from

Places that already exist and would take a button without inventing anything
new:

- Facility profile top right, next to the existing Facilities and Edit details
  buttons.
- The left hand section nav on the facility profile, which already lists
  Overview, Roles, Wards, Submissions and so on.
- Each ward row on the facility profile Wards section, which is already a
  collapsible header with a count on the right.
- The Facilities list table could carry a note count column, but that means
  loading every note at startup. Better left until the panel itself is proven.

---

## 8. Things I will hold to when building

- Notes are real data. Once typed and saved they are in the database and
  reverting the code does not remove them.
- Reasons fixed at six, as agreed in the brief's decision 4.
- No em dashes in any new code, comment or UI copy.
- Tabular numerals on every date and count.
- Shadows for separation, not border lines, per Direction C.
- One purple accent, soft status colours only where a note reason genuinely
  needs one.

---

## What I need from you before writing the SQL

1. **Separate `facility_notes` table, or a reason column on the existing
   `activity` table.** Section 2. This changes the SQL completely.
2. **If separate: does the old Activity note box on the facility page get
   retired at the same time,** so there is only one place to type a note.
3. **Ward notes keyed on ward name.** Section 3. Confirm you are happy with
   that rather than waiting for real ward ids, which is a bigger, later job.
