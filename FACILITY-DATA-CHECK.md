# Facility data check

Read only. No code changed, no SQL run that writes. Counts and values below
come from read-only queries against the live Supabase project on 28 July 2026,
plus a read of index.html. Read alongside FACILITY-BRIEF.md.

---

## Correction to the brief first

FACILITY-BRIEF.md, decision 2, says "There are around 120 facility records
today". That is wrong. **There are 49.**

The number 120 may have come from the contracts table, which has 112 rows.
Worth fixing in the brief before the decisions get made on it, because 49
records is a small enough number to assign to health services by hand, and 120
is closer to the point where you would want a rule instead.

---

## 1. How many facilities, and what fields exist

**49 facility records.**

By state: TAS 20, SA 11, WA 6, QLD 6, NT 6. Nothing in NSW, VIC or ACT.
By type: Public 45, Private 2, NGO 2.

The `facilities` table has 30 columns:

| Column | Filled |
|---|---|
| id, name, state, type, created_at, last_edited_at | 49 of 49 |
| preferred_status, remote_loading_applies, remote_loading_pct, accommodation_provided, car_required | 49 of 49, but these are defaulted booleans and numbers, not entered data |
| region | 45 of 49 |
| health_authority | 41 of 49 |
| aliases | 19 of 49 |
| beds, contact_name, contact_email, contact_phone, notes, accommodation_type, submission_email | 16 of 49 each |
| created_by | 11 of 49 |
| address, address_suburb, address_postcode | 1 of 49 each |
| last_edited_by | 1 of 49 |
| secondary_contact_name, secondary_contact_email, secondary_contact_phone, notes_candidate | 0 of 49 |

Note the 16 of 49 group. Those are all the same 16 facilities. They are the
original hand built seed records. The other 33 came in through the state import
scripts and carry name, state, region, health authority and nothing else.

---

## 2. Is there anything above facility level already

**Yes, in two places, and they do not agree with each other.**

### a. facilities.health_authority, plain text

41 of 49 facilities carry one. 21 distinct values:

```
Barkly Region                          Tas Health North
CAHS                                   Tas Health NW
Central Australia Health Service       Tas Health South
Central QLD HHS                        Tas Health Statewide
Central West HHS                       Tas Health West Coast
Flinders And Upper North LHN           Top End Region
Miwatj Health Aboriginal Corporation   Torres and Cape HHS
North West HHS                         WACHS Goldfields
SA Health                              WACHS Kimberley
South West HHS                         WACHS Midwest
                                       WACHS Pilbara
```

The granularity is inconsistent. "SA Health" is a whole state and covers 9
facilities. "WACHS Kimberley" is a region. "Miwatj Health Aboriginal
Corporation" is a single NGO operator. There is also an apparent duplicate:
"CAHS" and "Central Australia Health Service" are the same body under two names.

### b. compliance_requirements.level, a real cascade that already exists

The compliance table has a `level` column already carrying three tiers:

| level | rows |
|---|---|
| health_service | 438 |
| facility | 393 |
| state | 27 |

So a health service tier is **already live in the compliance data**, matched by
a text `scope_name`. 21 distinct health service names there too.

### c. The two vocabularies overlap by only 8 of 21

This is the most important finding in this document.

Both lists have 21 entries. Only these 8 appear in both:

```
Barkly Region        North West HHS
Central QLD HHS      South West HHS
Central West HHS     Top End Region
Flinders And Upper   Torres and Cape HHS
  North LHN
```

The compliance table knows about health services the facilities table has never
heard of (Cairns HHS, Gold Coast HHS, Darling Downs HHS, Mackay HHS, Townsville
HHS, Wide Bay HHS, Metro North IEMR, Barossa Hills LHN, Eyre And Far North LHN,
Limestone Coast LHN, Central Australia Region, Friendly Society Hospital, Mater
Private Hospitals). The facilities table has 13 the compliance table does not.

So there are two independent, half overlapping text lists describing the same
concept, and no table joins them. Whichever becomes the real Health Service
record, roughly two thirds of one side will need reconciling by hand.

### d. region is a third, separate geography

45 of 49 facilities have a `region` string, 28 distinct values, for example
"North TAS", "Riverland", "Pilbara", "APY Lands", "Cape York". This does not
line up with either list above. In some rows it is a health service by another
name, in others a plain geographic area. It is a third vocabulary.

---

## 3. Do wards exist as their own records

**Yes. There is a real `wards` table with 62 rows**, keyed to a facility, with
columns: id, facility_id, name, nurse_types, created_at, ward_code, emr_system,
min_experience_years, is_active.

But it is thinly populated and barely used:

- Only **17 of 49 facilities** have any ward records at all. The other 32 have none.
- 25 distinct ward names exist in the table.
- Roles, submissions and contracts do **not** point at these records. They each
  hold a plain `ward` text string instead. See section 4.
- Across all roles, submissions and contracts there are only **10 distinct ward
  strings** in use, against 25 ward names in the table. So most ward records are
  never referenced by anything.

The ward table is therefore real but effectively decorative today.

---

## 4. How roles, submissions and contracts link to facility and ward

**To facility: by real foreign key, and it is clean.**

| Table | Rows | facility_id set | Pointing at a missing facility |
|---|---|---|---|
| roles | 24 | 24 of 24 | 0 |
| submissions | 155 | 154 of 155 | 0 |
| contracts | 112 | 112 of 112 | 0 |

One submission has no facility_id. Nothing points at a facility that does not
exist.

**To ward: by text string only. There is no ward_id column on any of the three.**

