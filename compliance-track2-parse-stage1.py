# Compliance Track 2 parser — STAGE 1, PARSE ONLY.
#
# Reads the 8 state sheets (ACT, NSW, NT, QLD, SA, TAS, VIC, WA) from
# Contract_Paperwork_Requirements_CLEAN.xlsx directly via zipfile + XML
# (no openpyxl dependency, none is installed in this environment) and
# walks each sheet top-to-bottom as a state machine, tracking context
# exactly the way a human reading the sheet would.
#
# Writes ONLY to local output files. Does not touch Supabase, does not
# touch the CRM app.
#
# ── Sheet structure, reverse-engineered from the cell styles ───────────
# Every row's column-A cell carries a style id that reliably identifies
# its role (verified by sampling all 8 sheets before writing this):
#   s=4   state title (row 1)               -> skip
#   s=3   column header row ("Type" etc)    -> skip
#   s=5   region / HHS / facility header
#   s=6   note / "Last updated" / free text -> skip (see WA special-case)
#   s=7   section header: "SEND ON SUBMISSION" / "CREDENTIALS TO SEND /
#         HOLD ON FILE" / "FACILITIES IN THIS REGION (N)"
#   s=10  sub-header within a section (e.g. "Immunisations:", "CPDs:",
#         or a role-qualifier line like "Mental Health Only:")
#   s=11  note/footnote (contact emails, "*Nil to send")   -> skip
#   s=12  facility-list bullet row under "FACILITIES IN THIS REGION"
#         (Type column holds '›', the '›' rows the brief calls out) -> skip
# Column A on a real requirement row holds the Type value instead:
#   '√' (a check mark, U+221A) -> requirement, delivery from active section
#   'Zip File'                      -> requirement, delivery from active section
#   'Checklist Item'  (ACT ONLY)    -> requirement, but this is not one of
#                                      the two expected Type values, so it
#                                      is flagged in the output for review
#
# ── Region vs facility ──────────────────────────────────────────────────
# A style=5 header is tentatively treated as a FACILITY (region name AND
# facility name both set to its text, mirroring how the Regions &
# Facilities sheet duplicates single-site entries). If a "FACILITIES IN
# THIS REGION (N)" marker appears before the next section header, the
# header is reclassified as a REGION instead: region=text, facility=None
# ("region-wide"), and the facility list is captured for context.
#
# ── Role qualifier ───────────────────────────────────────────────────────
# Two independent mechanisms, both produce the same role_qualifier field:
#  1. Inline: a requirement row whose own label matches
#     "<prefix> Only - <rest>" (case-insensitive "Only") splits into
#     role_qualifier=<prefix> Only, item_label=<rest>. Self-contained,
#     doesn't touch ambient state.
#  2. Ambient: a standalone s=10 header whose text contains "Only" sets
#     an ambient role_qualifier. It applies ONLY to directly-following
#     BULLET rows ('•'-prefixed) -- the first non-bullet requirement row,
#     or any new header, ends its scope. This bullet-boundary heuristic
#     was verified against QLD's "Yellagundgimarra Only:" block and TAS's
#     "Maternity Only:" block, where the qualified items are consistently
#     bulleted and the row immediately after (not bulleted) is clearly
#     out of scope (e.g. TAS "All other clinical areas - ...").
#
# ── WA's extra timing labels ─────────────────────────────────────────────
# WA has three extra phrases the brief asked to be mapped: "DOCUMENTS
# REQUIRED TO QUEUE ON SHIFTMATCH" (s=5, sheet's very first row, before
# any real region), and "PRIOR TO SUBMISSION" / "PRIOR TO COMMENCEMENT"
# (s=6, sitting just above a real "SEND ON SUBMISSION" s=7 header).
# CONCLUSION, not an assumption: these are NOT alternate spellings of
# the delivery section headers. WA uses the exact same "SEND ON
# SUBMISSION" / "CREDENTIALS TO SEND / HOLD ON FILE" text as every other
# state (confirmed: 13 and 12 occurrences respectively). The three extra
# phrases are an orthogonal TIMING label layered above/alongside the
# real section header, not a delivery-type header themselves. No
# delivery mapping was applied for them -- delivery still comes purely
# from the nearest real "SEND ON SUBMISSION"/"CREDENTIALS..." header,
# exactly as in every other state. They are logged (see wa_timing_notes
# in the summary) for visibility, and any requirement rows that appear
# before WA's very first real region header (row 3's block, rows 5-20 in
# the raw sheet) are flagged as unsure since there is no real facility/
# region context established yet at that point.
#
# ── Skipped outright ─────────────────────────────────────────────────────
# Facility-list bullets (Type='›'), section/region/sub-headers themselves,
# "Last updated" and footnote/contact-email notes, blank rows, and any
# row whose Type is not one of '√' / 'Zip File' / 'Checklist Item'.

