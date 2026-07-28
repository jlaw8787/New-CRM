# Candidate profile Messages tab, findings

Read only. No code was changed to produce this. All line numbers are index.html
as it stands now.

---

## 1. What the Messages tab shows today

It already exists and already works. It is not empty.

Tab button at line 7877, render branch at 7904 to 7907.

It renders `renderMsgThread(c)` inside a fixed box: centred on the page, max
width 390px, height 660px. That gives you the phone style thread and nothing
else:

- the slide down reply banner (hidden until it fires)
- the contact header, avatar plus name plus classification
- the scrolling message history
- the composer at the bottom, or the red SMS blocked block if the candidate
  has not consented
- a "Dev: simulate inbound reply" button, ops role only

There is no tools rail. It is a single narrow centred column.

---

## 2. Can the chat pane and tools rail run without the conversations list

**Chat pane: yes, cleanly.** `renderMsgThread(c)` takes a candidate and knows
nothing about the hub. The profile page already calls it standalone today.

**Tools rail: half yes.** The three panel builders are already clean, they each
take the candidate as an argument and never look at the hub:

- `mtCtxHtml(c)` at 6299
- `mtTplHtml(c)` at 6337
- `mtPromoHtml(c)` at 6477

`mtShellHtml()` at 6128 takes no argument at all, it just writes the three tab
buttons and three empty containers.

The problem is six helper functions that reach for the hub's selected candidate
directly instead of being told which candidate to use:

| Function | Line | What it drives |
|---|---|---|
| `mtRenderAll` | 6146 | fills all three rail panels |
| `mtCtxToggle` | 6160 | expand or collapse a Context row |
| `mtChaseToggleSel` | 6226 | tick a compliance item to chase |
| `mtPromoSyncComposer` | 6383 | push the promo draft into the composer |
| `msgPromoSearch` | 6553 | the role search box |
| `mtRenderPromo` | 6559 | redraw the Job promo panel |

Each of these does `candidates.find(x => x.id === msgHubSelectedId)`.

On the candidate profile `msgHubSelectedId` is either null, or whoever happens
to be selected over in the Messages centre. So the rail would draw once and then
every click inside it would either do nothing or act on the wrong person.

One helper already solves this properly and can be copied. `tplCurrentCand()` at
6621 reads `msgHubSelectedId` when you are on the Messages page and `curCandId`
otherwise. That is why template insert already works from the profile today.

---

## 3. What the composer needs to work in a second place

The composer is found entirely by fixed element ids: `msgBox`, `msgSendBtn`,
`msgCnts`, `msgEmojiBtn`, `msgEmojiWrap`, `msgEmojiPanel`, plus `msgScroll` and
`msgBanner` on the thread around it. Every function that touches it does
`getElementById` and takes the first match on the page.

That is fine for a two pane layout, because there is still only one composer.
It lives inside the thread pane and the rail has no composer of its own. It only
breaks if two threads are ever drawn at the same time.

Things that assume one composer at a time, all fine with one, all broken with two:

- `msgBoxIsDraft` and `msgBoxText` (5651, 5654) are single shared variables
- `msgEmojiOpen` (5850) plus its document wide click and Escape listeners are
  single and global

Two behaviours worth knowing about, both of which already happen in the Messages
centre today and are not new problems:

- `msgRefreshUI()` at 5640 redraws the entire page. On the profile that means a
  full `renderCandPage()`, rebuilding the hero, the tab bar and the rail, every
  time a message sends, a note saves, an inbound arrives, or a message flips to
  delivered about a second after sending. Any rail state has to survive a full
  redraw, the way `mtCtxOpen` and `mtChaseSel` already do.
- The composer textarea is written out empty on every redraw, and nothing puts
  `msgBoxText` back into it. So a half typed unsent message is lost whenever
  anything triggers a refresh. `msgComposerHtml` also resets the draft flag and
  the emoji picker each time (5912, 5913).

---

## 4. The three rail tabs, Context, Templates, Job promo

All three run off the candidate object. None of them needs anything the profile
page does not already have.

