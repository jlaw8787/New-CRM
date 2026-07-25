# CAPTAIN CONTRACT — V2 UPGRADE PLAN

Status: PLANNING. This is the map, not a task. Build V2 as sequenced, shippable slices — never a big-bang rewrite. Each slice leaves the app working and verified before the next.

## Context

Captain Contract is a travel-nursing CRM: single-file vanilla JS (index.html) + Supabase, deployed to GitHub Pages. Currently a solo hobby build. Goal for V2: make it professional, polished, and consistent across every page, built so it CAN scale to real team use later without being over-built for scale it doesn't have yet.

The honest reason for a plan: "upgrade the whole system" done as one push is the most dangerous thing possible to a working app. One stale file or RLS gap has already cost hours. V2 must be ordered slices, each verified, each leaving the app working.

## The two foundations

Everything traces back to two things. Get these right and every page inherits the improvement. Get them wrong and you patch forever.

### 1. Consistent hierarchy model
State -> Region/HHS -> Facility -> Ward, with Clinical Area as a cross-cutting dimension. Today this lives inconsistently: facilities have a health_authority string, roles have a ward, compliance resolves through a cascade, candidates have loose specialty. If all of it referenced one clean hierarchy, then filtering, matching, compliance, and promo all speak the same language. This is the spine of V2.

### 2. Consistent interaction / design language
The grid pattern, coloured clinical-area pills (solid = primary, outlined = will-flex), inline editing, a legible type scale, applied the same way on candidates, facilities, job board — everywhere. So the app feels like one product, not twelve pages built at different times.

## Design language decisions (from mockups, agreed)

- Airtable-style dense grid views: sortable columns, filter chips, one row per record.
- Colour-per-clinical-area pills, consistent everywhere: ED=teal, Medical=blue, Renal=amber, Mental Health=purple, Theatre=pink, Midwifery=green, etc. Solid pill = primary area, outlined = will-flex.
- Inline editing: click a field, edit in place, save on the spot, no modal.
- Legibility: readable base font size, clear hierarchy, fix small/hard-to-read text (a real usability defect flagged repeatedly, not a taste thing).
- NOT a restyle. A restyle trial was built and rejected on sight. V2 is about working better, not repainting.

## Data model work (prerequisite for grid + filtering + matching)

These must be captured before the grid filters can work:
- Candidate: flex specialties (not just one primary), multiple states open to, availability with OPTIONAL end date.
- CRITICAL travel-nursing quirk: availability is often open-ended ("available from 1 Aug, ongoing", no end date). The model must store this as a first-class state and the filter must treat a missing end date as "available indefinitely from that date", NOT as an error or zero-length window. Get this wrong and the most-available nurses silently drop out of filter results.

## The build sequence (dependency order)

### Slice 0 — Inspection (do first, start of next session)
Report only, no code. Establish what already exists vs what's new:
- Candidate profile tabs: list each, flag underbuilt/placeholder/small-text ones.
- Candidate data: does it store flex specialties, multi-state, open-ended availability? (Likely not — flag gaps.)
- Notes: any free-text notes capability today?
- Audit: activity + contract_audit tables exist. What's actually logged vs what significant actions are NOT (compliance edits, rate changes, submissions)?
- Is there an activity-feed UI that notes + auto-events could share?
- Backend: confirm purely static + Supabase client, no send mechanism. Confirm what SMS/email would require.
- Hierarchy: how consistently is State/Region/Facility/Ward/Clinical-Area referenced across candidates, facilities, roles, compliance?

### Slice 1 — Candidate data capture
Add the fields the grid/filter/matching need: flex specialties, multi-state, open-ended availability. Small edit-form additions + migrations. Nothing visual yet. This unblocks everything after it.

### Slice 2 — Candidate grid (the big uplift)
Airtable-style grid of all candidates. Coloured clinical-area pills, sortable columns, filter chips (specialty, state, availability-overlap incl. open-ended, compliance, status). Click row -> profile. Absorbs the "better filtering everywhere" need. Legibility baked in since it's a fresh view.

