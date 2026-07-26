# Captain Contract, build brief: finish the Message Centre to the mockup

One pass. Rebuild the Messages hub to match messages-workspace-v2.html, and land
the last two features (Job promo builder, inbound alerts) in the same pass.
Working in index.html.

## Hard rules, non negotiable
1. No em dashes anywhere, in code, comments, UI copy or output. Commas, periods,
   or "to" for ranges.
2. Numbers, counts, segments and dates use font-variant-numeric: tabular-nums.
3. Borders are shadows: box-shadow: 0 0 0 1px rgba(22,21,26,.055), not border.
4. One accent, purple. Semantic colours for state only.
5. Plain copy, no filler.
Design and token reference: CAPTAIN-CONTRACT-DESIGN.md. Visual target:
messages-workspace-v2.html. Both are in the project folder. Read them first.

## Before you write anything
Confirm these exist in index.html and match what this brief assumes. If any
differ, stop and tell me rather than guessing:
- renderMessagesHub, renderMsgThread, msgComposerHtml, msgCnt, msgSegments,
  sendMessage (the consent gate), addNote, msgMarkThreadRead, msgConversations.
- Template logic already built: smsTemplates, mergeTemplate, tplMine, tplTeam,
  tplInsert, tplCurrentCand, plus the editor save and delete.
- roles (global array), roleMatchList(pool, role), facilities.
- getAutos(cands) and its alert object shape:
  {id, level:'red'|'amber'|'blue', type, title, desc, cid, tab}.
- Candidate messages carry direction 'out', 'in' or 'note', with readAt on
  inbound. CU is the current user with id, name, role.

## What already works, do not rebuild
The consent gate in sendMessage, msgSegments, the template merge and insert logic,
roleMatchList, getAutos. Reuse all of it. This brief re-homes and restyles, it
does not re-implement the engine underneath.

---

## STAGE 1, rebuild the hub layout to the mockup

The mockup is a three pane workspace. The live hub is two panes with the thread
in a plain box and templates in a popover. Rebuild renderMessagesHub to output
three panes, left to right:

1. Conversation list. Keep the existing data from msgConversations. Restyle to
   the mockup's list: gradient avatar, name, last message preview, time, unread
   pip, compliance chip.
