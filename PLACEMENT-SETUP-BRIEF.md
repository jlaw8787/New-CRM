# PLACEMENT-SETUP-BRIEF.md

Build brief for the Manage Placement screen.
Replaces the original approach to KNOWN-ISSUES #11 (scattered "Add" buttons
on travel sub-tabs) with a contract-scoped placement setup.

Written 2026-07-10. Not yet built.

---

## Why this changed

The original #11 plan was four standalone Add buttons (flight, accommodation,
car hire, expense) bolted onto the candidate's travel sub-tabs. That doesn't
match how the work actually happens. In real life a contract is confirmed,
and THEN travel and accommodation get arranged for that placement. Travel
records belong to a contract, they are not standalone.

So instead of scattered add forms, we build one "Manage Placement" screen per
contract that gathers everything needed to set that placement up.

## Decisions already made (do not re-litigate)

1. Travel and accommodation ALWAYS belong to a contract. Every flight,
   accommodation, car hire, and expense record created here is tied to the
   contract being managed (contract_id set), and to that contract's candidate
   (candidate_id set). No standalone travel records.
2. Build the plain "Manage Placement" screen FIRST (all forms gathered per
   contract). A guided checklist / wizard that nudges the user through steps
   comes LATER, layered on top of this. Not in this build.
3. Reuse existing modal styling (the contract-edit / new-contract modals).
   Do not invent new UI patterns.

## Arrangement status - the core of this design

Not every placement needs a flight, accommodation, or car. Sometimes the
nurse drives themselves; sometimes they book their own accommodation (with or
without a subsidy). The screen records the ARRANGEMENT, not just booking
details, so "nothing here" is never ambiguous - it's a deliberate status, not
a forgotten blank. This matters for duty of care: we always know where our
person is and how they got there and are housed.

Each of the three travel sections (Flight, Accommodation, Car) has a
three-way status, same labels across all three:

- Not required  (nothing needed - driving, local, etc.)
- Booked        (WE arranged it - full booking detail is then filled in)
- Self-booked   (THEY arranged it themselves)

Only when status is "Booked" does the full booking-detail form apply (dates,
ref, cost, etc.). "Not required" and "Self-booked" record the status with no
booking form required (a notes field is still available).

Subsidy (accommodation only): when accommodation is "Self-booked", a subsidy
field appears:
- Subsidy: None / Partial / Full
- If Partial or Full, a subsidy amount.

At-a-glance duty-of-care line: the top of the Manage Placement screen shows
the whole arrangement in one line, e.g.
  "Flight: Booked - Accom: Self-booked (partial subsidy $200) - Car: Not required"
so the arrangement is readable without opening each section.

## Schema additions needed (Stage 0 of the build)

The four travel tables currently hold booking details only - they have no
"status" concept. To store the arrangement statuses above, add:

- flights: a status column (text: 'Not required' / 'Booked' / 'Self-booked').
- accommodation: a status column (same three values), plus subsidy_type
  (text: 'None' / 'Partial' / 'Full') and subsidy_amount (numeric).
- car_hire: a status column (same three values).
- expenses: no status column - expenses are actual spend records, always
  "real", so they keep simple add/list behaviour (no three-way status).

All new columns nullable, sensible defaults. Never touch the identity id
columns. Light additive migration, same style as the contract_audit addition.

## Guard rails carried from earlier work

- All four tables (flights, accommodation, car_hire, expenses) have
  GENERATED ALWAYS AS IDENTITY ids. NEVER send an explicit id on insert.
- Do NOT use .upsert() with an explicit id anywhere (the 428C9 bug class
  fixed across four tables earlier).
- NOTE: the current travel save uses delete-then-reinsert, which churns ids
  on every save. It is currently harmless (nothing references these ids), but
  do NOT extend that pattern here. New records are added via plain .insert()
  (id defaults), and edits/deletes target a specific row by id
  (.update()/.delete().eq('id',...)). We are not re-churning the whole set.
- Verify every save in Supabase, not just on screen. The screen can lie.

## Table facts (from Stage 0 audit)

All four tables link: candidate_id -> candidates(id) ON DELETE CASCADE,
contract_id -> contracts(id) ON DELETE SET NULL.

User-editable fields per type (do NOT expose id, candidate_id, contract_id,
created_at, approval_status, approved_by, doc_* - those are set by save logic
or later features):

- flights: airline, flight_no, from_loc, to_loc, depart_date, return_date,
  booking_ref, cost, notes
- accommodation: name, address, check_in, check_out, booking_ref, cost,
  cost_unit (default "per night"), notes
- car_hire: provider, vehicle, pickup_location, pickup_date, return_date,
  booking_ref, cost, cost_unit (default "per day"), notes
- expenses: type, amount, description, expense_date, receipt_ref, notes

Asymmetry to know: the sidebar Travel page (renderTravel) shows Flights,
Accommodation, and Expenses but NOT car hire. The candidate sub-tab
(renderCpTravel) shows all four. This brief works off the contract, so it
covers all four regardless.

