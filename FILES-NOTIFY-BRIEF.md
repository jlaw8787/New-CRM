# FILES TAB + JOB NOTIFICATIONS + FLOW POLISH BRIEF
# Slot this in AFTER Stage 4 (candidate tabs) since the Files tab
# hangs off the tab structure. Standing rules apply: straight quotes,
# node --check after every edit, one feature at a time with sign-off.

---

## FEATURE A: CANDIDATE FILES TAB

A general document home per candidate, separate from compliance:
CVs, competitor rate sheets, contract photos, references, anything.
The documents table and storage bucket already exist from the
compliance document work; this reuses them.

### Storage prerequisite (user does this once in Supabase dashboard)
Bucket named documents must exist (created for compliance uploads).
If not: Storage > New bucket > "documents", public ON for sandbox.

### The tab
Add "Files" to the candidate page tabs, label shows count: Files (4).

Layout: an upload zone at top (click to browse AND drag-and-drop),
then a table: file icon by type | name | category | size | uploaded
by | date | actions (view, download, edit details, delete).

- Categories: CV, Contract, Rates/Competitor, Reference, Photo, Other.
  Category is a coloured chip, editable inline via a small select.
- Upload flow: pick or drop file(s), a row appears per file with a
  category select (default: guessed from filename, cv/resume => CV,
  jpg/png => Photo) and optional description, then Save uploads to
  storage path candidates/{id}/general/{filename} and inserts a
  documents row (candidate_id, file_name, file_url, file_size,
  file_type, category, description, uploaded_by, is_current).
- Multiple files at once supported, each shows upload progress.
- View opens in a new tab. Images and PDFs the browser renders
  natively, everything else downloads.
- Delete asks for confirmation, removes the storage object AND the
  documents row, logs activity "Deleted file {name}".
- Every upload logs activity "Uploaded {name} ({category})".
- "Tidy" affordances: sort by any column, filter chips by category,
  and a Mark Superseded action that sets is_current=false and greys
  the row (keeps history without clutter, old CVs stay findable).
- Compliance-linked documents (compliance_item_id not null) do NOT
  show here to avoid double handling; they live on the Compliance
  tab. A small note at the bottom links there.

### Facility files
Same component, mounted on the facility full page (rate cards,
agreements, ward info sheets). Path facilities/{id}/general/.

---

## FEATURE B: INSTANT JOB NOTIFICATIONS

Goal: a consultant knows about a new role within seconds of it being
added, without refreshing. Uses Supabase Realtime, which works with
the existing anon key and needs no server.

### Prerequisite (user does once)
In Supabase dashboard: Database > Replication > enable the roles
table (and submissions if we extend later) for Realtime.

### Implementation
1. On app load after login, subscribe:
   sb.channel('roles-feed').on('postgres_changes',
   {event:'INSERT', schema:'public', table:'roles'}, handler)
   .subscribe()
2. Handler (ignore events caused by this same session):
   - Add the role to in-memory state and re-render Job Board if open
   - Show a HIGH-VISIBILITY toast, distinct style from normal toasts:
     "NEW ROLE: {ward} RN at {facility}, starts {date}" with two
     buttons: View Role, and Matches (opens candidates list filtered
     to matching nurse_type + state + compliance >= 80%)
   - Toast persists 15s or until dismissed, and stacks if several
     arrive
   - Increment a NEW badge on the Job Board sidebar item, clears when
     the Job Board is visited
   - Play a short subtle notification sound (single tone, generated
     via WebAudio, no audio file dependency), respecting a per-user
     mute toggle stored in users table
3. Browser desktop notifications: on first login, request Notification
   permission. If granted, also fire a desktop notification for new
   roles so consultants see it even when the CRM tab is not focused.
   Clicking it focuses the tab and opens the role.
4. Job Board: new roles carry a NEW chip for 24h after created_at.
5. Reconnect handling: on channel disconnect, resubscribe with
   backoff, and on resubscribe do a silent refetch of roles so
   nothing is missed while offline.

### Out of scope for now (needs backend, note for later)
Email/SMS notifications require a Supabase Edge Function. Worth doing
before real rollout, not needed for demo.

---

## FEATURE C: FLOW POLISH PUNCH LIST

Targeted friction removal, in addition to Stage 5's items.

1. OPTIMISTIC UI everywhere: status changes, toggles, and small edits
   update the screen instantly, then confirm with the DB behind the
   scenes, rolling back with an error toast on failure. No visible
   wait for routine actions.
2. Full-row click targets: any list row opens its record when clicked
   anywhere on the row, not just on the name link. Buttons inside
   rows keep stopPropagation.
3. Back preserves context: returning from a candidate to the
   Candidates list restores scroll position and active filters.
4. Enter-to-save in single-field edits, Esc cancels any open modal or
   inline editor.
5. Sticky table headers on all long lists.
6. Recently viewed: last 5 records visited, accessible from the top
   bar, one click to jump back.
7. Every modal and flow can be driven start to finish by keyboard:
   tab order sane, focus moves into modals on open and back on close.
8. Consistent destructive-action pattern: delete anything = same
   confirm dialog style, red confirm button, names the thing being
   deleted.

Acceptance for C: a consultant can work a phone call (find record,
update status, log note) without touching the mouse, and nothing in
routine use ever shows a perceptible save delay.
