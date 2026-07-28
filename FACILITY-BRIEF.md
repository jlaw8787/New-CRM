# Facility hierarchy and knowledge brief

Status: brief only. Nothing agreed, nothing built.
Written 28 July 2026.

---

## What this is

Facilities in Captain Contract are currently flat records. This brief covers
turning them into a proper structure, State to Health Service to Facility to
Ward, and holding the operational knowledge that consultants currently keep in
their heads.

This is the largest structural change on the backlog. It gets built in slices,
each one tested live before the next starts. Do not attempt it in one pass.

---

## The problem it solves

Two problems, and the second one is the real one.

**Finding things.** A consultant working a rural placement needs to know what
this facility requires, who to call, and what the nurse is walking into. Today
that information is either not recorded or scattered.

**Knowledge walking out the door.** Consultants change often in this industry.
When one leaves, what they knew about a facility goes with them. Which places
allow partners. Which cap travel. Which ward has a nurse unit manager who
answers the phone and which one does not. None of that is written down anywhere.

---

## The structure

Four levels, each a real object with its own record.

```
State
  Health Service
    Facility
      Ward
```

Rules:

- A Role belongs to a Ward. A Ward belongs to a Facility. A Facility belongs to
  a Health Service. A Health Service belongs to a State.
- Information set at a higher level applies down unless a lower level overrides
  it. This already works for compliance packs, so reuse that cascade rather
  than building a second one.
- Counts roll up. A Health Service shows the total open roles across its
  facilities. A Facility shows the total across its wards.
- Not every facility has meaningful wards. The structure must not force a user
  to create a ward that does not exist.

---

## What gets held at each level

Only fields that change a decision or a conversation. Anything that does not is
noise.

### State
Compliance requirements. Already built as state packs, do not rebuild.

### Health Service
Terms of business. Payment approvals. Rate agreements. Contract dates.
Escalation contacts above facility level.

### Facility

**Getting there and staying there.** Nearest airport and drive time. Whether a
car is required on site. Accommodation type, agency arranged or self sourced.
Whether partners are permitted. Whether pets are permitted. Whether caravans
are permitted. Whether accommodation is nurses quarters, singles only, or open.

**Money.** Travel paid, capped, or not paid. What the cap is. Whether
accommodation is paid separately. Rate range actually paid, by nurse type.

**Clinical reality.** Doctors on site or on call. After hours cover. Patient
ratios. Whether it is a single nurse site.

**Requirements.** Facility specific compliance on top of the state pack.
Induction requirements and how long they take. Lead time needed before a nurse
can start.

**Relationship.** Who to call and what they actually do, not their job title.
Preferred supplier status. Last contact date. Next check in due.

### Ward

Ward level only holds what genuinely differs from the facility. Ratios.
Ward specific credentials, for example ALS on Emergency. Nurse unit manager.
Anything else defaults up to the facility.

---

## Slices, in order

Each slice ships and gets tested before the next begins.

**Slice 1. The structure.**
State, Health Service, Facility, Ward as real linked objects. Drill down
navigation. Rollup counts. No new fields yet. This proves the container works
before anything is poured into it.

**Slice 2. Notes.**
A right side panel that opens on any level. Quick notes typed during a call.
Each note tagged with a reason so notes can be filtered later. Suggested
starting reasons: rate discussion, complaint, extension, staffing request,
general. This is the highest value slice because notes get created naturally
during work that already happens.

**Slice 3. Facility knowledge fields.**
The accommodation, money, clinical and requirements fields above. Every field
optional. Every empty field shows an honest empty state, not a blank.

**Slice 4. Relationship tracking.**
Contacts with real roles. Last contact date. Check in reminders. Extension
follow up prompts tied to contract end dates.

**Slice 5. Nurse feedback.**
Feedback captured after a placement, held against the facility and the ward.
Needs a way to collect it, which is its own decision.

**Not scheduled. Patterns and pre-planning.**
Identifying seasonal demand and repeat vacancy patterns needs at least a year of
real history. The app does not have that yet. Revisit once real data has been
running for a while.

---

## Decisions needed before any of this is built

**1. Who fills it in, and when.**
This is the decision that determines whether the whole thing works. A facility
profile with 25 empty fields is worse than one with 6 filled. Options: a one off
data entry push per facility, filling in as it comes up during work, or fields
that populate as a byproduct of something else. Most likely a mix, but it needs
deciding per field group, not in general.

**2. What happens to existing facility records.**
There are around 120 facility records today with no health service above them
and no wards below them. They need assigning to a health service. Manually, or
by a rule, or left unassigned until touched.

**3. How far ward level goes.**
Every field held at ward level multiplies data entry by the number of wards.
Keep the ward record thin unless there is a reason not to.

**4. Whether the note reasons are fixed or editable.**
Fixed keeps the filtering useful. Editable means the list grows until it is
useless. Recommend fixed, with a review after real use.

---

## Deliberately not in this brief

**Finding returners fast.** Raised alongside this, but it is candidate search,
not a facility feature. Separate job.

**Rebuilding compliance packs.** The cascade already exists and works. This
structure should use it, not replace it.

---

## Risks

**Scope.** This brief contains months of work. The failure mode is starting
three slices and finishing none. One at a time, tested live, before the next.

**Empty screens.** Every new field is a new way for the screen to look broken.
Empty states are part of each slice, not a polish pass afterwards.

**Seed data.** Everything in the app today is invented. Designing screens around
clean fake facilities will not survive real ones, which arrive with missing
contacts, inconsistent names and blank fields. Slice 1 should be tested against
at least some real facility data.

**Migration.** Slice 1 changes how facilities relate to each other. That is a
data change, not a display change. It cannot be undone by reverting code.
Whatever SQL it needs gets written out and read before it is run.

---

## Next step

Agree the four decisions above. Then Slice 1 becomes its own build brief with
the SQL written out separately.
