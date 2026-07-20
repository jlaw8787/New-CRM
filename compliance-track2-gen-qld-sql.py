# Compliance Track 2, stage 2 (v3, junk-filtered): generates the QLD-only
# SQL migration from the stage-1 parsed output.
#
# Confirmed live facts used:
#   - health_authority values on live QLD facilities are title-case
#     ("Central QLD HHS" etc) and match this script's title_case() output.
#   - compliance_requirements now has a dedicated role_qualifier column.
#   - the 6 live QLD facilities (name + aliases) are hardcoded below, given
#     directly by the user (no live DB access from this environment).
#
# Does NOT run anything against Supabase. Does NOT touch index.html or
# resolveFacilityRequirements(). Reads compliance-track2-parsed.csv, writes:
#   compliance-track2-qld-load.sql                  (health_service rows +
#                                                     facility rows matched to
#                                                     a live facility, junk removed)
#   compliance-track2-qld-unmatched-facilities.sql   (facility rows with no
#                                                     live match, commented out)
#   compliance-track2-qld-junk-removed.txt           (audit list: every row
#                                                     dropped and why, plus the
#                                                     rows flagged but kept)
#
# v3 changes (source rows verified directly against the raw sheet XML before
# being added to DROP_SOURCE_ROWS -- see chat for the row-by-row evidence):
#   - 11 rows dropped: a 9-row facility/town list (Darling Downs HHS, rows
#     201-209) sitting between real documents with the same Zip File Type
#     marker, a lone town name (North West HHS, row 432), and a bare section
#     header that got a checkmark (North West HHS, row 420).
#   - 1 row (South West HHS, row 491) kept but flagged in-file: its
#     role_qualifier is a garbled multi-site list, not a clean "X Only"
#     restriction. Not auto-split -- flagged for a human call.
#   - v2's role_qualifier/exception_note, facility-match, and timing logic
#     unchanged.

import csv
import re
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IN_CSV = os.path.join(SCRIPT_DIR, 'compliance-track2-parsed.csv')
OUT_SQL = os.path.join(SCRIPT_DIR, 'compliance-track2-qld-load.sql')
OUT_UNMATCHED = os.path.join(SCRIPT_DIR, 'compliance-track2-qld-unmatched-facilities.sql')
OUT_JUNK = os.path.join(SCRIPT_DIR, 'compliance-track2-qld-junk-removed.txt')

ACRONYMS = {'HHS', 'IEMR', 'RACF', 'LHD', 'LHN', 'QLD', 'NSW', 'SA', 'WA', 'VIC', 'ACT', 'TAS', 'NT'}
CONNECTORS = {'and', 'of', 'the', 'in', 'on', 'for', 'to', 'at'}

LIVE_QLD_FACILITIES = {
    'Charleville Hospital': {'Charleville Hospital', 'Charleville'},
    'Emerald Hospital': {'Emerald Hospital', 'Emerald'},
    'Longreach Hospital': {'Longreach Hospital', 'Longreach'},
    'Mount Isa Base Hospital': {'Mount Isa Base Hospital', 'Mount Isa', 'Isa'},
    'Thursday Island Hospital': {'Thursday Island Hospital', 'Thursday Island'},
    'Weipa Hospital': {'Weipa Hospital', 'Weipa'},
}
ALL_MATCH_STRINGS = set()
for _names in LIVE_QLD_FACILITIES.values():
    ALL_MATCH_STRINGS |= _names

