-- Facility contacts migration
-- Written 28 July 2026. NOT YET RUN.
--
-- Decision: facility_contacts becomes the single source of truth for facility
-- contacts. The contact_name, contact_email and contact_phone columns on the
-- facilities table are retired.
--
-- This script copies the old values into facility_contacts so nothing is lost.
-- It does NOT delete or null anything on the facilities table. The old columns
-- are left exactly as they are, so this is reversible by deleting the inserted
-- rows (step 4 below shows how).
--
-- EXPECTED RESULT: 16 rows inserted, 0 of them marked primary.
--
-- Why 0 primary: all 16 facilities that carry an old contact already have at
-- least one facility_contacts row, and every one of those already has a primary.
-- The primary rule is still written into the insert so it behaves correctly if
-- that ever stops being true.
--
-- Run the steps in order. Step 1 and step 2 only read, they change nothing.


-- ===========================================================================
-- STEP 1. Preview. Read only. This is exactly what step 3 will insert.
-- Expect 16 rows back.
-- ===========================================================================

SELECT
  f.id                                                  AS facility_id,
  f.name                                                AS facility_name,
  NULLIF(TRIM(COALESCE(f.contact_name, '')),  '')       AS will_insert_name,
  NULLIF(TRIM(COALESCE(f.contact_email, '')), '')       AS will_insert_email,
  NULLIF(TRIM(COALESCE(f.contact_phone, '')), '')       AS will_insert_phone,
  NOT EXISTS (
    SELECT 1 FROM facility_contacts fc WHERE fc.facility_id = f.id
  )                                                     AS will_be_primary
FROM facilities f
WHERE (
     NULLIF(TRIM(COALESCE(f.contact_name, '')),  '') IS NOT NULL
  OR NULLIF(TRIM(COALESCE(f.contact_email, '')), '') IS NOT NULL
  OR NULLIF(TRIM(COALESCE(f.contact_phone, '')), '') IS NOT NULL
)
ORDER BY f.name;


-- ===========================================================================
-- STEP 2. Count check. Read only.
-- Expect: to_insert = 16, of_those_primary = 0
-- ===========================================================================

SELECT
  COUNT(*) AS to_insert,
  COUNT(*) FILTER (
    WHERE NOT EXISTS (SELECT 1 FROM facility_contacts fc WHERE fc.facility_id = f.id)
  ) AS of_those_primary
FROM facilities f
WHERE (
     NULLIF(TRIM(COALESCE(f.contact_name, '')),  '') IS NOT NULL
  OR NULLIF(TRIM(COALESCE(f.contact_email, '')), '') IS NOT NULL
  OR NULLIF(TRIM(COALESCE(f.contact_phone, '')), '') IS NOT NULL
);


-- ===========================================================================
-- STEP 3. The migration. This is the only step that writes.
--
-- Every inserted row is marked with the note "migrated from facility record"
-- so you can find them all later and merge duplicates by hand.
--
-- The final NOT EXISTS guard means running this twice will not insert the
-- rows a second time. It is safe to re-run.
-- ===========================================================================

BEGIN;

INSERT INTO facility_contacts (
  facility_id, name, title, email, phone, is_primary, is_submission_contact, notes
)
SELECT
  f.id,
  NULLIF(TRIM(COALESCE(f.contact_name, '')),  ''),
  NULL,
  NULLIF(TRIM(COALESCE(f.contact_email, '')), ''),
  NULLIF(TRIM(COALESCE(f.contact_phone, '')), ''),
  -- Primary only when this facility has no facility_contacts row at all.
  -- Evaluated before any of these inserts land, so an existing primary is
  -- never displaced and two rows are never both made primary.
  NOT EXISTS (
    SELECT 1 FROM facility_contacts fc WHERE fc.facility_id = f.id
  ),
  false,
  'migrated from facility record'
FROM facilities f
WHERE (
     NULLIF(TRIM(COALESCE(f.contact_name, '')),  '') IS NOT NULL
  OR NULLIF(TRIM(COALESCE(f.contact_email, '')), '') IS NOT NULL
  OR NULLIF(TRIM(COALESCE(f.contact_phone, '')), '') IS NOT NULL
)
AND NOT EXISTS (
  SELECT 1 FROM facility_contacts fc
  WHERE fc.facility_id = f.id
    AND fc.notes = 'migrated from facility record'
);

COMMIT;


-- ===========================================================================
-- STEP 4. Check what landed. Read only.
-- Expect 16 rows, all with is_primary = false.
-- ===========================================================================

SELECT
  fc.facility_id,
  f.name AS facility_name,
  fc.name,
  fc.email,
  fc.phone,
  fc.is_primary
FROM facility_contacts fc
JOIN facilities f ON f.id = fc.facility_id
WHERE fc.notes = 'migrated from facility record'
ORDER BY f.name;


-- Sanity check: no facility should have more than one primary contact.
-- Expect 0 rows back.

SELECT facility_id, COUNT(*) AS primaries
FROM facility_contacts
WHERE is_primary
GROUP BY facility_id
HAVING COUNT(*) > 1;


-- ===========================================================================
-- STEP 5. Review list for merging duplicates by hand.
-- Read only. Shows each facility's migrated contact next to its existing ones
-- so you can see which are the same person under a different name.
-- ===========================================================================

SELECT
  f.name AS facility_name,
  fc.name,
  fc.title,
  fc.email,
  fc.phone,
  fc.is_primary,
  CASE WHEN fc.notes = 'migrated from facility record'
       THEN 'MIGRATED' ELSE 'existing' END AS source
FROM facility_contacts fc
JOIN facilities f ON f.id = fc.facility_id
WHERE fc.facility_id IN (
  SELECT facility_id FROM facility_contacts
  WHERE notes = 'migrated from facility record'
)
ORDER BY f.name, source DESC, fc.name;


-- ===========================================================================
-- TO UNDO, if you need to. Deletes only the rows this script inserted.
-- Nothing on the facilities table was changed, so this puts things back
-- exactly as they were.
-- ===========================================================================

-- DELETE FROM facility_contacts WHERE notes = 'migrated from facility record';
