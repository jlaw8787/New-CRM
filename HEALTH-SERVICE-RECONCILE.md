# Health service reconciliation, decision list

Read only. No code changed, no SQL run that writes. Every number below comes
from read only queries against the live Supabase project on 28 July 2026, plus
a read of resolveFacilityRequirements in index.html. Read alongside
FACILITY-DATA-CHECK.md, which this confirms and extends.

Counts confirmed against live data: 49 facilities, 858 compliance rows,
438 at health service level, 393 at facility level, 27 at state level.

---

## Read this first, it changes what the decision is

Three things turned up that are more important than the name matching itself.

### 1. Only NT and QLD actually use the health service tier

Compliance rows by state and level:

| State | State level | Health service | Facility | Total |
|---|---|---|---|---|
| QLD | 0 | 204 | 0 | 204 |
| NT | 0 | 134 | 95 | 229 |
| SA | 0 | 100 | 192 | 292 |
| TAS | 27 | 0 | 106 | 133 |
| WA | 0 | 0 | 0 | 0 |

TAS has no health service tier at all. So the five "Tas Health" values on the
facilities table have nothing to map to, and nothing to gain. That removes 14 of
the 49 facilities from this decision entirely.

WA has no compliance rows of any kind. See point 3.

### 2. Mapping a name will show the same requirement twice

The facility level rows are largely copies of the health service list. Of NT's
95 facility level rows, 77 carry an item label that also exists at health
service level in the same state. In SA it is 165 of 192.

Worked example. Alice Springs Hospital holds 42 facility level rules today.
Central Australia Region holds 45 at health service level. 39 of them are the
same item label. Mapping CAHS to Central Australia Region adds 45 rules of which
only 6 are genuinely new, and the facility page then renders 39 requirements
twice, once under "This facility" and once under the health service heading,
because resolveFacilityRequirements returns them as separate groups and the page
prints every group.

So a name mapping is not a safe additive change. Each one needs the duplicated
facility level rows removed in the same pass, or the screen gets worse rather
than better.

### 3. WA is the real hole, and no name mapping fixes it

All 6 WA facilities resolve zero compliance requirements. Not because the names
disagree, but because there are no WA compliance rows in the database at any
level. The four WACHS values are correct names pointing at data that was never
loaded. WA is a data loading job, not a reconciliation job.

Only 6 of 49 facilities currently resolve nothing, and all 6 are the WA ones.

### 4. Nothing matches on facility_id

All 393 facility level rows resolve by name or alias. Zero resolve by
facility_id. Renaming any of those 29 facilities silently drops its rules. Not
part of this decision, but it is the same class of fragility and it is worth
fixing in the same pass.

---

## The decision list

Sorted by facilities affected, most first. "Rules today" is what that facility
resolves right now across all levels.

---

### 1. SA Health, 9 facilities

**Matches a compliance name exactly:** No.

**Facilities:** Tanunda (Barossa), Loxton (Riverland), Mannum (Murraylands),
Riverland General (Riverland), Kangaroo Island Health Service (Kangaroo
Island), Berri (Riverland), Lameroo and Pinnaroo (Murray Mallee), Riverland
Residential (Riverland), Nganampa Health Council (APY Lands).

**Best guess:** There is no single answer. "SA Health" is the whole state, not a
health service, so it cannot map to one record. The 9 have to be split by
region, and only some have a home:

- **Tanunda and Kangaroo Island Health Service** map to **Barossa Hills LHN**,
  22 rules. Barossa is plainly in it, and the real body is Barossa Hills Fleurieu
  LHN, which covers Kangaroo Island. The compliance name looks like a shortened
  version of the same body.
- **Loxton, Berri, Riverland General, Riverland Residential, Mannum, Lameroo and
  Pinnaroo**, 7 facilities, belong to Riverland Mallee Coorong LHN in real SA
  Health. **That name does not exist in the compliance table.** No good guess.
  Nothing to map to.
- **Nganampa Health Council** is an Aboriginal community controlled organisation
  in the APY Lands, not part of any LHN. Geographically it sits inside Eyre and
  Far North, but that would be wrong as an ownership claim. **No good guess.**

**Rules that would attach:** Tanunda 22, of which 3 are new. Kangaroo Island 22,
of which 4 are new. The other 7 gain nothing, because the record does not exist.

**Worth knowing:** all 9 already resolve 20 to 22 rules each through facility
level rows. They are not empty today. This mapping is mostly cosmetic.

---

### 2. Tas Health North, 5 facilities

**Matches a compliance name exactly:** No.

**Facilities:** Beaconsfield and George Town District Hospitals, Campbell Town
Health Service, CHaPS Launceston, Launceston General Hospital, Northern Cancer
Care.

**Best guess:** None available. TAS has zero health service level compliance
rows. The name is a real and sensible regional grouping, it simply has no
counterpart in the compliance data.

**Rules that would attach:** 0. There is nothing to attach.

**Worth knowing:** these 5 already resolve 27 to 41 rules each, through the TAS
state pack plus their own facility rows. Leaving this value exactly as it is
costs nothing today.

