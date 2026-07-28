-- Facility and ward notes
-- Written 28 July 2026. NOT YET RUN.
--
-- Creates one new table, facility_notes. It does not touch, move or delete
-- anything that already exists. Nothing on facilities, wards, activity or any
-- other table is read, changed or dropped by this script.
--
-- WHAT A NOTE HOLDS
--   which facility it belongs to
--   which ward it was written on, or nothing if it was written on the facility
--   the text
--   the reason, one of six fixed values
--   who wrote it, by name and by user id
--   when it was written
--
-- WHY THE WARD IS A NAME AND NOT A WARD ID
-- The facility editor deletes every ward row for a facility and inserts them
-- all again each time it saves, so ward ids change on every save. A note
-- pointing at a ward id would be silently orphaned the first time anyone
-- edited that facility. Roles, submissions and contracts already reference
-- wards by name for the same reason, so this matches the rest of the app.
-- When real ward ids arrive (open item 3 on the list) this column can be
-- backfilled to a ward_id then, in one pass, with the names still there to
-- match on.
--
-- EXPECTED RESULT: 1 new empty table. 0 rows. Nothing else changes.
--
-- Run the steps in order. Step 1 only reads.


-- ===========================================================================
-- STEP 1. Check the table does not already exist. Read only.
-- Expect 0 rows back. If it returns a row, stop, the table is already there.
-- ===========================================================================

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name = 'facility_notes';


-- ===========================================================================
-- STEP 2. Create the table. This is the only step that writes.
--
-- The reason CHECK is what stops a reason ever being free text. Adding a
-- seventh reason later means changing that constraint on purpose, which is
-- the point.
--
-- ON DELETE CASCADE: deleting a facility deletes its notes with it, the same
-- rule facility_contacts already uses.
--
-- author_id has no foreign key to users deliberately. The activity table
-- stores author_id the same loose way, and a note must still be readable if
-- the user record behind it is ever removed. The author name is stored
-- alongside it so a note always says who wrote it.
-- ===========================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS facility_notes (
  id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  facility_id bigint NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  ward_name   text,
  reason      text NOT NULL,
  body        text NOT NULL,
  author      text NOT NULL,
  author_id   bigint,
  created_at  timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT facility_notes_reason_check CHECK (reason IN (
    'Rate',
    'Complaint or issue',
    'Extension',
    'Staffing request',
    'Accommodation',
    'General'
  )),
  CONSTRAINT facility_notes_body_not_blank CHECK (btrim(body) <> '')
);

-- Newest first for one facility, which is every read the panel does.
CREATE INDEX IF NOT EXISTS facility_notes_facility_created_idx
  ON facility_notes (facility_id, created_at DESC);

-- Ward lookups within a facility.
CREATE INDEX IF NOT EXISTS facility_notes_facility_ward_idx
  ON facility_notes (facility_id, ward_name);

ALTER TABLE facility_notes ENABLE ROW LEVEL SECURITY;

-- Same anon_all policy every other table in this app uses. Login is still a
-- profile picker, so the app reaches Supabase as anon. Delete is restricted to
-- the note's author in the app, not here. When real auth lands this policy is
-- where that rule gets enforced properly.
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE
    tablename = 'facility_notes' AND policyname = 'anon_all') THEN
    CREATE POLICY "anon_all" ON facility_notes FOR ALL TO anon
      USING (true) WITH CHECK (true);
  END IF;
END $$;

COMMIT;


-- ===========================================================================
-- STEP 3. Check what landed. Read only.
-- Expect 7 rows, one per column, in this order:
--   id, facility_id, ward_name, reason, body, author, author_id, created_at
-- (8 rows, counting created_at.)
-- ===========================================================================

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'facility_notes'
ORDER BY ordinal_position;

-- Expect 0 rows. The table starts empty.
SELECT COUNT(*) AS notes_now FROM facility_notes;

-- Expect 1 row, policyname = anon_all.
SELECT policyname, cmd FROM pg_policies WHERE tablename = 'facility_notes';


-- ===========================================================================
-- TO UNDO, if you need to. Removes the table and everything in it.
-- Nothing else was changed by this script, so this puts things back exactly
-- as they were. Only safe while there are no notes you want to keep.
-- ===========================================================================

-- DROP TABLE IF EXISTS facility_notes;
