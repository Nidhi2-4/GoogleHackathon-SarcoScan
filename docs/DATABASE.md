# Database

Owner: Anish. Last updated: 2026-10-12.

PostgreSQL. Status: eight tables are defined in `backend/models.py`, tested on SQLite, and created on the team's development database (PostgreSQL 17 on Supabase), where the audit triggers were checked.

The spec defines 14 tables (pages 14 to 20). The hackathon build has 8 of them (`refresh_tokens` was removed on 2026-10-12 and is dropped at startup); `reports` comes with PDF reports. Columns below follow the spec unless a note says otherwise.

## Rules for every table

- Primary keys are UUIDs, except `audit_logs`, which uses a big serial.
- Timestamps are stored in UTC.
- Files are never stored in the database. A `*_storage_key` column holds a key from `backend/storage.py`: a file name in `backend/uploads/` on a laptop, or `sarcoscan/<name>` on Cloudinary when hosted.
- BMI is computed on the server: `weight_kg / (height_cm / 100) ** 2`.

## Tables to build first

### users

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| name | VARCHAR | |
| email | VARCHAR, UNIQUE | |
| password_hash | VARCHAR | argon2 |
| role | ENUM(admin, doctor, technician) | `technician` is retired: kept so old rows load, switched off at startup, cannot be created. Spec also has `patient`, added with patient login |
| is_active | BOOLEAN | |
| created_at, last_login_at | TIMESTAMP | |

### patients

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| mrn | VARCHAR | hospital record number |
| abha_id | VARCHAR, nullable | |
| name | VARCHAR | encrypted in the application, see `SECURITY.md` section 8 |
| age | INT | the spec also allows a date of birth |
| sex | ENUM(male, female, other) | |
| height_cm, weight_kg | FLOAT | |
| phone | VARCHAR, nullable | encrypted in the application; optional |
| phone_hash | VARCHAR, nullable | HMAC of the phone number, for exact-match search |
| consent_given | BOOLEAN | |
| consent_at | TIMESTAMP | |
| created_by | UUID, FK to users | |
| doctor_id | UUID, FK to users, indexed | the patient's doctor; only that doctor sees the record (admin reads all). Empty only for patients a non-doctor registered before 2026-10-10 |
| created_at | TIMESTAMP | |

### visits

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| patient_id | UUID, FK to patients | |
| performed_by | UUID, FK to users | |
| visit_date | TIMESTAMP | |
| status | ENUM(draft, in_progress, analyzed, reviewed, reported) | |
| bmi | FLOAT | computed |
| notes | TEXT | |
| sarcf_score | INT, nullable | 0 to 10 |
| chair_stand_5_sec | FLOAT, nullable | |
| calf_circumference_cm | FLOAT, nullable | |
| waist_cm | FLOAT, nullable | input of the muscle-mass model |
| arm_circ_cm | FLOAT, nullable | input of the muscle-mass model |
| history_json | TEXT, nullable | medical-history answers as JSON; empty when not asked |

The last three columns are the spec's `clinical_inputs` table. It is one-to-one with a visit, so it is folded in here.

### grip_measurements

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| visit_id | UUID, FK to visits | |
| hand | ENUM(left, right) | |
| trial_no | INT | 1 to 3 |
| value_kg | FLOAT | |
| is_best | BOOLEAN | one per hand per visit |
| source | ENUM(manual, simulated) | spec also has `ble`; dropped with Bluetooth |
| captured_at | TIMESTAMP | |

### xray_studies

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| visit_id | UUID, FK to visits | |
| source | not built | every study is an upload until Orthanc is added |
| storage_key | VARCHAR | key from `backend/storage.py` |
| laterality | ENUM(left, right, unknown) | |
| qc_passed | BOOLEAN | |
| qc_reason | VARCHAR | why the quality check failed |
| uploaded_at | TIMESTAMP | |