### Slice 3 — Notes + audit trail (one activity stream)
Free-text notes + auto-logged events (submitted, contract signed, compliance changed, rate edited) in ONE timeline on the candidate. Design an SMS-event slot for later. Confirm audit coverage is complete for compliance/audit purposes (immutable, who-did-what-when). Extends existing activity/contract_audit tables, not from zero.

### Slice 4 — Dashboard edits (start-of-day command centre)
The dashboard is how the day starts, so it matters. Wire remaining inert elements. "My available candidates" quick view tied to the new grid/filters. Surface notes/follow-ups due today. Legibility pass. Later: command palette (Cmd-K) for search + actions.

### Slice 5 — Role promo / marketing pack (new capability)
Client lists a role -> promote it to candidates. Generate a facility + destination + role pack like the Port Macquarie PDF example (facility info, specialties, lifestyle/destination, weekend info, "ask your consultant"). A "Promote role" fast-share button on roles. Reuses the client-side PDF machinery already proven by the contract generator. Sits on the hierarchy model.

### Slice 6 — Hierarchy consistency pass
Make State/Region/Facility/Ward/Clinical-Area reference one clean model across all pages. Improves matching logic and compliance resolution as a side effect. Touches core data, so careful and staged.

### Slice 7 — Inline editing + flow polish
Inline edit across grid and profiles. Optimistic UI + subtle save confirmation. Bulk actions on the grid. Duplicate-candidate detection.

### Slice 8 — Backend cluster (one deliberate project, later)
SMS sending, auto-email weekend handover, scheduled tasks. All need Supabase Edge Functions + a send service (Twilio/Resend). Do as ONE "go backend" project, not piecemeal, because they share the same infrastructure. This is also where the deferred team-tasks and auto-email handover land.

## What stays untouched / already done (don't rebuild)

Working and verified — leave alone unless a slice explicitly touches it:
- PDF contract generator (two-party, facility address, TBC handling)
- Weekend handover report (gap tally, per-contract travel)
- Compliance Track 2 QLD load (individual requirements, delivery split, role_qualifier) — other 7 states still to load, same proven pattern
- Facility aliases (search + requirement matching)
- Compliance-expiry-during-contract alert + persistent Manage Placement marker
- Clickable open-role cards -> Job Board role detail -> submit
- Dashboard/Facilities/Job Board tile wiring
- Morning Brief expandable rows
- Real Supabase auth (stages 1-3 done; stage 4 remove-picker + stage 5 full RLS pending, waiting on "official")
- RLS authenticated-role policies (added this session — the fix for the logged-in-sees-nothing bug)

## Open items to settle as slices reach them

- Compliance Track 2: load remaining 7 states (parked, pattern proven, see COMPLIANCE-TRACK2-BRIEF).
- Auth stage 4/5: backfill all users -> remove picker -> full RLS. Waiting until app goes official.
- Snooze vs persistent marker: verify snoozing an expiry alert leaves the Manage Placement marker visible (flagged for testing).
- "Submit any candidate" (not just matched) to a role: no candidate-search widget exists anywhere; needed for the full submit flow.

## Guardrails (unchanged, apply to every slice)

- Plan before building. One thing at a time.
- Inspect first — read the code before changing it. This discipline caught real problems repeatedly.
- Verify real behaviour in the browser AND Supabase before moving on.
- Test on the deployed site — changes need git push to appear on jlaw8787.github.io/New-CRM. (Most "it doesn't work" moments were unpushed code.)
- Commit + push after each verified piece.
- DELETE-and-replace or RLS changes: run by hand in the SQL editor, never auto-run, so you see the mapping/count before it fires.
- Distinguish "technically works" from "right for the workflow".
- No AI-sounding phrasing in any output. No em dashes.

