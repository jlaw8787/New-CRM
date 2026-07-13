# COMPLIANCE-PACKS-BRIEF.md

Feature: pre-loaded, cascading, editable paperwork/compliance packs attached
to the right facilities/regions/states, so consultants setting up a submission
or contract already have the correct required-documents pack, instead of
remembering it themselves.

Source data: Contract_Specific_Paperwork_Requirements.xlsx (per-state tabs) and
the Contract-Paperwork-Checklist.html / compliance_pack_form*.html the user
built. These hold the real requirement matrix.

UPDATE 2026-07-13: a cleaner, complete replacement source file now exists in
the CRM folder - Contract_Paperwork_Requirements_CLEAN.xlsx. All 8 states, a
Regions & Facilities directory (524 rows mapping facilities to state/region),
facility abbreviations, and ward mappings. This supersedes the original xlsx
as the source for Track 2 (see Track 2 section below) - NOT loaded yet, demo
runs on the existing Central QLD slice only.

Written 2026-07-11.

---

## Why this matters

Right now, knowing "what paperwork does QLD Central HHS need for this
placement" lives in a consultant's head or a spreadsheet. This feature moves
that knowledge into the CRM so it's automatic, consistent, and shown at the
point of work. It's a genuine client-facing differentiator: it makes the
submission process smarter and more reliable. It's the "guide the consultant"
principle applied to compliance.

## The core model: requirements CASCADE (confirmed with user)

A placement's required-documents pack is the SUM of every level that applies
to it:

  State-wide reqs  (apply to every facility in the state)
    + Health service / region reqs  (apply to facilities in that HHS/region)
      + Facility-specific reqs  (this facility only)
        + Ward-specific reqs  (this ward only)
        + Facility/ward EXCEPTIONS (e.g. "Woorabinda Only - Hep A",
          "Babinda Only - CRC", "Mental Health Only - Drivers Licence")

So packs attach at whatever level the requirement lives, and a given
placement resolves its full pack by collecting all applicable levels. This
matches how the source spreadsheet is actually organised (state tab -> health
service -> facilities -> per-item, with "X Only" exceptions inline).

## Structure seen in the real data (QLD tab, 282 rows)

- QLD contains Health Services: Central QLD HHS, Cairns HHS, Central West HHS,
  etc. Each lists its facilities (e.g. Central QLD: Banana MH, Baralaba,
  Biloela, Woorabinda, Capricornia Correctional Centre...).
- Each item has meaningful attributes worth preserving:
  - Timing: "send on submission" vs "on file before commencing" (two distinct
    columns in the sheet: CREDENTIALS TEAM TO SEND ON SUBMISSION vs PLACEMENTS
    CREDENTIALS TO RECEIVE/on file prior to commencing).
  - Delivery: "Zip File" flag (goes in the submission zip) vs individual.
  - A "confirmed" / spec tick (√) and a LAST UPDATED date per health service.
  - Facility-specific exceptions inline ("Woorabinda Only - ...").
- Example items: References (1 in last 3 months), AHPRA, Photo ID, Hep B
  (serology or doses), MMR, CPDs (BLS, CTP...), immunisations, CRC.

## Existing app hooks to build ON, not from scratch

- Facility pages already have a "Submission Checklist" section (currently
  "No submission checklist set up" empty state) - this is the natural home for
  facility-level pack items.
- Candidates already have compliance_items and a Compliance tab/percentage.
- So the pack (what's required) lives at facility/region/state level; the
  candidate's compliance is checked AGAINST the resolved pack for a placement.

---

## TWO TRACKS

### TRACK 1 - DEMO SLICE (before the boss/client demo)

Scope agreed with user: ONE STATE (QLD), loaded and cascading, EDITABLE in the
demo (add / remove / tick items). Broader than one facility but can be rougher
than the full system. Goal: show clients how the submission process gets
smarter - "the system already knows what this QLD site needs."

Demo slice needs:
1. QLD requirement data loaded into a structure the app can read - at least
   the state-wide items plus 2-3 health services with their facilities and a
   couple of "X Only" exceptions, enough to look real and cascade.
2. When viewing a QLD facility (or setting up a submission/contract for one),
   show the resolved pack: state items + that facility's HHS items + any
   facility exceptions, as a checklist.
3. Editable: add an item, remove an item, tick items done. Persists to
   Supabase.
4. Looks like the approved UI design language (this ships during the UI
   refresh, so it must match).

Deliberately NOT in the demo slice: all 8 states, perfect data cleaning, ward
level for every site, the full exception engine. Those are Track 2.

### TRACK 2 - FULL BUILD (after the demo)

SOURCE DATA FOR THIS TRACK (added 2026-07-13): use
Contract_Paperwork_Requirements_CLEAN.xlsx (in the CRM folder), not the
original Contract_Specific_Paperwork_Requirements.xlsx - the CLEAN file is a
complete, tidier replacement covering all 8 states, plus a dedicated Regions &
Facilities directory (524 rows mapping facilities to state/region), facility
abbreviations, and ward mappings, all in one place. Do NOT load this before
the demo - the demo runs entirely on the existing manually-seeded Central QLD
slice (compliance-qld-seed.sql). This file is for the post-demo full build
only.

- Clean and load all state tabs (ACT, QLD, NSW, SA, NT, TAS, VIC, WA) plus the
  Facility Abbreviations and RHH Wards reference tabs.
- Full cascade resolver: state + health service + facility + ward + exceptions.
- Preserve item attributes: timing (on submission vs before commencing),
  zip-file flag, confirmed/spec tick, last-updated date.
- Editable pack management UI (the user's compliance_pack_form HTML is a strong
  visual reference for this).
- Tie into candidate compliance: a placement shows which required items the
  candidate has vs is missing, driving the compliance %.
- Versioning / last-updated tracking so reqs can be maintained over time.

---

## Data handling notes (for whoever builds it)

- The xlsx is human-formatted: merged cells, section headers as rows,
  abbreviations, inline "X Only" notes. It needs parsing into clean records,
  not read literally. Budget real time for this - it's the hard part and the
  actual value.
- Suggested record shape per requirement:
  { level: state|health_service|facility|ward, scope_name, item, timing:
  on_submission|before_commencing, delivery: zip|individual, exception_note,
  confirmed: bool, last_updated }
- A resolver then, given a facility (and its state/HHS/ward), returns all
  records whose scope applies. Exceptions ("X Only") apply only when scope_name
  matches that facility/ward.

## Guard rails

- New tables get GENERATED ALWAYS AS IDENTITY ids - never write id explicitly,
  never upsert with explicit id (the 428C9 bug class).
- If built during the UI-refresh window, keep it behind its own commits so it
  can't destabilise the demo build. Data-load and UI as separate stages.
- Verify in Supabase, not just on screen.
