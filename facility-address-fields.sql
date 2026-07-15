-- Adds a physical address to facilities, mirroring the existing
-- address / address_suburb / address_postcode split already used on
-- candidates (see candidate-fields.sql). All nullable, no backfill —
-- existing facilities default to blank and the contract PDF generator
-- falls back to region/state when address is empty.
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS address text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS address_suburb text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS address_postcode text;
