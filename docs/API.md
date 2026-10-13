# API

Owner: Anish. Last updated: 2026-10-12.

All paths start with `/api/v1`. The endpoint list comes from the spec (pages 7 to 9), cut down to what the hackathon build needs.

This file lists which endpoints exist, who may call them, and how far along they are. It does not list request or response fields: when the backend is running, FastAPI's generated page at `/docs` shows those and is always current.

Status values: `planned`, `in progress`, `done`, `later` (after the demo flow works), `dropped`.

`done` here means: written, and passing the tests in `backend/tests/` on SQLite. The whole flow was also run through the web app, and the tables and audit triggers were created and checked on PostgreSQL 17.

Roles: D = doctor, A = admin. The role table in `SECURITY.md` is the source for these columns. A doctor reaches only their own patients (anything else is 404); an admin reads every patient and writes none.

## Auth

| Method | Path | Purpose | Who | Status |
|---|---|---|---|---|
| POST | `/auth/signup` | Name, email and password. Creates a doctor account and returns a login token. Open to anyone while this is a test build. | anyone | done |
| POST | `/auth/login` | Email and password. Returns a login token that lasts 7 days. | anyone | done |
| POST | `/auth/refresh`, `/auth/logout` | Refresh cookie. Removed on 2026-10-12: logging out is deleting the token in the browser. | | dropped |
| GET | `/auth/me` | Current user's profile and role. | logged in | done |

## Patients

| Method | Path | Purpose | Who | Status |
|---|---|---|---|---|
| POST | `/patients` | Register a patient; the doctor who registers becomes their doctor. Consent is required. A repeated MRN is refused. Phone is optional. | D | done |
| GET | `/patients` | List, or search with `?q=` by name, MRN, or full phone number. | D, A | done |
| GET | `/patients/{id}` | Patient details. | D, A | done |
| PATCH | `/patients/{id}` | Update details. | D, A | later |
| GET | `/patients/{id}/history` | All visits with best grip, stage, and risk tier. | D, A | done |

Name and phone are encrypted in the database (`SECURITY.md` section 8). Phone search is an exact match on the number; name and MRN match on any part.

## Visits and screening

| Method | Path | Purpose | Who | Status |
|---|---|---|---|---|
| POST | `/patients/{id}/visits` | Start a screening visit. BMI is worked out here. | D | done |
| GET | `/visits` | Recent visits with their results, newest first. Used by the dashboard and the reports list. | D, A | done |
| GET | `/visits/{id}` | Visit summary. | D, A | done |
| POST | `/visits/{id}/clinical-inputs` | SARC-F, chair stand, calf circumference. | D | done |
| POST | `/visits/{id}/grip` | Up to three readings per hand. Marks the best per hand and compares with the cutoff. Sending again replaces the earlier readings. | D | done |
| POST | `/visits/{id}/xray` | Upload the X-ray (multipart field `file`). PNG or JPG only for now. Runs the quality check. | D | done |
| POST | `/visits/{id}/analyze` | Run the analysis and store the result. Needs an X-ray that passed the quality check. | D | done |
| GET | `/visits/{id}/result` | Inputs, cutoffs, stage, risk, and the doctor's review if there is one. | D, A | done |
| POST | `/visits/{id}/review` | Doctor agrees or sets the final stage, with notes. | D | done |
| GET | `/visits/{id}/status` | Poll analysis status. Only needed if analysis moves to a queue. | D, A | later |

About "model not connected": `ml/predict.py` is not in the repo yet. Until it is, analyze stores the sarcopenia stage from the rule (grip and chair stand only) and leaves every image-based field empty. The result says `model_connected: false`. No value is invented.

The quality check looks at size, shape, colour, and contrast. It rejects colour photos, logos, and blank images. A greyscale photo or an X-ray of another body part still passes; recognising a knee AP view needs a trained check.

Patient ranges: age 18 to 120, height 120 to 220 cm, weight 25 to 250 kg.

`clinical-inputs` also takes `waist_cm`, `arm_circ_cm`, and `history` (an object of yes or no answers; the allowed keys are `HISTORY_QUESTIONS` in `backend/analysis.py`; leave it out when the patient was not asked). The result adds `low_muscle`, `low_muscle_prob`, `bone_loss`, and `bone_loss_prob`, all empty when `ml/tabular.py` cannot load. `/health` reports `model_connected` (X-ray models) and `tabular_connected`.

## Files

These two are not in the spec. They exist because X-rays sit on local disk and must never be reachable without a login.

| Method | Path | Purpose | Who | Status |
|---|---|---|---|---|
| GET | `/xrays/{id}/image` | The uploaded X-ray. | D, A | done |
| GET | `/xrays/{id}/overlay` | The overlay image from the analysis. 404 until the model writes one. | D, A | done |

A browser `<img>` tag cannot send the `Authorization` header. The UI fetches these with the header and shows the result as a blob.

## Reports

| Method | Path | Purpose | Who | Status |
|---|---|---|---|---|
| POST | `/visits/{id}/report` | Generate the PDF. | D | later |
| GET | `/reports/{id}/download` | Download the PDF. | D, A | later |
| GET | `/reports/{id}/fhir` | FHIR DiagnosticReport. | D, A | dropped for the hackathon |

## Admin and other

| Method | Path | Purpose | Who | Status |
|---|---|---|---|---|
| GET | `/audit-logs` | Audit trail, newest first. | A | done |
| GET | `/health` | Says the API is up and whether an ML model is connected. | anyone | done |
| GET | `/users` | List staff accounts. | A | done |
| POST | `/users` | Create a staff account (name, email, role, password). The only way to make an admin; doctors can also use `/auth/signup`. | A | done |
| PATCH | `/users/{id}` | Switch an account on or off (`is_active`). Switching off takes effect on that person's next request. An admin cannot switch off their own account. | A | done |
| GET, HEAD | `/ping` | For uptime monitors: answers `{"status":"ok"}` without touching the database or the models. | anyone | done |
| POST, GET, PATCH, DELETE | `/users` | Manage users. `python -m backend.seed` creates the first admin and doctor. Role is `doctor` or `admin`. | A | later |
| GET | `/stats/overview` | Dashboard numbers. | D, A | later |
| GET, POST | `/devices` | Grip devices. | A | dropped (Bluetooth removed in spec v2) |
| POST | `/integrations/orthanc/webhook` | New study from Orthanc. | system | dropped for the hackathon |

## Conventions

- Requests and responses are JSON, except the X-ray upload (multipart) and file downloads.
- Every call except signup, login, health, and ping carries `Authorization: Bearer <login token>`.
- Errors use FastAPI's default error body and these status codes:

| Code | Meaning |
|---|---|
| 401 | Not logged in, or the login token expired |
| 403 | Logged in, but the role is not allowed |
| 404 | No such record |
| 409 | The action does not fit the current state: repeated MRN or email, or analyze before a usable X-ray exists |
| 413 | Upload larger than 50 MB |
| 415 | Upload is not a readable PNG or JPG (DICOM is refused for now) |
| 422 | Input failed validation, or consent is missing |
| 502 | The X-ray could not be saved: file storage (Cloudinary) refused it |
| 500 | The analysis failed; the message tells the user to retry or upload another image |

- Every endpoint that reads or writes patient data writes a row to `audit_logs`.
- The patient role (read own report only) is in the spec but not in the hackathon build. Only staff roles log in.