---

## Build in stages. One sign-off per stage. Stop and report after each.

### STAGE 0 - Schema additions (migration only)

Add the columns listed under "Schema additions needed": a status column on
flights, accommodation, and car_hire; subsidy_type + subsidy_amount on
accommodation. All nullable. Never write to identity ids. Append to the
migrations file with a comment. Report the final shape of each table's new
columns. No app/UI code in this stage.

### STAGE 1 - The Manage Placement screen shell (read-only)

Add a "Manage Placement" button on each contract (on the Contracts page
and/or the candidate Pipeline tab contract card - match where the Edit
Contract button already lives).

Clicking it opens a Manage Placement view for THAT contract, showing:
- A header with the contract's key facts (candidate, facility, dates).
- The at-a-glance duty-of-care line (Flight / Accom / Car statuses in one
  line - showing whatever the current status values are, or "Not set" if
  none yet).
- Four sections: Flights, Accommodation, Car Hire, Expenses. Each lists the
  records already tied to this contract (read-only for now), plus the
  section's current status, or a clean empty state.

No add/edit/save yet. Just the screen showing the right contract, its status
values, and existing records. Report what was added.

### STAGE 2 - Flight section with status (the template)

The Flights section gets a status control: Not required / Booked /
Self-booked.
- Setting status to "Booked" reveals an "Add Flight" form (the flight fields).
  On save: plain .insert() into flights, id defaults, candidate_id and
  contract_id set from the managed contract, status stored.
- "Not required" / "Self-booked" just record the status (notes optional), no
  booking form required.
- The at-a-glance line updates to reflect the flight status.

Flights is the template. Get status + booking + the at-a-glance line fully
working and verified before cloning. Report what changed. Do not claim
verified.

### STAGE 3 - Clone to accommodation and car hire (+ expenses)

Once flights is verified, repeat the status-driven pattern for accommodation
and car hire, each with its own fields.
- Accommodation adds the subsidy fields (None / Partial / Full + amount),
  shown only when status is "Self-booked".
- Expenses has NO status - it keeps a simple "Add Expense" + list (expenses
  are real spend, always concrete).
Each insert sets candidate_id + contract_id, id defaults. The at-a-glance
line reflects all three statuses. Report what changed per type.

### STAGE 4 - Edit and delete existing records

Add edit and delete to each record row, per type:
- edit: .update(...).eq('id', <id>) - never send id in the payload.
- delete: .delete().eq('id', <id>).
Report what changed.

### STAGE 4B - File attachment per section (one file each)

Flight, Accommodation, and Car Hire each get a single attached document
(e.g. itinerary, journey/route plan for a driver, booking confirmation) -
one file per section. Duty-of-care value: the actual travel document lives
with the record.

FUTURE ENHANCEMENT (not now, deliberately deferred): auto-parse uploaded
documents to pre-fill fields (read a receipt -> fill amount/date/vendor; read
an itinerary -> fill flight no/times/route). This needs an external
OCR/extraction service (API keys, cost, human review of results) and should
come AFTER Phase 4 auth, since it means sending candidate/financial documents
to a third party. For now we build PLAIN attachment only - attach the file,
no parsing. Auto-parse is its own future project.

- Reuse the app's EXISTING Supabase Storage upload mechanism (already built
  for candidate and facility file uploads) - do not build a new upload path.
- Store the file link in the existing columns: doc_url, doc_added_by,
  doc_added_at (these already exist on flights and accommodation; check
  car_hire - Stage 0 audit noted car_hire may lack doc_* columns, so a small
  additive migration for car_hire's doc_* columns may be needed first).
- One document per section record. Show the attached file (view/download link)
  once uploaded, with who/when added.
- Expenses already has doc_url (receipts) - fold expense receipt upload in
  here too if straightforward.

Report what changed. Verify a real file uploads, the link persists in
Supabase, and re-opening the placement shows the attached file.

### STAGE 5 - Wire the sidebar Travel page + dead button

The sidebar Travel page (renderTravel) aggregates across all candidates and
currently has a dead "Add Booking" stub (qMod/goQ) that goes nowhere. Decide
at this stage: either point that button at the Manage Placement flow (user
picks a contract, lands on its placement screen) or remove it. Do not leave a
button that lies. Report the choice and what changed.

---

## How each stage is verified (by the human: browser + Supabase)

- Stage 1: open Manage Placement from a contract, confirm it shows the right
  contract's facts and its existing travel records (or empty states).
- Stage 2: add a flight, confirm it appears on screen AND lands in the flights
  table in Supabase with the correct candidate_id and contract_id, and a
  real generated id. Hard refresh, confirm it persists.
- Stage 3: same check for one record of each other type.
- Stage 4: edit a record, confirm the change persists in Supabase; delete a
  record, confirm it's gone from Supabase (not just hidden on screen).
- Stage 5: confirm the sidebar button now does something real (or is gone).

If any stage fails its check, stop and report before continuing.