---

### 3. Tas Health NW, 5 facilities

**Matches a compliance name exactly:** No.

**Facilities:** Mersey Community Hospital, King Island Hospital, Mersey Leven
Community Nursing, North West Regional Hospital, Smithton District Hospital.

**Best guess:** None available, same reason as Tas Health North. Note this is
North West, a different region from Tas Health North, not a duplicate of it.

**Rules that would attach:** 0.

---

### 4. Flinders And Upper North LHN, 2 facilities

**Matches a compliance name exactly:** **Yes.** 32 rules.

**Facilities:** Port Augusta Hospital (Far North SA), Whyalla Hospital (Eyre
Peninsula).

**Nothing to decide.** Both already resolve 32 rules through it. Worth noting
Whyalla sits in the Eyre Peninsula region but belongs to Flinders and Upper
North, which is correct in the real world, so do not "fix" it to Eyre And Far
North on the strength of the region string.

---

### 5. Tas Health West Coast, 2 facilities

**Matches a compliance name exactly:** No.

**Facilities:** Rosebery Community Health Centre, West Coast District Hospital.

**Best guess:** None available. No TAS health service tier.

**Rules that would attach:** 0.

---

### 6. Top End Region, 2 facilities

**Matches a compliance name exactly:** **Yes.** 45 rules.

**Facilities:** Gove District Hospital (East Arnhem), Katherine District
Hospital (Big Rivers).

**Nothing to decide.** Both resolve 45 rules and hold no facility level rows of
their own, so there is no duplication here either. This is the tier working as
intended.

---

### 7. Torres and Cape HHS, 2 facilities

**Matches a compliance name exactly:** **Yes.** 16 rules.

**Facilities:** Thursday Island Hospital, Weipa Hospital.

**Nothing to decide.**

---

### 8. CAHS, 1 facility

**Matches a compliance name exactly:** No.

**Facility:** Alice Springs Hospital (Central Australia). Rules today: 42, all
facility level.

**Best guess:** **Central Australia Region**, 45 rules. High confidence. CAHS is
the standard abbreviation for Central Australia Health Service, the facility is
in the Central Australia region, and the item labels line up almost exactly.

**Rules that would attach:** 45, but 39 of them duplicate a facility level rule
this facility already has. Net new: 6. Do not make this mapping without deleting
the 39 duplicated facility rows in the same pass.

**Flag:** same body as entry 9. See the duplicate section below.

---

### 9. Central Australia Health Service, 1 facility

**Matches a compliance name exactly:** No.

**Facility:** Alice Springs Correctional (Central Australia). Rules today: 32,
all facility level.

**Best guess:** **Central Australia Region**, 45 rules. Same reasoning as entry
8. This is the unabbreviated form of the same name.

**Rules that would attach:** 45, of which 31 duplicate what it already has. Net
new: 14.

**Flag:** same body as entry 8, under two different strings.

---

### 10. Miwatj Health Aboriginal Corporation, 1 facility

**Matches a compliance name exactly:** No.

**Facility:** Miwatj (East Arnhem, NT). Rules today: 21, all facility level.

**Best guess:** Weak. Two readings and they point different ways:

- Miwatj is an independent Aboriginal community controlled health organisation.
  It is not part of a government health service, so arguably it should stay as
  its own parent and never map to Top End Region.
- Geographically it operates in East Arnhem, inside the Top End. Mapping it to
  **Top End Region** would attach 45 rules, 41 of them genuinely new, since only
  4 item labels overlap with what it holds now. That is the largest real gain of
  any mapping on this list.

The 41 new rules are the argument for it, and the fact that Miwatj is not a
government service is the argument against. **This one is a judgement call about
whether Top End Region means the geography or the government body.** I would ask
whoever knows the NT desk before deciding.

**Flag:** the health_authority string and the facility name are the same
organisation. The parent is also the facility. That is a structural oddity worth
resolving when the hierarchy is built.

---

### 11 to 14. WACHS Goldfields, WACHS Kimberley, WACHS Midwest, WACHS Pilbara

1 facility each. Kalgoorlie Health Campus, Broome Health Campus, Geraldton
Hospital, Hedland Health Campus.

**Match a compliance name exactly:** No, none of them.

**Best guess:** None possible. There are zero WA compliance rows in the
database. These four names look correct for WA Country Health Service regions.
The problem is missing data, not a naming disagreement.

**Rules that would attach:** 0, whatever they are renamed to.

**Action:** leave all four exactly as they are. They become correct the moment
WA compliance data is loaded. Renaming them now would make things worse.

---

### 15. Barkly Region, 1 facility

**Matches a compliance name exactly:** **Yes.** 44 rules. Tennant Creek
Hospital. Nothing to decide.

### 16. Central QLD HHS, 1 facility

**Matches a compliance name exactly:** **Yes.** 42 rules. Emerald Hospital.
Nothing to decide.

### 17. Central West HHS, 1 facility

