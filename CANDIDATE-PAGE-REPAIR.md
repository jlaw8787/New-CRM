# CANDIDATE PAGE LAYOUT REPAIR BRIEF

Paste this to Claude Code in the New-CRM repo. Target file: index.html.

## Problem

The candidate full page (/#candidate/[id]) renders with no styling in the
main content area. Symptoms visible in the live app:

- Initials avatar renders as plain text ("SM") instead of a purple circle
- Phase badge and priority run together as unstyled text ("On AssignmentHigh")
- Compliance % renders as text, no progress bar
- Phone and email render as default blue/pink browser links
- KEY FACTS renders as one stacked column of label/value text, not a 2-col grid
- TEAM avatars render as squished ovals with overlapping text
- Section nav (Overview / Personal / etc) renders as a plain unstyled list
- Left and right columns are stacking vertically, not side by side

The sidebar is styled correctly, so the CSS variables exist. The candidate
page component classes are either missing from the stylesheet or the markup
class names do not match the CSS. Diagnose which, then fix. Do not rebuild
the whole page. Keep all existing data bindings and event handlers working.

## Required layout (from master brief Part 3/4)

Candidate page = 280px sticky left column + remaining scrollable right column.

```css
.entity-page {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
  align-items: start;
  padding: 32px;
}
.entity-left {
  position: sticky;
  top: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.entity-right {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

## Card base (all left column blocks sit in these)

```css
.card {
  background: var(--hca-card);
  border: 1px solid var(--hca-border);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  padding: 20px;
}
```

## Profile card

Structure: avatar circle, name, classification line, phase badge,
compliance bar, available-from line, phone + email buttons, hot toggle.

```css
.profile-avatar {
  width: 64px; height: 64px;
  border-radius: 50%;
  background: var(--hca-purple);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700;
  margin: 0 auto 12px;
}
.profile-name { font-size: 20px; font-weight: 700; text-align: center; color: var(--hca-text-primary); }
.profile-sub  { font-size: 13px; color: var(--hca-text-secondary); text-align: center; margin-bottom: 12px; }

.phase-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
/* apply per-phase colours from the brief token table, e.g. */
.phase-onassignment { background: #e8f5e9; color: #2e7d32; }

.compliance-bar-wrap { margin: 12px 0; }
.compliance-bar-label { display: flex; justify-content: space-between; font-size: 12px; color: var(--hca-text-secondary); margin-bottom: 4px; }
.compliance-bar { height: 6px; border-radius: 3px; background: var(--hca-border); overflow: hidden; }
.compliance-bar-fill { height: 100%; border-radius: 3px; background: var(--hca-green); }

.contact-btn {
  display: flex; align-items: center; gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border: 1px solid var(--hca-border);
  border-radius: 6px;
  background: #fff;
  font-size: 13px;
  color: var(--hca-text-primary);
  text-decoration: none;
  margin-top: 8px;
}
.contact-btn:hover { background: var(--hca-purple-light); }
```

## Key facts grid

```css
.key-facts {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 16px;
}
.key-fact-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--hca-text-muted);
}
.key-fact-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--hca-text-primary);
}
```

Each fact is a label/value pair inside one grid cell. Pairs per the brief:
Nurse Type | Years Exp, AHPRA # | Expiry, Home State | Has Car,
Block Pref | Min Rate, Accom Req | Partner Accom, Nearest Airport | Notice Days.
Empty values show an em-height dash in muted colour.

## Team block

```css
.team-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.team-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 12px; font-weight: 600;
}
.team-name { font-size: 13px; font-weight: 600; color: var(--hca-text-primary); }
.team-role { font-size: 11px; color: var(--hca-text-muted); }
```

The squished oval avatars in the current build are almost certainly a
missing flex-shrink: 0 or missing fixed width/height. Fix that specifically.

## Section navigation

```css
.section-nav { display: flex; flex-direction: column; gap: 2px; }
.section-nav a {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--hca-text-secondary);
  text-decoration: none;
}
.section-nav a:hover { background: var(--hca-purple-pale); }
.section-nav a.active {
  background: var(--hca-purple-light);
  color: var(--hca-purple);
  font-weight: 600;
}
```

## Page header

The header row (name, phase line, back button, Submit button) should be a
flex row with the buttons right-aligned, sitting above the two-column grid.
Back button = secondary button style, Submit = primary purple button, both
per the brief's component specs.

## Acceptance checks

1. Left column is 280px, sticky, right column scrolls beside it
2. Avatar is a proper circle with initials centred
3. Phase badge and priority are separate styled pills, not concatenated text
4. Compliance shows a bar with fill matching the percentage
5. Key facts render as a 2-column grid
6. Team avatars are 32px circles, text beside them, nothing squished
7. Section nav items highlight on hover and scroll the right column
8. No other page's styling regresses. Check Dashboard, Candidates list,
   and Facilities still render correctly after the change.

## Rules

- Vanilla CSS only, use the existing --hca-* tokens, no frameworks
- Do not rename existing JS functions or data attributes
- If class names in markup and CSS disagree, fix in one place consistently
- Test at localhost:8080 before calling it done
