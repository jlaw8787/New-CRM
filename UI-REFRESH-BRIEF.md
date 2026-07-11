# UI-REFRESH-BRIEF.md

Design refresh for HCA CRM. Goal: a modern recruitment-platform look
(clean/airy base with data-rich, guidance-driven work areas) for a boss demo
days away. Approved dashboard mockup is the reference.

Written 2026-07-11.

---

## THE HERO-MOMENT RULE (learned mid-rollout)

Cascading shadows/colours/radius through shared helpers makes a screen TIDY
but not IMPRESSIVE - it lands "so-so." Every major screen needs its own HERO
MOMENT: one designed, composed centrepiece, not just restyled existing boxes.

- Dashboard hero = the gradient header band with headline numbers.
- Candidate profile hero = a gradient header band with avatar chip, name +
  status, inline contact details, a compliance RING (real compliance data),
  and a key-facts strip beneath.
- Every other screen (contracts, job board, facility, etc.) must get an
  equivalent designed hero/header treatment appropriate to its content, not
  just cascaded card styling.

When restyling a screen, ask: "what's this screen's hero moment?" and design
that, then let the shared card language handle the rest. A screen with no hero
will read as unfinished even if every card has a shadow.

Rings/charts are allowed ONLY on real existing data (e.g. the candidate's real
compliance score as a ring). Never fabricate data for a visual.

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

## Design language (from the approved HIGH-POLISH dashboard mockup)

The bar is modern-SaaS polish (JobAdder/LiveHire/Monday tier), NOT a flat
colour swap. A token-only pass (colours + radius + weights) is explicitly NOT
enough - it lands at ~60% and reads unfinished. The approved mockup includes:

- Depth: cards have soft layered shadows so they lift off the page
  (e.g. box-shadow: 0 2px 6px rgba(38,33,92,.05), 0 16px 32px -22px rgba(38,33,92,.4)).
  Not flat.
- A hero header band: gradient purple (#26215C -> #534AB7) panel carrying the
  greeting and headline numbers, with subtle decorative circles.
- Icon tiles on metric cards (rounded-square coloured icon chips), trend pills
  (e.g. "▲ 12%").
- Real data viz: a trend line/area chart with gradient fill, a compliance
  progress ring (donut), gradient-filled progress bars in the team table.
- Rich guidance bands: the next-best-action prompt as a full coloured gradient
  banner with icon and CTA, not a plain box.
- Generous spacing, rounded 14-16px cards, avatar/initial chips with rounded
  squares.

Brand purple #26215C / #534AB7 / #EEEDFE tint. Gradients ARE allowed here
(hero band, progress bars, guidance banners) - this is a product UI, not a
flat doc. Semantic colours: success #0F6E56/#E1F5EE, warning #BA7517/#FAEEDA,
danger #993C1D/#FAECE7, info #185FA5/#E6F1FB.

Two font weights (400/500), sentence case, clean line icons.

## CRITICAL: keep all existing functional pieces

This is a RESTYLE. Every existing functional element on a screen stays and
keeps working - it just gets dressed in the new look. On Home specifically:
the Morning Brief, the reminders/needs-attention list, and every existing
action/button/link MUST remain, wired exactly as before. Do not drop, replace,
or stub any working piece to make it "look like the mockup." The mockup shows
the visual treatment to wrap around the real content, not a content
replacement. If the mockup shows an element the screen doesn't have (e.g. a
compliance ring), only add it if the data already exists to power it - never
fake data or invent features during the restyle.

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
