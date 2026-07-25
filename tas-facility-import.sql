-- TAS facility import — 19 new facilities (Mersey Community Hospital, id 16, already exists — excluded)
-- Source: Contract_Paperwork_Requirements_CLEAN.xlsx > Regions & Facilities (TAS rows) + RHH Wards + Facility Abbreviations
-- Region/health_authority policy: only set where geographically confident; everything else left NULL
-- to avoid resolving compliance against the wrong health_service scope. See inline notes per row.
-- DO NOT AUTO-RUN — paste into the Supabase SQL editor by hand and review before executing.

WITH new_facilities AS (
  INSERT INTO facilities (name, state, region, type, health_authority, aliases)
  VALUES
    ('Beaconsfield & George Town District Hospitals', 'TAS', 'North TAS', 'Public', 'Tas Health North', ARRAY[]::text[]),
    ('Calvary - Lenah Valley Hospital', 'TAS', 'South TAS', 'Private', NULL, ARRAY[]::text[]), -- health_authority NULL: private operator (Calvary), not Tas Health-administered, even though geographically in Hobart
    ('Campbell Town Health Service', 'TAS', 'North TAS', 'Public', 'Tas Health North', ARRAY[]::text[]),
    ('Cape Barren Island Clinic', 'TAS', NULL, 'Public', NULL, ARRAY[]::text[]), -- NULL: Bass Strait island, administrative grouping genuinely uncertain
    ('CHaPS - Child Health and Parenting Service (Launceston)', 'TAS', 'North TAS', 'Public', 'Tas Health North', ARRAY['CHaPS']),
    ('Flinders Island', 'TAS', NULL, 'Public', NULL, ARRAY[]::text[]), -- NULL: Bass Strait island, administrative grouping genuinely uncertain
    ('Hobart Private', 'TAS', 'South TAS', 'Private', NULL, ARRAY[]::text[]), -- health_authority NULL: private hospital, not Tas Health-administered, even though geographically in Hobart
    ('King Island Hospital', 'TAS', 'North West TAS', 'Public', 'Tas Health NW', ARRAY[]::text[]),
    ('Launceston General Hospital', 'TAS', 'North TAS', 'Public', 'Tas Health North', ARRAY['LGH']),
    ('Mersey Leven Community Nursing', 'TAS', 'North West TAS', 'Public', 'Tas Health NW', ARRAY[]::text[]),
    ('North West Regional Hospital', 'TAS', 'North West TAS', 'Public', 'Tas Health NW', ARRAY['NWRH']),
    ('Northern Cancer Care', 'TAS', 'North TAS', 'Public', 'Tas Health North', ARRAY[]::text[]),
    ('Rosebery Community Health Centre', 'TAS', 'West Coast TAS', 'Public', 'Tas Health West Coast', ARRAY[]::text[]),
    ('Royal Hobart Hospital', 'TAS', 'South TAS', 'Public', 'Tas Health South', ARRAY['RHH']),
    ('SMHS - Statewide Mental Health Service', 'TAS', 'Statewide', 'Public', 'Tas Health Statewide', ARRAY['SMHS']),
    ('Smithton District Hospital', 'TAS', 'North West TAS', 'Public', 'Tas Health NW', ARRAY[]::text[]),
    ('St Helen''s District Hospital', 'TAS', NULL, 'Public', NULL, ARRAY[]::text[]), -- NULL: East Coast, administrative grouping genuinely uncertain
    ('St Mary''s Health Centre', 'TAS', NULL, 'Public', NULL, ARRAY[]::text[]), -- NULL: East Coast, administrative grouping genuinely uncertain
    ('West Coast District Hospital', 'TAS', 'West Coast TAS', 'Public', 'Tas Health West Coast', ARRAY[]::text[])
  RETURNING id, name
)
INSERT INTO wards (facility_id, name, nurse_types)
SELECT id, ward_name, ARRAY['RN']
FROM new_facilities
CROSS JOIN (VALUES
  ('K9 East'),
  ('K9 West'),
  ('K8 East'),
  ('K8 West'),
  ('2J'),
  ('K10 East'),
  ('K10 West'),
  ('3A RAMU'),
  ('2A General Medical'),
  ('4A Short Stay Suite'),
  ('Theatre (including Scrub Scout/Anaesthetics/PACU)'),
  ('9A Oncology'),
  ('Maternity'),
  ('6A - TASU')
) AS w(ward_name)
WHERE new_facilities.name = 'Royal Hobart Hospital';