| Table | ward text set | Text not matching any ward record at that facility |
|---|---|---|
| roles | 24 of 24 | 0 |
| submissions | 154 of 154 | 13 |
| contracts | 112 of 112 | 0 |

So 13 submissions name a ward that does not exist as a record at that facility.
Everything else happens to match by string, but nothing enforces it. Renaming a
ward record today does not update anything pointing at it. index.html has a
`checkWardOrphans` routine that detects this after a facility edit and offers to
rewrite the strings, which is a workaround for exactly this missing link.

Contracts also duplicate the facility name as text in a `facility` column
alongside `facility_id`.

Role to ward is text, so Slice 1's rule "a Role belongs to a Ward" is not
currently true in the data. It would need a new column and a backfill.

---

## 5. How complete are the facility records

Three clear tiers.

**Tier 1, reasonably complete: 16 of 49 (33%).**
The original seed facilities. Name, state, region, type, beds, contact name,
email and phone, notes, accommodation type, submission email.

**Tier 2, name and geography only: 25 of 49 (51%).**
Imported. Name, state, region, health authority. No contact, no beds, no notes.

**Tier 3, missing even the health authority: 8 of 49 (16%).**
No parent of any kind. These have nothing to hang off in a hierarchy.

Specific coverage:

- **Contacts: 16 of 49 (33%).** There is also a separate `facility_contacts`
  table with 32 rows covering 16 facilities. It is the same 16. So two contact
  stores, no extra coverage from the second one. This matches KNOWN-ISSUES #8.
- **Addresses: 1 of 49 (2%).** Effectively no facility has an address.
- **Wards: 17 of 49 (35%).**
- **Beds: 16 of 49 (33%).**
- **Notes: 16 of 49 (33%).**

Put plainly: two thirds of facilities are a name, a state and a region. The
brief's risk note about designing against clean fake facilities is correct, and
the imported two thirds are closer to what real data will look like than the
seed sixteen are.

---

## 6. What would break if facilities gained a parent health service

Nothing would break at the database level. Adding a `health_service_id` column
is additive and no existing query would fail. The problems are all in the
application and the data.

**a. The facility editor cannot set health_authority, and never could.**
`renderFacModalBody` exposes 13 fields: name, state, region, type, beds, the
three contact fields, address, suburb, postcode, notes, wards. `saveFac` writes
those same columns and no others. `health_authority` is read by `mapFacility`
and displayed on the profile, but there is no way to set or correct it in the
app. So today the field driving the compliance cascade can only be changed by
hand in SQL. Any Slice 1 that relies on it needs the editor extended first.

The same is true of `preferred_status`, `remote_loading_applies`,
`remote_loading_pct`, `accommodation_provided`, `accommodation_type`,
`car_required`, `submission_email`, `secondary_contact_*`, `notes_candidate`
and `aliases`. All read, none writable from the UI. Worth knowing before Slice 3
adds more fields to a form that already cannot save the ones it has.

**b. The compliance cascade keys off the text field, not an id.**
`resolveFacilityRequirements` matches health service rows with
`r.scope_name === f.healthAuthority`, an exact string comparison. Facility rows
match on `facility_id`, or on name, or on an alias. Introducing a real health
service record without keeping that string in step would silently drop the 438
health service compliance rows out of the resolver. Silently, because a facility
with no matching rows renders as an empty section rather than an error.

**c. There is a dead branch in that same resolver.**
It also looks for `level === 'ward'` rows and matches them on `f.healthAuthority`,
which is a health service name, not a ward. There are zero rows at ward level so
it never fires today. If Slice 1 introduces ward level requirements, that branch
is already wrong.

**d. Three fields are already treated as interchangeable in the UI.**
The facility profile Wards section header does
`f.healthAuthority || f.region || f.state`, and the contract PDF generator
prints a single line labelled "Health authority / region" using
`fac.healthAuthority || fac.region`. Both assume these are the same kind of
thing. Once health service is a real level distinct from region, both read as
wrong rather than as a sensible fallback.

**e. The Facilities list has no concept of a parent.**
Filters are state and type. Sorts are name, state, wards, active contracts,
submissions, conversion. Columns are Facility, Region, Type, Wards, Active,
Subs, Conversion, Contact. Nothing groups or rolls up. Slice 1's drill down and
rollup counts are new build here, not a modification.

**f. Nothing else assumes a facility is top level.**
Search, the job board, matching and the submission flow all reach facilities
through `facility_id` or by name. None of them walk upwards. Adding a parent
does not disturb them.

---

## Summary for the four decisions in the brief

- **Decision 1, who fills it in.** Two thirds of facilities have nothing but a
  name and a region, and the facility editor currently cannot save most of the
  fields that already exist. That has to be fixed before more fields are added,
  or Slice 3 adds fields nobody can fill in.
- **Decision 2, existing records.** 49 records, not 120. 41 have a health
  authority string, 8 have nothing. Small enough to assign by hand, but the two
  vocabularies must be reconciled first, and only 8 of 21 names currently agree.
- **Decision 3, how far ward goes.** The ward table already exists and is
  already thin, 17 of 49 facilities, and nothing links to it by id. The first
  question is not how many fields to put on a ward, it is whether roles,
  submissions and contracts get a real ward_id at all.
- **Decision 4, note reasons.** Nothing in the data speaks to this.

---

## What I could not check

- Whether the Supabase tables have foreign key constraints, indexes or row level
  security policies. I read data through the REST API, not the schema catalogue,
  so column types, nullability and constraints are inferred from values.
- Whether any facility record is a duplicate of another under a different name,
  beyond the "CAHS" and "Central Australia Health Service" pair noted above.
- Anything about how these screens actually look or behave. This is a read of
  the data and the source, not a browser session.
