# SUBMIT-FLOW-BRIEF.md

Improve the candidate-to-role submission flow. DEMO-CRITICAL: submitting is
shown in the demo and the team does 100+ submissions/week, so this is the
priority feature after the visual rollout.

Written 2026-07-11.

---

## What's missing today

When submitting a candidate to a role, the consultant currently cannot:
1. Set the placement's start and end dates as part of the submission.
2. Attach documents - neither a full compliance pack nor just a CV for
   informal/speculative "fishing" outreach.

## Decisions (locked)

1. START/END DATES: always ask for start and end dates when submitting.
   Pre-fill from the ROLE's dates as a sensible default, but always show them
   and let the consultant change them per submission.

2. DOCUMENTS - support BOTH:
   - Pick an existing file already on the candidate (their stored CV, docs).
   - Upload a NEW file at submit time.

3. PACK vs CV - one flow, two levels of thoroughness:
   - A full compliance pack option (structured required docs - ties into the
     COMPLIANCE-PACKS feature when that's built), AND/OR
   - A quick CV-only option for speculative client outreach where the full
     pack isn't needed.
   The consultant chooses how much to attach - just a CV, or a full pack.

## Build approach (staged, after the visual rollout)

AUDIT FIRST (no code): find the current submit flow - the function(s) behind
the "Submit" buttons (on the Job Board match rows, candidate page, role
detail panel). Report: what a submission currently captures/saves, where it
writes (submissions table + any docs), and whether any date or document
fields already exist on that table to reuse. Confirm no upsert-with-explicit-id
bug risk.

Then stage:

### STAGE 1 - Start/end dates in the submit flow
Add start and end date fields to the submit dialog, pre-filled from the role's
dates, editable. Save them with the submission. Reuse existing submissions
table columns if present; if not, a small additive migration (nullable date
columns) first. Verify dates persist in Supabase.

### STAGE 2 - Attach existing candidate file
In the submit dialog, let the consultant pick from the candidate's existing
files/CV to include with the submission. Reuse the existing file/document
data already on the candidate. Verify the chosen file is linked to the
submission.

### STAGE 3 - Upload new file at submit time
Add the option to upload a new document during submission (reuse the existing
Supabase Storage upload mechanism - the same uploadToStorage helper used for
placement docs). Verify upload + link persists.

### STAGE 4 - Pack vs CV choice
Let the consultant choose the level: quick CV-only, or a fuller compliance
pack. For now (pre COMPLIANCE-PACKS build) the "pack" option can be a manual
multi-doc attach; once COMPLIANCE-PACKS exists, this option pulls the
facility's required pack. Keep the quick CV path always available for
speculative outreach.

## Guard rails
- Restyle any new UI to the established high-polish design language (the
  submit dialog should match the app's modal styling).
- No upsert with explicit id; new inserts let id default.
- Verify every stage in Supabase, not just on screen.
- Checkpoint commit before starting; commit each stage.

## Relationship to COMPLIANCE-PACKS
This submit-flow feature and COMPLIANCE-PACKS-BRIEF.md are related but
separate. Submit-flow adds dates + manual/CV attach to the submission (buildable
now). Compliance packs are the structured pre-loaded facility requirements
(bigger, separate). Stage 4 is where they eventually connect - the pack option
in the submit flow can draw on the compliance-packs data once it exists.
