# UI-REFRESH-BRIEF.md

Design refresh for HCA CRM. Goal: a modern recruitment-platform look
(clean/airy base with data-rich, guidance-driven work areas) for a boss demo
days away. Approved dashboard mockup is the reference.

Written 2026-07-11.

---

## THE ONE RULE ABOVE ALL

RESTYLE ONLY. NO LOGIC CHANGES. This refresh changes appearance, never
behaviour. Every button, save, filter, navigation, and data binding must work
exactly as before. If a change would touch what a function DOES (not how it
looks), stop and flag it - it does not belong in this refresh.

One screen per stage. Commit after each screen so any bad screen can be rolled
back individually. Never restyle multiple screens in one uncommitted batch.

Verify after each screen: the screen looks right AND everything on it still
works (click the buttons, check a save, confirm nav). Only then commit and
move to the next screen.

## Design language (from the approved dashboard mockup)

These are the rules every screen follows, so screens stay consistent.

Feel: airy and clean as the base (generous white space, calm surfaces),
data-rich and dense where the work happens (tables, lists, guidance panels).

Brand colour: purple #26215C (deep) and #534AB7 (mid), with #EEEDFE as the
light purple tint. Use purple as ACCENTS - primary buttons, header pills,
guidance boxes, avatar initials, active states - NOT as heavy background
washes. The base stays light.

Colour palette (semantic, consistent everywhere):
- Success / positive: green #0F6E56 text, #E1F5EE tint
- Warning / attention: amber #BA7517 text, #FAEEDA tint
- Danger / overdue: #993C1D text, #FAECE7 tint
- Info: #185FA5 text, #E6F1FB tint
- Neutral text: primary near-black, secondary grey, muted lighter grey

Cards: white surface, 12px border radius, 0.5px hairline border, ~16px
padding. Metric cards: light grey surface, no border, 12px label above, 26px
medium-weight number below, small coloured delta line beneath.

Typography: two weights only - 400 regular, 500 for emphasis/numbers/headings.
Never heavier. Sentence case everywhere (no ALL CAPS except tiny table column
labels, no Title Case). Headings ~20px/500.

Spacing: generous. ~14-16px gaps between cards, ~22px between major sections.
Let it breathe.

Buttons: primary action = purple #26215C background, white text, 8px radius.
Secondary = white/surface bg, 0.5px border, secondary-text colour. Sentence
case labels, verb-first ("New submission", not "Submit").

Guidance (the consultant-support element): where useful, surface a "next best
action" prompt (light purple box, purple text, a lightbulb/clock icon) and a
"needs attention" list that pulls urgent items (overdue follow-ups, expiring
contracts, unconfirmed travel) to the front. This is what makes it feel like a
tool that guides, not just displays.

Icons: clean line icons only, consistent set. No emoji.

## Dark mode

The mockup is light. Dark mode is a nice-to-have, NOT required for the demo.
Do not spend demo-timeline effort on dark mode now - get light mode excellent
first. If the app already has a dark mode toggle, just make sure the refresh
doesn't visibly break it; full dark-mode polish is post-demo.

---

## Build order - one screen per stage, commit after each

Dashboard first (it's the reference and the first thing seen), then the
screens most likely to come up in a demo, then the rest.

1. Dashboard - match the approved mockup exactly (metric cards, next-best-action
   guidance strip, team performance table, needs-attention panel).
2. Candidate profile - the most-viewed screen. Clean header, tabs, the info
   sections restyled to the card language.
3. Contracts page + Manage Placement - recently built, high-value to show.
4. Job Board - role cards and the slide-out panel.
5. Facilities list + facility profile.
6. Submissions / pipeline.
7. Everything remaining (Team, Travel & Expenses page, Settings, modals) -
   swept for consistency with the design language.

Global shared elements (sidebar, top bar, modals, buttons) should be restyled
early - ideally as part of stage 1 or a stage 0 - since they appear on every
screen. Establish the shared shell once so later screens inherit it.

## Per-stage process (repeat for each screen)

1. Restyle only that screen (and shared shell on stage 1) to the design
   language above. No logic changes.
2. Report what changed visually.
3. Human verifies: screen looks right, and everything on it still works.
4. Commit that screen with a clear message, push.
5. Move to the next screen.

If any screen's restyle accidentally breaks a function, roll back that
commit - do not try to fix logic inside the refresh.