**Context.** Reads the candidate only: classification, states open to,
compliance score and outstanding items, availability, SMS consent, and the last
internal note. Two buttons inside it call `openCandPage(c.id,'profile')`, at
6183 and 6315. On the profile page those would just switch you to the Profile
tab. Harmless, but they stop making sense once you are already there.

**Templates.** Reads `smsTemplates`, loaded once at startup, and the candidate
for the merge preview. Already page aware through `tplCurrentCand()`, so this
one needs nothing.

**Job promo.** Reads `roles` and `facilities`, both loaded at startup, plus the
candidate for match scoring and merge. One thing to flag: it also carries a
group send, `msgPromoSendGroup` at 6564, which sends to every matched candidate
rather than the one on screen, and its completion handler only refreshes the
screen when `curPage==='messages'` (6581). From the profile it would send
correctly but the page would not update itself afterwards.

**Shared state to be aware of.** The rail keeps its state in shared variables
that the hub and the profile would both be reading and writing:
`mtActiveTab` (6127), `mtCtxOpen` (6157), `mtChaseSel` (6223), and
`msgPromoRoleId`, `msgPromoFacId`, `msgPromoQ`, `msgPromoOpts` (6354, 6355).
`msgHubPick` clears some of these when you switch conversation in the hub
(6081, 6082). Nothing clears them when you open a different candidate's profile.

---

## 5. Rough size

Mostly wiring up what exists, not new code.

What the work actually consists of: a layout change in the messages branch of
`renderCandPage`, making those six helpers resolve the candidate the way
`tplCurrentCand` already does, and a CSS container for a two pane layout on the
profile. The existing `.msghub` class cannot be reused directly, it is a fixed
height three pane row sized for a full page.

No new logic, no new data, no database change, no new screens.

The real risk is not the amount of code. It is the shared rail state listed at
the end of section 4 leaking between the Messages centre and the profile.

---

## 6. Every tab on the candidate profile

Tab bar at 7868 to 7878, contents chosen at 7880 to 7911.

| Tab (label) | Internal value | What is inside it |
|---|---|---|
| Overview | `overview` | Overview section (spiel, matched roles, availability, block preference, preferred regions, travel notes, other preferences), then Next action if it is not already shown at the top, Key facts, Team, Submission readiness |
| Profile | `profile` | Personal Details, SMS Consent, Professional Details, Clinical Profile |
| Work preferences | `workpref` | Availability & Preferences, Rates & Increments |
| Compliance | `compliance` | Compliance only |
| Pipeline | `pipeline` | Submissions, Contracts |
| Travel | `history` | **Travel & Expenses, Activity, Admin & Flags** |
| Files | `files` | Files only |
| CV | `cv` | CV builder |
| Messages | `messages` | The thread, as described in section 1 |

**Activity lives in the Travel tab.** It sits between Travel & Expenses above it
and Admin & Flags below it. Admin & Flags only appears for admin and ops.

Note the mismatch: that tab is labelled "Travel" on screen but its internal
value is `history`.

---

## 7. How the tab bar is built

Hardcoded, and the tab names are repeated in several places. There is no single
list to edit.

Per tab, the identity is written out twice:

- the tab bar, one hand written button line each, 7869 to 7877
- the content dispatcher, a chain of if and else if on `_tab`, 7881 to 7911

The tab names also appear in:

- `_tabFor`, a map from section name to tab name, **duplicated word for word in
  two functions**, `openCandPageAt` at 4905 and `cpScrollTo` at 5024
- `openCandPage` at 4899, defaults to `overview` and special cases `messages`
- `setCpTab` at 5019, special cases `messages`
- `hashForPage` at 2203, defaults to `overview`
- nine call sites passing a tab name as a literal string: `pipeline` at 4900,
  `messages` at 3203 and 3219, `profile` at 5833, 6183 and 6315

So:

- **Renaming the visible label** is a one line change in the tab bar.
- **Adding a tab** means editing two places, the tab bar and the dispatcher.
- **Changing a tab's internal value** means editing both copies of `_tabFor`
  plus every call site that passes that value by name.

The URL routing does not need touching either way. `routeFromHash` at 2211
matches any word after the candidate id.
