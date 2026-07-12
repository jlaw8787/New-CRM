-- HCA CRM MIGRATIONS July 2026

ALTER TABLE users ADD COLUMN IF NOT EXISTS phone text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS title text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS region_focus text[] DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;
ALTER TABLE users ADD COLUMN IF NOT EXISTS supabase_auth_id uuid;
ALTER TABLE users ADD COLUMN IF NOT EXISTS pin_hash text;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at timestamptz;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_mode text;

ALTER TABLE facilities ADD COLUMN IF NOT EXISTS health_authority text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS preferred_status boolean DEFAULT false;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS remote_loading_applies boolean DEFAULT false;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS remote_loading_pct numeric DEFAULT 0;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS accommodation_provided boolean DEFAULT false;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS accommodation_type text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS car_required boolean DEFAULT false;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS submission_email text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS secondary_contact_name text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS secondary_contact_email text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS secondary_contact_phone text;
ALTER TABLE facilities ADD COLUMN IF NOT EXISTS notes_candidate text;

ALTER TABLE wards ADD COLUMN IF NOT EXISTS ward_code text;
ALTER TABLE wards ADD COLUMN IF NOT EXISTS emr_system text;
ALTER TABLE wards ADD COLUMN IF NOT EXISTS min_experience_years int;
ALTER TABLE wards ADD COLUMN IF NOT EXISTS is_active boolean DEFAULT true;

ALTER TABLE submissions ADD COLUMN IF NOT EXISTS role_id bigint;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submitted_by bigint REFERENCES users(id);
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS follow_up_date date;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS checklist_snapshot jsonb;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS facility_response_date date;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS facility_response_notes text;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS outcome_notes text;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submission_package_text text;

ALTER TABLE contracts ADD COLUMN IF NOT EXISTS submission_id bigint;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS role_id bigint;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS contract_number text;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS extension_count int DEFAULT 0;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS total_contract_value numeric;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS weekly_hours numeric;

ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS category text DEFAULT 'Other';
ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS item_label text;
ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS status text DEFAULT 'Not Started';
ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS verified_by text;
ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS verified_at timestamptz;
ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS is_required boolean DEFAULT true;
ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS document_url text;
ALTER TABLE compliance_items ADD COLUMN IF NOT EXISTS document_id bigint;

ALTER TABLE activity ADD COLUMN IF NOT EXISTS entity_type text DEFAULT 'candidate';
ALTER TABLE activity ADD COLUMN IF NOT EXISTS entity_id bigint;
ALTER TABLE activity ADD COLUMN IF NOT EXISTS author_id bigint;
ALTER TABLE activity ADD COLUMN IF NOT EXISTS metadata jsonb;

CREATE TABLE IF NOT EXISTS documents (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  candidate_id bigint REFERENCES candidates(id) ON DELETE CASCADE,
  facility_id bigint REFERENCES facilities(id) ON DELETE CASCADE,
  contract_id bigint REFERENCES contracts(id) ON DELETE SET NULL,
  compliance_item_id bigint REFERENCES compliance_items(id) ON DELETE SET NULL,
  submission_id bigint REFERENCES submissions(id) ON DELETE SET NULL,
  uploaded_by text,
  file_name text NOT NULL,
  file_url text NOT NULL,
  file_size bigint,
  file_type text,
  category text DEFAULT 'Other',
  description text,
  is_current boolean DEFAULT true,
  expires_at date,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all" ON documents;
CREATE POLICY "anon_all" ON documents FOR ALL TO anon USING (true) WITH CHECK (true);

CREATE TABLE IF NOT EXISTS facility_contacts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  facility_id bigint NOT NULL REFERENCES facilities(id) ON DELETE CASCADE,
  name text NOT NULL,
  title text,
  email text,
  phone text,
  is_primary boolean DEFAULT false,
  is_submission_contact boolean DEFAULT false,
  notes text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE facility_contacts ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "anon_all" ON facility_contacts;
CREATE POLICY "anon_all" ON facility_contacts FOR ALL TO anon USING (true) WITH CHECK (true);

-- PHASE 3 FEATURE 2: 24h/48h submission follow-ups
CREATE TABLE IF NOT EXISTS submission_followups (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  submission_id bigint REFERENCES submissions(id) ON DELETE CASCADE,
  candidate_id bigint REFERENCES candidates(id) ON DELETE CASCADE,
  due_at timestamptz NOT NULL,
  label text DEFAULT '24h chase',
  status text DEFAULT 'Pending',
  completed_at timestamptz,
  completed_by text,
  notes text,
  created_at timestamptz DEFAULT now()
);
ALTER TABLE submission_followups ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE
    tablename='submission_followups' AND policyname='anon_all') THEN
    CREATE POLICY "anon_all" ON submission_followups FOR ALL TO anon
      USING (true) WITH CHECK (true);
  END IF;
