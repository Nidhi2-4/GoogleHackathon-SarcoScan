# Architecture

Owner: Anish, reviewed by everyone. Last updated: 2026-10-12.

Status: the backend and the web app work together end to end, hosted on Render (API) and Vercel (web app) with the database on Supabase. Four models are connected; the hosted API loads the two body-measurement models only (512 MB free plan, see `DEPLOY.md`).

The spec is `Documentation - SarcoScan (2).pdf` in this folder. Where this file and the spec differ, this file is the current plan, and the difference is listed under "What we build first".

## What the product does

A doctor registers a patient, enters handgrip trials and optional clinical inputs, and uploads a knee AP X-ray. The system returns a sarcopenia stage and an osteoporosis risk tier, with an overlay on the X-ray. The doctor reviews the result; each doctor sees only their own patients. It goes into a PDF report and into the patient's history, so later visits show a trend.

It is a screening and referral tool. It does not replace DEXA and does not prescribe treatment (spec page 1, Non-Goals).

## System overview

```
  Web (browser)      Mobile (PWA, later Capacitor)      Desktop (PWA, later Tauri)
        \                        |                          /
         \_______________ one Next.js UI __________________/
                                 |
                          HTTPS, /api/v1
                                 |
                     FastAPI backend  (backend/)
                    /            |             \
           PostgreSQL     Cloudinary           ml/predict.py, ml/tabular.py
           (records)      (X-rays, overlays)   + ml/models/ (same process)
```

Three rules hold the design together:

1. **One backend** holds all data, logic, and security checks. Clients keep nothing sensitive except a login session.
2. **One UI codebase.** Mobile and desktop are shells that open the same UI. Nobody writes a screen twice.
3. **The model is a Python function** called inside the backend process. There is no queue and no separate ML server.

## Parts

| Part | Folder | Tech | Owner | Status |
|---|---|---|---|---|
| Backend API | `backend/` | Python, FastAPI, SQLAlchemy, Pydantic | Anish | done for the demo flow |
| Database | SQLite file locally, Supabase when hosted | PostgreSQL 17 | Anish | done |
| File storage | `backend/storage.py` | Cloudinary when hosted (private, nothing on disk); `backend/uploads/` on a laptop | Anish | done |
| Model training | `ml/training/`, `ml/data/` | PyTorch, XGBoost | Pravesh | in progress |
| Model inference | `ml/predict.py`, `ml/tabular.py`, `ml/muscle.py`, `ml/models/` | Python | Pravesh | done: four models, called from `backend/analysis.py` |
| Web UI | `frontend/web/` | Next.js 16, TypeScript, Tailwind, jsPDF | Nidhi | done: wired to the API. PWA manifest left. |
| Mobile | the web app; notes in `MOBILE.md` | PWA install first, Capacitor shell later | Nidhi | planned. `frontend/mobile/` is an unused Expo template. |
| Desktop | the web app; notes in `DESKTOP.md` | PWA install first, Tauri shell later | Nidhi, Anish | planned |

## One screening, start to finish

1. **Login.** The user signs in, or creates a doctor account, and gets one login token (see `SECURITY.md`).
2. **Find or register the patient.** Search by name, phone, or MRN.
3. **Start a visit.**
4. **Clinical inputs (optional).** SARC-F score, 5-chair-stand time, calf circumference.
5. **Handgrip.** Three trials per hand, typed in by the doctor. The backend marks the best value and compares it with the AWGS 2019 cutoff: below 28 kg for men, below 18 kg for women.
6. **X-ray upload.** The backend validates the file, saves it to storage (Cloudinary when hosted), records it in `xray_studies`, and runs the quality check.
7. **Analyze.** The backend calls `ml/predict.py` (X-ray) and `ml/tabular.py` (body measurements), saves the overlay image, and stores a row in `analysis_results`.
8. **Results screen.** Stage, risk tier, overlay, and measured values next to their cutoffs.
9. **Doctor review.** Accept or override, with notes.
10. **Report.** PDF with inputs, cutoffs, overlay, and a disclaimer.
11. **Follow-up.** On a repeat visit the history graph shows grip, ratios, and risk over time.

## Web, mobile, and desktop

The spec plans a Next.js web app and a React Native mobile app. The team also wants a desktop app, which the spec does not mention. One frontend developer cannot maintain three codebases during a hackathon, so all three use the same UI:

