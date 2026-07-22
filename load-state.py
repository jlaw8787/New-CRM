#!/usr/bin/env python3
"""
load-state.py -- one command to load a state's compliance data end to end.

Replaces the per-state hand-run dance. For each state it:
  - reads compliance-track2-parsed.csv,
  - runs an override-vs-cascade overlap check and PRINTS it (so a state that
    re-lists its region requirements at each facility is caught before it
    duplicates, the way NT would have),
  - builds the facility prep (imports + retags) and the compliance load,
  - then either writes ONE combined .sql file (default) or applies it straight
    to Supabase in a single transaction (--apply).

Usage:
  python load-state.py NT                 # writes nt-load-all.sql (review + run)
  python load-state.py NT --apply         # applies to Supabase (asks before the DELETE)
  python load-state.py NT --check         # only prints the overlap report, builds nothing

--apply needs DATABASE_URL set to your Supabase Postgres connection string
(Project settings -> Database -> Connection string -> URI). Uses psycopg2.
Default mode needs no credentials and touches nothing.

Adding a new state = add a block to STATE_CONFIGS. The overlap report tells you
whether that state is 'override' (facility lists supersede region) or 'cascade'
(region + facility are additive). Set model accordingly.
"""

import csv, os, re, sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IN_CSV = os.path.join(SCRIPT_DIR, 'compliance-track2-parsed.csv')

ACRONYMS = {'HHS','IEMR','RACF','LHD','LHN','QLD','NSW','SA','WA','VIC','ACT','TAS','NT'}
CONNECTORS = {'and','of','the','in','on','for','to','at'}