### analysis_results

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| visit_id | UUID, FK to visits | |
| xray_id | UUID, FK to xray_studies | |
| model_version | VARCHAR | a plain label for now; the spec's `model_versions` table comes later |
| mask_storage_key | VARCHAR, nullable | segmentation mask |
| overlay_storage_key | VARCHAR, nullable | overlay image |
| gradcam_storage_key | VARCHAR, nullable | |
| thigh_soft_to_bone | FLOAT, nullable | |
| calf_soft_to_bone | FLOAT, nullable | |
| soft_to_plateau | FLOAT, nullable | |
| soft_area_ratio | FLOAT, nullable | |
| cortical_index | not built | add if the model produces it |
| kl_grade | INT, nullable | 0 to 4, bonus output |
| sarcopenia_prob | FLOAT, nullable | stays empty while the stage comes from rules; see `ML.md` |
| low_muscle, low_muscle_prob | BOOLEAN, FLOAT, nullable | from the muscle-mass model in `ml/tabular.py` |
| bone_loss, bone_loss_prob | BOOLEAN, FLOAT, nullable | from the bone-loss model in `ml/tabular.py` |
| sarcopenia_stage | ENUM(none, possible, probable, severe) | |
| osteoporosis_prob | FLOAT, nullable | empty until a model is connected |
| osteoporosis_tier | ENUM(low, moderate, high), nullable | empty until a model is connected |
| inference_ms | INT | |
| created_at | TIMESTAMP | |

One X-ray can have several result rows (reruns with a newer model).

### audit_logs

| Column | Type | Notes |
|---|---|---|
| id | BIGSERIAL, PK | |
| user_id | UUID, FK to users | |
| action | VARCHAR | VIEW, CREATE, UPDATE, DOWNLOAD, LOGIN |
| entity_type | VARCHAR | for example `patient`, `visit`, `xray` |
| entity_id | UUID | |
| ip_address | VARCHAR | |
| created_at | TIMESTAMP | |

This table is append-only: database triggers reject UPDATE, DELETE, and TRUNCATE (`SECURITY.md` section 6). Rows hold ids, never patient names.

### doctor_reviews

| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| visit_id | UUID, FK to visits | |
| doctor_id | UUID, FK to users | |
| final_stage | ENUM(none, possible, probable, severe) | the system's stage when the doctor agrees |
| agrees_with_ai | BOOLEAN | |
| notes | TEXT, nullable | |
| reviewed_at | TIMESTAMP | |

Each review is a new row. The system's result in `analysis_results` is never changed by a review.

## Tables added with their feature

| Table | Add when | Columns |
|---|---|---|
| `reports` | PDF reports are built | id, visit_id, pdf_storage_key, generated_by, generated_at (spec also has `fhir_json`) |

## Tables left out of the hackathon build

| Table | Why |
|---|---|
| `hospitals` | One hospital in the demo. Adding it later means a `hospital_id` column on users and patients. |
| `clinical_inputs` | Folded into `visits`. |
| `devices` | Bluetooth dynamometer removed in spec v2. |
| `model_versions` | Replaced by the `model_version` text column for now. |

## Relationships

- patients 1 to many visits
- visits 1 to many grip_measurements (up to 6: three trials per hand)
- visits 1 to many xray_studies
- xray_studies 1 to many analysis_results
- users 1 to many visits (`performed_by`), audit_logs

## Indexes

- `patients(mrn)`, `patients(phone_hash)`
- `visits(patient_id, visit_date DESC)`
- `grip_measurements(visit_id)`
- `audit_logs(user_id, created_at)`

## Known gaps

- Patient `name` and `phone` are encrypted columns, so name search happens in the application, not in SQL. It reads every patient row, which is fine for a demo and too slow for thousands of patients.
- There are no migrations. `upgrade_schema()` in `backend/db.py` runs at startup: it makes the phone columns optional (they became optional after the first tables were created), switches on row-level security for every table on PostgreSQL (see `SECURITY.md`, "Supabase's REST API"), and adds new nullable columns to existing databases.
- The development database is reached through a connection pooler, so prepared statements are turned off in `backend/db.py`.
- Tables are created at startup. Changing a column means dropping and recreating the table, which is acceptable only while the data is throwaway.
