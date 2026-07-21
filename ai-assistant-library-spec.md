# AI ASSISTANT — EXPANDED SCRIPTED LIBRARY SPEC

For Claude Code to implement. These are canned/scripted responses (no real model). Each scenario = trigger keywords + a response template that pulls LIVE app data where noted in {braces}. Keep the existing typing-delay, Copy/Refine, and try/catch fallback wrapper. Add these on top of the existing ai* scenarios.

Tone: helpful, plain-spoken, a bit of dry wit where marked [zinger]. Never corporate. No em dashes. Match the existing register.

---

## CANDIDATE SCENARIOS

**Summarise candidate** (existing — keep, ensure it now reads primary_skill + states_open + available_to)
Triggers: "summarise", "tell me about", "who is", "brief me on" + open candidate
Response: "{name} is a {classification} based in {region}, currently {phase}. Primary area {primary_skill}, also does {flex skills}. Open to {states_open}. Available {availability, open-ended aware}. Compliance sits at {cmpScore}% — {missing items list, or 'all clear'}. {If submitted: 'Currently out to {facility}.' else 'Not currently submitted.'}"

**Draft follow-up** (existing — keep)

**Draft submission email** (existing — keep)

**Is this candidate ready / compliant**
Triggers: "ready", "compliant", "can I submit", "good to go" + open candidate
Response: "{name} is at {cmpScore}% compliance. {If 100%: 'All clear — ready to submit.'} {If gaps: 'Still outstanding: {missing items}. Sort those before submitting.'} {If expiring soon: 'Heads up — {item} expires {date}, worth renewing before a placement locks in.'}"

**What's this candidate's story / history**
Triggers: "history", "story", "background", "what have they done"
Response: pulls placements count, last contract facility, most recent activity. "{name} has done {n} placements, most recently {facility} ({ward}). Last activity: {activity}. {note if hot-listed}"

**Find me a nurse for X** [demo showpiece]
Triggers: "find me a", "who can do", "need a nurse for", "anyone for" + specialty/state
Response: reads candidates, filters by clinical area + availability + states. "I can see {n} matches for {criteria}. Top of the list: {top 3 names with compliance % and availability}. Want me to open the grid filtered to these?"

---

## COMPLIANCE / FACILITY SCENARIOS (showcases Track 2)

**What does {facility} require**
Triggers: "what does", "requirements for", "what's needed for" + facility name (match by name or alias)
Response: resolves facility requirements. "{facility} ({health_authority}) requires {n} items: {list first several, grouped on-submission vs before-commencing}. {If not loaded: 'No compliance pack loaded for {state} yet.'}"

**Is {candidate} compliant for {facility}**
Triggers: "compliant for", "ready for", "can X go to Y"
Response: cross-checks candidate compliance against facility requirements. "For {facility}, {candidate} has {x of y} requirements met. {If gaps: 'Missing: {items}.'} {If any expire during a likely contract window: 'And {item} expires {date} — that would fall mid-placement.'}"

**What's expiring**
Triggers: "expiring", "what's due", "renewals", "expiring soon"
Response: reads getAutos compliance alerts. "{n} compliance items expiring in the next 14 days. Most urgent: {item} for {candidate}, {expired/expires date}. {n} of those fall during an active contract — that's the audit risk pile."

**Compliance coverage**
Triggers: "coverage", "which states", "what's loaded", "compliance packs"
Response: "Compliance packs are live for {loaded states}. {remaining states} still to load. {n} facilities resolving requirements right now."

---

## MANAGER / EXEC SCENARIOS

**How's the team doing**
Triggers: "team", "performance", "how are we", "numbers"
Response: "{n} submissions this period, {accepted}% accepted, {placements} placed. Pipeline value sitting around {value}. {top consultant} leading on placements. {If any consultant below rate: 'Worth a look: {name} trending under team average.'}"

**Where are the risks**
Triggers: "risks", "what should I worry about", "problems", "attention"
Response: "Three things I'd watch: {n} contracts expiring with no extension talk ({value} at risk), {n} compliance items expiring during live placements, and {n} candidates overdue for check-in. Want the list on any of those?"

**Pipeline / forecast**
Triggers: "pipeline", "forecast", "value", "revenue"
Response: "{n} active contracts worth {value}, plus {n} in submission. Next 90 days looks like {value}. {n} up for extension — that's the low-hanging renewal money."

---

## SMALL TALK / META / ZINGERS

**Greeting**
Triggers: "hi", "hello", "hey", "morning"
Response: "Morning. {n} things on the board today. Where do you want to start?"

**What can you do**
Triggers: "what can you do", "help", "capabilities"
Response: "I can summarise any candidate, draft your follow-ups and submission emails, tell you who's compliant for a facility, flag what's expiring, and pull the numbers for a review. Open a candidate or name a facility and I'll show you."

**Thanks**
Triggers: "thanks", "cheers", "ta"
Response: "Anytime. [occasional zinger: 'Beats doing it in a spreadsheet.']"

**Zingers (sprinkle as occasional second-line flavour, not every time):**
- On a 100% compliant candidate: "Fully compliant, references and all. Rare as hen's teeth."
- On someone wildly overdue for check-in: "{name} hasn't been contacted in {n} days. At this point they might've changed careers."
- On a big compliance gap: "{cmpScore}% compliant. That's not a submission, that's a project."
- On a strong match list: "Spoilt for choice on this one."
- On asking what it can do: "Mostly I stop you drowning in tabs."
- On an expiring-during-contract item: "That cert expires mid-placement. The kind of thing that's fine until it very much isn't."
- On pipeline value: "That's the number that keeps the lights on."

---

## OUT OF SCOPE / HONEST LIMITS (keep existing behaviour)
- Actions it can't take (book, send, approve, delete): honest preview disclaimer, "I can draft the words, but I can't hit send myself. Yet."
- Unhandled/gibberish: graceful fallback pointing at what it CAN do.
- Never invent data. If a field is missing, say so plainly rather than making it up.

---

## IMPLEMENTATION NOTES FOR CLAUDE CODE
- All {braces} = live reads from existing app state/functions (candidates, facilities, resolveFacilityRequirements, cmpScore, getAutos, vc()). Do NOT hardcode values.
- Reuse the existing keyword-routing + typing-delay + Copy/Refine + try/catch fallback. This is additive.
- Zingers should be OCCASIONAL (e.g. random 1-in-3, or only on strong triggers), not on every response, or they wear thin.
- Keep responses to a few sentences. This is a canned demo assistant, not a chatbot novel.
- Guard every data read: missing field degrades to a sane line, never "undefined" or a throw.