# ---------------------------------------------------------------------------
# Per-state config. NT is fully worked out. SA / WA are stubs -- fill region_map
# / facility_map / imports / retags after reading that state's overlap report.
# ---------------------------------------------------------------------------
STATE_CONFIGS = {
    'NT': {
        'model': 'override',  # facility lists supersede region; do NOT cascade
        # source region text (upper) -> health_service scope_name
        'region_map': {
            'CENTRAL AUSTRALIA REGION': 'Central Australia Region',
            'TOP END REGION': 'Top End Region',
            'BARKLEY REGION': 'Barkly Region',   # source misspells "Barkly"
        },
        # source facility text (upper) -> facility scope_name (== live name)
        'facility_map': {
            'ALICE SPRINGS HOSPITAL': 'Alice Springs Hospital',
            'ALICE SPRINGS CORRECTIONAL': 'Alice Springs Correctional',
            'MIWATJ': 'Miwatj',
        },
        # facilities to create (health_authority chosen to NOT equal any region
        # scope_name above, so they carry only their own list, no inheritance)
        'import_facilities': [
            {'name': 'Alice Springs Correctional', 'region': 'Central Australia',
             'type': 'Public', 'health_authority': 'Central Australia Health Service'},
            {'name': 'Miwatj', 'region': 'East Arnhem',
             'type': 'Public', 'health_authority': 'Miwatj Health Aboriginal Corporation'},
        ],
        # existing facilities to retag so region rows resolve onto them
        'retag': [
            {'name': 'Gove District Hospital', 'health_authority': 'Top End Region'},
            {'name': 'Katherine District Hospital', 'health_authority': 'Top End Region'},
            {'name': 'Tennant Creek Hospital', 'health_authority': 'Barkly Region'},
        ],
    },
    'SA': {
        'model': 'override',  # facility lists supersede region; heavy cross-overlap
        # 4 clean LHN region lists (1 row per item in the source)
        'region_map': {
            'FLINDERS AND UPPER NORTH LHN': 'Flinders And Upper North LHN',
            'EYRE AND FAR NORTH LHN': 'Eyre And Far North LHN',
            'BAROSSA HILLS LHN': 'Barossa Hills LHN',
            'LIMESTONE COAST LHN': 'Limestone Coast LHN',
        },
        # named sites resolve by title_case of the source facility text, which
        # already equals the imported facility name, so no explicit map needed
        'facility_map': {},
        # HELD: broken or redundant in the parse, load separately after xlsx cleanup.
        #   Balaklava, Riverton -> 95 rows for 31 real items (tripled)
        #   Meningie            -> 45 rows for 24 items (doubled)
        #   ALL SITES           -> miscategorised as facility, 89-94% duplicated everywhere
        'hold': {'BALAKLAVA, RIVERTON', 'MENINGIE', 'ALL SITES'},
        # 9 clean named sites. health_authority is 'SA Health' on purpose: it does
        # NOT equal any LHN scope_name, so each site carries only its own list and
        # never inherits an LHN (which would duplicate ~90% of items). 'SA Health'
        # is a display placeholder, refine per-site later if wanted.
        'import_facilities': [
            {'name': 'Tanunda', 'region': 'Barossa', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Loxton', 'region': 'Riverland', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Mannum', 'region': 'Murraylands', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Riverland General', 'region': 'Riverland', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Kangaroo Island Health Service', 'region': 'Kangaroo Island', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Berri', 'region': 'Riverland', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Lameroo, Pinnaroo', 'region': 'Murray Mallee', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Riverland Residential', 'region': 'Riverland', 'type': 'Public', 'health_authority': 'SA Health'},
            {'name': 'Nganampa Health Council', 'region': 'APY Lands', 'type': 'Public', 'health_authority': 'SA Health'},
        ],
        # both live SA facilities sit under Flinders and Upper North (per user).
        # This overwrites Whyalla's current wrong tag ("Eyre Far North LHN").
        'retag': [
            {'name': 'Port Augusta Hospital', 'health_authority': 'Flinders And Upper North LHN'},
            {'name': 'Whyalla Hospital', 'health_authority': 'Flinders And Upper North LHN'},
        ],
    },
    # 'WA': { ... },
}

COLS = ['state','level','scope_name','facility_id','ward','role_qualifier','item_key',
        'item_label','timing','delivery','required','exception_note','confirmed',
        'source_last_updated','created_by']


def title_case(text):
    out = []
    for i, w in enumerate(text.split(' ')):
        parts = []
        for p in w.split('-'):
            core = p.strip()
            if not core:
                parts.append(p); continue
            up = core.upper()
            if up in ACRONYMS: parts.append(up)
            elif core.lower() in CONNECTORS and i != 0: parts.append(core.lower())
            else: parts.append(core[0].upper() + core[1:].lower())
        out.append('-'.join(parts))
    return ' '.join(out)


def item_key(label):
    return re.sub(r'[^a-z0-9]+', '_', (label or '').lower().strip()).strip('_') or 'item_unknown'


def sql_str(v):
    return 'NULL' if v is None or v == '' else "'" + str(v).replace("'", "''") + "'"


def rows_for(state):
    return [r for r in csv.DictReader(open(IN_CSV, encoding='utf-8-sig')) if r['state'] == state]


def scope_of(r):
    f = (r.get('facility') or '').strip()
    return f if f else (r.get('region') or '').strip()


def overlap_report(state):
    """Print how much each facility list repeats its region list. High overlap
    => override model (don't cascade). Low overlap => cascade is safe."""
    rows = rows_for(state)
    scopes = {}
    for r in rows:
        scopes.setdefault(scope_of(r), set()).add((r.get('item_label') or '').strip().lower())
    print(f'\n{state} overlap report ({len(rows)} source rows, {len(scopes)} scopes)')
    print('-' * 64)
    for name, labels in sorted(scopes.items(), key=lambda x: -len(x[1])):
        print(f'  {len(labels):>4} items  {name}')
    print('  (if a facility scope shares most of its items with a region scope,')
    print('   this state is OVERRIDE -- set model=override so they do not stack)')


def build_compliance_rows(state, cfg):
    hold = {h.upper() for h in cfg.get('hold', set())}
    out = []
    for r in rows_for(state):
        fac = (r.get('facility') or '').strip()
        reg = (r.get('region') or '').strip()
        # Skip scopes deliberately held back (broken/duplicated/redundant in the
        # source, to be cleaned and loaded separately). Match on the raw source
        # scope text (facility if present, else region).
        if (fac or reg).upper() in hold:
            continue
        if fac:
            level = 'facility'
            scope = cfg['facility_map'].get(fac.upper(), title_case(fac))
        else:
            level = 'health_service'
            scope = cfg['region_map'].get(reg.upper(), title_case(reg))
        delivery = r['delivery']
        timing = 'on_submission' if delivery == 'zip' else 'before_commencing' if delivery == 'individual' else None
        required = str(r.get('required', 'True')).strip().lower() != 'false'
        ward = (r.get('ward') or '').strip() or None
        role_q = (r.get('role_qualifier') or '').strip() or None
        out.append([state, level, scope, None, ward, role_q, item_key(r['item_label']),
                    r['item_label'], timing, delivery, required, None, False, None,
                    'Compliance Track 2 Parser'])
    return out


def build_sql(state, cfg):
    lines = []
    lines.append(f'-- {state} compliance load, generated by load-state.py. Review before running.')
    lines.append(f'-- Model: {cfg["model"]}. Runs facility prep then the compliance reload, one file.\n')

    if cfg.get('import_facilities'):
        lines.append('-- 1. Import missing facilities (id is identity, never set explicitly)')
        vals = []
        for fx in cfg['import_facilities']:
            vals.append("  ({}, {}, {}, {}, {}, 'Compliance Track 2')".format(
                sql_str(fx['name']), sql_str(state), sql_str(fx.get('region')),
                sql_str(fx.get('type', 'Public')), sql_str(fx['health_authority'])))
        lines.append('INSERT INTO facilities (name, state, region, type, health_authority, created_by)\nVALUES')
        lines.append(',\n'.join(vals) + ';\n')

    if cfg.get('retag'):
        lines.append('-- 2. Retag region-default facilities so region rows resolve onto them')
        for rt in cfg['retag']:
            lines.append("UPDATE facilities SET health_authority = {} WHERE state = {} AND name = {};".format(
                sql_str(rt['health_authority']), sql_str(state), sql_str(rt['name'])))
        lines.append('')

    crows = build_compliance_rows(state, cfg)
    lines.append(f'-- 3. Reload compliance ({len(crows)} rows). DELETE is {state}-only.')
    lines.append(f"DELETE FROM compliance_requirements WHERE state='{state}';\n")
    lines.append('INSERT INTO compliance_requirements\n  (' + ', '.join(COLS) + ')\nVALUES')
    vrows = []
    for row in crows:
        cells = [sql_str(v) if not isinstance(v, bool) else ('true' if v else 'false') for v in row]
        vrows.append('  (' + ', '.join(cells) + ')')
    lines.append(',\n'.join(vrows) + ';\n')

    lines.append('-- 4. Verify')
    lines.append(f"SELECT level, scope_name, count(*) FROM compliance_requirements WHERE state='{state}' GROUP BY 1,2 ORDER BY 1,2;")
    return '\n'.join(lines), crows


def apply_sql(sql_text):
    try:
        import psycopg2
    except ImportError:
        sys.exit('psycopg2 not installed. Run: pip install psycopg2-binary --break-system-packages')
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        sys.exit('DATABASE_URL not set. Supabase -> Project settings -> Database -> Connection string (URI).')
    print('\nThis will run a DELETE and reload against your live database.')
    if input('Type the state code to confirm and apply: ').strip().upper() != STATE:
        sys.exit('Not confirmed. Nothing applied.')
    conn = psycopg2.connect(dsn)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sql_text)
        print('Applied and committed.')
    finally:
        conn.close()


if __name__ == '__main__':
    args = [a for a in sys.argv[1:]]
    if not args:
        sys.exit('Usage: python load-state.py <STATE> [--apply|--check]')
    STATE = args[0].upper()
    mode = '--apply' if '--apply' in args else '--check' if '--check' in args else '--emit'

    if STATE not in STATE_CONFIGS:
        overlap_report(STATE)
        sys.exit(f'\nNo config for {STATE} yet. Read the report above, then add a STATE_CONFIGS block.')

    overlap_report(STATE)
    if mode == '--check':
        sys.exit(0)

    sql_text, crows = build_sql(STATE, STATE_CONFIGS[STATE])
    by = Counter((r[1], r[2]) for r in crows)
    print(f'\n{STATE}: {len(crows)} compliance rows')
    for (lvl, name), n in sorted(by.items()):
        print(f'  {n:>4}  {lvl:<15} {name}')

    if mode == '--apply':
        apply_sql(sql_text)
    else:
        out = os.path.join(SCRIPT_DIR, f'{STATE.lower()}-load-all.sql')
        open(out, 'w', encoding='utf-8').write(sql_text)
        print(f'\nWrote {out}. Review, then run it in Supabase, or rerun with --apply.')