**Matches a compliance name exactly:** **Yes.** 12 rules. Longreach Hospital.
Nothing to decide.

### 18. North West HHS, 1 facility

**Matches a compliance name exactly:** **Yes.** 20 rules. Mount Isa Base
Hospital. Nothing to decide.

### 19. South West HHS, 1 facility

**Matches a compliance name exactly:** **Yes.** 15 rules. Charleville Hospital.
Nothing to decide.

### 20. Tas Health South, 1 facility

**Matches a compliance name exactly:** No. Royal Hobart Hospital. No TAS health
service tier exists, so nothing to map to. Resolves 44 rules today through the
state pack and its own facility rows.

### 21. Tas Health Statewide, 1 facility

**Matches a compliance name exactly:** No. SMHS Statewide Mental Health Service.
Nothing to map to. This one is not really a region at all, it is a statewide
service, so it may be better modelled as a facility with no health service
above it than as a health service in its own right.

---

## Compliance health service names no facility points at

13 of the 21. Together these hold 207 rules that nothing currently resolves.

| Compliance name | State | Rules | Any facility that could use it |
|---|---|---|---|
| Central Australia Region | NT | 45 | Yes, entries 8 and 9, Alice Springs Hospital and Alice Springs Correctional |
| Eyre And Far North LHN | SA | 27 | No. Whyalla sits in the Eyre region but correctly belongs to Flinders and Upper North |
| Barossa Hills LHN | SA | 22 | Yes, Tanunda and Kangaroo Island Health Service |
| Mackay HHS | QLD | 20 | No facility in the table |
| Limestone Coast LHN | SA | 19 | No facility in the table |
| Townsville HHS | QLD | 16 | No facility in the table |
| Darling Downs HHS | QLD | 14 | No facility in the table |
| Mater Private Hospitals | QLD | 11 | No facility in the table |
| Cairns HHS | QLD | 9 | No facility in the table |
| Metro North IEMR | QLD | 8 | No facility in the table |
| Wide Bay HHS | QLD | 8 | No facility in the table |
| Gold Coast HHS | QLD | 7 | No facility in the table |
| Friendly Society Hospital | QLD | 6 | No facility in the table |

Only 3 of the 13 have any facility that could point at them. The other 10 are
health services the compliance load knows about but which have no facility on
the books at all, mostly QLD metro and coastal services where the agency has no
facility record yet. They are not errors, they are compliance data waiting for
facilities that do not exist yet. Nothing to do about them here.

---

## Same body under two names

**Confirmed: CAHS and Central Australia Health Service.** Entries 8 and 9. Two
facilities, both in the Central Australia region of NT, carrying the abbreviated
and unabbreviated form of the same organisation. Neither matches the compliance
table, which calls it Central Australia Region, a third name for the same thing.
So this body appears under three strings across two tables.

**Not duplicates, despite looking like it:**

- Tas Health North and Tas Health NW are different regions, North and North
  West. Both are real and distinct.
- Whyalla's region says Eyre Peninsula while its health authority says Flinders
  And Upper North LHN. Both are correct, an LHN boundary does not follow the
  geographic region name. Do not reconcile these two.

**Structural oddity rather than a duplicate:**

- Miwatj Health Aboriginal Corporation is both a health_authority value and a
  facility name, the same organisation at two levels.
- Tas Health Statewide is a service, not a region.
- SA Health is an entire state used where a health service belongs. It covers 9
  facilities across at least 4 different real LHNs.

---

## What I would do, in order

1. **Leave WA alone.** Four names, zero data behind them. Load WA compliance
   data instead. This is the only group where facilities currently resolve
   nothing at all.
2. **Leave TAS alone.** Five names, no health service tier in the data, and all
   14 facilities already resolve rules through the state pack. Decide separately
   whether TAS should gain a health service tier at all.
3. **Fix CAHS and Central Australia Health Service together**, both to Central
   Australia Region, and delete the duplicated facility level rows in the same
   pass. This is the one clear correctness win. 2 facilities, 1 body, 3 names.
4. **Decide Miwatj on advice**, not from the data. It is the biggest single gain
   available, 41 new rules, and also the one most likely to be wrong.
5. **Split SA Health only as far as the data allows.** Tanunda and Kangaroo
   Island to Barossa Hills LHN. The Riverland and Murraylands 7 have no record to
   point at, so either add Riverland Mallee Coorong LHN to the compliance table
   first or leave them.
6. **Then, separately, fix the matching itself.** 393 facility level rows match
   on a name string with no id behind them. Whatever is decided above, the
   resolver stays fragile until that changes.

---

## What I could not check

- Whether the compliance names are what the agency actually calls these bodies,
  or an artefact of how the state load scripts were written. Every mapping guess
  above is from the names, the regions and the item labels, not from anyone who
  works the desk.
- Whether the duplicated facility level rows were deliberate, for example a
  facility genuinely restating a health service requirement with a different
  expiry rule. I compared item labels only. Two rows with the same label could
  still differ in timing or currency window.
- Anything about how these screens look. This is a read of the data and the
  source, not a browser session.
