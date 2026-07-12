-- ============================================================
-- COMPLIANCE PACKS - QLD DEMO SEED (Central QLD HHS focus)
-- Built from Contract_Specific_Paperwork_Requirements.xlsx (QLD tab).
-- Cascade model: STATE (all QLD) -> HEALTH SERVICE (Central QLD HHS)
--                -> FACILITY/WARD exceptions.
-- Live facility used: Emerald Hospital (id 6, health_authority = 'Central QLD HHS').
-- Safe to re-run: deletes existing QLD rows first, then re-inserts.
-- ============================================================

-- Clean slate for QLD so re-running doesn't duplicate.
DELETE FROM compliance_requirements WHERE state = 'QLD';

-- ---------- STATE-WIDE (applies to EVERY QLD facility) ----------
INSERT INTO compliance_requirements
  (state, level, scope_name, facility_id, ward, item_key, item_label, timing, delivery, required, exception_note, confirmed, source_last_updated, created_by)
VALUES
  ('QLD','state','Queensland',NULL,NULL,'ahpra','AHPRA registration','on_submission','zip',true,NULL,true,'2024-04-30','Seed'),
  ('QLD','state','Queensland',NULL,NULL,'photo_id','Photo ID (passport / licence)','on_submission','zip',true,NULL,true,'2024-04-30','Seed'),
  ('QLD','state','Queensland',NULL,NULL,'references','References (1 in last 3 months, 2nd in last 12 months)','before_commencing','zip',true,'Must be on file prior to commencement, not forwarded to facility',true,'2024-04-30','Seed'),
  ('QLD','state','Queensland',NULL,NULL,'immunisations','Immunisations: Hep B, MMR (pre-1966/serology/doses), Varicella, Pertussis','on_submission','zip',true,NULL,true,'2024-04-30','Seed');

-- ---------- CENTRAL QLD HHS (applies to Central QLD facilities, incl. Emerald id 6) ----------
INSERT INTO compliance_requirements
  (state, level, scope_name, facility_id, ward, item_key, item_label, timing, delivery, required, exception_note, confirmed, source_last_updated, created_by)
VALUES
  ('QLD','health_service','Central QLD HHS',NULL,NULL,'cpds','CPDs - BLS, CTP (n/a Mental Health), Fire, Hand Hygiene, Manual Handling, OVA, Cultural Competence, Infection Prevention, Mandatory Report, Code of Conduct, Cyber Security, Fraud Control, Domestic & Family Violence, WHS Induction','on_submission','zip',true,NULL,true,'2024-04-30','Seed'),
  ('QLD','health_service','Central QLD HHS',NULL,NULL,'converter_letter_note','Note: non-converter doctors letters are NOT accepted','before_commencing','individual',true,'Policy note for Central QLD HHS',true,'2024-04-30','Seed');

-- ---------- FACILITY / WARD EXCEPTIONS (the cascade showpiece) ----------
-- Ward-level: Mental Health wards anywhere in Central QLD need a driver's licence.
INSERT INTO compliance_requirements
  (state, level, scope_name, facility_id, ward, item_key, item_label, timing, delivery, required, exception_note, confirmed, source_last_updated, created_by)
VALUES
  ('QLD','ward','Central QLD HHS',NULL,'Mental Health','mh_drivers_licence','Driver''s licence (Mental Health placements only)','on_submission','zip',true,'Mental Health only',true,'2024-04-30','Seed');

-- Facility-name exceptions (scope_name based; these facilities aren't in the live
-- table yet, but the rows demonstrate the exception model and can be shown in the demo).
INSERT INTO compliance_requirements
  (state, level, scope_name, facility_id, ward, item_key, item_label, timing, delivery, required, exception_note, confirmed, source_last_updated, created_by)
VALUES
  ('QLD','facility','Woorabinda',NULL,NULL,'woorabinda_hepa','Hep A (serology or doses)','on_submission','zip',true,'Woorabinda only',true,'2024-04-30','Seed'),
  ('QLD','facility','Woorabinda',NULL,NULL,'woorabinda_ndis','NDIS Worker Screening','before_commencing','zip',true,'Woorabinda only',true,'2024-04-30','Seed'),
  ('QLD','facility','Capricornia Correctional Centre',NULL,NULL,'capr_qcs','QCS Criminal History Check (all nurses)','before_commencing','individual',true,'Capricornia Correctional Centre only. 2-6 week processing time',true,'2024-04-30','Seed'),
  ('QLD','facility','Capricornia Correctional Centre',NULL,NULL,'capr_nz_vetting','NZ Police Vetting Form (NZ nurses)','before_commencing','individual',true,'Capricornia Correctional Centre only, NZ-trained nurses',true,'2024-04-30','Seed');

-- ---------- EMERALD-SPECIFIC (attached to the real live facility id 6) ----------
-- A facility-level row bound to the actual Emerald Hospital row, so the demo can
-- show a requirement resolving via a real facility_id, not just scope_name.
INSERT INTO compliance_requirements
  (state, level, scope_name, facility_id, ward, item_key, item_label, timing, delivery, required, exception_note, confirmed, source_last_updated, created_by)
VALUES
  ('QLD','facility','Emerald Hospital',6,NULL,'emerald_orientation','Facility orientation booking confirmation','before_commencing','individual',true,'Emerald Hospital only',true,'2024-04-30','Seed');