| Stage | What it gives | Cost |
|---|---|---|
| 1. Responsive web UI | Works in desktop and phone browsers | Part of building the UI |
| 2. PWA manifest | "Install" on phones and desktops: own icon, own window | A manifest file and icons. Needs HTTPS. |
| 3. Shells (optional) | A real `.exe` installer (Tauri) and a real APK (Capacitor) that open the same UI | Small config projects in `desktop/` and `mobile/` |

Why no React Native: the only native-only feature in the spec was the Bluetooth dynamometer. Spec version 2 changed must-have item 7 to manual handgrip entry, so nothing needs native code. X-ray upload uses the browser's file picker, which offers the camera and gallery on a phone.

Why Tauri and not Electron for desktop: in Tauri the UI has no Node.js access and native APIs are off unless allowed one by one, so there is less to attack. Details in `SECURITY.md` and `FRONTEND.md`.

## What we build first

| In the spec | Hackathon build | Bring it back when |
|---|---|---|
| MinIO object storage | Local folder `backend/uploads/` | The system runs on more than one server |
| Celery and Redis queue | Analysis runs inside the request | Analysis takes more than a few seconds, or many users screen at once |
| Orthanc PACS, FHIR export | Not built | Spec Phase 2 |
| Nginx reverse proxy | Next.js forwards `/api` to the backend | On-prem install |
| React Native and Expo app | Responsive web, PWA, optional Capacitor shell | A feature needs native code |
| Bluetooth dynamometer and firmware | Manual entry (spec v2, item 7) | The hardware exists |
| 14 database tables | 9 tables (`DATABASE.md`) | A feature needs them |
| Alembic migrations | Tables created at startup | The schema changes after real data exists |
| Not in the spec | Desktop app (PWA, then Tauri) | |

## Where it runs

- **Local:** `npm run dev` runs the API and the web app on one machine with a SQLite file; `npm run setup` writes the `.env`.
- **Hosted demo:** API on Render (root directory `backend`), web app on Vercel (root directory `frontend/web`), PostgreSQL on Supabase. Steps and limits are in `DEPLOY.md`. The Vercel address has the HTTPS certificate that PWA install and the shells need.
- **One-command install:** a `docker-compose.yml` with three services (database, backend, web) is planned for milestone M3. It shows the on-prem story without MinIO, Redis, or a worker.
- **On-prem (the product story):** the same stack on a hospital server on the local network, with no internet needed (spec page 3).
- Target hardware from the spec: Intel i5, 16 GB RAM, no GPU, analysis under 5 seconds per study. This is a target; nothing has been measured yet.

## Decisions

| Date | Decision | Status |
|---|---|---|
| 2026-10-04 | PostgreSQL as the database | decided |
| 2026-10-04 | Handgrip is manual entry | decided (spec v2) |
| 2026-10-04 | Backend framework is FastAPI, the spec's choice, because the ML code is Python too | decided |
| 2026-10-04 | Files on local disk; a Cloudinary copy only for a hosted demo, free tier | replaced on 2026-10-10 |
| 2026-10-10 | Hosted: X-rays live only on Cloudinary (private, authenticated), nothing on the server's disk; the database stays on Supabase | decided by Anish |
| 2026-10-04 | The web app keeps its own look; the design canvas linked in `FRONTEND.md` is a reference | decided |
| 2026-10-04 | Development database on the Supabase free tier, reached through its pooler | decided by Anish |
| 2026-10-04 | The PDF report is made in the browser from the stored result | decided |
| 2026-10-04 | A result comes from an explicit Run screening action and is stored; it is not recalculated live as inputs change | decided |
| 2026-10-04 | One UI plus shells, not separate native apps | proposed; team confirms |
| 2026-10-04 | Tauri for the desktop shell | proposed |
| 2026-10-04 | Sarcopenia stage comes from AWGS-style rules until labelled data exists | proposed; see `ML.md` |
| 2026-10-04 | Patient name and phone encrypted in the application; audit log append-only | proposed; Anish owns security, see `SECURITY.md` |
| 2026-10-04 | Overlay shown as stacked images with a toggle, not as coordinates drawn on a canvas | proposed |
| 2026-10-10 | Two roles only: doctor and admin. The technician role is dropped; each patient belongs to the doctor who registered them, and an admin reads all patients but changes none | decided by Anish |
| 2026-10-12 | Login made simple for the test build: open doctor sign-up, one 7-day token in the browser, no refresh cookie, no rate limit, demo doctor created at startup. To be tightened before real patient data (`SECURITY.md`, section 2) | decided by Anish |
| 2026-10-09 | Hosting for the demo: API on Render (free plan, root directory `backend`), web app on Vercel, database on Supabase | decided by Anish |
