-- WA facility import — 3 new on-tender facilities
-- Source: Contract_Paperwork_Requirements_CLEAN.xlsx > Regions & Facilities (WA rows) + WA sheet + Facility Abbreviations
-- Off-tender WA locations (Derby, Halls Creek & Wyndham, KPHU, Meekatharra, Great Southern towns, Pilbara towns)
-- are deliberately NOT imported here — same "add when you take work there" approach as NSW/VIC/ACT.
-- Region/health_authority policy: matches the convention already live on Broome/Hedland/Kalgoorlie
-- (region = short WACHS region name, health_authority = "WACHS " + region), except the two ACCHS
-- facilities where health_authority is left NULL on purpose (not WACHS-administered) while region is
-- still set as a geographic label only, per Josh's confirmation.
-- DO NOT AUTO-RUN — paste into the Supabase SQL editor by hand and review before executing.

INSERT INTO facilities (name, state, region, type, health_authority, aliases)
VALUES
  ('Geraldton Hospital', 'WA', 'Midwest', 'Public', 'WACHS Midwest', ARRAY['GRH', 'Geraldton Regional Hospital']),
  ('Mawarnkarra Health Service', 'WA', 'Pilbara', 'NGO', NULL, ARRAY[]::text[]), -- ACCHS, not WACHS-administered; region is a geographic label only
  ('Spinifex Health Service - Paupiyala Tjarutja', 'WA', 'Goldfields', 'NGO', NULL, ARRAY[]::text[]) -- ACCHS, not WACHS-administered; region is a geographic label only
RETURNING id, name;
