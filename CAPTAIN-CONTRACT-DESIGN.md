# Captain Contract, design system

The reference for all new UI. Benchmarked against Linear, Attio, Vercel Geist,
Stripe and Front. Apply to new features first, then migrate existing pages
incrementally. Do not attempt a single big-bang restyle of index.html.

## Rules
1. No em dashes anywhere, in code, comments, UI copy or generated documents.
2. Numbers, dates, money and counts always use `font-variant-numeric: tabular-nums`.
3. Borders are shadows, not borders. Use `box-shadow: 0 0 0 1px rgba(22,21,26,.055)`
   instead of `border: 1px solid`. This keeps layout stable and looks softer.
4. One accent colour. Purple. Semantic colours only for state, never decoration.
5. Motion: 150 to 250ms for micro interactions, ease-out on entry.
6. Every primary action needs a keyboard path.

## Tokens

```css
:root{
  /* ink ramp */
  --ink:#16151A; --ink2:#3E3B47; --ink3:#6F6B7B; --ink4:#9E9AAB; --ink5:#C4C1CE;

  /* surfaces */
  --bg:#FCFCFD; --panel:#fff; --panel2:#FAFAFB; --panel3:#F4F3F6;
  --line:#EAE9EF; --line2:#E0DFE7;

  /* brand purple, Radix violet derived */
  --v3:#F6F3FF; --v4:#EDE9FE; --v6:#DDD5F8;
  --v9:#6E56CF; --v10:#644FC1; --v11:#5B47B0; --v12:#3D2E72;

  /* semantic */
  --g3:#E9F9EE; --g9:#30A46C; --g11:#18794E;   /* valid, available, delivered */
  --a3:#FFF7E0; --a9:#F5A524; --a11:#A15C07;   /* expiring, warning, internal note */
  --r3:#FFEFEF; --r9:#E5484D; --r11:#CD2B31;   /* expired, blocked, opted out */

  /* elevation */
  --sh-b:0 0 0 1px rgba(22,21,26,.055);
  --sh-1:0 0 0 1px rgba(22,21,26,.05), 0 1px 2px rgba(22,21,26,.04);
  --sh-2:0 0 0 1px rgba(22,21,26,.05), 0 2px 6px rgba(22,21,26,.05), 0 10px 26px rgba(22,21,26,.07);
  --sh-3:0 0 0 1px rgba(22,21,26,.06), 0 24px 64px rgba(22,21,26,.20), 0 6px 16px rgba(22,21,26,.10);

  /* motion */
  --e:cubic-bezier(.16,1,.3,1);
  --spring:cubic-bezier(.34,1.28,.5,1);
}
```

## Direction C, calm premium (rollout in progress)

Chosen visual direction for the next pass, calmer and more premium than the
original bright KPI chips. Rolling out screen by screen, Dashboard first.
These tokens sit alongside the set above, a migrated screen reads from these,
everything else keeps reading from the original set until its own pass.

Paper cards: white cards on a soft grey page, separated by soft shadows,
never border lines, generous padding. One primary accent, purple, on
buttons, active tab underlines, avatar tiles, progress bars and primary
links. Metric tiles carry a soft colour identity each, a pale tinted icon
chip in the tile's own colour on an otherwise white tile, calm by default. A
tile only deepens to a full coloured fill with a faint inset ring when it
represents something that needs attention, loud only when it matters.
Status by colour stays soft and only shows on chips, alert dots and the one
attention tile, not on every element. Text stays readable, a solid
secondary grey rather than a washed out one, a full near black primary, and
a minimum body size.

```css
:root{
  /* surfaces */
  --dc-bg:#F4F4F2; --dc-card:#FFFFFF; --dc-tile:#F4F4F2;

  /* text, do not go lighter than secondary */
  --dc-t1:#14140F; --dc-t2:#54544E; --dc-t3:#8F8D84;

  /* purple, one accent */
  --dc-purple:#6936B8; --dc-purple-mid:#7F77DD; --dc-purple-deep:#534AB7;
  --dc-purple-soft:#EEEDFE;

  /* status, soft by default, full fill and ring only on the tile that needs attention */
  --dc-green:#158060; --dc-green-soft:#E1F5EE; --dc-green-deep:#0B5A45;
  --dc-amber:#9C6212; --dc-amber-soft:#FAEEDA; --dc-amber-deep:#6E4109; --dc-amber-ring:#EDC987;
  --dc-red:#A32D2D; --dc-red-soft:#FCEBEB;
  --dc-blue:#185FA5; --dc-blue-soft:#E6F1FB;
  --dc-grey:#8F8D84;

  /* shape */
  --dc-r-card:14px; --dc-r-control:10px; --dc-r-pill:20px; --dc-r-avatar:14px;
  --dc-shadow-card:0 2px 8px rgba(0,0,0,.05);
  --dc-shadow-row:inset 0 -1px 0 rgba(0,0,0,.05);
}
```