END $$;

-- PHASE 3: Accepted -> Contract flow
-- Submission-level expected dates (auto-copied from linked role, or
-- entered manually for ad-hoc submissions). Contract dates remain the
-- authoritative source once a contract exists.
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS start_date date;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS end_date date;

-- CONTRACT-EDIT-BRIEF Stage 1: field-level audit trail for contract edits.
-- One row per changed field (old value, new value, who, when), not a
-- single "was edited" note. changed_by is provisional until Phase 4 auth
-- lands (see CONTRACT-EDIT-BRIEF.md "Known limitation, accepted on purpose").
CREATE TABLE IF NOT EXISTS contract_audit (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  contract_id bigint REFERENCES contracts(id) ON DELETE CASCADE,
  field_name text NOT NULL,
  old_value text,
  new_value text,
  changed_by text,
  changed_at timestamptz DEFAULT now()
);
ALTER TABLE contract_audit ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE
    tablename='contract_audit' AND policyname='anon_all') THEN
    CREATE POLICY "anon_all" ON contract_audit FOR ALL TO anon
      USING (true) WITH CHECK (true);
  END IF;
END $$;

-- PLACEMENT-SETUP-BRIEF Stage 0 (per explicit instruction; brief file not
-- present in the repo at time of writing — this migration reflects exactly
-- the columns specified in chat, nothing more).
ALTER TABLE flights ADD COLUMN IF NOT EXISTS status text;
ALTER TABLE accommodation ADD COLUMN IF NOT EXISTS status text;
ALTER TABLE car_hire ADD COLUMN IF NOT EXISTS status text;
ALTER TABLE accommodation ADD COLUMN IF NOT EXISTS subsidy_type text;
ALTER TABLE accommodation ADD COLUMN IF NOT EXISTS subsidy_amount numeric;

-- PLACEMENT-SETUP-BRIEF Stage 4B prep (per Stage 4B audit, 2026-07-11).
-- flights and accommodation already had doc_url/doc_added_by/doc_added_at;
-- car_hire had none of the three, expenses had doc_url only. This brings
-- all four tables to the same shape. All nullable, no identity ids touched.
ALTER TABLE car_hire ADD COLUMN IF NOT EXISTS doc_url text;
ALTER TABLE car_hire ADD COLUMN IF NOT EXISTS doc_added_by text;
ALTER TABLE car_hire ADD COLUMN IF NOT EXISTS doc_added_at timestamptz;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS doc_added_by text;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS doc_added_at timestamptz;

-- SUBMIT-FLOW-BRIEF Stage 2 prep: link table between submissions and the
-- existing documents table (not jsonb, unlike checklist_snapshot — a doc
-- attachment is a live reference to a first-class documents row that can
-- be reused across multiple submissions, not a frozen snapshot). Mirrors
-- the submission_followups link-table pattern already used for submissions.
CREATE TABLE IF NOT EXISTS submission_documents (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  submission_id bigint REFERENCES submissions(id) ON DELETE CASCADE,
  document_id bigint REFERENCES documents(id) ON DELETE CASCADE,
  added_by text,
  added_at timestamptz DEFAULT now(),
  UNIQUE(submission_id, document_id)
);
ALTER TABLE submission_documents ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE
    tablename='submission_documents' AND policyname='anon_all') THEN
    CREATE POLICY "anon_all" ON submission_documents FOR ALL TO anon
      USING (true) WITH CHECK (true);
  END IF;
END $$;