# source_row (from the stage-1 CSV) -> reason. Verified by reading the raw
# sheet XML directly, not by pattern-matching alone.
DROP_SOURCE_ROWS = {
    '201': 'facility/site name, not a document (Mt Lofty Heights Nursing Home)',
    '202': 'facility/site name, not a document (The Oaks Nursing Home)',
    '203': 'facility/site name, not a document (Karingal Nursing Home)',
    '204': 'facility/site name, not a document (Dr EAF McDonald Nursing Home)',
    '205': 'facility/site name, not a document (Forest View Residential Care Unit)',
    '206': 'facility/site name, not a document (Milton House Residential Aged Care)',
    '207': 'town name, not a document (Wondai)',
    '208': 'town name, not a document (Inglewood)',
    '209': 'town name, not a document (Millmerran)',
    '432': 'town name, not a document (Julia Creek)',
    '420': 'bare section header leaked in as a row ("* Mandatory competencies:")',
}
FLAG_SOURCE_ROWS = {
    '491': 'role_qualifier is a garbled multi-site list, not a clean "X Only" restriction '
           '("Roma - Westhaven Aged Care, Dirranbandi, Waroona Nursing Home (Charleville), Mitchell Only") '
           '-- kept, requirement itself (NDIS Clearance) is real, but needs a human call on the qualifier.',
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

    if facility:
        level = 'facility'
        scope_name = title_case(facility)
    elif region:
        level = 'health_service'
        scope_name = title_case(region)
    else:
        level = 'state'
        scope_name = 'Queensland'

    timing = 'on_submission' if delivery == 'zip' else 'before_commencing' if delivery == 'individual' else None

    return {
        'state': 'QLD', 'level': level, 'scope_name': scope_name, 'facility_id': None,
        'ward': None, 'role_qualifier': role_q or None,
        'item_key': item_key_from_label(item_label), 'item_label': item_label,
        'timing': timing, 'delivery': delivery, 'required': True,
        'exception_note': None,
        'confirmed': False, 'source_last_updated': None,
        'created_by': 'Compliance Track 2 Parser',
    }, level, facility


def row_to_sql_values(row):
    return '  (' + ', '.join([
        sql_str(row['state']), sql_str(row['level']), sql_str(row['scope_name']),
        'NULL', 'NULL', sql_str(row['role_qualifier']), sql_str(row['item_key']),
        sql_str(row['item_label']), sql_str(row['timing']), sql_str(row['delivery']),
        sql_bool(row['required']), sql_str(row['exception_note']), sql_bool(row['confirmed']),
        'NULL', sql_str(row['created_by']),
    ]) + ')'


def main():
    rows = list(csv.DictReader(open(IN_CSV, encoding='utf-8')))
    qld = [r for r in rows if r['state'] == 'QLD']

    loadable = []       # (row, flag_reason_or_None)
    unmatched = []
    dropped = []

    for r in qld:
        src = r['source_row']
        if src in DROP_SOURCE_ROWS:
            dropped.append((r, DROP_SOURCE_ROWS[src]))
            continue
        row, level, raw_facility = build_row(r)
        flag = FLAG_SOURCE_ROWS.get(src)
        if level == 'facility':
            if row['scope_name'] in ALL_MATCH_STRINGS:
                loadable.append((row, flag))
            else:
                unmatched.append((row, raw_facility))
        else:
            loadable.append((row, flag))

    hhs_count = sum(1 for r, _ in loadable if r['level'] == 'health_service')
    fac_matched_count = sum(1 for r, _ in loadable if r['level'] == 'facility')

    with open(OUT_SQL, 'w', encoding='utf-8') as f:
        f.write('-- Compliance Track 2, stage 2 (v3, junk-filtered): QLD load.\n')
        f.write('-- QLD ONLY. Does not touch the other 7 states.\n')
        f.write(f'-- {len(loadable)} rows ({hhs_count} health_service, {fac_matched_count} facility). '
                 f'{len(dropped)} junk rows removed -- see compliance-track2-qld-junk-removed.txt.\n')
        f.write('-- Review before running -- this was not auto-executed.\n\n')
        f.write("DELETE FROM compliance_requirements WHERE state='QLD';\n\n")
        f.write('INSERT INTO compliance_requirements\n')
        f.write('  (' + ', '.join(COLS) + ')\n')
        f.write('VALUES\n')
        value_lines = []
        for i, (row, flag) in enumerate(loadable):
            line = row_to_sql_values(row)
            if flag:
                line = f'  -- FLAGGED, review before relying on this row: {flag}\n' + line
            value_lines.append(line)
        f.write(',\n'.join(value_lines))
        f.write(';\n')

    with open(OUT_UNMATCHED, 'w', encoding='utf-8') as f:
        f.write('-- Compliance Track 2, stage 2: QLD facility-level rows with NO live facility\n')
        f.write('-- match (by name or alias) as of this run. Kept here, commented out, for\n')
        f.write('-- when these facilities get added to the live table. Do NOT run as-is.\n')
        f.write(f'-- {len(unmatched)} rows.\n\n')
        by_facility = {}
        for row, raw in unmatched:
            by_facility.setdefault(row['scope_name'], []).append(row)
        f.write('-- Distinct unmatched facility names (source spreadsheet, title-cased):\n')
        for name, rws in sorted(by_facility.items()):
            f.write(f'--   {name}  ({len(rws)} rows)\n')
        f.write('\n')
        f.write('-- INSERT INTO compliance_requirements\n')
        f.write('--   (' + ', '.join(COLS) + ')\n')
        f.write('-- VALUES\n')
        lines = []
        for row, raw in unmatched:
            lines.append('--   ' + row_to_sql_values(row)[2:])
        f.write(',\n'.join(lines))
        f.write(';\n')

    with open(OUT_JUNK, 'w', encoding='utf-8') as f:
        f.write('COMPLIANCE TRACK 2, QLD LOAD -- JUNK REMOVED / FLAGGED (audit list)\n')
        f.write('=' * 70 + '\n\n')
        f.write(f'DROPPED ({len(dropped)} rows, not in the load file at all):\n')
        f.write('-' * 70 + '\n')
        for r, reason in dropped:
            f.write(f"source_row={r['source_row']}  region={r['region']}  "
                     f"label={r['item_label']!r}\n  reason: {reason}\n\n")
        f.write(f'\nFLAGGED BUT KEPT ({len(FLAG_SOURCE_ROWS)} rows, in the load file with a warning comment):\n')
        f.write('-' * 70 + '\n')
        for r in qld:
            if r['source_row'] in FLAG_SOURCE_ROWS:
                f.write(f"source_row={r['source_row']}  region={r['region']}  "
                        f"role_qualifier={r['role_qualifier']!r}  label={r['item_label']!r}\n"
                        f"  reason: {FLAG_SOURCE_ROWS[r['source_row']]}\n\n")

    print(f'health_service rows: {hhs_count}')
    print(f'facility rows matched (loaded): {fac_matched_count}')
    print(f'facility rows unmatched (commented out): {len(unmatched)}')
    print(f'junk rows dropped: {len(dropped)}')
    print(f'rows flagged but kept: {len(FLAG_SOURCE_ROWS)}')
    print(f'Wrote {OUT_SQL}')
    print(f'Wrote {OUT_UNMATCHED}')
    print(f'Wrote {OUT_JUNK}')


if __name__ == '__main__':
    main()