2. Stage, the phone framed thread. This is the middle pane. Port the mockup's
   phone screen: a white panel with a 30px radius screen and layered shadow, a
   contact header at the top (avatar and name), the thread body, then the
   composer. Bubbles per the design file: outbound linear-gradient(170deg,
   #7E67DE,#5D48C0), inbound #E9E9EB, consecutive messages group and only the
   last gets a tail, receipts right aligned under the last outbound bubble,
   internal notes in amber labelled not visible to the candidate.
3. Tools rail. The right pane, with three tabs: Context, Templates, Job promo.
   Ports the mockup's tools column. Tab switching is local state, no reload.

Port the mockup's CSS for the panes, phone screen, bubbles and rail into the app
stylesheet. Namespace so it does not collide with existing classes. Make sure
every CSS variable the mockup uses resolves against the app :root. If a variable
the mockup references is not defined in the app, add it, do not leave an
undefined var.

Composer fix, important, this is the ugly one. On the live app the text field has
a box inside a box, because both the field wrapper and the textarea draw their own
border and background. Fix so it is one clean field: the textarea inside the
composer must be background: transparent, border: none, outline: none,
box-shadow: none, and the single visible border lives on the wrapper only. Note
mode keeps its amber inset on the wrapper, not on the textarea.

Scope note. The three pane workspace is the Messages hub only. The candidate
profile Messages tab stays a single column thread, but restyled to the same phone
screen so they match. Do not put the list or the tools rail on the candidate
profile tab.

Validate stage 1 before moving on: hub shows three panes, thread looks like the
mockup, composer is one clean field, candidate profile Messages tab still works
and matches the styling.

---

## STAGE 2, move Templates into the Tools rail

Retire the popover. Templates now live in the Templates tab of the rail.

- Render My Templates (tplMine) and Team Templates (tplTeam), each row showing the
  name and the merged preview via mergeTemplate against the open candidate.
- Clicking a row calls tplInsert to drop merged text into the composer. Because
  the tab is always mounted, there is no outside click race, so the insert is
  stable. This is the point of moving it.
- Keep the editor (create, edit, delete personal templates, team read only unless
  CU.role is ops) exactly as already built, surfaced from the tab.
- Remove the composer Templates button and the popover functions
  (tplTogglePopover, tplPopoverHtml, tplClosePopoverOnce) or repoint them at the
  tab. Do not leave dead popover code wired to the composer.

Validate: open the Templates tab, previews resolve for the open candidate, click
inserts and merges, switching candidate updates the previews, create and delete
still work.

---

## STAGE 3, Job promo builder in the Job promo tab

Port the mockup's promo builder (renderPromo, promoText, sendPromo), wired to real
data instead of the mock JOBS array.

- Role picker: list from the real roles array. Tag roles that match the open
  candidate, using the same signal roleMatchList uses (classification or specialty
  and open states), so the relevant roles float up.
- Detail toggles: dates, rate, ward, fact sheet link.
- Assemble the SMS with a promoText(role, cand, opts) function:
  "Hi {first_name}, {ward} role at {facility}" then, if dates on, ", {start} to
  {end}", then ".", then if rate on and a rate exists " Rate: {rate}.", then if
  link on " Fact sheet: <link>", then always " Interested? Reply YES. Reply STOP
  to opt out." The opt out line is always appended, it is a legal requirement.
- Rate handling: roles have no rate field today. If role.rate exists, use it. If
  not, hide the rate line and disable the rate toggle. Roles can gain an optional
  rate field later, do not block on it now.
- Segment count on the assembled text via msgSegments, shown with tabular-nums,
  warn in amber past one segment.
- Send to one: route through sendMessage(cand.id, text) so the consent gate and
  logging apply. If the candidate has no consent, show the red blocked line and
  disable send.
- Send to group: use roleMatchList to get matches for the picked role, filter to
  those with smsConsent true and doNotContact false, show the count, confirm with
  showConfirm, then loop sendMessage for each. Report how many were sent and how
  many were skipped for consent.

Validate: pick a role, toggles change the assembled text and the segment count,
single send lands in the thread and respects consent, group send confirms and
reports counts.

---

## STAGE 4, inbound alerts and the banner

Inbound messages already land on the candidate as direction 'in' with a readAt.
No new table.

- getAutos branch: for each candidate with an unread inbound message (direction
  'in', no readAt), push one alert:
  {id:'inbound:'+c.id, level:'amber', type:'message',
   title:'New reply: '+c.name,
   desc:<last inbound message preview, trimmed>,
   cid:c.id, tab:'Messages'}.
  One per candidate, deduped by id. Make sure the Alerts count and any alert
  rendering handle the new type gracefully (icon and click through to the
  candidate Messages tab).
- Banner: port the mockup's slide down banner into the phone stage. When the open
  thread has a fresh unread inbound, show the iOS style banner at the top of the
  screen, then clear it when msgMarkThreadRead runs for that candidate.
- Testability without a provider: add a dev only affordance, visible when
  CU.role is ops, a small "Simulate inbound reply" button on the open thread that
  inserts a direction 'in' message on the open candidate, so the banner and the
  alert can be exercised before any SMS provider exists. Keep it clearly labelled
  as a dev tool.

Optional SQL to seed one inbound for testing, run by hand, swap the candidate_id
for a real consented candidate:

```sql
insert into public.messages (candidate_id, direction, body, status, author, created_at)
values (1, 'in', 'Yes keen, when does it start?', 'delivered', 'Candidate', now());
```

Validate: an unread inbound raises one alert, opening the thread shows the banner,
reading the thread clears both.

---

---

## STAGE 5, composer additions: emoji and note delete

### Emoji picker
- Add an emoji button in the composer top row, next to the Internal note toggle
  and the Templates entry. Clicking opens a small emoji panel anchored to the
  composer.
- Native unicode emoji only. No external library, no CDN, no image assets, the
  app is a single file. A curated set is enough, a few groups (smileys, gestures
  and hands, hearts, common objects and symbols) with a few dozen each.
- Clicking an emoji inserts it at the cursor position in the textarea, not just
  appended to the end, then re-runs msgCnt so the counter updates. Keep the panel
  open for multiple inserts, close on outside click or Esc. Mount it so an outside
  click does not wipe the textarea, same lesson as the old templates popover.
- Works in both the SMS composer and the internal note composer.

### Segment counting with emoji, cost accuracy
An emoji forces an SMS from GSM 7 bit encoding to the wide UCS-2 encoding, which
changes the limits. msgSegments currently assumes GSM (160 then 153). Update it:
- Only GSM characters present: 160 for one segment, then 153 per segment.
  Unchanged.
- Any non GSM character present (emoji and similar): 70 for one segment, then 67
  per segment.
Detect with a GSM character check. This matters because one emoji can turn a
single segment message into several, and the promo builder costs on segments.
Warn in amber as soon as it tips past one segment under whichever encoding
applies. Keep tabular-nums on the readout.

### Delete an internal note
Notes are useful but need to be removable.
- Each internal note bubble gets a small remove control, a trash icon, visible to
  staff. Notes are staff only already, so no extra permission gate beyond being
  logged in.
- Clicking confirms with showConfirm ("Delete this note? This cannot be undone."),
  then removes the note from c.messages and deletes the row from the messages
  table by id, then re-renders. If the note is unsynced (temp id, no DB row),
  remove it locally only.
- Scope: delete applies to internal notes only. Outbound and inbound SMS are left
  as an immutable log, since they record what was actually sent or received. We
  can revisit deleting those later.

Validate: emoji inserts at the cursor and the counter updates, the counter switches
to the 70 and 67 limits when an emoji is present, a note can be deleted after
confirm and stays gone after refresh, sent and received SMS have no delete control.

---

---

## STAGE 6, speed refinements: kill double handling

Standing principle for this stage and the app in general: kill pointless double
handling. Sending a consultant to another page is fine when it has point and
purpose. What to remove is the loop with no payoff, open a page, read one value,
come back, and retype it. Where a screen can carry the information or the action
itself, it should.

### 6.1 Job promo, surface the compose panel on pick
Bug: in mtPromoHtml the INCLUDE toggles, SMS PREVIEW, counter and send buttons are
appended after the full role list, so with ten or more open roles they render below
the fold. Clicking a role looks like it does nothing because the panel is off
screen.
Fix: when a role is picked, show the compose panel at the top of the Job promo tab,
not after the list. On pick, render the selected role as a compact header
(facility, ward, dates) with a "Pick a different role" link, then the INCLUDE
toggles, the SMS preview, the counter, and the Send and Group buttons, all above or
in place of the list. No scrolling to reach the send button. The link restores the
full list.

### 6.2 Context rows become workable, not just readable
Today mtCtxHtml renders flat, non interactive rows. Make each Context row
expandable: click to drop down its detail and any actions that belong to it, click
again to collapse. One open at a time is fine. The row keeps its summary value when
collapsed. This turns Context from a readout into a workspace.

### 6.3 Compliance in Context, show what is missing and act on it
The flagship no double handling fix. The Context compliance row shows a bare
percentage today, which forces the consultant to open the candidate's Compliance
tab, read what is missing, come back, and act. Remove that loop.
When the compliance row is expanded, list the actual outstanding items inline:
anything missing, unverified, or expiring soon, each with its status chip and, where
relevant, its expiry date. Reuse the existing compliance breakdown logic from the
Compliance tab, do not reinvent the model. Add a useful inline action per item, at
minimum a one click chase that inserts a templated chase for that credential into
the composer, so the consultant sees what is missing and acts on it without leaving
Messages.
Keep the collapsed summary as the percentage plus a short "N outstanding" count so
the row stays glanceable.

Validate stage 6: picking a role shows the compose panel at the top with no
scrolling, Context rows expand and collapse, and the compliance row lists the real
outstanding items and offers an inline action.

---

## Provider
Stays parked. Sending remains the stubbed setTimeout, no SMS provider in this
pass.

## Finish
Stages 1 to 4 are already built and pushed. Do not rebuild or restyle them. Build
Stage 5 and Stage 6 only, validating each as written. When both validate, commit
index.html with the message
"Message centre stage 5 and 6, emoji, note delete, promo fix, context actions"
and push. Give me the commit hash and confirm the push. Do not touch anything
outside the Message Centre. Confirm no em dashes anywhere in the diff.
