# CONTRACT-EDIT-BRIEF.md

Build brief for adding contract editing to HCA CRM.
Addresses KNOWN-ISSUES item #10 (no UI path to edit an existing contract).

Written 2026-07-10. Not yet built.

---

## What this builds

An "Edit Contract" form reachable from the Contracts page, letting a user
change any contract field, with every change recorded to a permanent audit
trail storing the old value and the new value.

## Decisions already made (do not re-litigate these)

1. All contract fields are editable EXCEPT status.
2. Status stays on the existing inline status dropdown on contract cards.
   The dropdown is already built and works - do not move status into the
   new form.
3. Every change is logged with old value, new value, who, and when. This is
   a full field-level audit trail, not a single "was edited" note.
4. The status dropdown must ALSO write to the audit trail when status
   changes, so status changes are captured alongside everything else.
5. The Edit button lives on the Contracts page.

## Known limitation, accepted on purpose

The app currently has no real auth - "who" is whoever is selected on the
user-switcher screen, not a verified login. The audit trail will record that
unverified "who" for now. When Phase 4 auth lands, the audit trail's author
field gets re-pointed at the real authenticated user. We are building the
audit structure now and accepting the "who" is provisional until then. This
is a deliberate choice, not an oversight.

## The save path is already fixed - reuse it

The contracts write path (per-row .update().eq('id',...)) was fixed and
verified on 2026-07-09 (KNOWN-ISSUES item #5). Do NOT reintroduce
.upsert() with an explicit id on the contracts table - that is the exact
bug class fixed across four tables that session. The edit form must save
through the confirmed-working per-row update pattern. Any new insert
(e.g. audit rows) must let the id default - never send an explicit id to a
GENERATED ALWAYS AS IDENTITY column.

---

## Build in stages. One stage per sign-off. Stop after each and report.

### STAGE 0 - Audit only, no code

Before writing anything, report back:

- The exact list of columns on the `contracts` table, with their types, so
  we know every field the edit form must cover.
- Whether a suitable audit table already exists (something like
  contract_audit, audit_log, activity). If one exists, show its columns. If
  not, say so - Stage 1 will create one.
- The name of the existing function that renders the Contracts page, and the
  function behind the existing inline status dropdown, so Stages 2 and 4
  hook into the right places.
- Confirm the contracts save currently uses per-row update (not upsert), so
  we know the fixed pattern is still in place before extending it.

Do not write or change any code in Stage 0. Just report.

### STAGE 1 - The audit table

Create the audit table if Stage 0 found none. Suggested shape (adjust names
to match the app's existing conventions):

- id (GENERATED ALWAYS AS IDENTITY - never write to it explicitly)
- contract_id (which contract was changed)
- field_name (which field changed, e.g. "end_date")
- old_value (text)
- new_value (text)
- changed_by (the current user - provisional until Phase 4 auth)
- changed_at (timestamp)

Store old/new as text so any field type can be logged the same way.

Report the final table shape. Do not build the form yet.

### STAGE 2 - The edit form (read + display only, no save yet)

Add an "Edit" button to each contract on the Contracts page. Clicking it
opens a form (modal or inline, matching the pattern used by the existing
New Contract flow - reuse that styling, don't invent a new look).

The form shows every editable contract field (all fields EXCEPT status),
pre-filled with the contract's current values.

At this stage the Save button does nothing yet - we are only confirming the
form opens, shows the right contract, and pre-fills correctly. This lets the
form be tested on its own before any write logic is added.

Report what was added. Then stop for sign-off and manual test.

### STAGE 3 - Wire up save + audit logging

Make the form's Save actually save, through the confirmed per-row
.update().eq('id',...) pattern. Never send id in the update payload.

On save, for each field that actually changed, write one row to the audit
table (old value, new value, field name, current user, timestamp). Only log
fields that changed, not every field every time.

Keep the existing [DB] console logging so saves can be watched during test.

Report what changed, one line per function. Do not claim it is verified -
that is done by hand.

### STAGE 4 - Wire the status dropdown into the audit trail

The existing inline status dropdown keeps owning status. Extend it so that
when status changes, it also writes an audit row (field_name "status", old
status, new status, current user, timestamp), using the same audit table and
the same pattern as Stage 3.

Do not move status into the edit form. Only add audit logging to the
dropdown's existing save.

Report what changed. Stop for sign-off.

---

## How each stage gets verified (by the human, in the browser + Supabase)

Same discipline as the regression pass - the screen can lie, Supabase is the
truth:

- Stage 2: open Edit on a contract, confirm the form shows that contract's
  real current values. No save to check yet.
- Stage 3: change a field, save, hard refresh, confirm the new value is in
  the contracts table in Supabase (not just on screen). Then check the audit
  table has a new row with the correct old value, new value, field, and who.
  Change two fields at once and confirm exactly two audit rows appear, one
  per changed field, and unchanged fields produce no rows.
- Stage 4: change status via the dropdown, confirm the status change persists
  in Supabase AND an audit row was written for the status change.

If any stage fails its check, stop and report before moving on.