## IMMEDIATE NEXT SESSION — finish compliance requirements (Track 2 continuation)

Highest-completion, lowest-risk, most token-friendly next task. The parser output already exists (compliance-track2-parsed.csv, 1762 rows across 8 states). QLD is loaded and proven. The other states are the SAME load with different data — no inspection, no re-parse, just repeat.

Method (token-friendly, actionable):
1. FIRST: check which states your ~16 live facilities are actually in. Load ONLY those states. A state with zero live facilities = requirements that resolve to nothing yet = pointless until facilities exist there. This likely shrinks the job from 7 states to 4-5.
2. Per state, one prompt: generate compliance-track2-<state>-load.sql from the parsed CSV, same column mapping + junk filter + facility-match-or-park logic as QLD. Do NOT auto-run.
3. Run each by hand in the SQL editor (it's a DELETE-and-replace). Verify ONE facility in that state resolves. Then next state.
4. Commit after each.

Do NOT bundle facility-seeding-from-Excel into this. That's a reconciliation project (522 facilities, name mismatches, junk rows, TAS wards-as-facilities) and belongs with Slice 6 hierarchy work.

### CONFIRMED: which states to load (checked live)

Live facility counts: QLD 6 (DONE), NT 4, WA 3, SA 2, TAS 1. NSW/VIC/ACT have ZERO facilities.

So load ONLY: NT, WA, SA, TAS (4 states). Skip NSW, VIC, ACT — no facilities there, so their requirements would resolve to nothing. Load them later if/when facilities in those states get added.

Order suggestion: smallest first to build rhythm — TAS (1 facility), SA (2), WA (3), NT (4). One state per prompt, run by hand in SQL editor, verify one facility resolves, commit, next.

## TAS FACILITY IMPORT — reconciliation done, DECISIONS PENDING (next session)

Path B chosen: import real facilities per state from the Excel, THEN load that state's requirements. State by state. TAS first (hardest small state — has the RHH ward mess).

TAS reconciliation is DONE (report generated). Key findings:
- 20 real TAS facilities in the source. 1 already exists (Mersey Community Hospital, id 16). So 19 new + RHH's wards.
- 14 "facility" rows under Royal Hobart Hospital are actually WARDS of one facility, not 14 facilities. Confirmed by the sheet's own "FACILITIES IN THIS REGION (14)" subheading.
- ALL SITES and All Other Clinical Areas = non-facility requirement buckets. Exclude.
- CRITICAL: the source has NO region, health_authority, facility type, or per-ward nurse-type data. All of that was INFERRED by Claude Code and must be confirmed by a human before insert. Inferred data going into the live facilities table is a real risk (candidates get matched against it).

5 DECISIONS needed from Josh before any TAS insert:
1. 6A Surgical vs TASU — one ward or two? (RHH Wards sheet maps 6A -> TASU as its clinical area, implying they're the same; R&F lists them separately.)
2. Maternity and Pool (Paeds/NICU/MHHITH) — RHH wards, a standalone statewide pool entity, or excluded like ALL SITES?
3. Missing clinical-area labels for: 4A Short Stay Suite, Theatre, 9A Oncology, plus Peacock 1&2 and Peacock 3 (which appear in RHH Wards sheet but NOT the R&F ward list).
4. Confirm/correct every inferred Region and health_authority value (see report table).
5. Facility type (Calvary + Hobart Private are almost certainly Private, not Public) and a nurse-type default for all new wards (source has none).

Suggested next-session flow: make the 5 calls -> insert the 18 straightforward facilities first -> resolve RHH wards -> insert RHH -> then load TAS requirements against the now-fuller facility set -> verify -> commit. That becomes the template for WA, SA, NT.

HONEST NOTE: this is data-AUTHORING, not a data-load. The Excel lacks region/authority/type/nurse-type. Each state needs Josh's domain knowledge to complete cleanly. Budget accordingly — this is several careful sessions, not one.