import zipfile
import xml.etree.ElementTree as ET
import re
import csv
import json
import sys
from collections import Counter, defaultdict

import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
XLSX_PATH = r'C:\Users\joshd\Project\CRM\Contract_Paperwork_Requirements_CLEAN.xlsx'
OUT_CSV = os.path.join(SCRIPT_DIR, 'compliance_requirements_parsed.csv')
OUT_JSON = os.path.join(SCRIPT_DIR, 'compliance_requirements_parsed.json')
OUT_SUMMARY = os.path.join(SCRIPT_DIR, 'compliance_parse_summary.txt')

NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

SHEET_IDS = {3: 'ACT', 4: 'NSW', 5: 'NT', 6: 'QLD', 7: 'SA', 8: 'TAS', 9: 'VIC', 10: 'WA'}

SECTION_MAP = {
    'SEND ON SUBMISSION': 'zip',
    'CREDENTIALS TO SEND / HOLD ON FILE': 'individual',
}

WA_TIMING_PHRASES = ('QUEUE ON SHIFTMATCH', 'PRIOR TO SUBMISSION', 'PRIOR TO COMMENCEMENT')

BULLET_CHARS = ('•',)  # the leading bullet found on requirement labels
FACILITY_BULLET_TYPE = '›'  # the '>' style marker used for "FACILITIES IN THIS REGION" lists
CHECKMARK = '√'


def strip_bullet(text):
    t = text.strip()
    for b in BULLET_CHARS:
        if t.startswith(b):
            t = t[len(b):].strip()
    return t


ONLY_INLINE_RE = re.compile(r'^(?P<prefix>.+?\bOnly)\s*[-–]\s*(?P<rest>.+)$', re.IGNORECASE)
ONLY_WORD_RE = re.compile(r'\bOnly\b', re.IGNORECASE)


def split_inline_only(label):
    """Returns (role_qualifier, label) if label matches '<prefix> Only - <rest>', else (None, label)."""
    m = ONLY_INLINE_RE.match(label)
    if not m:
        return None, label
    prefix = m.group('prefix').strip()
    rest = m.group('rest').strip()
    if not rest:
        return None, label
    return prefix, rest


