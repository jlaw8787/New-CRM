# PHASE-MODEL-BRIEF.md

Change the candidate "phase" model to match real travel-nursing workflow.
LOCKED decision. To be built AFTER the candidate page redesign.

Written 2026-07-11.

---

## Why

The current 10 phases (New Lead, Screening, Compliance, Submission, Offer,
Contract, Travel & Onboarding, On Assignment, Redeployment, Extension/Exit)
don't match how the team actually works and aren't natural industry language.
Key problems: Screening + Compliance are really one "get them cleared" stage;
Submission is an action not a state; and Travel & Onboarding / On Assignment /
Redeployment tried to make CONTRACT-level steps into candidate phases.

## The new phase list (LOCKED - 8 phases, in order)

1. New Lead      - just in, getting to know them
2. Compliance    - chasing paperwork and clearances
3. Available     - compliant and ready to submit (new OR returning from an
                   assignment - this merges the old "ready to submit" and
                   "available again" into one)
4. Submitted     - put forward to one or more roles (open or client outreach)
5. Offer         - role offered
6. Contracted    - contract locked in / on assignment
7. Extension     - extending current placement
8. Cancelled     - fell through or withdrew

## Critical modelling decision

Travel / accommodation / first-shift / contract-compliance confirmation is NOT
a candidate phase. It only applies once a contract is locked in, and it belongs
to THAT contract. This is already handled by the existing Manage Placement
feature on the contract. So it must NOT reappear as a candidate phase. The
"Contracted" phase is where a candidate sits while that contract-level
confirmation happens via Manage Placement.

## Manual override (required)

Phase is automatic by default (computed from the candidate's real state), BUT
consultants must be able to manually set/override a candidate's phase when
reality doesn't match what the system computed. Automatic default + manual
override.

## Build approach (when we get to it, after the redesign)

1. AUDIT FIRST (no changes): how are phases currently defined, what list drives
   them, and what automatically assigns a phase (is it computed from
   submission/contract status, or stored on the candidate?). Find every place
   phase values are referenced - the pipeline strip, badges, filters, any
   phase-based logic - so nothing is missed.
2. Map old -> new: decide how each old phase maps to a new one for existing
   data (e.g. Screening -> Compliance, Submission -> Submitted, On Assignment
   -> Contracted, Redeployment -> Available, Extension/Exit -> Extension or
   Cancelled). Migrate existing candidates to the new phases.
3. Replace the phase list and update the automatic-assignment logic to the new
   8 phases.
4. Add manual override UI (a phase control on the candidate page - likely in
   the new identity header or overview - letting a consultant set phase
   directly, which then sticks over the automatic value).
5. Update the pipeline strip, badges, filters, and any colour/order mapping.
6. Verify: existing candidates show sensible new phases, automatic assignment
   works, manual override works and persists to Supabase.

## Guard rails
- This is a LOGIC + DATA change, do it as its own task, not mixed into the UI
  redesign.
- Checkpoint commit before starting.
- Verify phase changes persist in Supabase, not just on screen.
