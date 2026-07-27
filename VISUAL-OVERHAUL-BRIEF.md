# Visual overhaul brief, Direction C (warm operations)

## What this is
A visual overhaul of Captain Contract to a calmer, more premium, more engaging look, called Direction C. Do the design tokens first, then the Dashboard only, then STOP for review before any other screen. Do not repaint the whole app at once.

## Order of work, do not skip the stop
1. Write the token values into CAPTAIN-CONTRACT-DESIGN.md as a new section.
2. Apply them to the Dashboard screen only.
3. Report back and wait. Do not touch any other screen until I have tested the Dashboard live and told you to continue.

## The look, in plain terms
- Paper cards: white cards on a soft grey page background, separated by soft shadows, never border lines. Generous padding, real spacing.
- One primary accent, purple. Buttons, active tab underline, avatar tiles, progress bars, primary links.
- Metric tiles get a soft colour identity each (Option 2): a pale tinted icon chip in the tile's own colour, on a white tile. The tile only deepens to a full coloured fill with a faint inset ring when that tile represents something that needs attention (e.g. compliance alerts with items expiring). Calm by default, loud only when it matters.
- Status by colour, kept soft: green good, amber warning, red urgent, grey inactive. Used on compliance chips, alert dots, and the one-that-matters tile. Never turn every element into its own colour.
- Readable text: a solid secondary grey, not a washed-out light grey. A full near-black primary. A minimum body size so nothing strains to read.

## Token values to write into CAPTAIN-CONTRACT-DESIGN.md
Use these as the defined values. Name them as CSS variables or however the file already defines tokens, matching the existing convention in that doc.

Surfaces:
- Page background: #F4F4F2
- Card background: #FFFFFF
- Soft inner tile background (sub-stats): #F4F4F2

Text:
- Primary text: #14140F
- Secondary text: #54544E (this is the readable grey, do not go lighter)
- Muted text (hints only): #8F8D84
- Minimum body text size: 14px. Small meta text no smaller than 13px.

Accent (the one purple):
- Purple strong: #6936B8
- Purple mid: #7F77DD
- Purple deep: #534AB7
- Purple soft fill: #EEEDFE

Status (soft, for chips, dots, and the attention tile):
- Green text #158060, green soft fill #E1F5EE, green deep text #0B5A45
- Amber text #9C6212, amber soft fill #FAEEDA, amber deep text #6E4109, amber ring #EDC987
- Red text #A32D2D, red soft fill #FCEBEB
- Blue identity (submissions tile) text #185FA5, blue soft fill #E6F1FB
- Grey inactive #8F8D84

Card and shape:
- Card radius: 14px
- Control/chip radius: 10px, pills 20px
- Card shadow: 0 2px 8px rgba(0,0,0,0.05)
- Row divider inside a card: inset 0 -1px 0 rgba(0,0,0,0.05) as a shadow, never a border line
- Avatar tile: rounded square, radius 12px to 16px, purple fill #6936B8 with white initials, or purple soft fill #EEEDFE with #534AB7 initials for secondary

Numbers:
- Tabular numerals on every number. font-variant-numeric: tabular-nums.

## Dashboard changes specifically
- Remove the four separate tile colours currently used (green, blue, purple, coral all at once). Replace with Option 2: soft tinted icon chip per tile, white tile, and only the compliance alerts tile deepens to amber fill with the amber ring because it has items expiring. If a tile has nothing wrong, it stays calm white.
- Metric number is the hero: large (around 30 to 32px), weight 500, primary text colour, first thing read. Label above it in secondary grey.
- Replace the loud full-purple gradient welcome banner with the calm treatment: plain greeting in primary text, date line in secondary grey, tiles below on the page background. No gradient.
- Fix all em dashes on this screen. The date line "Monday 27 July 2026 — Consultant" becomes "Monday 27 July 2026, Consultant". "Morning brief — 85 actions" and every other dash on the Dashboard becomes a comma or is reworded. No em dashes anywhere.
- Cards (Morning brief, Other reminders, My candidates, Recent wins) all move to the paper-card treatment: white, 14px radius, the card shadow above, soft shadow dividers between rows, secondary text in the readable grey.
- Alert dots on reminder rows use the soft status colours: red urgent, amber warning, green good.

## Hard rules, every line
- No em dashes anywhere. Commas, periods, or "to" for ranges.
- Tabular numerals on all numbers.
- Borders as shadows, never lines.
- One purple accent. The tile colour identities are the only sanctioned extra colour, and they must stay soft unless signalling attention.
- Plain tone, no filler, no AI phrasing.
- Read CAPTAIN-CONTRACT-DESIGN.md before writing any UI, and write the new tokens into it before applying them.

## When done with the Dashboard
Report what changed, confirm no em dashes remain on the Dashboard, and confirm every number on it is tabular. Then stop and wait for me to test live before any other screen. Do not roll out to other screens in the same turn.