def header_role_qualifier(text):
    """If a standalone sub-header line is a role-qualifier line, return the cleaned qualifier text."""
    if not ONLY_WORD_RE.search(text):
        return None
    # trim to end right after "Only" (drop trailing ':' / '-' / whitespace), keep any
    # parenthetical that comes before it (e.g. "Maternity Only (AKA ...)").
    m = re.search(r'^(.*?\bOnly\b(?:\s*\([^)]*\))?)', text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return text.rstrip(':- ').strip()


def load_sheet_rows(z, sheet_id):
    data = z.read(f'xl/worksheets/sheet{sheet_id}.xml')
    root = ET.fromstring(data)
    sheet_data = root.find('s:sheetData', NS)
    rows = []
    for row in sheet_data.findall('s:row', NS):
        r = int(row.get('r'))
        cell_a, style_a = '', None
        cell_b = ''
        for c in row.findall('s:c', NS):
            ref = c.get('r')
            col = ''.join(ch for ch in ref if ch.isalpha())
            is_el = c.find('s:is', NS)
            text = ''
            if is_el is not None:
                t_el = is_el.find('s:t', NS)
                text = (t_el.text if t_el is not None else '') or ''
            if col == 'A':
                cell_a, style_a = text, c.get('s')
            elif col == 'B':
                cell_b = text
        rows.append({'row': r, 'style_a': style_a, 'a': cell_a, 'b': cell_b})
    return rows


def parse_state(state, rows):
    out = []
    unsure = []
    wa_timing_notes = []

    region = None
    facility = None
    facility_list = None
    pending_header_is_region = False  # set True once "FACILITIES IN THIS REGION" seen for the current s=5 header
    current_delivery = None
    role_qualifier = None
    last_was_bullet_qualified_block = False  # true only while consuming bullets right after a qualifier header

    for row in rows:
        r = row['row']
        style = row['style_a']
        a = (row['a'] or '').strip()
        b = (row['b'] or '').strip()

        if r <= 2:
            continue  # title row / column header row

        if style == '5':
            # WA's pseudo-region timing label - not a real region/facility.
            if state == 'WA' and any(p in a.upper() for p in WA_TIMING_PHRASES):
                wa_timing_notes.append((r, a))
                continue
            region = a
            facility = a  # tentative: treated as a facility until proven otherwise
            facility_list = []
            pending_header_is_region = False
            current_delivery = None
            role_qualifier = None
            last_was_bullet_qualified_block = False
            continue

        if style == '6':
            if state == 'WA' and any(p in a.upper() for p in WA_TIMING_PHRASES):
                wa_timing_notes.append((r, a))
            continue  # notes / "Last updated" - skip

        if style == '11':
            continue  # footnote / contact email note - skip

        if style == '7':
            if a in SECTION_MAP:
                current_delivery = SECTION_MAP[a]
                role_qualifier = None
                last_was_bullet_qualified_block = False
                continue
            if a.startswith('FACILITIES IN THIS REGION'):
                # confirms the most recent s=5 header is a region, not a single facility
                facility = None
                pending_header_is_region = True
                continue
            # unrecognised style-7 header - flag it
            unsure.append({'row': r, 'reason': 'unrecognised section header', 'text': a})
            continue

        if style == '12':
            continue  # facility-list bullet ('>' row) under FACILITIES IN THIS REGION - skip

        if style == '10':
            rq = header_role_qualifier(a)
            if rq:
                role_qualifier = rq
                last_was_bullet_qualified_block = True
            else:
                # plain sub-header (Immunisations:, CPDs:, etc) - clears any ambient qualifier scope
                role_qualifier = None
                last_was_bullet_qualified_block = False
            continue

        # By elimination this is a data row: Type value lives in col A, label in col B.
        type_val = a
        label_raw = b
        if type_val == FACILITY_BULLET_TYPE:
            continue  # safety net, shouldn't hit style!=12 with this but just in case
        if not label_raw:
            continue  # blank / stray row

        checklist_item_flag = False
        if type_val == CHECKMARK or type_val == 'Zip File':
            pass
        elif type_val == 'Checklist Item':
            checklist_item_flag = True  # ACT-only anomaly, per brief: treat as requirement, flag it
        else:
            continue  # not a requirement row (Type blank, or something unrecognised)

        label = strip_bullet(label_raw)
        was_bullet = label_raw.strip().startswith(BULLET_CHARS)

        inline_rq, inline_label = split_inline_only(label)
        row_role_qualifier = None
        row_flags = []
        if checklist_item_flag:
            row_flags.append('act_checklist_item_type')

        if inline_rq:
            row_role_qualifier = inline_rq
            label = inline_label
        elif role_qualifier and was_bullet and last_was_bullet_qualified_block:
            row_role_qualifier = role_qualifier
        elif role_qualifier and not was_bullet and last_was_bullet_qualified_block:
            # ambient qualifier was active, but this row isn't a bullet continuation of it -
            # scope is genuinely unclear, don't guess.
            unsure.append({'row': r, 'reason': 'non-bullet row after active qualifier header, scope unclear',
                            'text': label_raw, 'ambient_qualifier': role_qualifier})
            last_was_bullet_qualified_block = False

        if current_delivery is None:
            unsure.append({'row': r, 'reason': 'requirement row with no active section (delivery unknown)',
                            'text': label_raw})
            delivery = None
        else:
            delivery = current_delivery

        if region is None and facility is None:
            unsure.append({'row': r, 'reason': 'requirement row with no region/facility established yet',
                            'text': label_raw})

        out.append({
            'state': state,
            'region': region,
            'facility': facility if not pending_header_is_region else None,
            'ward': None,
            'role_qualifier': row_role_qualifier,
            'item_label': label,
            'delivery': delivery,
            'required': True,
            'source_row': r,
            'raw_type': type_val,
            'flags': ';'.join(row_flags) if row_flags else '',
        })

    return out, unsure, wa_timing_notes


def main():
    z = zipfile.ZipFile(XLSX_PATH)
    all_rows = []
    all_unsure = []
    all_wa_notes = []
    per_state_counts = {}
    per_state_role_q = {}

    for sheet_id, state in SHEET_IDS.items():
        rows = load_sheet_rows(z, sheet_id)
        parsed, unsure, wa_notes = parse_state(state, rows)
        all_rows.extend(parsed)
        for u in unsure:
            u['state'] = state
        all_unsure.extend(unsure)
        all_wa_notes.extend([(state, r, t) for r, t in wa_notes])
        per_state_counts[state] = len(parsed)
        per_state_role_q[state] = sum(1 for p in parsed if p['role_qualifier'])

    fieldnames = ['state', 'region', 'facility', 'ward', 'role_qualifier', 'item_label',
                  'delivery', 'required', 'source_row', 'raw_type', 'flags']
    with open(OUT_CSV, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in all_rows:
            w.writerow(row)

    with open(OUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(all_rows, f, indent=2, ensure_ascii=False)

    total = len(all_rows)
    total_rq = sum(per_state_role_q.values())
    checklist_flagged = sum(1 for r in all_rows if 'act_checklist_item_type' in r['flags'])
    no_delivery = sum(1 for r in all_rows if r['delivery'] is None)

    with open(OUT_SUMMARY, 'w', encoding='utf-8') as f:
        f.write('COMPLIANCE TRACK 2 PARSER - STAGE 1 SUMMARY\n')
        f.write('=' * 60 + '\n\n')
        f.write(f'Total requirement rows parsed: {total}\n\n')
        f.write('Per state:\n')
        for state in SHEET_IDS.values():
            f.write(f'  {state:4s}  {per_state_counts[state]:4d} rows   '
                     f'{per_state_role_q[state]:3d} with role_qualifier\n')
        f.write(f'\nTotal with role_qualifier: {total_rq}\n')
        f.write(f'ACT "Checklist Item" type rows flagged: {checklist_flagged}\n')
        f.write(f'Rows with no active section (delivery=None): {no_delivery}\n')
        f.write(f'\nWA timing-label rows encountered (not mapped to delivery, see script header comment):\n')
        for state, r, t in all_wa_notes:
            f.write(f'  row {r}: {t!r}\n')
        f.write(f'\nUnsure / needs-review cases: {len(all_unsure)}\n')
        f.write('-' * 60 + '\n')
        reason_counts = Counter(u['reason'] for u in all_unsure)
        for reason, cnt in reason_counts.most_common():
            f.write(f'  [{cnt:3d}] {reason}\n')
        f.write('\nFull unsure list:\n')
        for u in all_unsure:
            extra = f" ambient_qualifier={u['ambient_qualifier']!r}" if 'ambient_qualifier' in u else ''
            f.write(f"  {u['state']} row {u['row']}: {u['reason']} -- {u['text']!r}{extra}\n")

    print(f'Wrote {total} rows to {OUT_CSV} / {OUT_JSON}')
    print(f'Summary written to {OUT_SUMMARY}')


if __name__ == '__main__':
    main()
