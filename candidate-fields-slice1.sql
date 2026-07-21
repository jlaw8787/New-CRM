-- V2 Slice 1: candidate data capture (flex specialty, states open to, open-ended availability)
-- Additive only. Does not touch matchScore or any filter/matching logic (that's Slice 2).
-- DO NOT AUTO-RUN -- paste into the Supabase SQL editor by hand.

ALTER TABLE candidates ADD COLUMN IF NOT EXISTS primary_skill text;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS available_to date;
ALTER TABLE candidates ADD COLUMN IF NOT EXISTS states_open text[] DEFAULT '{}';

-- Optional backfill -- run separately, after the ALTERs above, only if you want it.
-- Sets primary_skill to each candidate's first clinical_skills entry, wherever
-- primary_skill is still unset and clinical_skills is non-empty. states_open is
-- intentionally left empty for existing candidates (fill later, per your call).
UPDATE candidates
SET primary_skill = clinical_skills[1]
WHERE primary_skill IS NULL
  AND clinical_skills IS NOT NULL
  AND array_length(clinical_skills, 1) > 0;
