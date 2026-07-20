# Compliance Track 2, stage 2: generates the TAS-only SQL migration from the
# stage-1 parsed output. Same proven pattern as compliance-track2-gen-qld-sql.py
# (title_case(), item_key_from_label(), sql_str/sql_bool, live-facility-name
# matching gate, junk-removed audit log) -- adapted where TAS's source
# structure genuinely differs from QLD's, documented below.
#
# How TAS differs from QLD (why this isn't a blind copy-paste):
#   - QLD's "region" column is a real multi-facility health-authority grouping
#     (e.g. "Central QLD HHS" covers many facilities) -- that's what QLD's
#     health_service level and health_authority matching is for.
#   - TAS's "region" column is, for almost every row, just the facility name
#     repeated (facility == region). There is NO true multi-facility grouping
#     in this TAS source data at all. Confirmed: 0 rows end up at
#     level='health_service' in this load. health_authority values just
#     imported (Tas Health North/NW/South/West Coast/Statewide) have nothing
#     in this source to match against yet -- they'll matter if/when TAS gets
#     genuine multi-facility compliance content later.
#   - TAS's "ALL SITES" rows (region==facility=='ALL SITES', 27 rows) are
#     handled as level='state' (scope_name='Tasmania'), matching QLD script's
#     own state-level fallback branch -- just actually triggered here, since
#     QLD's source never had literal state-wide rows to exercise it. This is
#     a deliberate, reported deviation, not a silent reinterpretation.
#   - Royal Hobart Hospital's 15 rows have facility=='' (blank) with
#     region=='ROYAL HOBART HOSPITAL' -- a stage-1 parsing quirk, not a
#     separate entity. Per user decision, these load as level='facility',
#     scope_name='Royal Hobart Hospital' (matches the live RHH facility by
#     name/alias), NOT as separate rows per ward.
#   - 'Maternity' (facility=='Maternity', 2 rows) is, per user decision, an
#     RHH ward -- loaded as level='facility', scope_name='Royal Hobart
#     Hospital', with ward='Maternity' kept as metadata (the app doesn't
#     currently filter facility-level display by ward, but the column exists
#     and the fact is preserved for future use).
#   - 'Pool' (Paeds/NICU/MHHITH, 4 rows) is EXCLUDED per user decision.
#   - 'All Other Clinical Areas' (1 row) is dropped as junk: an ambiguous
#     statewide catch-all the user did not rule on this pass (same status as
#     it had in the facility-reconciliation report -- not resolved, not
#     guessed).
#   - Two facility names don't survive generic title_case() intact --
#     "CHAPS - CHILD HEALTH AND PARENTING SERVICE LAUNCESTON" title-cases to
#     "Chaps - Child Health and Parenting Service Launceston" (wrong
#     mid-word case, missing the "(Launceston)" parens the live facility
#     name uses) and "SMHS - STATEWIDE MENTAL HEALTH SERVICE" title-cases to
#     "Smhs - ..." (SMHS isn't in the ACRONYMS set). Both are corrected via
#     an explicit SCOPE_NAME_OVERRIDES map to their live alias ('CHaPS',
#     'SMHS') rather than silently trusting generic title-casing to match.
#
# No junk rows found in the QLD sense (facility-name-only rows, bare section
# headers, garbled multi-site role_qualifiers) -- TAS's stage-1 parser output
# only ever captured checkmarked (raw_type='root') requirement rows, verified
# by reading every one of the 138 TAS rows directly. DROP_SOURCE_ROWS is
# empty; the only "drops" are the Pool/All Other Clinical Areas scope
# exclusions above, which are scope decisions, not junk/garble cleanup.
#
# Does NOT run anything against Supabase. Does NOT touch index.html or
# resolveFacilityRequirements(). Reads compliance-track2-parsed.csv, writes:
#   compliance-track2-tas-load.sql                  (state + facility rows
#                                                     matched to a live
#                                                     facility)
#   compliance-track2-tas-unmatched-facilities.sql   (facility rows with no
#                                                     live match, commented
#                                                     out -- expected to be
#                                                     empty for this run)
#   compliance-track2-tas-junk-removed.txt           (audit list: every row
#                                                     excluded and why)

import csv
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IN_CSV = os.path.join(SCRIPT_DIR, 'compliance-track2-parsed.csv')
OUT_SQL = os.path.join(SCRIPT_DIR, 'compliance-track2-tas-load.sql')
OUT_UNMATCHED = os.path.join(SCRIPT_DIR, 'compliance-track2-tas-unmatched-facilities.sql')
OUT_JUNK = os.path.join(SCRIPT_DIR, 'compliance-track2-tas-junk-removed.txt')

ACRONYMS = {'HHS', 'IEMR', 'RACF', 'LHD', 'LHN', 'QLD', 'NSW', 'SA', 'WA', 'VIC', 'ACT', 'TAS', 'NT'}
CONNECTORS = {'and', 'of', 'the', 'in', 'on', 'for', 'to', 'at'}

