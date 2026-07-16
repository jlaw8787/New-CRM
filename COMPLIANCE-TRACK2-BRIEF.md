# COMPLIANCE-PACKS-TRACK2-BRIEF

Status: PARKED. This is a dedicated project, not a quick data load. Do not start it half-committed.

## What it was assumed to be

"Load the 524-row CLEAN.xlsx into compliance_requirements so compliance packs covers all 8 states instead of just Central QLD." Assumed to be a data job feeding the existing (working, verified) cascade resolver.

## What it actually is

A parser-building project with data-model decisions attached. A Step 1 inspection (14 July 2026) found:

- The file is NOT a clean table. It's a 12-sheet workbook. The "524 rows" is just a facility directory (names only), redundant with the state sheets. The real requirements live in 8 state sheets and total ~3,045 content rows, ~1,762 of which carry an actual requirement flag.
- Each state sheet has one overloaded "Type" column that means five different things depending on which header block a row sits under (region header / facility bullet / doc-status flag / section label / blank footnote). There is NO column saying "this row is a requirement." Loading requires a contextual parser that tracks state to region to facility/ward/role to section to row, the way a human reads the sheet.
- No usable item_key exists in the file. Must be derived per row (existing seed does this by hand).

## Traps that would silently break the feature if loaded raw

1. CASE MISMATCH. Xlsx headers are ALL CAPS (CENTRAL QLD HHS). The resolver matches scope_name by exact title-case string equality against facilities.health_authority (Central QLD HHS). A raw load looks like it worked but matches nothing, and compliance comes back empty for candidates. Must normalise case on load.
2. CURATED vs RAW GRAIN. Existing QLD seed collapses ~13 CPD line items into one clean cpds row. The file has them exploded. Loading the file over existing QLD data replaces curated work with raw dump, and loading both makes Emerald Hospital (and other Central QLD facilities) show duplicated/conflicting requirements.
3. DELIVERY FIELD MEANING. The file's own Key sheet defines the zip/individual flags as a staleness/confidence marker ("reconfirm requirements next placement"), NOT a delivery method. The existing seed uses delivery:'zip'/'individual' with a different invented meaning (bundled vs ad hoc). This is a real question about the data model that must be settled before scaling to ~1,700 rows.

## Per-state special cases found

- WA: uses different section headers ("QUEUE ON SHIFTMATCH" / "PRIOR TO SUBMISSION" / "PRIOR TO COMMENCEMENT") instead of the two-section pattern the other 7 states use. Universal timing rule mis-maps all ~94 WA rows unless WA is special-cased.
- ACT: uses an undefined flag word "Checklist Item" (16 rows) not defined in the Key sheet.
- "X Only:" qualifiers (Mental Health Only, Maternity Only, Corrections Only, Immuniser Roles Only, etc) are role/clinical-stream restrictions, not facilities or wards. They don't fit the state/health_service/facility/ward cascade. No reliable syntactic rule distinguishes a genuine facility name from one of these without checking against the facility list.
- RHH Wards: only one facility (Royal Hobart Hospital) has ward-level detail; the rest don't.

## Decisions the human must make before build (cannot be guessed)

1. What does "ward" hold, and how are role/stream qualifiers ("Mental Health Only") handled vs actual wards?
2. What should "delivery" mean, given the file's legend contradicts the current seed's usage?
3. Curated summary rows (like the existing QLD seed) or raw exploded rows as the thing the resolver serves? Pick one grain and apply consistently.
4. Central QLD dedupe. QLD sheet's first block (rows 3-83) is the same 15 Central QLD facilities already curated in the seed. Options:
   - (a) Replace all QLD: delete existing QLD rows, re-insert full QLD from parsed file. Full coverage, loses curation.
   - (b) Add only non-QLD: 7 other states fresh, leave QLD as-is. Safest, QLD stays incomplete.
   - (c) Dedupe: keep curated Central QLD, load only the other 12 QLD health services plus 7 states. Most surgical, but grain is inconsistent across the dataset.

## Recommended approach when picked up

Do NOT touch the cascade resolver, it is verified working (checked against Hannah Johnson, id 38). This is a data + parser task only. Build the parser incrementally: settle the 4 decisions above first, then load and verify ONE state against a real candidate before loading the next. One state at a time, verified each time, committed each time.

Source file: Contract_Paperwork_Requirements_CLEAN.xlsx (in project folder).
