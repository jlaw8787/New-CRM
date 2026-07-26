# Captain Contract, backlog

One working list so nothing lives only in a chat. Work top down by priority.
Update status as you go. No em dashes anywhere, same as the rest of the project.

Status key: TODO, IN PROGRESS, BLOCKED, DONE.
Priority key: P1 now, P2 next, P3 later.

## Standing principle
Kill pointless double handling. Navigation is fine when it has point and purpose.
What to remove is the loop with no payoff, open a page, read one value, come back,
and retype it. Where a screen can carry the information or the action itself, it
should. This governs every new build.

---

## CV builder, manual edit function
Status: TODO
Priority: P2
Raised: this session, as a side note off the Messages work.

What it is: let the user override the assembled CV output without corrupting the
source data. The CV builds from confirmed contracts and compliance and nothing is
retyped, so an edit has to sit somewhere that does not rewrite a real record.

Decision to settle before building, this is the whole design:
- Option A, overlay. The edit sits on top of the CV output only. Source contract
  and compliance records stay untouched. Reversible. The CV can show an edited
  value without changing the candidate's real data.
- Option B, write back. Editing the CV changes the underlying record. Cleaner
  data model but risky, a typo on a CV would rewrite a real compliance date.

Recommendation: Option A, overlay. It keeps the one source of truth intact and
matches how cvAhpraLine() already centralises that data. Confirm this before any
code gets written.

Open questions once the approach is picked: which fields are editable, whether an
edited CV is flagged as edited, and where the overlay is stored (per candidate CV
state versus a saved CV version).

Reference: cv-builder-v2.html mockup, renderCvDoc and renderCpCv in index.html.

---

## Messages, remaining stages

### Templates and merge preview
Status: IN PROGRESS
Priority: P1
Built and pushed. Insert into composer was not landing text, fix prompt sent to
Claude Code. Confirm on the live site after the next push, then run the click
through, then mark DONE. Watch the popover clipping inside overflow hidden.

### SMS job promo builder
Status: TODO
Priority: P2
Pick a role, toggle which details to include, assemble an SMS with segment
costing and an auto appended opt out line, send to one candidate or a matched
group. Builds on templates and the segment counter. Mockup: renderPromoPanel and
renderPromo in the workspace file.

### Inbound message alerts
Status: TODO
Priority: P2
getAutos needs a branch so an inbound message raises an alert. First decision is
where inbound messages land so getAutos can see them. Buildable now against
seeded test rows, does not need the provider.

### SMS provider
Status: BLOCKED
Priority: P2, but it unblocks real outreach
Australian provider behind a small abstraction, Cellcast or MessageMedia, inbound
by webhook, which needs a backend since the app is client side. Consent, sender
ID and opt out are legal requirements. Sender ID Register enforcement lands
1 July 2026. This is the thing that turns Messages from a rehearsal into a real
channel.

---

## From the two pass audit

### Alerts firehose, severity and sticky dismiss
Status: TODO
Priority: P1
The Alerts count runs into the hundreds, which is noise not a worklist. Add hard
severity tiers and a dismiss that sticks. Helps the senior desk and stops a new
starter drowning. Pairs with the expiry queue below.

### Cross desk compliance expiry queue
Status: TODO
Priority: P1
A single board showing everyone expiring inside 30 days across the desk, separate
from the Alerts firehose. Reuses cmpScore and the credential model already fixed,
so low risk, high value. Good candidate for the next build brief.

### New starter orientation and glossary
Status: TODO
Priority: P2
A short first run: what the app is, where to start, and a one screen map of the
ten pipeline phases. Plus inline definitions for the domain terms, AHPRA, per
diem, loading, currency window, phase names. Biggest lever on ramp time for a new
consultant.

### Plain language next steps on compliance flags
Status: TODO
Priority: P3
Compliance shows a status chip but not what to fix or how. Add a plain next step
so a beginner is not staring at a red flag with no instruction.

---

## From the market evaluation

### Facilities hierarchy and ward level work
Status: TODO
Priority: P1 structural
Health Service to Facility to Ward to Role, each a first class object with its own
contacts, requirements and rollup counts. Wards become workspaces you can open,
not badges. Aligns the facilities data with the compliance cascade that already
assumes this shape. Highest value structural change, compounds into Job Board,
cascade and matching. Ready to become a Claude Code brief when picked up.

### AI helper knowledge tier plus glossary
Status: TODO
Priority: P2
One knowledge base covering the glossary (phases, per diem, loading, currency
window), AHPRA facts, clinical areas, and live facility and ward info. Surface it
three ways, the assistant, an in app glossary, and hover definitions. Plus a first
run phase map. Build once, use everywhere.

### Natural language candidate matching
Status: TODO
Priority: P3, but this is the market leapfrog
"Who is compliant and available for an ICU role at Logan." The direction the whole
market is moving and where incumbents are weak. Needs the Claude API in app or a
backend. Sits on top of the facilities hierarchy and the compliance engine.

### Automated AHPRA verification and expiry monitoring
Status: TODO
Priority: P3
The Australian version of the automated verification the credentialing leaders
compete on. Register checks and continuous expiry monitoring on top of the
credential model. Needs a backend for scheduled checks.

---

## Housekeeping

### Em dash sweep
Status: TODO
Priority: P3
Find and replace across index.html to clear legacy em dashes, the login dropdown
separator and some contract status toasts among them. Do it as its own pass on a
clean tree so it does not tangle with a feature build.

---

## Candidate profile Messages tab, bring the message centre in

Right now the profile Messages tab is just the thread and composer. The
tools rail (Context, Templates, Job promo, compliance chase, emoji) only
exists in the Messages centre, so you can reply from a profile but not act.

Goal: surface the same tools rail inside the profile Messages tab so you can
do everything without bouncing out to the centre. Context rows, template
insert, job promo into the composer, tick and chase compliance, emoji, all
of it, working against the candidate whose profile you are on.

Reuse the existing rail components (mtCtxHtml, templates, promo, chase), do
not rebuild them. Watch that they key off the profile candidate, not the
hub's selected conversation. Kill the double handling of leaving the profile
to send a promo or chase.