# 20 live TAS facilities (name + aliases), per the just-generated
# tas-facility-import.sql (19 new + Mersey Community Hospital, id 16,
# already live). Used only to gate facility-level matching -- confirmed
# against the real live facilities table for Mersey, and against the
# import script for the other 19 (not yet run at the time of this script).
LIVE_TAS_FACILITIES = {
    'Beaconsfield & George Town District Hospitals': {'Beaconsfield & George Town District Hospitals'},
    'Calvary - Lenah Valley Hospital': {'Calvary - Lenah Valley Hospital'},
    'Campbell Town Health Service': {'Campbell Town Health Service'},
    'Cape Barren Island Clinic': {'Cape Barren Island Clinic'},
    'CHaPS - Child Health and Parenting Service (Launceston)': {'CHaPS - Child Health and Parenting Service (Launceston)', 'CHaPS'},
    'Flinders Island': {'Flinders Island'},
    'Hobart Private': {'Hobart Private'},
    'King Island Hospital': {'King Island Hospital'},
    'Launceston General Hospital': {'Launceston General Hospital', 'LGH'},
    'Mersey Community Hospital': {'Mersey Community Hospital', 'Mersey'},
    'Mersey Leven Community Nursing': {'Mersey Leven Community Nursing'},
    'North West Regional Hospital': {'North West Regional Hospital', 'NWRH'},
    'Northern Cancer Care': {'Northern Cancer Care'},
    'Rosebery Community Health Centre': {'Rosebery Community Health Centre'},
    'Royal Hobart Hospital': {'Royal Hobart Hospital', 'RHH'},
    'SMHS - Statewide Mental Health Service': {'SMHS - Statewide Mental Health Service', 'SMHS'},
    'Smithton District Hospital': {'Smithton District Hospital'},
    "St Helen's District Hospital": {"St Helen's District Hospital"},
    "St Mary's Health Centre": {"St Mary's Health Centre"},
    'West Coast District Hospital': {'West Coast District Hospital'},
}
ALL_MATCH_STRINGS = set()
for _names in LIVE_TAS_FACILITIES.values():
    ALL_MATCH_STRINGS |= _names

# Generic title_case() doesn't survive these two source strings intact
# (see header note). Keyed by the raw source facility text, upper-cased.
SCOPE_NAME_OVERRIDES = {
    'CHAPS - CHILD HEALTH AND PARENTING SERVICE LAUNCESTON': 'CHaPS',
    'SMHS - STATEWIDE MENTAL HEALTH SERVICE': 'SMHS',
}

# Scope exclusions -- not junk/garble, deliberate scope decisions (see header).
DROP_REGIONS = {
    'Pool': 'excluded per user decision (Pool: Paeds/NICU/MHHITH) -- not attributed to any live facility',
    'All Other Clinical Areas': 'ambiguous statewide catch-all, not ruled on this pass -- excluded pending a decision, not guessed',
}


def title_case(text):
    words = text.split(' ')
    out = []
    for i, w in enumerate(words):
        parts = w.split('-')
        newparts = []
        for p in parts:
            core = p.strip()
            if not core:
                newparts.append(p)
                continue
            up = core.upper()
            if up in ACRONYMS:
                newparts.append(up)
            elif core.lower() in CONNECTORS and i != 0:
                newparts.append(core.lower())
            else:
                newparts.append(core[0].upper() + core[1:].lower())
        out.append('-'.join(newparts))
    return ' '.join(out)


def item_key_from_label(label):
    key = re.sub(r'[^a-z0-9]+', '_', (label or '').lower().strip())
    key = key.strip('_')
    return key or 'item_unknown'


def sql_str(v):
    if v is None or v == '':
        return 'NULL'
    return "'" + str(v).replace("'", "''") + "'"


def sql_bool(v):
    return 'true' if v else 'false'


COLS = ['state', 'level', 'scope_name', 'facility_id', 'ward', 'role_qualifier', 'item_key',
        'item_label', 'timing', 'delivery', 'required', 'exception_note', 'confirmed',
        'source_last_updated', 'created_by']


def build_row(r):
    facility = (r['facility'] or '').strip()
    region = (r['region'] or '').strip()
    role_q = (r['role_qualifier'] or '').strip()
    item_label = r['item_label']
    delivery = r['delivery']
    ward = None

    if region.upper() == 'ALL SITES':
        level = 'state'
        scope_name = 'Tasmania'
    elif region.upper() == 'ROYAL HOBART HOSPITAL' and not facility:
        level = 'facility'
        scope_name = 'Royal Hobart Hospital'
    elif region == 'Maternity':
        level = 'facility'
        scope_name = 'Royal Hobart Hospital'
        ward = 'Maternity'
    elif facility:
        level = 'facility'
        scope_name = SCOPE_NAME_OVERRIDES.get(facility.upper(), title_case(facility))
    else:
        # Not expected to be reached: Pool / All Other Clinical Areas (the
        # only other blank/ambiguous cases) are dropped before build_row runs.
        level = 'state'
        scope_name = 'Tasmania'

    timing = 'on_submission' if delivery == 'zip' else 'before_commencing' if delivery == 'individual' else None

    return {
        'state': 'TAS', 'level': level, 'scope_name': scope_name, 'facility_id': None,
        'ward': ward, 'role_qualifier': role_q or None,
        'item_key': item_key_from_label(item_label), 'item_label': item_label,
        'timing': timing, 'delivery': delivery, 'required': True,
        'exception_note': None,
        'confirmed': False, 'source_last_updated': None,
        'created_by': 'Compliance Track 2 Parser',
    }, level


