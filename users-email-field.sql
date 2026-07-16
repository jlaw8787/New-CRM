-- Auth stage 1 of 5: adds an email address to users, in preparation for
-- real Supabase Auth (see PHASE2-BRIEF.md). Nullable, no backfill —
-- existing users default to blank. This does not touch auth, RLS, or the
-- profile-picker login; email is not yet read by any login path, it is
-- only wired into the existing user edit form (Settings > Add/Edit user).
ALTER TABLE users ADD COLUMN IF NOT EXISTS email text;
