# Plan

Owner: everyone. Last updated: 2026-10-04.

This is the task list. Tick a box when the thing works, not when it is started. Update it in the same commit as the work.

## Team

| Person | Area | Folder |
|---|---|---|
| Anish | Backend, database, security | `backend/` |
| Pravesh | Models and inference | `ml/` |
| Nidhi | Web UI, mobile and desktop, spec document | `frontend/web/` |
| Soham | Pitch deck and demo | `docs/` |

## Milestones

| # | Milestone | Done when |
|---|---|---|
| M0 | Repo ready | First commit is on GitHub and all four can push |
| M1 | One flow works | Log in, create a patient, enter grip, upload an X-ray, see a result screen, all through the real API and database. The model output may be a placeholder. |
| M2 | Real pieces | Osteoporosis model, muscle ratios, sarcopenia rules, overlay, history graph, PDF report |
| M3 | Ready to show | Security checklist done, PWA installs, demo data loaded, backup video recorded, deck final |

M1 is reached: the flow runs through the web app, the API and the database, and the osteoporosis and KL grade models are connected. Local commits are pushed to GitHub.

M1 comes before making any single piece good. Joining the parts on the last day is how hackathon demos fail.

## Anish

Ticked items pass the tests in `backend/tests/` on SQLite.

- [x] FastAPI confirmed as the backend framework
- [ ] First commit and push (M0)
- [x] The API run against PostgreSQL (the Supabase development database)
- [x] `.env.example` written
- [x] The 9 tables in `DATABASE.md`
- [x] Auth: argon2, login, refresh with rotation, logout, me
- [x] Seed script: one admin, one doctor, one technician
- [x] Shared role dependency and audit dependency
- [x] Patient endpoints
- [x] Visit, clinical inputs, and grip endpoints
- [x] X-ray upload with size, type, and name checks (PNG and JPG)
- [x] X-ray and overlay served through authenticated endpoints
- [x] Analyze endpoint calling `ml/predict.py`, and result endpoint. Connected to the osteoporosis and KL grade models.
- [x] History endpoint
- [x] Doctor review endpoint
- [x] PDF report (made in the web app)
- [x] Test: each role is refused where `SECURITY.md` says No
- [x] Append-only triggers on `audit_logs`, checked on PostgreSQL
- [x] Name and phone encryption, with `phone_hash` for search
- [ ] Cloudinary copies of X-rays made private (`SECURITY.md` checklist item 17)
- [ ] DICOM uploads converted to PNG (only if DICOM upload is supported)
- [ ] `docker-compose.yml` with database, backend, and web (M3)

## Pravesh

- [ ] Write in `ML.md` what is being trained and on which dataset
- [ ] Overlap check between `main` and `external` for both tasks
- [ ] Osteoporosis classifier with metrics on internal and external test sets
- [x] Final model in `ml/models/`, row added to Results in `ML.md` (internal test only)
- [x] Preprocessing in `ml/predict.py` matches the training scripts, now in `ml/training/`
- [ ] Pravesh: train with stronger brightness augmentation; a 30% brighter copy of one image changed the tier
- [x] Muscle-mass and bone-loss models connected (`ml/tabular.py`), with waist, arm, and history inputs
- [x] Soft-tissue ratios and overlay from image processing (`ml/muscle.py`); shown, not used in the stage
- [ ] Pravesh: external test and overlap check for both models
- [ ] Pravesh: the bone-loss model flags almost everyone; raise its cutoff or retrain
- [ ] `ml/predict.py` with a function the backend can call (M1, a placeholder is fine at first)
- [ ] Muscle ratios with a threshold mask, and the overlay image
- [ ] Sarcopenia stage rules
- [ ] Heatmap (Grad-CAM)
- [ ] KL grade classifier (bonus)
- [ ] Time one analysis on a laptop CPU

## Nidhi

- [x] Web app in `frontend/web/`: app shell, dashboard, patient list, new patient, patient profile
- [x] Login and token handling against the backend
- [x] Screening wizard with one Run screening action (M1)
- [x] Results, report page, doctor review, PDF download
- [x] History graph
- [ ] Click through every screen in a browser and on a real phone, including the PDF download
- [ ] PWA manifest and icons
- [ ] Spec PDF: add the desktop app, remove the 13 leftover Bluetooth lines
- [ ] Optional: Tauri shell (`DESKTOP.md`), Capacitor shell (`MOBILE.md`)

## Soham

- [x] Deck: `docs/HackPulse - Codesharks.pdf`
- [ ] Fix the deck's claims listed under "Review of the current deck" in `PITCH.md`
- [ ] Architecture slide from `ARCHITECTURE.md`
- [ ] 3 to 5 sample X-rays for the demo, from the public datasets only
- [ ] Demo script
- [ ] Screenshots once M1 works
- [ ] Backup demo video
- [ ] Final check of every number on every slide against `ML.md`

## Working together

- Work in your own folder. If you need a change in someone else's, ask them.
- Work on a branch named `yourname/topic`. Merge into `main` at least once a day. Pull before you push.
- Small commits with a message that says what changed.
- Ten minutes every day: what is done, what is next, who is waiting on whom.
- When a change makes a doc wrong, fix the doc in the same commit.
- Never commit `.env`, datasets, zip files, real patient X-rays, or training checkpoints.

## Left out on purpose

Mobile app in React Native, Bluetooth dynamometer, Orthanc, FHIR, Celery and Redis, MinIO, multi-language UI, patient login. See "What we build first" in `ARCHITECTURE.md` for when each comes back.

## Open questions

| Question | Who decides |
|---|---|
| When is the submission deadline? | Team. The milestones have no dates until this is known. |
| Where does the demo run: a laptop or a cloud server? Files stay on local disk either way, with a Cloudinary copy if it is hosted. | Anish |
| Two AI assistants have edited `backend/` at the same time. Which one writes backend code from here on? | Anish |
| Do the judges need real installers, or is PWA install enough? | Team |
| Which value counts as "low muscle proxy"? | Pravesh |