def row_to_sql_values(row):
    return '  (' + ', '.join([
        sql_str(row['state']), sql_str(row['level']), sql_str(row['scope_name']),
        'NULL', sql_str(row['ward']), sql_str(row['role_qualifier']), sql_str(row['item_key']),
        sql_str(row['item_label']), sql_str(row['timing']), sql_str(row['delivery']),
        sql_bool(row['required']), sql_str(row['exception_note']), sql_bool(row['confirmed']),
        'NULL', sql_str(row['created_by']),
    ]) + ')'


def main():
    rows = list(csv.DictReader(open(IN_CSV, encoding='utf-8-sig')))
    tas = [r for r in rows if r['state'] == 'TAS']

    loadable = []       # (row, level)
    unmatched = []
    dropped = []

    for r in tas:
        region = (r['region'] or '').strip()
        if region in DROP_REGIONS:
            dropped.append((r, DROP_REGIONS[region]))
            continue
        row, level = build_row(r)
        if level == 'facility':
            if row['scope_name'] in ALL_MATCH_STRINGS:
                loadable.append(row)
            else:
                unmatched.append(row)
        else:
            loadable.append(row)

    state_count = sum(1 for r in loadable if r['level'] == 'state')
    hhs_count = sum(1 for r in loadable if r['level'] == 'health_service')
    fac_matched_count = sum(1 for r in loadable if r['level'] == 'facility')

    with open(OUT_SQL, 'w', encoding='utf-8') as f:
        f.write('-- Compliance Track 2, stage 2: TAS load.\n')
        f.write('-- TAS ONLY. Does not touch the other 7 states.\n')
        f.write(f'-- {len(loadable)} rows ({state_count} state, {hhs_count} health_service, '
                 f'{fac_matched_count} facility). {len(dropped)} rows excluded -- see '
                 f'compliance-track2-tas-junk-removed.txt.\n')
        f.write('-- Review before running -- this was not auto-executed.\n\n')
        f.write("DELETE FROM compliance_requirements WHERE state='TAS';\n\n")
        f.write('INSERT INTO compliance_requirements\n')
        f.write('  (' + ', '.join(COLS) + ')\n')
        f.write('VALUES\n')
        f.write(',\n'.join(row_to_sql_values(row) for row in loadable))
        f.write(';\n')

    with open(OUT_UNMATCHED, 'w', encoding='utf-8') as f:
        f.write('-- Compliance Track 2, stage 2: TAS facility-level rows with NO live facility\n')
        f.write('-- match (by name or alias) as of this run. Kept here, commented out, for\n')
        f.write('-- when these facilities get added to the live table. Do NOT run as-is.\n')
        f.write(f'-- {len(unmatched)} rows.\n\n')
        by_facility = {}
        for row in unmatched:
            by_facility.setdefault(row['scope_name'], []).append(row)
        f.write('-- Distinct unmatched facility names (source spreadsheet, title-cased):\n')
        for name, rws in sorted(by_facility.items()):
            f.write(f'--   {name}  ({len(rws)} rows)\n')
        f.write('\n')
        f.write('-- INSERT INTO compliance_requirements\n')
        f.write('--   (' + ', '.join(COLS) + ')\n')
        f.write('-- VALUES\n')
        lines = ['--   ' + row_to_sql_values(row)[2:] for row in unmatched]
        f.write(',\n'.join(lines))
        f.write(';\n' if lines else '\n')

    with open(OUT_JUNK, 'w', encoding='utf-8') as f:
        f.write('COMPLIANCE TRACK 2, TAS LOAD -- EXCLUDED ROWS (audit list)\n')
        f.write('=' * 70 + '\n\n')
        f.write(f'EXCLUDED ({len(dropped)} rows, not in the load file at all):\n')
        f.write('-' * 70 + '\n')
        for r, reason in dropped:
            f.write(f"source_row={r['source_row']}  region={r['region']}  "
                     f"label={r['item_label']!r}\n  reason: {reason}\n\n")
        f.write('\nNo QLD-style junk found (facility-name-only rows, bare section headers,\n'
                'garbled multi-site role_qualifiers) -- every TAS source row is a genuine\n'
                'checkmarked requirement. All exclusions above are scope decisions, not\n'
                'parser garbage.\n')

    print(f'state rows: {state_count}')
    print(f'health_service rows: {hhs_count}')
    print(f'facility rows matched (loaded): {fac_matched_count}')
    print(f'facility rows unmatched (commented out): {len(unmatched)}')
    print(f'rows excluded: {len(dropped)}')
    print(f'Wrote {OUT_SQL}')
    print(f'Wrote {OUT_UNMATCHED}')
    print(f'Wrote {OUT_JUNK}')


if __name__ == '__main__':
    main()
