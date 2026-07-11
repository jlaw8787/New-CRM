# CANDIDATE-PAGE-OVERHAUL-BRIEF.md

Full redesign of the candidate profile page to a SaaS-leading standard
(inspired by Bullhorn/JobAdder/Vincere/Loxo, but better). Approved mockup is
the reference.

Part of the UI refresh. Follows UI-REFRESH-BRIEF.md's rules, especially:
RESTYLE/REARRANGE ONLY, NO LOGIC CHANGES. Every tab, edit, save, compliance,
pipeline, manage-placement, travel, files, and contact function keeps working
with its existing functions and arguments. We move and redress existing
rendered pieces; we never rebuild what they DO or fabricate data.

Written 2026-07-11.

---

## The approved structure (top to bottom)

1. IDENTITY HEADER
   - Gradient strip with the avatar (rounded-square, gradient) overlapping it.
   - Name + status pill(s) (On assignment, Hot, etc. - from existing data).
   - Subtext: role / years / home state / availability.
   - Action buttons on the right: Call, Email, Submit (wired to the existing
     contact links / submit flow).

2. GLANCE ROW - three smart cards:
   - NEXT ACTION (prominent, dark gradient): the candidate's current most
     urgent action + a resolve button. Uses existing next-action data/logic.
     Hide if none.
   - COMPLIANCE: a ring showing the candidate's REAL compliance score, plus
     plain-English status ("Cleared to work" / not) and an expiring heads-up
     if that data exists. Never fabricate.
   - CURRENT PLACEMENT: the active/upcoming contract as a mini card (facility,
     ward, rate, end date, progress bar). Existing contract data. Tidy empty
     state if none.

3. TABBED BODY (Overview, Profile, Work prefs, Compliance, Pipeline, Travel,
   Activity, Files):
   - All existing tab content moves in UNCHANGED.
   - Overview tab opens with the key-facts grid, then COLLAPSIBLE detail
     sections beneath (clinical skills, references, notes, etc.).

## Build in stages. Commit after each. Verify each before moving on.

Checkpoint commit FIRST (before stage 1) so there's a clean rollback.

### STAGE 1 - Identity header
Replace the current header/profile card with the new identity header (gradient
strip, overlapping avatar, name+status, subtext, Call/Email/Submit actions
wired to existing functions). Nothing else changes yet. Verify contact/submit
work. Commit.

### STAGE 2 - Glance row
Add the three glance cards (next action / compliance ring / current placement)
below the header, each fed by REAL existing data, each hiding gracefully if no
data. The next-action button and placement link use existing functions.
Verify. Commit.

### STAGE 3 - Tabbed body + Overview
Move all existing tab content into the cleaned tab bar. Overview tab = key
facts grid + collapsible detail sections. All tab switching, edits, saves,
compliance, pipeline, manage-placement, travel, files keep working. This is
the biggest/riskiest stage - go carefully, report exactly what moved. Verify
EVERY tab + an edit/save + manage-placement. Commit.

### STAGE 4 - Collapsible sections
Make the Overview detail sections (and other long sections where it helps)
collapsible - a lightweight show/hide toggle, remembering nothing between
visits is fine. Pure UI interaction, no data logic. Verify. Commit.

### STAGE 5 - Notes / activity search (SEPARATE FEATURE, do last)
Add a search box to the Activity tab that filters activity/notes entries by
text. This is a NEW feature (filter logic), kept separate from the layout work
so it can't destabilise it. Verify search filters correctly and clearing it
restores the full list. Commit.

## Verification bar (every stage)
Looks right AND works. For this page specifically, always re-test after each
stage: every tab opens, an edit saves, manage-placement opens from the
placement, contact links work, next-action completes. If a stage breaks a
function, roll back that stage's commit - do not patch logic inside the
refresh.

## Guard rails
- No fabricated data. Rings/next-action/placement use real data or hide.
- No logic changes in stages 1-4. Stage 5 is the only new-logic stage.
- Reuse shared tokens/shell already established. Don't redefine them.