Body text on these tokens is 14px minimum, small meta never smaller than
13px. Every number, tabular-nums, no exceptions.

Avatar tile: rounded square, 12 to 16px radius. Primary is `--dc-purple`
fill with white initials. Secondary is `--dc-purple-soft` fill with
`--dc-purple-deep` initials.

Row dividers inside a paper card are a shadow, `--dc-shadow-row`, never a
border line.

## Type
Inter, loaded from Google Fonts, weights 400 450 500 550 600 650.
```css
body{
  font-family:'Inter',-apple-system,'Segoe UI',Roboto,sans-serif;
  font-size:13.5px; letter-spacing:-.011em;
  -webkit-font-smoothing:antialiased;
  font-feature-settings:'cv02','cv03','cv04','ss01','zero';
}
```
Scale: page title 19 to 21px at 600 weight and -.03em tracking. Section label
10 to 10.5px at 650 weight with .08em tracking in `--ink4`. Body 13 to 13.5px.
Table cells 13px. Meta 11.5 to 12px in `--ink3`.

## Layout
- Spacing on an 8px grid. 4, 8, 12, 16, 24, 32.
- Radius: 7 to 8px controls, 9 to 11px cards, 14px panels, 20px+ modals.
- Dark rail on the far left at `#131217`, 56px icon only or 232px with labels.
  Active item gets a 2px purple bar on its left edge and a subtle white wash.
- Content sits on `--bg`, cards on `--panel`.

## Components

**Button primary**
```css
background:linear-gradient(180deg,#7B63D8,var(--v9)); color:#fff;
box-shadow:0 1px 2px rgba(90,69,181,.28),0 3px 9px rgba(110,86,207,.2),inset 0 1px 0 rgba(255,255,255,.14);
```
Hover lifts by .5px. Secondary uses `--sh-b` on white.

**Saved views** across the top of any list: coloured dot, label, count. Active
view gets `--v4` background and `--v11` text. This is the Attio pattern and it
is how Candidates, Job Board and Submissions should all work.

**Compliance meter**: five 15x4px segments. Green at 90 and above, amber 75 to
89, red below 75. Always paired with a "next expiry" value in days.

**Status chips**: 11.5px, 500 weight, 6px radius, semantic tint background with
matching dark text. Never use a coloured dot alone.

**Empty states**: 46px rounded icon tile in `--v3`, title at 14px 600, one line
of `--ink3` beneath, and a primary action.

**Toast**: dark `#1B1A20`, bottom centre, 11px radius, small tinted icon tile,
fades up over 300ms, auto dismisses at about 2.8s.

## Keyboard
- Cmd or Ctrl K opens the command palette. It searches candidates, jumps to
  views, and runs actions, with shortcuts shown inline so it teaches itself.
- J and K move through lists, Enter opens, Esc closes.
- Enter sends in any composer, Shift Enter makes a new line.

## Feature specific

### Messages
Thread lives on the candidate record. It is surfaced in two places and both read
the same data: a dedicated Messages hub with a conversation list, and a Messages
tab on the candidate profile.

The thread renders as an iMessage style screen: no phone bezel, just a white
panel with 30px radius and layered shadow. Outbound bubbles use
`linear-gradient(170deg,#7E67DE,#5D48C0)`, inbound `#E9E9EB`. Consecutive
messages from the same side group, only the last gets a tail. Delivery and read
receipts sit right aligned under the last outbound bubble.

Internal notes are a distinct message type in amber, visible to staff only,
labelled clearly as not visible to the candidate.

Inbound replies raise an iOS style notification banner that slides down over the
top of the thread, and an in-app alert.

Consent is enforced by the system. If `sms_consent` is false the composer is
replaced by a red block explaining the candidate opted out, and any send path is
disabled. This is a legal requirement under the Australian Spam Act, not a
preference.

Character counter shows segments: 1 segment to 160 characters, then 153 per
segment. Warn in amber past one segment because cost multiplies.

### CV builder
The CV assembles from data the system already holds. Confirmed contracts become
work history. Compliance records supply AHPRA and CPD. Nothing is retyped.

The output is a document, not a dashboard. Restraint over decoration.

Header carries name, classification, AHPRA number. Nothing else. No contact
details on any setting.

Work history is stacked lines, one per line, in this order:
```
Feb 2026 to Present
Regional Base Hospital, NT
Registered Nurse
Intensive Care Unit
```

Section order: About, Qualifications and CPD, Work history, Skills checklist,
References. Sections toggle on and off and reorder.

Name display has three levels: full name, first name plus surname initial, or
reference number only.

Skills checklist and reference PDF parsing are later work, render as placeholders
with a clear note.
